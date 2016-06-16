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

@author: Jennifer Chou , Cisco Systems, Inc.
"""
import os, glob
from datetime import datetime
import logging
import shutil
import lxml.etree as ET
from zipfile import ZipFile
from django.http import HttpResponse
from explorer.utils.misc import ServerSettings
from django.conf import settings
from explorer.utils.misc import Response
from explorer.utils.adapter import Adapter
from explorer.utils.yang import Parser
import explorer.utils.uploader as Uploader

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

get_schema_list_rpc = '''
<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get>
    <filter type="subtree">
      <netconf-state xmlns=
        "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
        <schemas/>
      </netconf-state>
    </filter>
  </get>
</rpc>
'''

get_schema_rpc = '''
<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
    <identifier/>
  </get-schema>
</rpc>
'''


def get_schema(request, req, all=True):
    """
    This API get yang schema from device
    """
    logger.debug('Get Yang Schema')

    req = req.replace('<metadata>', '')
    req = req.replace('</metadata>', '')

    protocol, device, fmt, payload = Adapter.parse_request(req)
    if device.get('host', None) is None:
        return HttpResponse(Response.error('get', 'no host info'))

    rpc_xml= ET.fromstring(get_schema_list_rpc)
    xml = Adapter.run_netconf(request.user.username, device, rpc_xml) 
    if xml is None:
        return HttpResponse(Response.error('get', 'failed to get schema'))
 
    if xml.text is not None:
        if xml.text.find('error'):
            return HttpResponse(Response.error('get', xml.text))

    sclist = xml[0][0][0][0]
    schemas = ET.Element('schemas')
    for sc in sclist:
        schema = ET.Element('schema')
        id  = sc[0].text
        ver = sc[1].text
        if all == False:
            if id.isupper() or '-MIB' in id or 'SNMP' in id:
                continue
        schema.set('name', id)
        if ver is None:
            schema.set('version', '')
        else:
            schema.set('version', ver)
        unmatched = validate_schema(request.user.username, id, ver)
        if unmatched is not None:
            schema.set('unmatched', unmatched)

        schemas.append(schema) 

    return HttpResponse(Response.success('get', 'ok', xml=schemas))


def download_helper(username, device, dest, rpc, models):
    """Download list of models in destination directory from device"""
    if not models:
        return

    logger.info('Downloading ' + str(models))

    identifier = rpc[0][0]
    dep_models = set()

    # dowload all models in the list
    for modelname in models:
        identifier.text = modelname.split('@')[0]
        fname = os.path.join(dest, identifier.text + '.yang')

        if not os.path.exists(fname):
            schema = Adapter.run_netconf(username, device, rpc)

            # write to file
            with open(fname, 'w') as f:
                f.write(schema[0][0].text)

            # calculate dependency
            parser = Parser(fname)
            dep_models |= set(parser.get_dependency())

    # recursively download dependency
    download_helper(username, device, dest, rpc, dep_models)


def download_yang(request, req):
    """
    This API download yang schema from device
    """
    logger.debug('Download Yang Schema')

    req = req.replace('<metadata>', '')
    req = req.replace('</metadata>', '')

    protocol, device, fmt, payload = Adapter.parse_request(req)
    if device.get('host', None) is None:
        return HttpResponse(Response.error('download', 'Netconf agent address missing!!'))

    # clear session directory if it exists
    Uploader.clear_upload_files(None, request.session.session_key)

    # create session directory if it does not exist
    session_dir = Uploader.create_session_storage(request.session.session_key)
    if session_dir is None:
        logger.error('download_yang: Invalid session')
        return HttpResponse(Response.error('download', 'Invalid session_id'))

    # extact list of models from request
    req_xml = ET.fromstring(req)
    models = [sc.text.strip() for sc in req_xml.find('schemas')]

    # download all models recursively
    rpc = ET.fromstring(get_schema_rpc)
    download_helper(request.user.username, device, session_dir, rpc, models)

    # prepare list of downloaded models
    modules = ET.Element('modules')
    for _file in glob.glob(os.path.join(session_dir, '*.yang')):

        # see if we need to rename file with revision date
        parser = Parser(_file)
        new_fname = os.path.join(session_dir, parser.get_filename())
        if _file != new_fname:
            os.rename(_file, new_fname)

        module = ET.Element('module')
        module.text = os.path.basename(new_fname)
        modules.append(module)
    return modules


def download_schema(request, req):
    """
    This API download yang schema from device and bundle it
    """
    logger.debug('Download Schemas')

    modules = download_yang(request, req)    

    session_dir = ServerSettings.schema_path(request.session.session_key)
    http_host = request.META['HTTP_HOST']
    current = str(datetime.now())
    current = current.replace(' ', '-')
    current = current[:current.rindex('.')]
    zfname = 'schema-' + current + '.zip'
    zfile = session_dir + '/' + zfname

    homedir = os.getcwd()
    os.chdir(session_dir)
    with ZipFile(zfile, "w") as lz:
        for f in glob.glob("*.yang"):
            lz.write(f)
            os.remove(f)
    if not lz.namelist():
        os.remove(zfile)
    os.chdir(homedir)

    url = '\nhttp://' + http_host + '/' + 'download/session/'
    url += request.session.session_key + '/' + zfname
    return HttpResponse(Response.success('download', msg=url))


def add_schema(request, req):
    """
    This API download yang schema from device
    """
    logger.debug('Add Schemas')
    modules = download_yang(request, req)
    return HttpResponse(Response.success('add', 'ok', xml=modules))


def validate_schema(user, name, version):
    if not version:
        fn = os.path.join(ServerSettings.yang_path(user), name + '.yang')
    else:
        fn = os.path.join(ServerSettings.yang_path(user), name + '@'+ version + '.yang')
    
    if os.path.exists(fn):
        return None 

    dirpath = os.path.join(settings.BASE_DIR, ServerSettings.yang_path(user))
    sfile = os.path.basename(fn.split('@')[0])
    if not sfile.endswith('.yang'): 
        sfile = sfile + '.yang'

    for file in os.listdir(dirpath):
        yfile = os.path.basename(file.split('@')[0])
        if not yfile.endswith('.yang'):
            yfile = yfile + '.yang'
        if sfile == yfile: 
            return '[out-of-sync]'
    return '[not-exist]'
