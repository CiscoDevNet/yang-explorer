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
import logging
import lxml.etree as ET
from django.conf import settings
from explorer.models import User, UserProfile
from explorer.utils.yang import Compiler
from explorer.utils.dygraph import DYGraph
from explorer.utils.misc import ServerSettings


class ModuleAdmin:
    @staticmethod
    def get_modules(username):
        """
        Return list of modules available to user + subscribed
        """
        logging.info("ModuleAdmin.get_modules: enter")

        modules = ET.Element('modulelist')
        user = User.objects.filter(username=username)
        for _file in glob.glob(os.path.join(ServerSettings.yang_path(username), '*.yang')):
            module = ET.Element('module')
            module.text = os.path.basename(_file)
            name = module.text.split('.yang')[0]
            if UserProfile.objects.filter(user=user, module=name).exists():
                module.set('subscribed', 'true')

            modules.append(module)

        logging.debug("ModuleAdmin.get_modules: returning (%d) modules .. exit" % len(modules))
        return modules

    @staticmethod
    def find_matching(target, directory, modules):
        logging.debug('Searching target %s in %s' % (target, directory))
        if not modules:
            modules = [os.path.basename(_file) for _file in glob.glob(os.path.join(directory, '*.yang'))]

        for module in modules:
            if module == target + '.yang':
                return os.path.join(directory, module)
            if module.startswith(target + '@'):
                return os.path.join(directory, module)
        return None

    @staticmethod
    def cxml_path(username, modulename):
        _dir = ServerSettings.cxml_path(username)
        modules = [os.path.basename(_file) for _file in glob.glob(os.path.join(_dir, '*.xml'))]
        for module in modules:
            if module == modulename + '.xml':
                return os.path.join(_dir, module)
            if module.startswith(modulename + '@'):
                return os.path.join(_dir, module)
        return None

    @staticmethod
    def get_modulelist(username):
        """
        Return list of modules available to user
        """
        users = User.objects.filter(username=username)
        if not users:
            logging.warning("ModuleAdmin.admin_action: Invalid user " + username)
            return []

        modules = []
        files = glob.glob(os.path.join(ServerSettings.cxml_path(username), '*.xml'))
        for _file in files:
            module = os.path.basename(_file).split('.xml')[0]
            if UserProfile.objects.filter(user=users[0], module=module).exists():
                modules.append(module)
        return modules

    @staticmethod
    def admin_action(username, payload, request):
        logging.debug("ModuleAdmin.admin_action: enter (%s -> %s)" % (username, request))

        if payload is None:
            logging.error('ModuleAdmin.admin_action: invalid payload in request !!')
            return False, "Invalid payload !!"

        modified = False
        modules = ET.fromstring(payload)

        if request == 'graph':
            return dependencies_graph(username, modules)

        users = User.objects.filter(username=username)
        if not users:
            logging.error("ModuleAdmin.admin_action: invalid user " + username)
            return False, 'Unknown User %s !!' % username

        user = users[0]
        if not ServerSettings.user_aware():
            if (request == 'delete') and not user.has_perm('explorer.delete_yangmodel'):
                return False, 'User %s does not have permission to delete models!!' % username

        for module in modules:
            name = module.text.split('.yang')[0]

            logging.debug("ModuleAdmin.admin_action: %s ->  %s" % (request, name))

            # delete modules from user profile
            if request in ['delete', 'unsubscribe']:
                if UserProfile.objects.filter(user=user, module=name).exists():
                    profile = UserProfile.objects.filter(user=user, module=name)
                    profile.delete()
                    logging.debug('Module %s deleted for user %s' % (module.text, username))

            # delete yang and cxml files for delete request
            if request == 'delete':
                for _type in [('cxml', '.xml'), ('yang', '.yang')]:
                    _file = os.path.join('data', 'users', username, _type[0], name + _type[1])
                    if os.path.exists(_file):
                        os.remove(_file)
                        modified = True
                        logging.debug('Deleted %s (user: %s)' % (_file, username))

            if request == 'subscribe':
                if not is_browsable(username, name):
                    logging.debug('Module %s can not be subscribed ' % (module.text))
                    return False, 'Module %s  can not be subscribed, not a main module !!' % name

                if not UserProfile.objects.filter(user=user, module=name).exists():
                    profile = UserProfile(user=user, module=name)
                    profile.save()
                    logging.debug('User %s subscribed to %s module ..' % (username, module.text))
                else:
                    logging.debug('User %s already subscribed to %s module ' % (username, module.text))

        # if any yang model modified, delete dependency file
        if modified:
            _file = os.path.join(ServerSettings.yang_path(username), 'dependencies.xml')
            if os.path.exists(_file):
                os.remove(_file)
                logging.debug('Deleted dependency file %s (user: %s)' % (_file, username))

        return True, None


def dependencies_graph(username, modules=[]):
    depfile = os.path.join(ServerSettings.yang_path(username), 'dependencies.xml')
    if not os.path.exists(depfile):
        (rc, msg) = Compiler.compile_pyimport(username, None)
        if not rc:
            return rc, msg

    dgraph = DYGraph(depfile)
    g = dgraph.digraph([m.text.split('.yang')[0] for m in modules])
    if g is None:
        return (False, """Failed to generate dependency graph, please make sure that grapviz
python package is installed !!""")

    try:
        g.render(filename=os.path.join(settings.BASE_DIR, 'static', 'graph'))
    except:
        return (False, """Failed to render dependency graph, please make sure that grapviz
binaries (http://www.graphviz.org/Download.php) are installed on
the server !!""")

    return True, g.comment


def is_browsable(username, module):
    cxml_path = os.path.join(ServerSettings.cxml_path(username), module + '.xml')
    browsable = False
    if os.path.exists(cxml_path):
        try:
            root = ET.parse(cxml_path).getroot()
            if root.find('node'):
                browsable = True
        except:
            logging.error('is_browsable: Exception in parse -> ' + cxml_path)
    return browsable
