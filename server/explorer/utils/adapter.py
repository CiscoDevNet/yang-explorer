"""
    Copyright 2015, Cisco Systems, Inc

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

    @author: Pravin Gohite, Cisco Systems, Inc.
    @author: Michael Ott, Cisco Systems, Inc.
"""

import json
import logging
from collections import OrderedDict
import lxml.etree as ET
from django.template.loader import render_to_string
from explorer.utils.netconf import gen_netconf
from explorer.utils.restconf import gen_restconf
from explorer.utils.runner import NCClient, RestClient
from explorer.utils.ncparse import NetconfParser

from ydk.app_maker import YdkAppMaker

class Adapter(object):
    """ Class adapter for NCClient """
    @staticmethod
    def parse_request(payload):
        """ Parse user request """
        request = ET.fromstring(payload)
        protocol = request.get('protocol', None)
        fmt = request.get('format', 'xpath')
        lock = request.get('lock-option', 'False') == 'True'
        rpc = None
        auth = {}
        for child in request:
            tag = child.xpath('local-name()')
            if tag == 'device-auth':
                auth['platform'] = child.get('platform', None)
            elif tag == 'netconf-auth':
                auth['host'] = child.get('host', None)
                auth['port'] = child.get('port', 830)
                if auth['port']:
                    auth['port'] = int(auth['port'])

                auth['user'] = child.get('user', None)
                auth['passwd'] = child.get('passwd', None)
            elif tag == 'raw':
                if protocol == 'netconf':
                    rpc = ET.fromstring(child.text)
                else:
                    rpc = child.text
            elif tag == 'keyvalue' and len(child):
                rpc = ''
        return protocol, auth, fmt, lock, rpc

    @staticmethod
    def run_request(username, payload):
        """
        Execute a RPC request using NCClient
        """
        logging.debug('run_request (%s)' % username)

        # hack
        payload = payload.replace('<metadata>', '')
        payload = payload.replace('</metadata>', '')

        protocol, device, fmt, lock, rpc = Adapter.parse_request(payload)
        if device.get('host', None) is None:
            reply = ET.Element('reply')
            reply.text = 'Device info missing'
            logging.error("Device information is not provided in request payload")
            return reply

        if fmt == 'xpath' and rpc == '':
            rpc = Adapter.gen_rpc(username, payload)

        logging.debug("run_request: Protocol %s, Host %s, Port %s, User %s" %
                      (protocol, device['host'], device['port'], device['user']))

        if protocol == 'netconf':
            return Adapter.run_netconf(username, device, rpc, lock)
        elif protocol == 'restconf':
            return Adapter.run_restconf(username, device, rpc)

        reply = ET.Element('reply')
        reply.text = 'Invalid protocol in the payload'
        return reply

    @staticmethod
    def run_netconf(username, device, rpc, lock=False):
        """ Execute Netconf request """

        plat = device.get('platform', None)
        if plat is not None and plat not in ['', 'other']:
            params = {'name' : plat}
        else:
            params = {}

        session = NCClient(device['host'], device['port'],
                           device['user'], device['passwd'], params)

        # If rpc is not provided, return capabilities
        if rpc is None or rpc == '':
            return session.get_capability()
        return session.run(rpc, lock)

    @staticmethod
    def run_restconf(username, device, msg):
        """ Execute Restconf request """

        session = RestClient(device)
        if session is None:
            reply = ET.Element('reply')
            reply.text = 'Could not create session for %s' % protocol
            return reply

        if isinstance(msg, str):
            msg = json.loads(msg)

        url = 'http://' + device['host'] + ':' + str(device['port'])
        if msg is None or msg  == '':
            return session.get_capability(url)

        msg['url'] = url + msg['url']
        return session.run(msg)

    @staticmethod
    def gen_rpc(username, payload):
        """
        Generate Netconf / Restconf RPC
        """
        if payload == '':
            logging.debug('gen_rpc: Rcvd: ' + 'None')
            return None

        logging.debug('gen_rpc: Rcvd: \n' + payload)

        request = ET.fromstring(payload)
        protocol = request.get('protocol', None)
        if protocol is None:
            logging.error('gen_rpc: Invalid payload, protocol missing !!')
            return None

        if protocol == 'restconf':
            res = Adapter._gen_rpc(username, request)
            ''' returns json '''
            return build_response(res)
        else:
            rpc = Adapter._gen_rpc(username, request)

        logging.debug('gen_rpc: Generated : \n' + rpc)

        ''' returns xml '''
        return ET.fromstring(rpc, parser=ET.XMLParser(remove_blank_text=True))

    @staticmethod
    def get_ydk_def_names(python_ydk_defs):
        """
        Get the Python YDK definition names
        """

        logging.debug('get_ydk_def_names: python_ydk_defs : \n' + python_ydk_defs)

        import re

        ydk_def_names = ""
        for m in re.finditer(r"def \w+()", python_ydk_defs):
            logging.debug('get_ydk_def_names: m.group(0): \n' + m.group(0))
            tmp_str = m.group(0).replace('def ', '')
            ydk_def_names = ydk_def_names + tmp_str + " "

        logging.debug('get_ydk_def_names: ydk_def_names : \n' + ydk_def_names)

        return ydk_def_names

    @staticmethod
    def gen_script(username, payload, target='ncclient'):
        if target == 'ydk':
            return Adapter.gen_ydk_script(username, payload)

        if target == 'ncclient':
            return Adapter.gen_ncclient_script(username, payload)

        logging.debug('gen_script: Invalid target %s\n' % str(target))
        return 'Invalid target %s for script gen' % str(target)


    @staticmethod
    def gen_ydk_script(username, payload):
        """
        Generate YDK python script that uses Netconf provider and Netconf/CRUD services 
        """

        logging.debug('gen_ydk_script: payload : \n' + payload)

        payload = payload.replace('<metadata>', '')
        payload = payload.replace('</metadata>', '')

        _, device, fmt, lock, rpc = Adapter.parse_request(payload)
        if fmt == 'xpath' and rpc == '':
            request = ET.fromstring(payload)
            logging.debug('gen_ydk_script: request etree string : \n' +
                          ET.tostring(request, pretty_print=True))

            rpc = Adapter._gen_rpc(username, request)

        if rpc is None:
            logging.error('gen_ydk_script: Invalid RPC Generated')
            return None

        logging.debug('gen_ydk_script: generated rpc : \n' + rpc)

        # currently we only support Netconf service provider and CRUD services
        parser = NetconfParser(rpc)
        op = parser.get_operation()
        datastore = parser.get_datastore()

        if datastore == None:
            datastore = ""

        logging.error('gen_ydk_script: datastore : \n' + datastore)

        python_ydk_defs = ""
        for child in parser.get_data():
            logging.debug('gen_ydk_script: child element : \n' + ET.tostring(child, pretty_print=True))

            # generate ydk script snippet for child element
            yam = YdkAppMaker(type='xml')
            python_ydk_defs = python_ydk_defs + yam.payload2python(ET.tostring(child))

        # TBD: auto-discover service type, currently hardcoded to 'netconf'
        #      change to 'crud' if you want to use crud
        service_type = 'netconf'

        # setup template args
        args = dict()

        args['service_type'] = service_type
        args['ydk_obj_defs'] = python_ydk_defs
        args['datastore'] = datastore

        if op == 'edit-config':
            # TBD: currently hardcoded to 'create' (to handle create or merge operation)
            #      Need to parse xc operations to set to other options such as 
            #      'replace' or 'delete' based on values of xc operations. This would
            #      have to be done on a per-node basis. 
            args['service'] = 'create'
        elif op == "get":
            args['service'] = 'get'
        elif op == "get-config":
            args['service'] = 'get_config'
        else:
            args['service'] = 'unsupported'

        args['host'] = device.get('host', '')
        args['port'] = device.get('port', '830')
        args['user'] = device.get('user', '')
        args['passwd'] = device.get('passwd', '')

        if not args['host']:
            args['host'] = '<address>'

        if not args['port']:
            args['port'] = '830'

        if not args['user']:
            args['user'] = '<username>'

        if not args['passwd']:
            args['passwd'] = '<password>'

        args['ydk_obj_names'] = Adapter.get_ydk_def_names(python_ydk_defs)

        # generate script
        rendered = render_to_string('ydkscript.py', args)
        script = ET.Element('script')
        script.text = ET.CDATA(rendered)
        return script

    @staticmethod
    def gen_ncclient_script(username, payload):
        """
        Generate Netconf / Restconf RPC
        """
        payload = payload.replace('<metadata>', '')
        payload = payload.replace('</metadata>', '')

        _, device, fmt, lock, rpc = Adapter.parse_request(payload)
        if fmt == 'xpath' and rpc == '':
            rpc = Adapter.gen_rpc(username, payload)

        if rpc is None:
            logging.error('gen_script: Invalid RPC Generated')
            return None

        parser = NetconfParser(rpc)
        op = parser.get_operation()
        data = ET.tostring(parser.get_data(), pretty_print=True)
        datastore = parser.get_datastore()

        # setup template args
        args = dict()
        args['data'] = data.strip()
        args['datastore'] = datastore
        args['host'] = device.get('host', '')
        args['port'] = device.get('port', '830')
        args['user'] = device.get('user', '')
        args['passwd'] = device.get('passwd', '')
        args['platform'] = device.get('platform', '')

        if not args['host']:
            args['host'] = '<address>'

        if not args['user']:
            args['user'] = '<username>'

        if not args['passwd']:
            args['passwd'] = '<password>'

        if not args['platform']:
             args['platform'] = 'csr'

        if op == 'get':
            args['nccall'] = 'm.get(payload).xml'
        elif op == 'get-config':
            args['nccall'] = "m.get_config(source='%s', filter=payload).xml" % datastore
        elif op == 'edit-config':
            e_opt = parser.get_error_option()
            if e_opt is None or e_opt == '':
                args['nccall'] = "m.edit_config(target='%s', config=payload).xml" % datastore
            else:
                args['nccall'] = "m.edit_config(target='%s', error_option='%s', config=payload).xml" % (datastore, e_opt)
            args['lock'] = lock
        else:
            args['nccall'] = "m.dispatch(ET.fromstring(payload)).xml"

        # generate script
        rendered = render_to_string('pyscript.py', args)
        script = ET.Element('script')
        script.text = ET.CDATA(rendered)
        return script

    @staticmethod
    def _gen_rpc(username, request, mode = ''):
        """ Wrapper for rest & netconf module """
        protocol = request.get('protocol', '')
        if mode == '': mode = request.get('operation', '')

        # Generate RESTCONF
        if protocol == 'restconf':
            return gen_restconf(username, request, mode)

        # Generate NETCONF
        return gen_netconf(username, request, mode)


def build_response(res):
    rest_ops = {"merge": "PATCH",
                "create": "POST",
                "replace": "PUT",
                "delete": "DELETE",
                "get": "GET"}
    msg = OrderedDict()
    for r in res:
        op, url, data, hdr = r
        msg['method'] = str(rest_ops.get(op, op))
        msg['url'] = url
        msg['params'] = hdr
        msg['data'] = json.loads(data, object_pairs_hook=OrderedDict)

    reply = json.dumps(msg, indent=3, separators=(',', ': '))
    logging.debug('Json: ' + reply)
    return reply
