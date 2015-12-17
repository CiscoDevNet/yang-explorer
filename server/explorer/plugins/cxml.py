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

import optparse
import sys
import re
import string
from pyang import types
from pyang import plugin
from pyang import statements
import xml.etree.ElementTree as ET
#from lxml import etree as ET

def CDATA(text=None):
    element = ET.Element('![CDATA[')
    element.text = text
    return element

ET._original_serialize_xml = ET._serialize_xml


def _serialize_xml(write, elem, encoding, qnames, namespaces):
    if elem.tag == '![CDATA[':
        write("<%s%s]]>%s" % (elem.tag, elem.text, elem.tail))
        return
    return ET._original_serialize_xml(
         write, elem, encoding, qnames, namespaces)
ET._serialize_xml = ET._serialize['xml'] = _serialize_xml

def pyang_plugin_init():
    plugin.register_plugin(CxmlPlugin())

class CxmlPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['cxml'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--cxml-help",
                                 dest="cxml_help",
                                 action="store_true",
                                 help="Print help on cxml symbols and exit"),
            ]
        g = optparser.add_option_group("CXML output specific options")
        g.add_options(optlist)

    def setup_ctx(self, ctx):
        if ctx.opts.tree_help:
            print_help()
            sys.exit(0)

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False

    def emit(self, ctx, modules, fd):
        if ctx.opts.tree_path is not None:
            path = string.split(ctx.opts.tree_path, '/')
            if path[0] == '':
                path = path[1:]
        else:
            path = None

        cxml = Cxml(modules, fd, path)
        cxml.emit_cxml()

def print_help():
    print("""
    pyang -f cxml [option] <yang>
""")

class Cxml:
    def __init__(self, modules, fd, path):
        self.identity_deps = {}
        self.module_namespaces = {}
        self.module_prefixes = {}
        self.modules = modules
        self.fd = fd
        self.path = path
        self.name = self.modules[-1].arg

        if not self.modules[-1].search_one('prefix'):
            return

        for module in self.modules[0].i_ctx.modules.values():
            if module.keyword == "module":
                uri = module.search_one("namespace").arg
                self.module_namespaces[module.arg] = uri
                imports = module.search('import')

                related = False
                #build prefix to import modulename map
                i_prefixes = {}
                for i in imports:
                    #indirect dependancies
                    if i.arg == self.name:
                        related = True
                    pfx = i.search_one('prefix')
                    if pfx is not None:
                        i_prefixes[pfx.arg] = i.arg + ':'
                        # direct imports
                        if module.arg == self.name:
                            self.add_prefix(i, True)

                self.add_prefix(module, False)

                for idn in module.i_identities.values():
                    curr_idn = module.arg + ':' + idn.arg
                    base_idn = idn.search_one("base")
                    if base_idn:
                        #identity has a base
                        base_idns = base_idn.arg.split(':')
                        if len(base_idns) > 1:
                            #base is located in other modules
                            b_idn = i_prefixes.get(base_idns[0], '') + base_idns[1]
                        else:
                            b_idn = module.arg + ':' + base_idn.arg

                        if self.identity_deps.get(b_idn, None) is None:
                            self.identity_deps.setdefault(b_idn, [])
                        #print 'Adding %s -> %s' % (b_idn, curr_idn)
                        self.identity_deps[b_idn].append(curr_idn)
                    else:
                        self.identity_deps.setdefault(curr_idn, [])

    def add_prefix(self, module, direct):
        name = module.arg
        pfx  = module.search_one('prefix')
        if pfx is None:
            return
        pfx_str = pfx.arg
        prefix = self.module_prefixes.get(name, None)
        if prefix is None or direct:
            self.module_prefixes[module.arg] = (pfx_str, direct)

    def make_node(self, name):
        node = ET.Element('node')
        node.set('name', name)
        return node

    def emit_cxml(self):
        fd = self.fd
        path = self.path
        module = self.modules[-1]
        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs if ch.arg == path[0]]
            path = path[1:]

        prefix = module.search_one('prefix')
        if not prefix:
            return

        module_node = self.make_node(module.arg)
        module_node.set('prefix', prefix.arg)
        module_node.set('type', 'module')

        for name in self.module_prefixes:
            (pfx, direct) = self.module_prefixes[name]
            namespace = ET.Element('namespace')
            namespace.set('prefix', pfx)
            namespace.set('module', name)
            namespace.set('import', (str(direct)).lower())
            namespace.text = self.module_namespaces[name]
            module_node.append(namespace)

        if len(chs) > 0:
            self.print_children(chs, module, module_node, path, 'data')

        rpcs = [ch for ch in module.i_children if ch.keyword == 'rpc']
        if path is not None:
            if len(path) > 0:
                rpcs = [rpc for rpc in rpcs if rpc.arg == path[0]]
                path = path[1:]
            else:
                rpcs = []
        if len(rpcs) > 0:
            self.print_children(rpcs, module, module_node, path, 'rpc')

        notifs = [ch for ch in module.i_children if ch.keyword == 'notification']
        if path is not None:
            if len(path) > 0:
                notifs = [n for n in notifs if n.arg == path[0]]
                path = path[1:]
            else:
                notifs = []
        if len(notifs) > 0:
            self.print_children(notifs, module, module_node, path, 'notification')

        #fd.write(ET.tostring(module_node, pretty_print=True))
        fd.write(ET.tostring(module_node))

    def print_children(self, i_children, module, parent, path, mode):
        for ch in i_children:
            if ((ch.keyword == 'input' or ch.keyword == 'output') and
                len(ch.i_children) == 0):
                continue

            if ch.keyword in ['input', 'output']:
                mode = ch.keyword
            self.print_node(ch, module, parent, path, mode)

    def print_node(self, s, module, parent, path, mode):
        if s.i_module.i_modulename == module.i_modulename:
            name = s.arg
        else:
            name = s.i_module.i_prefix + ':' + s.arg

        flags = self.get_flags_str(s, mode)
        node = self.make_node(name)
        if flags is not None:
            node.set(flags[0], flags[1])

        node.set('type', s.keyword)
        if s.keyword == 'list':
            if s.search_one('key') is not None:
                node.set('key', s.search_one('key').arg)
        elif s.keyword == 'container':
            p = s.search_one('presence')
            if p is not None:
                node.set('presence', 'true')
        elif s.keyword  == 'choice':
            m = s.search_one('mandatory')
            if m is None or m.arg == 'false':
                node.set('mandatory', 'true')

            d = s.search_one('default')
            if d is not None:
                node.set('default', d.arg)

            values = self.type_choice_values(s)
            if values:
                node.set('values', values)
        elif s.keyword in ['leaf', 'leaf-list']:
            typename = self.get_typename(s)
            node.set('datatype', typename)

            m = s.search_one('mandatory')
            if m is not None and m.arg == 'true' or hasattr(s, 'i_is_key'):
                node.set('mandatory', 'true')

            if hasattr(s, 'i_is_key'):
                node.set('is_key', 'true')

            d = s.search_one('default')
            if d is not None:
                node.set('default', d.arg)

            t = s.search_one('type')
            if t is not None:
                tv = self.type_values(t)
                if tv != '':
                    node.set('values', tv)

        description = self.get_description(s)
        if description != '':
            desc = description.replace('<', '&lt')
            desc += description.replace('>', '&gt')
            cdata = ET.Element('![CDATA[')
            cdata.text = desc
            desc_node = ET.Element('description')
            desc_node.append(cdata)
            node.append(desc_node)

        parent.append(node)
        if hasattr(s, 'i_children'):
            chs = s.i_children
            if path is not None and len(path) > 0:
                chs = [ch for ch in chs if ch.arg == path[0]]
                path = path[1:]
            self.print_children(chs, module, node, path, mode)

    def get_status_str(self, s):
        status = s.search_one('status')
        if status is None or status.arg == '':
            return ('status', 'current')
        elif status.arg in ['current', 'deprecated', 'obsolete']:
            return ('status', status.arg )

    def get_description(self, s):
        desc = s.search_one('description')
        if desc is None:
            return "";
        else:
            return desc.arg

    def get_flags_str(self, s, mode):
        if mode == 'input':
            return ('access', 'write')
        elif (s.keyword == 'rpc' or s.keyword == ('tailf-common', 'action')):
            return ('access', 'write')
        elif s.keyword == 'notification':
            return ('access', 'read-only')
        elif s.i_config == True:
            return ('access', 'read-write')
        elif s.i_config == False or mode in ['output', 'notification']:
            return ('access', 'read-only')
        else:
            return None

    def get_typename(self, s):
        t = s.search_one('type')
        if t is not None:
            if t.arg == 'leafref':
                p = t.search_one('path')
                if p is not None:
                    # Try to make the path as compact as possible.
                    # Remove local prefixes, and only use prefix when
                    # there is a module change in the path.
                    target = []
                    curprefix = s.i_module.i_prefix
                    for name in p.arg.split('/'):
                        if name.find(":") == -1:
                            prefix = curprefix
                        else:
                            [prefix, name] = name.split(':', 1)
                        if prefix == curprefix:
                            target.append(name)
                        else:
                            target.append(prefix + ':' + name)
                            curprefix = prefix
                    return "-> %s" % "/".join(target)
                else:
                    return t.arg
            elif t.arg == 'identityref':
                idn_base = t.search_one('base')
                return t.arg + ":" + idn_base.arg
            else:
                return t.arg
        else:
            return ''

    def type_enums(self, t):
        tv = ''
        enum = t.search('enum')
        if enum != []:
            tv = '|'.join([e.arg for e in enum])
        return tv

    def type_values(self, t):
        if t is None:
            return ''
        if t.i_is_derived == False and t.i_typedef != None:
            return self.type_values(t.i_typedef.search_one('type'))
        if t.arg == 'boolean':
            return 'true|false'
        if t.arg == 'union':
            return self.type_union_values(t)
        if t.arg == 'enumeration':
            return self.type_enums(t)
        if t.arg == 'identityref':
            return self.type_identityref_values(t)
        return ''

    def type_union_values(self, t):
        vlist = []
        membertypes = t.search('type')
        for types in membertypes:
            v = self.type_values(types)
            if v != '':
                vlist.append(v)
        return '|'.join(vlist)

    def type_identityref_values(self, t):
        base_idn = t.search_one('base')
        if base_idn:
            #identity has a base
            idn_key = None
            base_idns = base_idn.arg.split(':')
            if len(base_idns) > 1:
                for module in self.module_prefixes:
                    if base_idns[0] == self.module_prefixes[module][0]:
                        idn_key = module + ':' + base_idns[1]
                        break
            else:
                idn_key = self.name + ':' + base_idn.arg

            if idn_key is None:
                return ''

            value_stmts = []
            stmts = self.identity_deps.get(idn_key, [])
            for value in stmts:
                ids = value.split(':')
                value_stmts.append(self.module_prefixes[ids[0]][0] + ':' + ids[1])
            if stmts:
                return '|'.join(value_stmts)
        return ''

    def type_choice_values(self, s):
        cases = s.search('case')
        values = ''
        if cases:
            clist = [c.arg for c in cases]
            values = '|'.join(clist)
        return values

