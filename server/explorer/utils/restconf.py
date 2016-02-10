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

    @author: Michael Ott, Cisco Systems, Inc.
    @author: Pravin Gohite, Cisco Systems, Inc.
"""

import os
import re
import logging
import json
import subprocess
import datetime
import lxml.etree as et
from jinja2 import Template, Environment, FileSystemLoader
from collections import OrderedDict
from explorer.utils.admin import ModuleAdmin

def get_op(keyvalue, mode):
    '''
    Return option and path depth of option to use for URL.
    URL should extend to where option is placed and message body
    should contain everything beyond.
    '''
    for child in keyvalue:
        op = child.attrib.get("option", "")
        if mode in ["get", "get-config"]:
            op = child.attrib.get('flag')
        path = child.attrib.get("path")
        path_len = len(path.split("/"))
        if op == 'remove':
            return ('delete', path_len-2)
        elif op == 'replace':
            return ('merge', path_len-2)
        elif op:
            return (op, path_len-2)
        elif op in ["get", "get-config"]:
            return (op, path_len-2)
    if not op:
        if mode in ["get", "get-config"]:
            return ('get', 0)
        return ('merge', 0)

def url_escape_chars(val):
    '''
    Some characters must be converted to work in a URL
    '''
    if not isinstance(val, (str, unicode)):
        return val
    return val.replace("/", "%2F").replace(":", "%3A").replace(" ", "%20")


def set_type(val):
    '''
    Using json.dumps() to convert dict to JSON strings requires that
    actual Python values are correct in dict
    TODO: Not sure if all correct datatypes are here.  What about
    typedefs?  Can they be represented in string form?
    '''
    if not val.text:
        return None
    if val.datatype == 'string' or ':' in val.datatype:
        return val.text
    if val.datatype.startswith('int') or val.datatype.startswith('uint'):
        return int(val.text)
    return val.text


def add_container(seg, msg):
    cont = OrderedDict()
    if seg.presence == 'true':
        return cont
    for leaf in seg.leaves:
        cont[leaf.name] = set_type(leaf)
    return cont


def add_list(seg, msg):
    kdict = OrderedDict()
    for key in seg.keys:
        kdict[key.name] = set_type(key)
    for leaf in seg.leaves:
        kdict[leaf.name] = set_type(leaf)
    return kdict


def build_msg(segs, msg=OrderedDict()):
    for seg in segs:
        if seg.type == 'container':
            cont = add_container(seg, msg)
            msg[seg.name] = cont
            build_msg(seg.segments, cont)
        elif seg.type == 'list':
            lst = add_list(seg, msg)
            msg[seg.name] = [lst]
            build_msg(seg.segments, lst)
        else:
            msg[seg.name] = set_type(seg)

    return msg


class Segment(object):
    '''
    Utility class to make handling of lxml Element classes easier to deal with
    '''
    def __init__(self, seg, text=''):
        self.name = seg.attrib.get('name')
        self.type = seg.attrib.get('type')
        self.datatype = seg.attrib.get('datatype')
        self.presence = seg.attrib.get('presence')
        self.text = text
        self.leaves = []
        self.segments = []
        self.keys = []
        self.depth = 0

    def __eq__(self, x):
        '''
        Takes an lxml Element object based on cxml node tags and compares the
        name attribute.  Makes it easier to use "==" and "in" operators
        '''
        if hasattr(x, 'attrib'):
            return self.name == x.attrib.get('name')
        return False

    def __str__(self):
        return self.name


def parse_url(username, request, mode):
    '''
    Main function that creates a URL and message body that uses the cxml (lxml)
    Element nodes from a defined test from the YangExplorer GUI

    Rules:
    https://tools.ietf.org/html/draft-ietf-netconf-restconf-09

    No option attribute defaults to PATCH operation with shortest possible URL.
    Rest of data is put in message body in JSON format.

    Option found in path denotes length of URL.  Any data beyond option is put
    into message body.
    '''
    keyvalue = request.find('keyvalue')
    cxml = None
    name = ''
    tpath = []
    master_segment = None
    op, op_location = get_op(keyvalue, mode)
    paths = []
    url = None
    pdict = {}
    msg = {}

    #pdb.set_trace()
    for child in keyvalue:

        path = child.get('path', '')
        path = path.split("/")
        if not cxml:
            name = path[0]
            url = [path[1]]
            #if op not in ['delete', 'replace']:
            #    return (name, op, url)
            filename = ModuleAdmin.cxml_path(username, path[0])
            cxml = et.parse(filename)
        paths.append((path, child))

    prev_seg = False

    for path, child in paths:

        rt = cxml.getroot()
        prev_list = False
        depth = 0

        for p in path:
            depth += 1
            chld = rt.getchildren()
            for n in chld:
                if n.attrib and n.attrib.get('name') == p:
                    if prev_list:
                        if n.attrib.get('is_key') == 'true':
                            if n not in prev_list.keys:
                                t = n.attrib.get('name')
                                index = prev_list.keys.index(t[t.find(':')+1:])
                                s = Segment(n)
                                s.text = child.text
                                prev_list.keys[index] = s
                            more = [f for f in prev_list.keys if not isinstance(f, Segment)]
                            if not more:
                                prev_list = False
                            rt = n
                            continue
                    if n.attrib.get('type') in ['leaf', 'leafref', 'leaf-list']:
                        if prev_seg:
                            prev_seg.leaves.append(Segment(n, child.text))
                        if n not in tpath:
                            tpath.append(Segment(n, child.text))
                    elif n.attrib.get('type') == 'list':
                        if n in tpath:
                            for t in tpath:
                                if n == t:
                                    prev_list = t
                        else:
                            prev_list = Segment(n)
                            if not master_segment:
                                master_segment = prev_list
                            elif prev_seg:
                                prev_seg.segments.append(prev_list)
                            prev_list.depth = depth
                            tpath.append(prev_list)
                            prev_list.keys = n.attrib.get('key').split()
                        prev_seg = prev_list
                        rt = n
                        break
                    elif n.attrib.get('type') in ['container']:
                        if n in tpath:
                            for t in tpath:
                                if n == t:
                                    prev_seg = t
                        else:
                            cont = Segment(n)
                            cont.depth = depth
                            if not master_segment:
                                master_segment = cont
                            elif prev_seg:
                                for i, t in enumerate(tpath):
                                    if t.name == prev_seg.name and t.depth == depth-1:
                                        t.segments.append(cont)
                                        break
                            prev_seg = cont
                            tpath.append(prev_seg)

                        rt = n
                        break
                    elif n.attrib.get('type') in ['case', 'choice']:
                        depth -= 1
                        rt = n
                        break

    if op not in ["get", "get-config", 'delete']:
        msg = build_msg([tpath[op_location:][0]], OrderedDict())
    if op_location:
        url = []
        for i, seg in enumerate(tpath):
            if seg.type in ['leaf', 'leafref', 'leaf-list']:
                if op in ["get", "get-config", 'delete']:
                    if len(tpath)-1 >= i:
                        continue
                else:
                    continue
            s = url_escape_chars(seg.name)
            url.append(s)
            if op not in ["get", "get-config", 'delete'] and i == op_location:
                break
            if seg.type == 'list':
                keys = []
                for key in seg.keys:
                    if key is None: break
                    if isinstance(key, str): continue;
                    keys.append(key.text)

                if len(keys) > 0:
                    k = ','.join(keys)
                    k = url_escape_chars(k)
                    url.append(k)

    return (name, op, '/'.join(url), json.dumps(msg, indent=2))


def gen_restconf(username, request, mode):
    '''
    Request from YangExplorer GUI is processed and URL, headers, and message
    body is produced.

    request - xml.etree.ElementTree root (should move to lxml)
    mode - edit-config or get-config
    '''
    rpc_exec = []
    target = request.attrib.get('target', 'running')
    device_data = request.find('device-auth')
    if device_data is not None:
        platform = device_data.attrib.get('platform', 'IOS-XE')
        if platform == 'csr': platform = 'IOS-XE'
    else:
        platform = 'IOS-XE'

    name, op, path, data = parse_url(username, request, mode)

    if platform == 'IOS-XE':
        url = "/api/"+target+'/'+path
    else:
        url = "/restconf/data/"+target+'/'+path

    hdr = {}
    print("OP "+str(op))
    if op in ['merge', 'replace', 'delete']:
        if platform == 'IOS-XE':
            hdr["Accept"] = "application/vnd.yang.collection+json, application/vnd.yang.data+json, application/vnd.yang.errors+json"
            hdr["Content-type"] = "application/vnd.yang.data+json"
        else:
            hdr["Accept"] = "application/yang.collection+json, application/yang.data+json, application/yang.errors+json"
            hdr["Content-type"] = "application/yang.data+json"

    if op == 'get':
        if platform == 'IOS-XE':
            hdr["Accept"] = "application/vnd.yang.data+json, application/vnd.yang.errors+json"
            hdr["Content-type"] = "application/vnd.yang.data+json"
        else:
            hdr["Accept"] = "application/yang.data+json, application/yang.errors+json"
            hdr["Content-type"] = "application/yang.data+json"

    if op == 'get-config':
        op = 'get'
        '''
        TODO:
        IOS-XR uses data={"content": "nonconfig"} for get and
        data={"content": "config"} for get-config.  It does not use deep
        '''
        if platform == 'IOS-XE':
            hdr["Accept"] = 'application/vnd.yang.collection+json, application/vnd.yang.data+json, application/vnd.yang.datastore+json'
        else:
            hdr["Accept"] = 'application/yang.collection+json, application/yang.data+json, application/yang.datastore+json'

    rpc_exec.append((op, url, data, hdr))

    return rpc_exec
