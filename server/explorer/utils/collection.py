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
import glob
import lxml.etree as ET
import logging
from collections import defaultdict
from explorer.models import Collection as Col
from explorer.models import User
from explorer.utils.dygraph import DYGraph
from explorer.utils.cxml import Cxml

class Collection(object):
    ''' This class implements utility routines to work with
    collections '''

    @staticmethod
    def add(metadata, payload):
        ''' Add a collection entry '''
        if metadata in [None, '']:
            logging.error('Invalid metadata')
            return False

        if payload in [None, '', 'null']:
            logging.error('Invalid payload')
            return False

        metadata = ET.fromstring(metadata)
        payload = ET.fromstring(payload)

        logging.debug(ET.tostring(metadata))
        logging.debug(ET.tostring(payload))

        cname = metadata.find('collection').text
        author = metadata.find('author').text
        name = metadata.find('name').text
        if not Col.objects.filter(name=cname).exists():
            if not User.objects.filter(username=author).exists():
                logging.error('User %s does not exist !!' % author)
                return False

            user = User.objects.filter(username=author)
            obj = Col(name=cname, user=user)
            obj.save()
            logging.debug('Created new collection ' + cname)

        path = os.path.join('data', 'collections', cname)
        if not os.path.exists(path):
            logging.error('Path to collection does not exist : %s !!' % path)
            return False

        for child in payload:
            if child.tag == 'metadata':
                for elem in metadata:
                    child.append(elem)

        cfile = os.path.join(path, name + '.xml')
        with open(cfile, 'w') as f:
            f.write(ET.tostring(payload))

        logging.debug('%s was saved successfully in collection %s' % (name, cname))
        return True

    @staticmethod
    def remove(metadata):
        ''' Remove a entry from collection '''
        if metadata is None or metadata == '':
            logging.error('Invalid metadata')
            return False

        metadata = ET.fromstring(metadata)
        cname = metadata.find('collection').text
        name = metadata.find('name').text

        if name is None or not name:
            logging.error('Invalid entry %s in argument!!' % name)
            return False

        if not Col.objects.filter(name=cname).exists():
            logging.debug('Collection %s does not exists !!' % cname)
            return True

        path = os.path.join('data', 'collections', cname, name + '.xml')
        if not os.path.exists(path):
            logging.debug('Path to collection does not exist : %s !!' % path)
            return True

        os.remove(path)
        logging.debug('%s was successfully removed from collection %s' % (name, cname))
        return True

    @staticmethod
    def list():
        """ get list of all collection entries """

        cols_elem = ET.Element('collections')
        for col in Col.objects.all():
            path = os.path.join('data', 'collections', col.name)
            if not os.path.exists(path):
                logging.error('Collection has inconstancy : %s !!' % col.name)
                continue
            files = glob.glob(os.path.join(path, '*'))
            for _file in files:
                payload = ET.parse(_file)
                for child in payload.getroot():
                    if child.tag == 'metadata':
                        cols_elem.append(child)

        return cols_elem

    @staticmethod
    def load(metadata):
        """ Load a collection entry """

        if metadata is None or metadata == '':
            logging.error('Invalid metadata')
            return False

        metadata = ET.fromstring(metadata)
        cname = metadata.find('collection').text
        name = metadata.find('name').text

        if not Col.objects.filter(name=cname).exists():
            logging.debug('Collection %s does not exists !!' % cname)
            return False

        _file = os.path.join('data', 'collections', cname, name + '.xml')
        if not os.path.exists(_file):
            logging.error('Collection entry not found')
            return False

        payload = ET.parse(_file).getroot()
        resp = process_collection(payload)
        return resp

def _get_tag(elem):
    if '{' in elem.tag:
        v = elem.tag.split('}')
        return (v[1], v[0].split('{')[1])
    return (elem.tag, None)

def _find_child(node, tag):
    for child in node:
        if child.xpath('local-name()') == tag:
            return child
    return None

def process_collection(payload):
    if payload is None:
        return None

    logging.debug("process_collection: enter..")
    for child in payload:
        tag = child.xpath('local-name()')
        if tag == 'metadata':
            user = process_metadata(child)
        elif tag == 'rpc':
            return process_netconf(child, user)
        else:
            logging.debug("process_collection: Unexpected tag " + child.tag)
    return None

def process_metadata(metadata):
    user = metadata.find('author')
    return user.text

def process_netconf(rpc, user):
    logging.debug("process_netconf: enter")
    for child in rpc:
        rpc_op = child.xpath('local-name()')
        if rpc_op == 'edit-config':
            payload = _find_child(child, 'config')
        elif rpc_op in ['get-config', 'get']:
            payload = _find_child(child, 'filter')
        else:
            rpc_op = 'rpc'
            payload = rpc

    return process_netconf_payload(payload, rpc_op, user)

def process_netconf_payload(payload, mode, user):
    logging.debug("process_netconf_payload: enter (mode: %s, user %s)" % (mode, user))
    if payload is None:
        logging.error('process_netconf_payload: Invalid RPC')
        return None

    modules = defaultdict(list)
    dfile = os.path.join('data', 'users', user, 'yang', 'dependencies.xml')
    dgraph = DYGraph(dfile)

    for child in payload:
        namespace = _get_tag(child)[1]
        module = dgraph.get_module_by_namespace(namespace)
        if module is None:
            logging.waring("process_netconf_payload: module not found for ns -> " + namespace)
            continue
        build_keyvalues(child, mode, module.get_modulename(), modules)
    return build_tree(modules, user)


def build_keyvalues(payload, mode, modulename, modules):
    # build key-value pair for rpc
    kv_pairs = []

    # build top level path <modulename> / <top-node>
    path = modulename + '/' + _get_tag(payload)[0]
    if build_xpaths(payload, mode, path, kv_pairs):
        if mode in ['get', 'get-config', 'rpc']:
            kv_pairs.append((path, {'value': '<' + mode +'>'}))

    # update xpaths in modules dictionary
    if modulename not in modules:
        modules[modulename] = kv_pairs
    else:
        modules[modulename].extend(kv_pairs)

def _build_value(val, mode):
    rval = '<' + mode + '>'
    if mode == 'edit-config':
        if val is None or val == '':
            rval = '<empty>'
        else:
            rval = val
    return rval

def build_xpaths(rpc, mode, path, kv_pairs):
    """ Build path value pair """
    if len(rpc) == 0:
        val = rpc.text
        if val is not None and val != '':
            kv_pairs.append((path, {'value': val}))
            return True
        else:
            kv_pairs.append((path, {'value': _build_value(val, mode)}))
        return False

    insert_op = ''
    for child in rpc:
        has_key = build_xpaths(child, mode, path + '/' + _get_tag(child)[0], kv_pairs)
        if has_key and mode in ['get', 'get-config', 'rpc']:
            insert_op = '<' + mode + '>'

    if insert_op:
        kv_pairs.append((path, {'value': insert_op}))
    return False

def build_tree(modules, user):
    """ Build lazy tree from keyvalue dictionary"""
    tree = ET.Element('module')
    for name in modules:
        filename = os.path.join('data', 'users', user, 'cxml', name + '.xml')
        if not os.path.exists(filename):
            continue
        cxml = Cxml(filename)
        logging.debug('build_tree: (path, value) = (%s, %s)' % modules[name][0])
        tree.append(cxml.get_lazy_tree(modules[name]))

    module_tree = ET.Element('module-tree')
    module_tree.append(tree)
    return module_tree
