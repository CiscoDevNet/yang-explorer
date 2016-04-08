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
import lxml.etree as ET


class Response(object):
    """
    Utility class to build HTTP response
    """

    @staticmethod
    def _build(_type, tag, msg, xml):
        """ Create HTTP response """

        response = ET.Element('response')
        if _type:
            response.set('type', _type)

        msgtag = ET.Element(tag)
        if msg:
            msgtag.text = msg
        response.append(msgtag)

        if xml is not None:
            response.append(xml)
        return ET.tostring(response)

    @staticmethod
    def error(_type, msg, xml=None):
        """ Build error response """
        return Response._build(_type, 'error', msg, xml)

    @staticmethod
    def success(_type, msg, xml=None):
        """ Build success response """
        return Response._build(_type, 'success', msg, xml)


class ServerSettings(object):
    @staticmethod
    def user_aware():
        return True

    @staticmethod
    def session_path(session):
        """ Build path to session directory """
        return os.path.join('data', 'session', session)

    @staticmethod
    def yang_path(user):
        """ Build path to user's yang directory """
        return os.path.join('data', 'users', user, 'yang')

    @staticmethod
    def cxml_path(user):
        """ Build path to user's yang directory """
        return os.path.join('data', 'users', user, 'cxml')