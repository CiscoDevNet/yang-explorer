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


import logging
import xml.etree.ElementTree as ET
from explorer.utils.admin import ModuleAdmin

logging.basicConfig(level=logging.INFO)

rpc_xmlns = 'urn:ietf:params:xml:ns:netconf:base:1.0'
rpc_template = '''<rpc message-id="{msg_id}" xmlns="{rpc_ns}">
{msg_payload}
</rpc>'''


def build_rpc(request, payload, operation):

    source = request.get('source', 'running')
    target = request.get('target', 'candidate')

    if operation == 'get-config':
        datastore = '<source><' + source + '/></source>\n'
        payload = '<filter>\n' + payload + '</filter>\n'
        payload = '<get-config>\n' + datastore + payload + '</get-config>'
    elif operation == 'edit-config':
        datastore = '<target><' + target + '/></target>\n'
        payload = '<config xmlns:xc="' + rpc_xmlns  + '">\n' +  payload + '</config>\n'
        payload = '<edit-config>\n'  + datastore + payload + '</edit-config>'
    elif operation == 'get':
        payload = '<filter>\n' + payload + '</filter>\n'
        payload = '<get>\n' + payload + '</get>'

    return rpc_template.format(msg_id='101', rpc_ns=rpc_xmlns, msg_payload=payload)


def get_namespace(tree, prefix=''):
    module_prefix = tree.get('prefix', '')
    if prefix == '':
        prefix = module_prefix
    ns = ''
    for child in tree:
        if child.tag == 'namespace':
            pfx = child.get('prefix', '')
            if pfx == prefix:
                if module_prefix == pfx:
                    ns += ' xmlns="%s"' % child.text
                else:
                    ns += ' xmlns:%s="%s"' % (pfx, child.text)
        else:
            break
    return ns


def pop_keyvalue(d, path, mode):
    """ Extract path, value pair from dictionary and
        delete the list entry as we will processing
        this pair in current step

        Returns value and netconf operation pair.
    """
    index = 0
    for key in d:
        # leaf-list has '='' in path, extact path in this case
        _key = key[0].split('=')[0] if '=' in key[0] else key[0]
        if _key == path:
            obj = key[1]
            val = obj.value
            option = ''
            # ignore default edit config operation
            if mode == 'edit-config' and (obj.option not in ['', 'merge']):
                option = ' xc:operation="' + obj.option + '"'

            d.pop(index)
            return val, option, True
        index += 0
    return '', '', False


def process_terminal(tree, d, node, prefix, ns, mode):
    (val, option, found) = pop_keyvalue(d, prefix, mode)
    if not found:
        return ''

    if ':' in val:
        pfx = val.split(':')
        if len(pfx) > 1:
            ns = get_namespace(tree, pfx[0])

    name = node.get('name', '')
    if val != '':
        msg = '<' + name + ns + option + '>' + val + '</' + name + '>\n'
    else:
        msg = '<' + name + ns + option +'/>\n'

    return msg


def process_leaflist(tree, d, node, prefix, ns, mode):
    msg = ''
    _msg = process_terminal(tree, d, node, prefix, ns, mode)
    while _msg != '':
        msg += _msg
        _msg = process_terminal(tree, d, node, prefix, ns, mode)
    return msg


def process_xml(tree, d, node, prefix, ns, mode):
    name = node.get('name', '')
    type_ = node.get('type', '')
    prefix = prefix + '/' + name
    msg = ''

    if type_ == 'leaf-list':
        msg = process_leaflist(tree, d, node, prefix, ns, mode)
    elif type_ in ['leaf', 'leafref']:
        msg = process_terminal(tree, d, node, prefix, ns, mode)
    elif type_ in ['module','choice', 'case', 'input', 'output']:
        for child in node:
            msg += process_xml(tree, d, child, prefix, '', mode)
    elif type_ in ['list', 'container']:
        (val, option, found) = pop_keyvalue(d, prefix, mode)

        for child in node:
            msg += process_xml(tree, d, child, prefix, '', mode)

        if msg != '':
            msg = '<' + name + ns + option + '>\n' + msg + '</' + name + '>\n'
        elif found:
            msg = '<' + name + ns + option + '/>\n'
    else:
        logging.debug('processXML: UnknownType: ' + type_)

    return msg


class ValueObject:
    pass


class RPCRequestModule:
    def __init__(self, name):
        self.name = name
        self.kvDict = []
        self.prefixes = []

    def add_keyvalue(self, key, value):
        self.kvDict.append((key, value))

    def add_namespace_pfx(self, namespace):
        self.prefixes.extend(namespace)

    def get_namespace_pfx(self):
        return list(set(self.prefixes))

    def get_keyvalues(self):
        return self.kvDict

def parseRequest(request):
    keyvalue = request.find('keyvalue')
    modules = {}

    for child in keyvalue:
        logging.info('Node : <%s %s>%s' , child.tag, child.attrib, child.text)
        if child.tag != 'node':
            logging.error('Invalid node in the request data : %s' % child.tag)
            break
        path = child.get('path', '')
        name = path.split('/')[0]

        module = modules.get(name, None)
        if module is None:
            module = RPCRequestModule(name)
            modules[name] = module

        flag = child.get('flag', '')

        obj = ValueObject()
        obj.option = child.get('option', '')
        obj.value = ''
        if flag in ['get-config', 'get', 'empty']:
            module.add_keyvalue(path, obj)
        else:
            if child.text is not None:
                obj.value  = child.text
            module.add_keyvalue(path, obj)

        # add required namespace in a list
        namespace = [elem.split(':')[0] for elem in path.split('/') if ':' in elem]
        module.add_namespace_pfx(namespace)
    return modules


def convert_rpc(rpc, mode):
    """ Covert a edit-config RPC to get-config"""
    if not rpc:
        return rpc

    if mode == 'get-config':
        rpc = rpc.replace('<edit-config>', '<get-config>')
        rpc = rpc.replace('</edit-config>', '</get-config>')
        rpc = rpc.replace('<target>', '<source>')
        rpc = rpc.replace('<candidate/>', '<running/>')
        rpc = rpc.replace('</target>', '</source>')
        rpc = rpc.replace('<config ', '<filter ')
        rpc = rpc.replace('</config>', '</filter>')
        return rpc
    return rpc


def gen_netconf(username, request, mode):
    msg = ''
    rpc = ''

    _format = request.get('format', 'xpath')    
    if mode == '': mode = request.get('operation', '')

    logging.debug('Generating netconf RPC, operation : "%s" format: %s' % (mode, _format))
    
    if _format == 'raw':
        rpc = request.find('rpc').text
        rpc = rpc.replace('&gt;','>')
        rpc = rpc.replace('&lt;','<')
        return convert_rpc(rpc, mode)
    # Parse test-payload key-values pairs for each modules and
    # create a dictionary of modules.
    modules =  parseRequest(request)

    # Process each module key-value separatly
    for name in modules:
        module = modules[name]
        kvDict = module.get_keyvalues()
        logging.debug('Opening file %s.xml' % name)
        
        filename = ModuleAdmin.cxml_path(username, name)
        if filename is None:
            logging.debug('file %s.xml not found !!' % name)
            continue

        with open(filename, 'r') as f:
            tree = ET.parse(f).getroot()
            logging.info("Root node %s" % tree.get('name'))
            # get root namespace for module
            ns = get_namespace(tree)

            # get derived namespaces
            prefixes  = module.get_namespace_pfx()
            for pfx in prefixes:
                ns += get_namespace(tree, pfx)

            # start processing CXML
            for child in tree:
                if child.tag != 'namespace':
                    msg += process_xml(tree, kvDict, child, name, ns, mode)

    # Finally build RPC header
    rpc += build_rpc(request, msg, mode)
    logging.debug('Generated netconf RPC')
    logging.debug(rpc)
    return rpc


def get_rpc_from_request(request):
    _format = request.get('format', 'xpath')
    if _format == 'xpath':
        return None

    rpc = request.find('rpc').text
    rpc = rpc.replace('&gt;','>')
    rpc = rpc.replace('&lt;','<')
    return rpc
