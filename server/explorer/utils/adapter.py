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

import logging
import lxml.etree as ET
from explorer.utils.runner import NCClient

class Adapter(object):
    """ Class adapter for NCClient """

    @staticmethod
    def run_request(request):
        """
        Execute a RPC request using NCClient
        """

        request = ET.fromstring(request)
        rpc = None
        auth = None
        device = None
        for child in request:
            tag = child.xpath('local-name()')
            if tag == 'metadata':
                auth = child.find('netconf-auth')
                host = auth.get('host', None)
                port = int(auth.get('port', 830))
                user = auth.get('user', None)
                passwd = auth.get('passwd', None)
                dev = child.find('device-auth')
                device = dev.get('platform', None)
            elif tag == 'rpc':
                rpc = child

        if auth is None:
            logging.error("Device information is not provided in request payload")
            reply = ET.Element('reply')
            reply.text = 'Device info missing'
            return reply

        logging.debug("IP  : %s,  Port: %s" % (host, port))
        logging.debug("User: %s,  PWD:  %s" % (user, passwd))

        params = None
        if device is not None:
            params = {'name' : device}

        if rpc is None:
            session = NCClient(host, port, user, passwd, params)
            return session.get_capability()

        logging.debug("RPC: " + ET.tostring(rpc))
        session = NCClient(host, port, user, passwd, {'name': "csr"})
        return session.run(ET.tostring(rpc))
