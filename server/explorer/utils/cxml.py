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
            logging.debug('Parsing %s' % filename)
            try:
                self.cxml = ET.parse(filename)
            except:
                self.cxml = None
                logging.error('ET Failed to parse %s' % filename)
        else:
            self.cxml = None
            logging.error('File %s does not exists' % filename)

    def getroot(self):
        return self.cxml.getroot()

    def toxpath(self, path):
        if path:
            path_elems = path.split('/')
            xpath = '[@name="%s"]' % path_elems[0]
            for elem in path_elems[1:]:
                xpath += '/node[@name="%s"]' % elem
        else:
            xpath = '/'
        return xpath

    def toxpath_filter(self, path, prefix):
        """
        Returns an xpath filter that is used in RPCs.

        For example: module/node1/node2 -> /module_prefix:node1/node2
        YANG-Push subscribers use it to specify
        data of interest in establish-subscription RPCs.
        """
        if path and prefix:
            path_elems = path.split('/')
            xpath = path.replace(path_elems[0] + '/',
                                 '/' + prefix + ':', 1)
        else:
            xpath = ''
        return xpath

    def get_lazy_node_internal(self, cxml_element, base='', module_prefix=''):
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

        if base != '' and module_prefix != '':
            xpath_filter = self.toxpath_filter(base + cxml_element.get('name'),
                                               module_prefix)
            node.set('xpath_filter', xpath_filter)

        if add_placeholder:
            pnode = ET.Element('node')
            pnode.set('name', 'Loading ..')
            pnode.set('type', '__yang_placeholder')
            node.append(pnode)

        return node

    def get_lazy_node(self, path='', add_ns=True):
        """
        Returns yang explorer compatible lazy node xml. A lazy
        node only returns a cxml node which is requested. All
        other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        """
        logging.debug('get_lazy_node: ' + path)
        root = ET.Element('root')
        if self.cxml is None:
            return root

        cxml_root = self.getroot()

        if path == '':
            node = self.get_lazy_node_internal(cxml_root)
            nslist = [c.get('prefix') + ',' + c.text for c in cxml_root if c.tag == 'namespace']
            node.set('namespaces', '|'.join(nslist))
            node.set('name', self.modulename)
            root.append(node)
            return root

        module_prefix = cxml_root.get('prefix', '')

        # move root node to requested node
        elements = path.split('/')
        for name in elements[1:]:
            for child in cxml_root:
                if child.get('name', '') == name:
                    cxml_root = child
                    break

        for child in cxml_root:
            if child.tag == 'node':
                node = self.get_lazy_node_internal(child, path, module_prefix)
                root.append(node)

            if child.tag == 'namespace' and add_ns:
                if cxml_root.get('prefix', '') == child.get('prefix'):
                    child.set('default', 'true')
                root.append(child)
        return root

    def get_lazy_tree_one(self, path, value):
        """
        Returns yang explorer compatible lazy tree xml. A lazy
        tree  returns a cxml nested tree from root to requested
        node.

        Other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        """

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
        """
        Returns yang explorer compatible lazy tree xml. A lazy
        tree  returns a cxml nested tree from root to requested
        node.

        Other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        """

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
            level += 1
        # end while

        return tree

    def get_lazy_subtree(self, base, path):
        """
        Returns yang explorer compatible lazy subtree xml. A lazy
        tree  returns a cxml nested tree from base to requested
        node.

        Other node along the path returned as _placeholder_
        nodes for on-demand loading in client tree.
        """

        tree = self.get_lazy_node(base)
        if not path:
            return tree

        path_elems = path.split('/')
        xpath = ''
        subpath = base
        for elems in path_elems[1:]:
            subpath += '/' + elems
            logging.info('Query: ' + subpath)
            nodes = self.get_lazy_node(subpath)
            if not xpath:
                xpath = 'node[@name="%s"]' % elems
            else:
                xpath += '/node[@name="%s"]' % elems
            temp = tree.find(xpath)
            if temp is not None and nodes:
                tree.find(xpath).remove(tree.find(xpath)[0])
                for child in nodes:
                    tree.find(xpath).append(child)
            else:
                logging.error('Error: %s not found' % xpath)
                break
        return tree

    def get_namespaces(self):
        if self.cxml is None:
            return []

        return [(ns.get('prefix', ''), ns.get('module', ''), ns.text)
                for ns in self.cxml.getroot() if ns.tag == 'namespace']


class CxmlIterator(object):
    """ XPath Iterator for Cxml
        @params filename:string - cxml file path
        @params include-keys: bool - include keys in xpath
        @params include-prefixes:list - list of included namespaces/prefixes
        @params include-default:bool - include xpath with root-prefix
        @params add-root-prefix:bool - add root-prefix in xpath
    """
    def __init__(self, filename, cxml=None, options={}):
        if cxml:
            self.handle = cxml
        else:
            self.handle = ET.parse(filename)
        self.inc_keys = options.get('include-keys', False)
        self.inc_prefixes = options.get('include-prefixes', [])
        self.inc_default = options.get('include-default', False)
        self.add_root_prefix = options.get('add-root-prefix', False)
        self.current = self.handle.getroot()
        self.prefix = self.current.get('prefix', None)
        self.path = [self.current.get('name')]

    def __iter__(self):
        return self

    def reset(self):
        self.current = self.handle.getroot()
        self.prefix = self.current.get('prefix', None)
        self.path = [self.current.get('name')]

    def _get_next_parent(self):
        _parent = self.current.getparent()
        while _parent is not None:
            uncle = _parent.getnext()
            if uncle is None:
                _parent = _parent.getparent()
                self.path.pop()
                continue
            if self._filter(uncle):
                _parent = _parent.getparent()
                continue
            return uncle
        return _parent

    def _set_xpath(self):
        _name = self.current.get('name', None)

        # add keys in xpath if required
        if self.inc_keys and self.current.get('type', '') == 'list':
            _keys = self.current.get('key', '')
            _name += '[' + _keys + ']'

        # add default prefix in xpath if required
        if self.add_root_prefix and ':' not in _name:
            _name = self.prefix + ':' + _name

        # append to xpath list
        self.path.append(_name)

    def _get_prefix(self, node):
        name = node.get('name', None)
        return name.split(':')[0] if ':' in name else None

    def _filter(self, node):
        """ Filter xpath """
        if not self.inc_prefixes:
            return False

        pfx = self._get_prefix(node)
        if pfx is not None:
            return pfx not in self.inc_prefixes
        return False

    def next(self):
        # Depth First Traversal

        # Look for children first
        if len(self.current):
            for child in self.current.findall('node'):
                if self._filter(child):
                    continue
                self.current = child
                self._set_xpath()
                if self.has_prefix():
                    return '/'.join(self.path), self.current
                return self.next()

        # Look for siblings next
        _next = self.current.getnext()
        self.path.pop()
        while _next is not None:
            if self._filter(_next):
                _next = _next.getnext()
                continue
            self.current = _next
            self._set_xpath()
            if self.has_prefix():
                return '/'.join(self.path), self.current
            return self.next()

        # Look for parent last
        _parent = self._get_next_parent()
        if _parent is None:
            raise StopIteration()

        self.path.pop()
        if not self._filter(_parent):
            self.current = _parent
            self._set_xpath()

        if self.has_prefix():
            return '/'.join(self.path), self.current
        return self.next()

    def has_prefix(self):
        if not self.inc_prefixes:
            return True

        if self.inc_default:
            if self.add_root_prefix:
                if not any(not elem.startswith(self.prefix + ':') for elem in self.path[1:]):
                    return True
            else:
                if not any(':' in elem for elem in self.path[1:]):
                    return True

        for i_pfx in self.inc_prefixes:
            if any(elem.startswith(i_pfx + ':') for elem in self.path):
                return True
        return False


def get_cxml(filename):
    """ Create and return CXML object from File or LocalCache """
    cxml = Cxml(filename)
    return cxml
