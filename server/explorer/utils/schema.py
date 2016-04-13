##############################################################
# Netconf schema download 
#
# March 2016, Jennifer Chou 
#
# Copyright (c) 2016, Cisco Systems Inc
##############################################################
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



get_schema_rpc = '''
<rpc message-id="101"
     xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
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

rpc = ET.Element("rpc")
rpc.set("message-id", "101")
rpc.set("xmlns", "urn:ietf:params:xml:ns:netconf:base:1.0")

def get_schema(request, req, all=False):
    '''
    This API get yang schema from device
    '''
    logging.debug('Get Yang Schema')

    req = req.replace('<metadata>', '')
    req = req.replace('</metadata>', '')

    protocol, device, fmt, payload = Adapter.parse_request(req)
    if device.get('host', None) is None:
        return HttpResponse(Response.error('get', 'no host info'))

    rpc_xml= ET.fromstring(get_schema_rpc)
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

def download_yang(request, req):
    '''
    This API download yang schema from device
    '''
    logging.debug('Download Yang Schema')

    req = req.replace('<metadata>', '')
    req = req.replace('</metadata>', '')

    protocol, device, fmt, payload = Adapter.parse_request(req)
    if device.get('host', None) is None:
        return HttpResponse(Response.error('download', 'no host info'))

    session_dir = ServerSettings.schema_path(request.session.session_key)
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    if not os.path.exists(session_dir):
        return HttpResponse(Response.error('download', 'No session directory'))

    for fname in os.listdir(session_dir):
        if fname.endswith('.yang'):
            fn = os.path.join(session_dir, fname)
            os.remove(fn)

    modules = ET.Element('modules')
    reqxml = ET.fromstring(req)
    schemas = reqxml.find('schemas')
    for sc in schemas:
        id = sc.text
        module = ET.Element('module')
        get_sc = ET.Element('get-schema')
        get_sc.set("xmlns", "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring")
        identifier = ET.Element("identifier")
        sfile = id.split('@')[0]
        identifier.text = sfile
        module.text = id+'.yang'
        get_sc.append(identifier)
        rpc.append(get_sc)
        modules.append(module)
        schema = Adapter.run_netconf(request.user.username, device, rpc)
        fname = os.path.join(session_dir, id+'.yang')
        with open(fname, 'w') as f:
            f.write(schema[0][0].text)
        rpc.remove(get_sc)

    return modules

def download_schema(request, req):
    '''
    This API download yang schema from device and bundle it
    '''
    logging.debug('Download Schemas')

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

    url = '\nhttp://' + http_host + '/' + 'download/session/' + request.session.session_key + '/' + zfname
    return HttpResponse(Response.success('download', msg=url))

def add_schema(request, req):
    '''
    This API download yang schema from device 
    '''
    logging.debug('Add Schemas')
    modules = download_yang(request, req)
    return HttpResponse(Response.success('add', 'ok', xml=modules))

def validate_schema(user, name, version):
    if version is None:
        fn = os.path.join(ServerSettings.yang_path(user), name + '.yang')
    else:
        fn = os.path.join(ServerSettings.yang_path(user), name+'@'+version+'.yang')
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
