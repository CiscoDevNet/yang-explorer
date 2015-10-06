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
import logging
import subprocess
import lxml.etree as ET
from django.conf import settings

class Parser(object):
    '''
    Basic Yang parser module
    '''
    def __init__(self, filename):
        self.module = None
        self.revision = None

        if not os.path.exists(filename):
            return

        module_re = re.compile("^\s*[sub]*module\s+([\w+[\-\w+]+)\s*")
        revision_re = re.compile("^\s*revision\s+(\w+-\w+-\w+)\s*")

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
        plugins = os.path.join(settings.BASE_DIR, 'explorer', 'plugins')
        if not os.path.exists(plugins):
            logging.error('CXML Plugin directory is missing .. !!')
            return (False, None)

        if subprocess.call(['which', 'pyang']) != 0:
            logging.error('Could not find pyang compiler, please install pyang .. !!')
            return (False, None)

        logging.debug('Compiling %s .. !!' % filename)

        _filename = os.path.join(settings.BASE_DIR, filename)
        _base = os.path.dirname(_filename)
        _file = os.path.basename(_filename)
        _exec = os.path.join(settings.BASE_DIR, 'bin', 'synchronize.sh')

        cmd = ['/bin/bash', _exec, _filename, username]
        if session is not None:
            cmd.append(session)

        logging.debug('Exec: ' + ' '.join(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            lines = stderr.split('\n')
            logging.debug('Pyang Compile Errors: ' + str(lines))
            rmfile = os.path.join(_base, os.path.splitext(_file)[0] + '.xml')

            if os.path.exists(rmfile):
                logging.debug('Deleting %s' % rmfile)
                os.remove(rmfile)
            rc = False
        else:
            rc = True
            lines = stdout.split('\n')

        messages = ET.Element('messages')
        for line in lines:
            msg = ET.Element('message')
            msg.text = line
            messages.append(msg)

        return (rc, messages)

    @staticmethod
    def compile_pyimport(username, session=''):
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

        _exec = os.path.join(settings.BASE_DIR, 'bin', 'dygraph.sh')
        cmd = ['/bin/bash', _exec, username, session]

        logging.debug('Exec: ' + ' '.join(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            lines = stderr.split('\n')
            logging.debug('Pyang Compile Errors: ' + str(lines))
            rc = False
        else:
            rc = True
            lines = stdout.split('\n')

        messages = ET.Element('messages')
        for line in lines:
            msg = ET.Element('message')
            msg.text = line
            messages.append(msg)

        return (rc, messages)


