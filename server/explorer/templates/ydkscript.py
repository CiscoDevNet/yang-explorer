#!/usr/bin/env python

#  ----------------------------------------------------------------
# Copyright 2016 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------

from __future__ import print_function
from ydk.providers import NetconfServiceProvider
from ydk.services import CRUDService, NetconfService, Datastore

{% spaceless %}
{{ydk_obj_defs|safe}}
{% endspaceless %}

def _init_logging():
    import logging
    log = logging.getLogger('ydk')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    log.addHandler(ch)

{% spaceless %}
{% if service_type == 'crud' %}
def crud_create(crud_service, provider, ydk_obj):
    print('==============\nCRUD CREATE SERVICE\n==============')

    crud_service.create(provider, ydk_obj)

def crud_update(crud_service, provider, ydk_obj):
    print('==============\nCRUD UPDATE SERVICE\n==============')

    crud_service.update(provider, ydk_obj)

def crud_delete(crud_service, provider, ydk_obj):
    print('==============\nCRUD DELETE SERVICE\n==============')

    crud_service.delete(provider, ydk_obj)

def crud_get(crud_service, provider, ydk_obj):
    print('==============\nCRUD READ SERVICE\n==============')

    only_config = FALSE
    crud_service.read(provider, ydk_obj, only_config)

def crud_get_config(crud_service, provider, ydk_obj):
    print('==============\nCRUD READ CONFIG SERVICE\n==============')

    only_config = TRUE
    crud_service.read(provider, ydk_obj, only_config)
{% endif %}
{% if service_type == 'netconf' %}
def netconf_create(netconf_service, provider, ydk_obj, 
                   datastore=Datastore.candidate, default_operation=None, 
                   error_option=None, test_option=None):
    print('==============\NETCONF CREATE SERVICE\n==============')

    netconf_service.edit_config(provider, ydk_obj, 
                                datastore, default_operation, 
                                error_option, test_option)

def netconf_replace(netconf_service, provider, ydk_obj,
                   datastore=Datastore.candidate, default_operation=REPLACE,
                   error_option=None, test_option=None):
    print('==============\nNETCONF REPLACE SERVICE\n==============')

    netconf_service.edit_config(provider, ydk_obj, 
                                datastore, default_operation, 
                                error_option, test_option)

def netconf_delete(netconf_service, provider, datastore=Datastore.candidate):
    print('==============\nNETCONF DELETE SERVICE\n==============')

    netconf_service.delete_config(provider, datastore)

def netconf_get(netconf_service, provider, ydk_obj,
                with_defaults_option=None):
    print('==============\nNETCONF GET SERVICE\n==============')

    netconf_service.read(provider, ydk_obj, only_config)

def netconf_get_config(netconf_service, provider, ydk_obj,
                       datastore=Datastore.candidate, with_defaults_option=None):
    print('==============\nNETCONF GET CONFIG SERVICE\n==============')

    netconf_service.get_config(provider, datastore, ydk_obj, with_defaults_option)
{% endif %}{% endspaceless %}

if __name__ == "__main__":
    _init_logging()
    provider = NetconfServiceProvider(address='{{host}}', 
                                      username='{{user}}', 
                                      password='{{passwd}}', 
                                      protocol='ssh', 
                                      port={{port}})

    {% spaceless %}
    {% if service_type == 'crud' %}crud_service = CRUDService()
    {% if service == 'create' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    crud_create(crud_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'update' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    crud_update(crud_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'delete' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    crud_delete(crud_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'get' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    crud_get(crud_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'get_config' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    crud_get_config(crud_service, provider, ydk_obj)
    {% endfor %}{% endif %}{% endif %}

    {% if service_type == 'netconf' %}netconf_service = NetconfService()
    {% if service == 'create' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    netconf_create(netconf_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'update' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    netconf_replace(netconf_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'delete' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    netconf_delete(netconf_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'get' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    netconf_get(netconf_service, provider, ydk_obj)
    {% endfor %}{% endif %}
    {% if service == 'get_config' %}{% for i in ydk_obj_names.split %}
    ydk_obj = {{i}}()
    netconf_get_config(netconf_service, provider, ydk_obj)
    {% endfor %}{% endif %}{% endif %}
    {% endspaceless %}

    exit()
