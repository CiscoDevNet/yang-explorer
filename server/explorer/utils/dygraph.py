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
from graphviz import Digraph

class DYModule(object):
    """
    Module class
    """
    def __init__(self, module):
        self.name = module.get('id', None)
        self.prefix = module.get('prefix', None)
        self.revisions = []
        self.imports = []
        self.includes = []
        self.depends = []
        self.namespace = None

        for child in module:
            if child.tag == 'namespace':
                self.namespace = child.text
            elif child.tag == 'prefix':
                self.prefix = child.text
            elif child.tag == 'revisions':
                for r in child:
                    self.revisions.append(r.get('date', ''))
            elif child.tag == 'imports':
                for i in child:
                    self.imports.append(i.get('module', ''))
            elif child.tag == 'includes':
                for i in child:
                    self.includes.append(i.get('module', ''))

    def __str__(self):
        _str = self.name + '@' + str(self.revisions) + ' -> [ '
        for i in self.imports:
            _str += str(i) + ' '
        _str += ']\n'
        for i in self.depends:
            _str += str(i) + ' '
        _str += ']\n'
        return _str

    def add_revision(self, rev):
        """ add revision statement """
        self.revisions.append(rev)

    def add_import(self, module):
        """ add import statement """
        self.imports.append(module)

    def add_prefix(self, prefix):
        """ add prefix statement """
        self.prefix = prefix

    def add_namespace(self, ns):
        """ add namespace statement """
        self.namespace = ns


class DYGraph(object):
    """
    Dependency graph
    """

    def __init__(self, filename):
        self.modules = {}
        logging.debug('Parsing %s !!' % filename)
        root = ET.parse(filename).getroot()

        for child in root:
            module = DYModule(child)
            self.modules[module.name] = module

        for name in self.modules:
            module = self.modules[name]
            for imp in module.imports:
                i_module = self.modules.get(imp, None)
                if i_module is None:
                    logging.warning('Dependent modules %s not found in dependency list !!' % imp)
                    continue
                if imp not in i_module.depends:
                    i_module.depends.append(name)

            for inc in module.includes:
                i_module = self.modules.get(inc, None)
                if i_module is None:
                    logging.warning('Included modules %s not found in dependency list !!' % inc)
                    continue
                if inc not in i_module.depends:
                    i_module.depends.append(name)

    def __str__(self):
        _str = ''
        for module in self.modules:
            _str += str(module)
        return _str

    def _apply_style(self, graph):
        """
        Apply css like styles to graphviz graph
        """

        styles = {
            'graph': {
                'fontsize': '16',
                'fontcolor': 'white',
                'bgcolor': '#333333',
                'rankdir': 'BT',
            },
            'nodes': {
                'fontname': 'Helvetica',
                'shape': 'rectangle',
                'fontcolor': 'white',
                'color': 'white',
                'style': 'filled',
                'fillcolor': '#006699',
            },
            'edges': {
                'style': 'dashed',
                'color': 'white',
                'arrowhead': 'open',
                'fontname': 'Courier',
                'fontsize': '12',
                'fontcolor': 'white',
            }
        }
        graph.graph_attr.update(
            ('graph' in styles and styles['graph']) or {})
        graph.node_attr.update(
            ('nodes' in styles and styles['nodes']) or {})
        graph.edge_attr.update(
            ('edges' in styles and styles['edges']) or {})
        return graph

    def dependency_module(self, yangfile):
        """
        Get dependency module object for given yang
        """
        module = os.path.basename(yangfile)
        modulename = module.split('.yang')[0]

        if '@' in modulename:
            modulename = modulename.split('@')[0]

        module = self.modules.get(modulename, None)
        return module

    def digraph(self, files=[]):
        """
        Create a graph object
        """
        modules = []
        for _file in files:
            module = os.path.basename(_file)
            modulename = module.split('.yang')[0]
            if '@' in modulename:
                modulename = modulename.split('@')[0]
            modules.append(modulename)

        title = modules[0] if len(modules) == 1 else 'Dependency Graph'
        return self._gen_graph(modules, title)

    def digraph_all(self):
        """
        Return graph for all modules
        """
        return self._gen_graph(self.modules.keys())

    def _gen_graph(self, modules, title='Dependency Graph'):
        """
        Invoke graphviz and generate graph
        """
        try:
            graph = Digraph(comment=title, strict=True, format='jpeg')
            logging.debug('Creating graph ..')
        except TypeError:
            logging.warning('graphviz module does not support strict graphs, please upgrade python graphviz !!')
            graph = Digraph(comment=title, format='jpeg')
        except:
            logging.error('Failed to create dependency graph !!')
            return None

        for name in modules:
            m = self.modules.get(name, None)
            if m is None:
                continue

            for imp in m.imports:
                graph.node(imp)
                graph.edge(name, imp)
            for inc in m.includes:
                graph.node(inc)
                graph.edge(name, inc)
            for dep in m.depends:
                graph.node(dep)
                graph.edge(dep, name)

        return self._apply_style(graph)
