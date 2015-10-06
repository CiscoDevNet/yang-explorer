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

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from explorer.models import User, Collection, UserProfile


class Command(BaseCommand):
    help = 'Setup yang-explorer initial database'

    def create_superuser(self):
        User.objects.create_superuser(username='admin', password='admin', email='')

    def create_guestuser(self):
        guest = User()
        guest.username = 'guest'
        guest.first_name = 'Guest'
        guest.last_name = 'User'
        guest.set_password('guest')
        guest.is_staff = True
        guest.save()

        # add permissions
        for table in ['session', 'collection', 'userprofile', 'deviceprofile']:
            for code in ['add', 'change', 'delete']:
                code_name = code + '_' + table
                permission = Permission.objects.get(codename=code_name)
                guest.user_permissions.add(permission)

        # create default model
        profile = UserProfile(user=guest, module='ietf-interfaces@2013-12-23')
        profile.save()

        # add default collection
        col = Collection(name='default', user=guest, description='Default Collection')
        col.save()

    def handle(self, *args, **options):
        self.create_superuser()
        self.create_guestuser()