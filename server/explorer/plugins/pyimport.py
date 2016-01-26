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
from pyang import plugin
import xml.etree.ElementTree as ET

def pyang_plugin_init():
    plugin.register_plugin(PyImportPlugin())

def print_help():
    print("""
    pyang -f pyimport [option] <yang>
    """)

class PyImportPlugin(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        self.multiple_modules = True
        fmts['pyimport'] = self

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option("--pyimport-help",
                                 dest="pyimport_help",
                                 action="store_true",
                                 help="Print help on PyImport and exit"),
            ]
        g = optparser.add_option_group("PyImport output specific options")
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

        xmodules = ET.Element('modules')
        for module in modules:
            xmodule = self.emit_imports(module)
            if xmodule is not None:
                xmodules.append(xmodule)

        fd.write(ET.tostring(xmodules))

    def emit_imports(self, module):
        _module = ET.Element('module')
        _module.set('id', module.arg)

        # module prefix
        prefix_obj = module.search_one('prefix')
        if prefix_obj is not None:
            _module.set('prefix', prefix_obj.arg)

        # module namespace
        uri_stmt = module.search_one("namespace")
        if uri_stmt is not None:
            _namespace = ET.Element('namespace')
            _namespace.text = uri_stmt.arg
            _module.append(_namespace)

        # includes statements
        _includes = ET.Element('includes')
        _module.append(_includes)
        includes_stmt = module.search('include')
        for i_stmt in includes_stmt:
            _include = ET.Element('include')
            _include.set('module', i_stmt.arg)
            revision_stmt = i_stmt.search_one('revision-date')
            if revision_stmt is not None:
                _include.set('rev-date', revision_stmt.arg)
            _includes.append(_include)

        # import statements
        _imports = ET.Element('imports')
        _module.append(_imports)

        imports_stmt = module.search('import')
        for i_stmt in imports_stmt:
            _import = ET.Element('import')
            _import.set('module', i_stmt.arg)
            revision_stmt = i_stmt.search_one('revision-date')
            if revision_stmt is not None:
                _import.set('rev-date', revision_stmt.arg)
            _imports.append(_import)

        # module revision statement
        _revisions = ET.Element('revisions')
        _module.append(_revisions)

        revision_stmts = module.search("revision")
        for rev in revision_stmts:
            _revision = ET.Element('revision')
            _revision.set('date', rev.arg)
            _revisions.append(_revision)

        return _module