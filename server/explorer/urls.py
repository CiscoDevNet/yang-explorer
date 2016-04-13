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

from django.conf.urls import url
from explorer import views, profile_view

urlpatterns = [
    url(r'^modules', views.module_handler, name='module_handler'),
    url(r'^login', views.login_handler, name='login_handler'),
    url(r'^session', views.session_handler, name='session_handler'),
    url(r'^upload', views.upload_handler, name='upload_handler'),
    url(r'^admin', views.admin_handler, name='admin_handler'),
    url(r'^netconf', views.request_handler, name='request_handler'),
    url(r'^schema', views.schema_handler, name='schema_handler'),
    url(r'^userprofiles', profile_view.profile_handler, name='profile_handler'),
]
