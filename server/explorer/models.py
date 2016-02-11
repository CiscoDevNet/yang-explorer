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
import shutil
import logging
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, post_save
from django.contrib.sessions.models import Session
from django.conf import settings

class Collection(models.Model):
    '''
    Collection of user defined messages
    '''
    name = models.CharField(max_length=128, primary_key=True, verbose_name='Collection Name')
    user = models.ForeignKey(User)
    description = models.CharField(max_length=128, blank=True)

    def save(self, *args, **kwargs):
        super(Collection, self).save(*args, **kwargs)
        name = getattr(self, 'name')
        directory = os.path.join('data', 'collections', name)
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __unicode__(self):
        return self.name

class UserProfile(models.Model):
    user   = models.ForeignKey(User)
    module = models.CharField(max_length=256)

    def __unicode__(self):
        return str(self.user) + ':' + str(self.module)

class DeviceProfile(models.Model):
    '''
    Collection of device profiles
    '''
    CHOICES = (('csr','csr'), ('nexus','nexus'), ('iosxe','iosxe'), ('iosxr','iosxr'), ('default','default'), ('other','other'))
    profile = models.CharField(max_length=128, primary_key=True)
    device = models.CharField(max_length=32, choices=CHOICES, default='csr')
    user = models.ForeignKey(User)

    nc_address = models.CharField(max_length=15, blank=True, default='', verbose_name='NetConf IP',
                                  help_text='Optional NetConf IP')
    nc_port = models.CharField(max_length=5, blank=True, default='830', verbose_name='NetConf Port',
                                    help_text='Optional NetConf Port')
    nc_username = models.CharField(max_length=32, blank=True, default='', verbose_name='NetConf Username',
                                    help_text='Optional NetConf Username')
    nc_password = models.CharField(max_length=32, blank=True, default='', verbose_name='NetConf Password',
                                    help_text='Optional NetConf Password')

    rest_address = models.CharField(max_length=15, blank=True, default='', verbose_name='RestConf IP',
                                  help_text='Optional RestConf IP')
    rest_port = models.CharField(max_length=5, blank=True, default='8008', verbose_name='RestConf Port',
                                  help_text='Optional RestConf Port')
    rest_username = models.CharField(max_length=32, blank=True, default='', verbose_name='RestConf Username',
                                  help_text='Optional RestConf Username')
    rest_password = models.CharField(max_length=32, blank=True, default='', verbose_name='RestConf Password',
                                  help_text='Optional RestConf Password')

    description = models.CharField(max_length=128)

    shared = models.BooleanField(default=False, verbose_name='Shared Device ?')

    def __unicode__(self):
        return self.profile

def sessionend_handler(sender, **kwargs):
    # cleanup session (temp) data
    logging.debug('Session closing, cleanup ..')
    session = kwargs.get('instance').session_key
    if session != '':
        tempdir = os.path.join('data', 'session', session)
        if os.path.exists(tempdir):
            logging.debug('Deleting %s ..' % tempdir)
            shutil.rmtree(tempdir)

def signal_create_user(sender, instance, created, **kwargs):
    username = instance.username
    path = os.path.join(settings.BASE_DIR, 'data', 'users', username)
    if created:
        logging.debug('Setting up user workspace ..')
        if not os.path.exists(path):
            os.makedirs(path)

        if not os.path.exists(os.path.join(path, 'yang')):
            os.makedirs(os.path.join(path, 'yang'))

        if not os.path.exists(os.path.join(path, 'cxml')):
            os.makedirs(os.path.join(path, 'cxml'))

def signal_delete_user(sender, **kwargs):
    logging.debug('Cleaning user workspace ..')
    username = kwargs.get('instance').username
    path = os.path.join(settings.BASE_DIR, 'data', 'users', username)
    if os.path.exists(path):
        shutil.rmtree(path)

pre_delete.connect(sessionend_handler, sender=Session)
post_save.connect(signal_create_user, sender=User, dispatch_uid="create_user")
pre_delete.connect(signal_delete_user, sender=User)