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
import re
import glob
import logging
import subprocess
from sets import Set
import lxml.etree as ET
from django.conf import settings
from explorer.utils.dygraph import DYGraph
from explorer.utils.misc import ServerSettings

class Parser(object):
    '''
    Basic Yang modulename parser
    '''
    def __init__(self, filename):
        self.module = None
        self.revision = None

        if not os.path.exists(filename):
            return

        module_re = re.compile("""^\s*[sub]*module\s+['"]?\s*([\w+[\-\w+]+)\s*['"]?\s*""")
        revision_re = re.compile("""^\s*revision\s+['"]?\s*(\w+-\w+-\w+)\s*['"]?\s*""")

        with open(filename, 'r') as f:
            for line in f:
                if self.module == None:
                    res = module_re.match(line)
                    if res is not None:
                        self.module = res.group(1).strip()

                if self.revision == None:
                    res = revision_re.match(line)
                    if res is not None:
                        self.revision = res.group(1).strip()
                        break

    def get_filename(self):
        '''
        Returns yang file name with version suffix.
        '''
        if self.revision is not None:
            return self.module + '@' + self.revision + '.yang'
        return self.module + '.yang'

    def __str__(self):
        return self.get_filename()


class Compiler(object):
    '''
    Compile yang models into cxml
    '''
    @staticmethod
    def compile_cxml(username, session, filename):
        '''
        Compile yang model and return tuple (boolean, list-of-errors)
        '''
        logging.debug('Compiling %s .. !!' % filename)

        plugins = os.path.join(settings.BASE_DIR, 'explorer', 'plugins')
        if not os.path.exists(plugins):
            logging.error('CXML Plugin directory is missing .. !!')
            return (False, None)

        if subprocess.call(['which', 'pyang']) != 0:
            logging.error('Could not find pyang compiler, please install pyang .. !!')
            return (False, None)

        basename = os.path.basename(filename)
        modulename = basename.split('.')[0].strip()

        session_dir = ''
        if session is not None:
            session_dir = ServerSettings.session_path(session)
            if not os.path.exists(session_dir):
                logging.error('compile_cxml: Session directory %s not found !!',  session_dir)
                return (False, ["Session error !!"])
            yangfile = os.path.join(session_dir, modulename + '.yang')
            cxmlfile = os.path.join(session_dir, modulename + '.xml')
        else:
            yangfile = os.path.join(ServerSettings.yang_path(username), modulename + '.yang')
            cxmlfile = os.path.join(ServerSettings.cxml_path(username), modulename + '.xml')

        # Verify if yang file exists
        if not os.path.exists(yangfile):
            logging.debug("compile_cxml: " + yangfile + ' not found !!')
            return (False, ["Yang module %s not found on server !!" % modulename])

        command = ['pyang', '-f', 'cxml', '--plugindir', 'explorer/plugins', '-p']

        # include path for pyang compilation
        includes = ServerSettings.yang_path(username)
        if session_dir:
            includes += ':' + session_dir

        command.append(includes)

        # include dependent models
        command += Compiler.get_dependencies(username, [filename], session)

        # finally add target module
        command.append(yangfile)

        return  Compiler.invoke_compile(command, cxmlfile)

    @staticmethod
    def compile_pyimport(username, session=None):
        '''
        Compile yang model and return tuple (boolean, list-of-errors)
        '''
        plugins = os.path.join(settings.BASE_DIR, 'explorer', 'plugins')
        if not os.path.exists(plugins):
            logging.error('CXML Plugin directory is missing .. !!')
            return (False, None)

        if subprocess.call(['which', 'pyang']) != 0:
            logging.error('Could not find pyang compiler, please install pyang .. !!')
            return (False, None)

        logging.debug('Rebuilding dependencies for user %s' % username)

        # build include path
        includes = [ServerSettings.yang_path(username)]
        if session is not None:
            session_dir = ServerSettings.session_path(session)
            if not os.path.exists(session_dir):
                logging.error('compile_pyimport: Session directory %s not found !!',  session_dir)
                return (False, ["Session error !!"])
            includes.append(session_dir)
            depfile = os.path.join(session_dir, 'dependencies.xml')
        else:
            depfile = os.path.join(includes[0], 'dependencies.xml')

        target_yangs = []
        for yang_dir in includes:
            for _file in glob.glob(os.path.join(yang_dir, '*.yang')):
                target_yangs.append(_file)

        if not target_yangs:
            logging.debug('compile_pyimport: No yang file found !!')
            return (True, ET.Element('messages'))

        command = ['pyang', '-f', 'pyimport', '--plugindir', 'explorer/plugins', '-p']
        command += [':'.join(includes)]
        command += target_yangs

        return Compiler.invoke_compile(command, depfile)

    @staticmethod
    def get_dependencies(username, modules, session):
        """
        return dependencies for given yang models
        """
        session_dir = ''
        logging.debug("get_dependencies: Target Modules " + str(modules))
        if session is not None:
            session_dir = ServerSettings.session_path(session)
            dfile = os.path.join(session_dir, 'dependencies.xml')
        else:
            dfile = os.path.join(ServerSettings.yang_path(username), 'dependencies.xml')

        if not os.path.exists(dfile):
            logging.error('get_dependencies: dependency file %s missing!!', dfile)
            return []

        if session_dir:
            session_files = [os.path.basename(_file) for _file in glob.glob(os.path.join(session_dir, '*.yang'))]

        yang_path = ServerSettings.yang_path(username)
        yang_files = [os.path.basename(_file) for _file in glob.glob(os.path.join(yang_path, '*.yang'))]

        dmodules = Set([])
        dgraph = DYGraph(dfile)
        for m in modules:
            module = dgraph.dependency_module(m)
            if module is None:
                continue
            for name in module.imports:
                dmodules.add(name)
            for name in module.depends:
                dmodules.add(name)

        dmodules_list = list(dmodules)

        deplist = []
        for _file in dmodules_list:
            # prefer freshly uploaded files
            if session_dir:
                depfile = _find_matching(_file, session_dir, session_files)
            else:
                depfile = _find_matching(_file, yang_path, yang_files)

            if depfile is not None:
                deplist.append(depfile)
            else:
                logging.warning("get_dependencies: Dependency (%s) not satisfied, compilation will fail !!" %  _file)

        logging.debug("get_dependencies: Computed " + str(deplist))
        return deplist

    @staticmethod
    def invoke_compile(command, outfile):
        """
        Invoke pyang compilation and return result
        """

        logging.debug("invoke_compile: CMD: " + str(command))

        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()

        rc = True
        lines = []
        if stderr:
            lines = stderr.split('\n')

        if p.returncode != 0:
            logging.error('invoke_compile: Compile Errors: ' + str(lines))
            if os.path.exists(outfile):
                os.remove(outfile)
            rc = False
        elif stdout:
            with open(outfile, 'w') as fd:
                fd.write(stdout)
                logging.debug('invoke_compile: %s -> done', outfile)
            logging.debug('invoke_compile: Compile Warning: ' + str(lines))
        else:
            logging.error('invoke_compile: Empty output from pyang!!')

        messages = ET.Element('messages')
        for line in lines:
            msg = ET.Element('message')
            msg.text = line
            messages.append(msg)

        return (rc, messages)

def _find_matching(target, directory, modules):
    logging.debug('Searching target %s in %s' % (target, directory))
    if not modules:
        modules = [os.path.basename(_file) for _file in glob.glob(os.path.join(directory, '*.yang'))]

    for module in modules:
        if module == target + '.yang':
            return os.path.join(directory, module)
        if module.startswith(target + '@'):
            return os.path.join(directory, module)
    return None
