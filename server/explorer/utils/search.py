"""
    Copyright 2016, Cisco Systems, Inc

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
from explorer.utils.cxml import CxmlIterator
from explorer.utils.admin import ModuleAdmin


def search_module(username, module, query):
    """ Search query in one module """
    result = []
    filename = ModuleAdmin.cxml_path(username, module)
    cxml_i = CxmlIterator(filename)
    for path, _ in cxml_i:
        if query in path:
            result.append(path)
    return result


def search(username, query):
    """
    Search query text in user modules
    Args:
        username: Request username
        query: Search String

    Returns: An XML object with result XPATHs
    """
    logging.debug('Searching query %s in user (%s) modules' % (query, username))
    response = ET.Element('result')

    modulenames = ModuleAdmin.get_modulelist(username)
    for module in modulenames:
        result = search_module(username, module, query)
        for xpath in result:
            path = ET.Element('path')
            path.set('module', module)
            path.text = xpath
            response.append(path)

    return True, response
