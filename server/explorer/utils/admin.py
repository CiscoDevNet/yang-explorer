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
from explorer.models import User, UserProfile

class ModuleAdmin:
    @staticmethod
    def get_modules(username):
        '''
        Return list of modules available to user
        '''
        modules = ET.Element('modulelist')
        user = User.objects.filter(username=username)
        for _file in glob.glob(os.path.join('data', 'users', username, 'yang', '*.yang')):
            module = ET.Element('module')
            module.text = os.path.basename(_file)
            name = module.text.split('.yang')[0]
            if UserProfile.objects.filter(user=user, module=name).exists():
                module.set('subscribed', 'true')

            modules.append(module)
        return modules
    
    @staticmethod
    def get_modulelist(username):
        '''
        Return list of modules available to user
        '''
        files = glob.glob(os.path.join('data', 'users', username, 'cxml', '*.xml'))
        return [os.path.basename(_file).split('.xml')[0] for _file in files]

    @staticmethod
    def admin_action(username, payload, request):
        if payload is None:
            logging.debug('Invalid request: %s for user %s' % (request, username))
            return False

        modified = False
        modules = ET.fromstring(payload)
        user = User.objects.filter(username=username)
        for module in modules:
            name = module.text.split('.yang')[0]
            # delete modules from user profile
            if request in ['delete', 'unsubscribe']:
                if UserProfile.objects.filter(user=user[0], module=name).exists():
                    profile = UserProfile.objects.filter(user=user[0], module=name)
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
                if not UserProfile.objects.filter(user=user[0], module=name).exists():
                    profile = UserProfile(user=user[0], module=name)
                    profile.save()
                    logging.debug('User %s subscribed to %s module ..' % (username, module.text))
                else:
                    logging.debug('User %s already subscribed to %s module ' % (username, module.text))

        # if any yang model modified, delete dependency file
        if modified:
            _file = os.path.join('data', 'users', username, 'dependencies.xml')
            if os.path.exists(_file):
                os.remove(_file)
                logging.debug('Deleted dependency file %s (user: %s)' % (_file, username))

        return True

