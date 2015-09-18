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
"""

import optparse
import sys
import re
import string
from pyang import types
from pyang import plugin
from pyang import statements

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
                prefix = module.search_one("prefix").arg
                self.module_namespaces[module.arg] = uri
                imports = module.search('import')
                
                related = False
                #build prefix to import modulename map
                i_prefixes = {}
                for i in imports:
                    if i.arg == self.name:
                        related = True
                    pfx = i.search_one('prefix')
                    if pfx is not None:
                        i_prefixes[pfx.arg] = i.arg + ':'

                if module.arg != self.name and not related:
                    continue

                if prefix is not None:
                    self.module_prefixes[module.arg] = prefix
                
                for idn in module.i_identities.values():
                    curr_idn = module.arg + ':' + idn.arg
                    base_idn = idn.search_one("base")
                    if base_idn:
                        #identity has a base
                        base_idns = base_idn.arg.split(':')
                        if len(base_idns) > 1:
                            #base is located in other modules
                            b_idn = i_prefixes.get(base_idns[0], '') + base_idns[1]
                            # check for nested identity:
                            # if curr_idn is the base itself, replace its children's
                            # base_idn to the grandparent
                            values = self.identity_deps.get(curr_idn, None)
                            if values is not None:
                                self.identity_deps.pop(curr_idn, None)
                                for value in values:
                                    if self.identity_deps.get(b_idn, None) is None:
                                        self.identity_deps.setdefault(b_idn, [])
                                    self.identity_deps[b_idn].append(value)
                        else:
                            b_idn = module.arg + ':' + base_idn.arg

                        if self.identity_deps.get(b_idn, None) is None:
                            self.identity_deps.setdefault(b_idn, [])
                        #print 'Adding %s -> %s' % (b_idn, curr_idn)
                        self.identity_deps[b_idn].append(curr_idn)
                    else:
                        self.identity_deps.setdefault(curr_idn, [])

    def emit_cxml(self): 
        fd = self.fd
        path = self.path

        fd.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        
        module = self.modules[-1]
        chs = [ch for ch in module.i_children
               if ch.keyword in statements.data_definition_keywords]
        if path is not None and len(path) > 0:
            chs = [ch for ch in chs if ch.arg == path[0]]
            path = path[1:]

        prefix = module.search_one('prefix')
        if not prefix:
            return
        
        fd.write('<node name="%s" type="module" prefix="%s">\n' % (module.arg, prefix.arg))
        
        for name in self.module_prefixes:
            fd.write('  <namespace prefix="%s">%s</namespace>\n' % 
                (self.module_prefixes[name], self.module_namespaces[name]))
        
        if len(chs) > 0:
            self.print_children(chs, module, fd, ' ', path, 'data')

        '''for augment in module.search('augment'):
            if (hasattr(augment.i_target_node, 'i_module') and
                augment.i_target_node.i_module not in modules):
                fd.write("augment %s:\n" % augment.arg)
                print_children(augment.i_children, module, fd,
                               ' ', path, 'augment')'''

        rpcs = [ch for ch in module.i_children
                if ch.keyword == 'rpc']
        if path is not None:
            if len(path) > 0:
                rpcs = [rpc for rpc in rpcs if rpc.arg == path[0]]
                path = path[1:]
            else:
                rpcs = []
        if len(rpcs) > 0:
            self.print_children(rpcs, module, fd, ' ', path, 'rpc')

        notifs = [ch for ch in module.i_children
                  if ch.keyword == 'notification']
        if path is not None:
            if len(path) > 0:
                notifs = [n for n in notifs if n.arg == path[0]]
                path = path[1:]
            else:
                notifs = []
        if len(notifs) > 0:
            self.print_children(notifs, module, fd, ' ', path, 'notification')
        fd.write('</node>')

    def print_children(self, i_children, module, fd, prefix, path, mode, width=0):
        def get_width(w, chs):
            for ch in chs:
                if ch.keyword in ['choice', 'case']:
                    w = get_width(w, ch.i_children)
                else:
                    if ch.i_module.i_modulename == module.i_modulename:
                        nlen = len(ch.arg)
                    else:
                        nlen = len(ch.i_module.i_prefix) + 1 + len(ch.arg)
                    if nlen > w:
                        w = nlen
            return w

        if width == 0:
            width = get_width(0, i_children)

        for ch in i_children:
            if ((ch.keyword == 'input' or ch.keyword == 'output') and
                len(ch.i_children) == 0):
                pass
            else:
                if (ch == i_children[-1] or
                    (i_children[-1].keyword == 'output' and
                     len(i_children[-1].i_children) == 0)):
                    # the last test is to detect if we print input, and the
                    # next node is an empty output node; then don't add the |
                    newprefix = prefix + '   '
                else:
                    newprefix = prefix + '   '
                if ch.keyword == 'input':
                    mode = 'input'
                elif ch.keyword == 'output':
                    mode = 'output'
                self.print_node(ch, module, fd, newprefix, path, mode, width)

    def print_node(self, s, module, fd, prefix, path, mode, width):
        fd.write("%s" % (prefix[0:-1]))
        #fd.write("%s%s--" % (prefix[0:-1], get_status_str(s)))

        if s.i_module.i_modulename == module.i_modulename:
            name = s.arg
        else:
            name = s.i_module.i_prefix + ':' + s.arg

        flags = self.get_flags_str(s, mode)
        fd.write("<node name=\"" + name + "\" " + flags + " ")

        description = self.get_description(s)
        close_tag = False
        
        if s.keyword == 'list':
            fd.write(" type=\"list\"")
            if s.search_one('key') is not None:
                fd.write(" key=\"" + s.search_one('key').arg + "\"")
            fd.write(">")
        elif s.keyword == 'container':
            p = s.search_one('presence')
            if p is not None:
                fd.write(" type=\"container\" presence=\"true\">")
            else:
                fd.write(" type=\"container\">")
            #fd.write(flags + " " + name)
        elif s.keyword  == 'choice':
            fd.write(' type="choice"')
            m = s.search_one('mandatory')
            if m is None or m.arg == 'false':
                fd.write(' mandatory="true"')
            fd.write('>')
        elif s.keyword == 'case':
            fd.write(" type=\"case\">")
        elif s.keyword in ['leaf', 'leaf-list']:
            typename = self.get_typename(s)
            fd.write(' type="' + s.keyword + '" datatype="' + typename + '"')

            if 'identityref' in typename:
                values = self.get_identityref_values(s)
                if values != '':
                    fd.write(' values=\"' + values + '\"')
            
            m = s.search_one('mandatory')
            if m is not None and m.arg == 'true' or hasattr(s, 'i_is_key'):
                fd.write(" mandatory=\"true\"")
            if hasattr(s, 'i_is_key'):
                fd.write(" is_key=\"true\"")
            
            d = s.search_one('default')
            if d is not None:
                fd.write(" default=\"" + d.arg + "\"")
            
            t = s.search_one('type')
            if t is not None:
                tv = self.type_enums(t)
                if tv != '':
                  fd.write(' values=\"' + tv + '\"')
            
            if description != '':
                close_tag = True
                fd.write('>')
            else:
                fd.write('/>')
        elif s.keyword == 'rpc' or s.keyword == 'notification' or s.keyword == 'input' or s.keyword == 'output':
            fd.write(' type="' + s.keyword + '">')
        else: 
            close_tag = True

        if description != '':
            fd.write('\n%s  <description><![CDATA[' %  prefix[0:-1])
            description.replace('<', '&lt')
            description.replace('>', '&gt')
            fd.write(description)
            fd.write(']]>\n%s  </description>' %  prefix[0:-1])
        
        if close_tag:
            fd.write("\n%s</node>" % (prefix[0:-1]))

        #features = s.search('if-feature')
        #if len(features) > 0:
        #    fd.write(" {%s}?" % ",".join([f.arg for f in features]))

        fd.write('\n')
        if hasattr(s, 'i_children'):
            chs = s.i_children
            if path is not None and len(path) > 0:
                chs = [ch for ch in chs
                       if ch.arg == path[0]]
                path = path[1:]
            if s.keyword in ['choice', 'case']:
                self.print_children(chs, module, fd, prefix, path, mode, width)
                fd.write("%s</node> \n" % (prefix[0:-1]))
            elif not s.keyword in ['leaf', 'leaf-list']:
                self.print_children(chs, module, fd, prefix, path, mode)
                fd.write("%s</node> \n" % (prefix[0:-1]))

    def get_status_str(self, s):
        status = s.search_one('status')
        if status is None or status.arg == 'current':
            return 'status="current"'
        elif status.arg == 'deprecated':
            return 'status="current"'
        elif status.arg == 'obsolete':
            return 'status="obsolete"'

    def get_description(self, s):
        desc = s.search_one('description')
        if desc is None:
            return "";
        else:
            return desc.arg

    def get_flags_str(self, s, mode):
        if mode == 'input':
            return 'access="write"'
        elif (s.keyword == 'rpc' or s.keyword == ('tailf-common', 'action')):
            return 'access="write"'
        elif s.keyword == 'notification':
            return 'access="read-only"'
        elif s.i_config == True:
            return 'access="read-write"'
        elif s.i_config == False or mode == 'output' or mode == 'notification':
            return 'access="read-only"'
        else:
            return ''

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

    def get_identityref_values(self, leaf):
        _type = leaf.search_one('type')
        if _type and _type.arg == 'identityref':
            base_idn = _type.search_one('base')
            if base_idn:
                #identity has a base
                idn_key = None
                base_idns = base_idn.arg.split(':')
                if len(base_idns) > 1:
                    for module in self.module_prefixes:
                        if base_idns[0] == self.module_prefixes[module]:
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
                    value_stmts.append(self.module_prefixes[ids[0]] + ':' + ids[1])
                return '|'.join(value_stmts)
            else:
                return ''
        return ''

    def type_enums(self, t):
        tv = ''
        if t.i_is_derived == False and t.i_typedef != None:
            return self.type_enums(t.i_typedef.search_one('type'))
        enum = t.search('enum')
        if enum != []:
            tv = '|'.join([e.arg for e in enum])
        elif statements.has_type(t, ['boolean']) != None:
            tv = 'true|false'
        return tv
