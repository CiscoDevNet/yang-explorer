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
import lxml.etree as ET
import logging
from explorer.models import Collection as Col
from explorer.models import User
from explorer.utils.adapter import Adapter


class Collection(object):
    """ This class implements utility routines to work with
    collections """

    @staticmethod
    def add(metadata, payload):
        """ Add a collection entry """
        if metadata in [None, '']:
            logging.error('Invalid metadata')
            return False

        if payload in [None, '', 'null']:
            logging.error('Invalid payload')
            return False

        metadata = ET.fromstring(metadata)
        payload = ET.fromstring(payload)

        logging.debug(ET.tostring(metadata))
        logging.debug(ET.tostring(payload))

        cname = metadata.find('collection').text
        author = metadata.find('author').text
        name = metadata.find('name').text
        if not Col.objects.filter(name=cname).exists():
            if not User.objects.filter(username=author).exists():
                logging.error('User %s does not exist !!' % author)
                return False

            user = User.objects.filter(username=author)
            obj = Col(name=cname, user=user[0])
            obj.save()
            logging.debug('Created new collection ' + cname)

        path = os.path.join('data', 'collections', cname)
        if not os.path.exists(path):
            logging.error('Path to collection does not exist : %s !!' % path)
            return False

        for child in payload:
            if child.tag == 'metadata':
                for elem in metadata:
                    child.append(elem)

        cfile = os.path.join(path, name + '.xml')
        with open(cfile, 'w') as f:
            f.write(ET.tostring(payload))

        logging.debug('%s was saved successfully in collection %s' % (name, cname))
        return True

    @staticmethod
    def remove(metadata):
        """ Remove a entry from collection """
        if metadata is None or metadata == '':
            logging.error('Invalid metadata')
            return False

        metadata = ET.fromstring(metadata)
        cname = metadata.find('collection').text
        name = metadata.find('name').text

        if name is None or not name:
            logging.error('Invalid entry %s in argument!!' % name)
            return False

        if not Col.objects.filter(name=cname).exists():
            logging.debug('Collection %s does not exists !!' % cname)
            return True

        path = os.path.join('data', 'collections', cname, name + '.xml')
        if not os.path.exists(path):
            logging.debug('Path to collection does not exist : %s !!' % path)
            return True

        os.remove(path)
        logging.debug('%s was successfully removed from collection %s' % (name, cname))
        return True

    @staticmethod
    def list():
        """ get list of all collection entries """

        cols_elem = ET.Element('collections')
        for col in Col.objects.all():
            path = os.path.join('data', 'collections', col.name)
            if not os.path.exists(path):
                logging.error('Collection has inconstancy : %s !!' % col.name)
                continue
            files = glob.glob(os.path.join(path, '*'))
            for _file in files:
                payload = ET.parse(_file)
                for child in payload.getroot():
                    if child.tag == 'metadata':
                        cols_elem.append(child)
        return cols_elem

    @staticmethod
    def load(username, metadata):
        """ Load a collection entry """

        if metadata is None or metadata == '':
            logging.error('Invalid metadata')
            return None

        metadata = ET.fromstring(metadata)
        cname = metadata.find('collection').text
        name = metadata.find('name').text

        if not Col.objects.filter(name=cname).exists():
            logging.debug('Collection %s does not exists !!' % cname)
            return None

        _file = os.path.join('data', 'collections', cname, name + '.xml')
        if not os.path.exists(_file):
            logging.error('Collection entry not found')
            return None

        data = None
        with open(_file, 'r') as f:
            data = f.read()
            data = data.replace('&gt;','>')
            data = data.replace('&lt;','<')
            payload = ET.fromstring(data)

        if data is None:
            logging.error('Collection entry is empty')
            return None

        fmt = payload.get('format', 'raw')
        if fmt == 'xpath':
            return Adapter.gen_rpc(username, data)
        return payload
