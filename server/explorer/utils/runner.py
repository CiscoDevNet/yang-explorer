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
"""

import os
import json
import requests
import logging
import lxml.etree as ET
from ncclient import manager
from ncclient.operations import RPCError


class NotConnectedError(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr('NotConnectedError:' + self.value)


class InvalidNetConfRPC(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr('InvalidNetConfRPC:' + self.value)


class NCClient(object):
    """ NCClient wrapper class """

    def __init__(self, host, port, user, password, params):
        self.host = host
        self.port = port
        self.username = user
        self.password = password
        self.params = params
        self.handle = None
        logging.debug('__init__: ' + self.__str__())

    def __str__(self):
        return 'Host: %s, Port: %d, Username: %s, Params %s' % \
               (self.host, self.port, self.username, self.params)

    def _getchild(self, payload, tags):
        """ get child tag """

        for child in payload:
            if child.xpath('local-name()') in tags:
                return child
        return None

    def _get_datastore(self, payload):
        """ Get datastore name from payload """

        dsnode = self._getchild(payload, ['source', 'target'])
        if dsnode is not None:
            return dsnode.getchildren()[0].xpath('local-name()')
        return None

    def _is_connected(self):
        """ Check if session is connected """

        return self.handle is not None

    def _unknown_host_cb(self, host, fp):
        return True

    def connect(self):
        """ Establish netconf session """

        try:
            # timeout is configurable as environment variable
            timeout = int(os.getenv("NCCLIENT_TIMEOUT", 30))
            self.handle = manager.connect(host=self.host,
                                          port=self.port,
                                          username=self.username,
                                          password=self.password,
                                          device_params=self.params,
                                          unknown_host_cb=self._unknown_host_cb,
                                          look_for_keys=False,
                                          timeout=timeout)
        except:
            logging.exception("Failed to create netconf session:")
            self.handle = None
            return False

        logging.debug("Connected: %s" % self.__str__())
        return True

    def execute(self, payload):
        """ Execute RPC """

        rpc = ET.fromstring(payload)
        logging.debug("SEND: \n========\n%s\n========\n" % ET.tostring(rpc, pretty_print=True))
        for action in rpc:
            try:
                reply = self.handle.dispatch(action)
            except RPCError as e:
                reply = e.info
        return str(reply)

    def run(self, payload):
        """ Entry routing for this class """

        if payload is None or payload == '':
            raise InvalidNetConfRPC('Invalid RPC message!!')

        reply = ET.Element('reply')
        if not self._is_connected():
            if not self.connect():
                reply.text = 'NetConf Session could not be established {%s}' % str(self)
                return reply

        result = self.execute(payload)
        if result is None:
            reply.text = 'Failed to get reply !!'
            logging.error(reply.text)
        else:
            try:
                response = ET.fromstring(result)
                reply.append(response)
                logging.debug("RECEIVE: \n=====\n%s\n=====\n" % ET.tostring(response, pretty_print=True))
            except:
                reply.text = 'No data received from netconf agent (device)'
                logging.exception('Faild to encode to XML: ' + str(result))

        self.disconnect()
        return reply

    def get_capability(self):
        """ Returns device capabilities """

        logging.debug('get_capability ..')
        reply = ET.Element('reply')
        if not self._is_connected():
            if not self.connect():
                reply.text = 'NetConf Session could not be established {%s}' % str(self)
                return reply

        self.disconnect()
        caps = self.handle.server_capabilities
        if caps:
            reply.text = '\n'.join(caps)
            logging.info('Received device capabilities ..')
        return reply

    def disconnect(self):
        """ Disconnect netconf session """

        if self.handle is not None:
            self.handle.close_session()
            logging.debug("Disconnected: %s" % self.__str__())


class RestClient(object):
    def __init__(self, device):
        self.device = device
        self.auth = requests.auth.HTTPBasicAuth(device['user'],device['passwd'])
        logging.debug('__init__: ' + self.__str__())

    def get_capability(self, url):
        reply = ET.Element('reply')
        reply.text = 'Not-Implemented'
        return reply

    def run(self, msg):
        method = msg['method']
        url = msg['url']
        params = msg['params']
        payload = msg['data']
        reply = ET.Element('reply')

        logging.info("@%s %s" % (method, url))

        try:
            if method in ['GET', 'DELETE']:
                method_func =  eval('requests.' + method.lower())
                response = method_func(url, headers=params, auth=self.auth)
            elif method in ['POST', 'PUT', 'PATCH']:
                method_func =  eval('requests.' + method.lower())
                response = method_func(url, data=json.dumps(payload), headers=params, auth=self.auth)
            else:
                reply.text = 'Invalid Rest Method ' + method
                logging.error(reply.text)
                return reply

            msg = '@%s %s %s\n' % (method, url, 'OK' if response.ok else 'ERROR')
            msg += 'Status Code: ' + str(response.status_code) + '\n'
            if response.content:
                msg += 'Content: ' + response.content
        except:
            logging.exception('Restconf Request Aborted : ')
            msg = '@%s %s %s\n' % (method, url, 'ABORTED')
            msg += 'Content: ' + 'Exception while running request, please verify'
            msg += 'device restconf ip, port, authentication parameters !!'

        reply.text = msg
        logging.debug(msg)
        return reply
