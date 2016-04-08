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
import logging
import lxml.etree as ET
from django.db.models import Q
from explorer.models import DeviceProfile, Collection
from django.http import HttpResponse
from explorer.utils.misc import Response


def _build_proto(proto, addr, port, uname, pwd):
    """ Build one proto xml instance """

    transport = ET.Element('transport')
    transport.set('type', proto)

    elem = ET.Element('address')
    elem.text = addr
    transport.append(elem)

    elem = ET.Element('port')
    elem.text = port
    transport.append(elem)

    elem = ET.Element('username')
    elem.text = uname
    transport.append(elem)

    elem = ET.Element('password')
    elem.text = pwd
    transport.append(elem)

    return transport


def _build_device_profile(e):
    """ Build device profile xml instance """

    profile = ET.Element('profile')
    profile.set('type', 'device')
    profile.set('name', e.profile)

    elem = ET.Element('platform')
    elem.text = e.device
    profile.append(elem)

    netconf = _build_proto('netconf', e.nc_address, e.nc_port, e.nc_username,
                           e.nc_password)
    restconf = _build_proto('restconf', e.rest_address, e.rest_port, e.rest_username,
                            e.rest_password)

    elem = ET.Element('transports')
    elem.append(netconf)
    elem.append(restconf)
    profile.append(elem)
    return profile


def _build_collection_profile(p):
    """ Build collection profile xml instance """

    profile = ET.Element('profile')
    profile.set('type', 'collection')
    profile.set('name', p.name)
    return profile


def profile_handler(request):
    """ HTTP request handler for profile request """

    profiles = ET.Element('profiles')
    if request.user.is_authenticated():
        uid = request.user.id
        logging.debug("User Authenticated (%s)" % request.user.username)
        entries = DeviceProfile.objects.filter(Q(user=uid) | Q(shared=True))
        for e in entries:
            profile = _build_device_profile(e)
            profiles.append(profile)

        entries = Collection.objects.all()
        for e in entries:
            profile = _build_collection_profile(e)
            profiles.append(profile)
    return HttpResponse(Response.success('profile', 'ok', xml=profiles))
