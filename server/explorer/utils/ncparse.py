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

import lxml.etree as ET


class NetconfParser(object):
    """ Netconf Utility Class """
    def __init__(self, rpc):
        if isinstance(rpc, str):
            self.rpc = ET.fromstring(rpc)
        else:
            self.rpc = rpc

    def __repr__(self):
        return '%s(%r, %r, %r)' % (self.__class__.__name__, self.rpc.__class__.__name__)

    def __str__(self):
        return ET.tostring(self.rpc, pretty_print=True)

    def get_namespace(self):
        """ Return netconf version namespace """
        if self.rpc.tag.startswith('{'):
            return self.rpc.tag.split('}')[0].split('{')[1]

    def get_operation(self):
        """ Return netconf operation from rpc """
        return NetconfParser._get_tag(self.rpc[0])

    def get_datastore(self):
        """ Return netconf datastore from rpc """
        op = self.get_operation()
        ns = self.get_namespace()
        if op == 'edit-config':
            target = self.rpc.find('{%s}edit-config/{%s}target' % (ns,ns))
            return NetconfParser._get_tag(target[0])
        if op == 'get-config':
            source = self.rpc.find('{%s}get-config/{%s}source' % (ns,ns))
            return NetconfParser._get_tag(source[0])
        return None

    def get_error_option(self):
        """ Return netconf datastore from rpc """
        op = self.get_operation()
        ns = self.get_namespace()
        print self
        if op == 'edit-config':
            option = self.rpc.find('{%s}edit-config/{%s}error-option' % (ns,ns))
            if option is not None:
                return option.text
        return None

    def get_data(self):
        """ Return netconf data from rpc """
        op = self.get_operation()
        ns = self.get_namespace()
        if op in ['edit-config']:
            return self.rpc.find('{%s}edit-config/{%s}config' % (ns, ns))
        if op in ['get-config']:
            return self.rpc.find('{%s}get-config/{%s}filter' % (ns, ns))
        if op in ['get']:
            return self.rpc.find('{%s}get/{%s}filter' % (ns, ns))
        return self.rpc[0]

    @staticmethod
    def _get_tag(elem):
        if elem.tag.startswith('{'):
            return elem.tag.split('}')[1]
        return elem.tag


if __name__ == '__main__':
    rpc = """
<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <edit-config>
    <target>
      <running/>
    </target>
    <config>
      <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
        <interface>
          <name>Gi1</name>
        </interface>
      </interfaces>
    </config>
  </edit-config>
</rpc>
"""
    p = NetconfParser(rpc)
    assert p.get_namespace() == 'urn:ietf:params:xml:ns:netconf:base:1.0'
    assert p.get_operation() == 'edit-config'
    assert p.get_datastore() == 'running'
    assert p.get_data()[0].tag == '{urn:ietf:params:xml:ns:yang:ietf-interfaces}interfaces'