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
from __future__ import print_function

import os
import logging
import shutil
import lxml.etree as ET
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from explorer.utils.cxml import Cxml
from explorer.utils.misc import Response
from explorer.utils.adapter import Adapter
from explorer.utils.collection import Collection
from explorer.utils.misc import ServerSettings
from explorer.utils.admin import ModuleAdmin
from explorer.utils.schema import get_schema, download_schema, add_schema
import explorer.utils.uploader as Uploader

logging.basicConfig(level=logging.WARNING)


@csrf_exempt
def login_handler(request):
    """ HTTP Request handler function for user login / logout requests """
    session = ET.Element('session')
    if request.POST:
        action = request.POST['action']
        if action == 'login':
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                # Correct password, and the user is marked "active"
                login(request, user)
                session.text = username
            else:
                return HttpResponse(Response.error('login', 'Authentication Failed'))
        else:
            try:
                if request.session.session_key is not None and request.session.session_key != '':
                    session_dir = ServerSettings.session_path(request.session.session_key)
                    if os.path.exists(session_dir):
                        logging.debug('Cleaning ' + session_dir)
                        shutil.rmtree(session_dir)
                logout(request)
            except:
                logging.exception("Failed")
            else:
                logging.debug('Logout success!!')
        return HttpResponse(Response.success(action, 'ok', session))
    return HttpResponse(Response.error('unknown', 'Invalid request!!'))


@csrf_exempt
def session_handler(request):
    """ HTTP Request handler function to check if user session exists """
    session = ET.Element('session')
    if request.user.is_authenticated():
        session.text = request.user.username
    return HttpResponse(Response.success('session', 'ok', session))


@csrf_exempt
def upload_handler(request):
    """ HTTP Request handler function to upload yang models """

    mode = request.GET.get('mode', '')
    logging.debug(request.method + ':Received upload request .. ' + mode)

    if not request.user.is_authenticated():
        logging.warning('User must be logged in !!')
        return HttpResponse(Response.error(mode, 'Unauthorized'))

    if not ServerSettings.user_aware():
        if not request.user.has_perm('explorer.delete_yangmodel') or \
                not request.user.has_perm('explorer.change_yangmodel'):
            logging.warning('Unauthorized upload request .. ')
            return HttpResponse(Response.error(mode, 'User does not have permission to upload !!'))

    if request.method == 'POST':
        # create a temporary storage for this session
        directory = ServerSettings.session_path(request.session.session_key)
        _file = Uploader.upload_file(request.FILES['Filedata'], directory)
        if _file is not None:
            module = ET.Element('module')
            module.text = _file
            rval = Response.success('upload', 'ok', xml=module)
            logging.debug(rval)
            return HttpResponse(rval)
        return HttpResponse(Response.error('upload', 'Failed to upload'))
    elif request.method == 'GET':
        if mode == 'sync':
            filename = request.GET.get('file', '')
            index = request.GET.get('index', '')
            logging.info('Received sync request for ' + filename + ', index ' + index)
            success, response = Uploader.sync_file(request.user.username,
                                                   request.session.session_key,
                                                   filename, index)
            if success:
                return HttpResponse(Response.success(mode, 'ok'))
            return HttpResponse(Response.error(mode, 'compilation failed', xml=response))

        elif mode == 'commit':
            success, modules = Uploader.commit_files(request.user.username, request.session.session_key)
            if success:
                return HttpResponse(Response.success('commit', 'ok', modules))

        elif mode == 'init':
            success, modules = Uploader.get_upload_files(request.user.username, request.session.session_key)
            if success:
                return HttpResponse(Response.success(mode, 'ok', modules))

        elif mode == 'clear':
            success, modules = Uploader.clear_upload_files(request.user.username, request.session.session_key)
            if success:
                return HttpResponse(Response.success(mode, 'ok', modules))
        return HttpResponse(Response.error(mode, 'failed'))

    return render_to_response('upload.html')


def admin_handler(request):
    """ HTTP Request handler function to handle actions on yang modules """

    if not request.user.is_authenticated():
        return HttpResponse(Response.error(None, 'User must be logged in'))

    if request.method != 'GET':
        return HttpResponse(Response.error(None, 'Invalid admin Request'))

    action = request.GET.get('action', '')
    logging.info('Received admin request %s for user %s' % (action, request.user.username))

    if action in ['subscribe', 'unsubscribe', 'delete', 'graph']:
        payload = request.GET.get('payload', None)
        print(str(payload))
        (rc, msg) = ModuleAdmin.admin_action(request.user.username, payload, action)
        if not rc:
            return HttpResponse(Response.error(action, msg))

    if action == 'graph':
        return HttpResponse(Response.success(action, msg))

    modules = ModuleAdmin.get_modules(request.user.username)
    return HttpResponse(Response.success(action, 'ok', xml=modules))


def request_handler(request):
    """ HTTP Request handler function to handle actions on collections """

    mode = request.GET.get('mode', '')
    reply_xml = None

    logging.info('request_handler: Received Request: (%s)' % mode)

    if mode == 'get-collection-list':
        reply_xml = Collection.list()

    elif mode == 'load-collection':
        metadata = request.GET.get('metadata', '')
        reply_xml = Collection.load(request.user.username, metadata)

        if reply_xml is None:
            return HttpResponse(Response.error(mode, 'Failed'))

        if isinstance(reply_xml, str):
            return HttpResponse(Response.success(mode, reply_xml))

    elif mode == 'add-collection':
        metadata = request.GET.get('metadata', '')
        payload = request.GET.get('payload', '')
        logging.debug('metadata: ' + metadata)
        logging.debug('payload: ' + payload)
        if not Collection.add(metadata, payload):
            return HttpResponse(Response.error(mode, 'Failed'))

        reply_xml = Collection.list()
        mode = 'get-collection-list'

    elif mode == 'delete-collection':
        metadata = request.GET.get('metadata', '')
        if not Collection.remove(metadata):
            return HttpResponse(Response.error(mode, 'Failed'))

        reply_xml = Collection.list()
        mode = 'get-collection-list'

    elif mode == 'rpc':
        req = request.GET.get('payload', '')
        reply_xml = Adapter.gen_rpc(request.user.username, req)
        if isinstance(reply_xml, str):
            return HttpResponse(Response.success(mode, reply_xml))

    elif mode in ['get-cap', 'run-rpc']:
        payload = request.GET.get('payload', '')
        logging.debug('run: ' + payload)
        reply_xml = Adapter.run_request(request.user.username, payload)

    return HttpResponse(Response.success(mode, 'ok', reply_xml))


def module_handler(request):
    """
    Handle module request from UI. Response from this request builds
    UI Explorer tree
    """
    logging.debug("module_handler: enter")
    lst = []
    if request.user.is_authenticated():
        path = request.GET.get('node', '')

        username = request.user.username
        if path == 'root':
            # Request for root models
            modules = ModuleAdmin.get_modulelist(username)
            modules.sort()
            path = ''
        else:
            modules = [path.split('/')[0]]

        for module in modules:
            filename = ModuleAdmin.cxml_path(username, module)
            if filename is not None:
                logging.debug("module_handler: loading " + filename)
                module = Cxml(filename)
                nodes = module.get_lazy_node(path)
                lst.extend([ET.tostring(node) for node in nodes])
            else:
                logging.error("module_handler: %s not found !!" + module)

    logging.debug("module_handler: exit")
    return render_to_response('loader.xml', {'nodes': lst}, RequestContext(request))

def schema_handler(request):
    '''
    Handle schema request from UI.
    '''
    logging.debug("schema_handler: enter")
    req = request.GET.get('payload', '')
    action = request.GET.get('action', '')
    logging.debug('Recieved schema Request (%s)' % action)

    if not request.user.is_authenticated():
        logging.error('User must be logged in !!')
        return HttpResponse(Response.error(action, 'Unauthorized'))
    if action == 'get-schema':
        return get_schema(request, req)
    elif action == 'get-all-schema':
        return get_schema(request, req, all=True)
    elif action == 'download-schema':
        return download_schema(request, req)
    elif action == 'add-schema':
        return add_schema(request, req)

