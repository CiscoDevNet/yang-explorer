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
import logging
import lxml.etree as ET

class Cxml:
    def __init__(self, filename):
        self.filename = filename
        self.modulename = os.path.splitext(os.path.basename(filename))[0]
        if os.path.exists(filename):
            self.cxml = ET.parse(filename)
        else:
            self.cxml = None
            logging.error('File %s does not exists' % filename)

    def toxpath(self, path):
        path_elems = path.split('/')
        xpath = '[@name="%s"]' % path_elems[0]
        for elem in path_elems[1:]:
            xpath += '/node[@name="%s"]' % elem
        return xpath

    def get_lazy_node_internal(self, cxml_element, base=''):
        node = ET.Element('node')
        add_placeholder = True

        # Add attributes from cxml node
        for attrib in cxml_element.attrib:
            node.set(attrib, cxml_element.attrib[attrib])
            # Terminal nodes does not requires to lazy nodes.
            if (attrib == 'type' and cxml_element.attrib[attrib] in \
                ['leaf', 'leafref', 'leaf-list']):
                add_placeholder = False
        try:
            desc = cxml_element.find('description')
            if desc is not None:
                node.set('description', desc.text.strip())
        except:
            pass

        if base == '':
            node.set('path', self.modulename)
        else:
            base += '/'
            node.set('path', base + cxml_element.get('name'))

        if add_placeholder:
            pnode = ET.Element('node')
            pnode.set('name', 'Loading ..')
            pnode.set('type', '__yang_placeholder')
            node.append(pnode)

        return node

    def get_lazy_node(self, path='', add_ns=True):
        '''
        Returns yang explorer compatible lazy node xml. A lazy
        node only returns a cxml node which is requested. All
        other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        '''
        logging.debug('get_lazy_node: ' + path)
        cxml_root = self.cxml.getroot()
        root = ET.Element('root')
        if path == '':
            node = self.get_lazy_node_internal(cxml_root)
            nslist = [c.get('prefix') + ',' + c.text for c in cxml_root if c.tag == 'namespace']
            node.set('namespaces', '|'.join(nslist))
            node.set('name', self.modulename)
            root.append(node)
            return root

        #move root node to requested node
        elements = path.split('/')
        for name in elements[1:]:
            for child in cxml_root:
                if child.get('name', '') == name:
                    cxml_root = child
                    break

        for child in cxml_root:
            if child.tag == 'node':
                node = self.get_lazy_node_internal(child, path)
                root.append(node)

            if child.tag == 'namespace' and add_ns:
                if cxml_root.get('prefix', '') == child.get('prefix'):
                    child.set('default', 'true')
                root.append(child)
        return root

    def get_lazy_tree_one(self, path, value):
        '''
        Returns yang explorer compatible lazy tree xml. A lazy
        tree  returns a cxml nested tree from root to requested
        node.

        Other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        '''

        tree = None
        path_elems = path.split('/')
        subpath = xpath = ''

        for elems in path_elems:
            nodes = self.get_lazy_node(subpath)
            if tree is None:
                tree = nodes.find('node')
                xpath = '[@name="%s"]' % elems
                logging.info(ET.tostring(tree))
            else:
                subpath += '/'

                temp = tree.find(xpath)
                if temp is not None:
                    tree.find(xpath).remove(tree.find(xpath)[0])
                    for child in nodes:
                        if child.get('path') == path:
                            child.set('value', value)
                        tree.find(xpath).append(child)

                xpath += '/node[@name="%s"]' % elems
            subpath += elems

        return tree

    def get_lazy_tree(self, pathvalues):
        '''
        Returns yang explorer compatible lazy tree xml. A lazy
        tree  returns a cxml nested tree from root to requested
        node.

        Other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        '''

        logging.debug('get_lazy_tree: Building lazy tree..')

        plist = []
        vdict = {}
        for (path, value) in pathvalues:
            plist.append(path.split('/'))
            vdict[path] = value

        level = 0
        logging.info(str(plist))

        tree = self.get_lazy_node()
        tree = tree[0]

        while True:
            pending = []
            for path_elems in plist:
                if level >= len(path_elems):
                    continue

                cxpath = '/'.join(path_elems[:level + 1])
                if cxpath not in pending:
                    pending.append(cxpath)

            if len(pending) == 0:
                break

            for cxpath in pending:
                subtree = self.get_lazy_node(cxpath, False)
                xpath = self.toxpath(cxpath)

                if len(subtree) == 0:
                    continue

                tree.find(xpath).remove(tree.find(xpath)[0])
                for child in subtree:
                    cpath = child.get('path', '')
                    values = vdict.get(cpath, '')
                    if values is not None:
                        for key in values:
                            child.set(key, values[key])
                    tree.find(xpath).append(child)
            level = level + 1
        #end while

        return tree

    def get_namespaces(self):
        return [(ns.get('prefix', ''), ns.get('module', ''), ns.text) \
         for ns in self.cxml.getroot() if ns.tag == 'namespace']
