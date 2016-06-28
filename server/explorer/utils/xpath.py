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


class XPathTree(object):
    def __init__(self, name, attrib):
        self.name = name
        self.attrib = attrib
        self.children = set()

    def __str__(self):
        return self.name

    def _insert(self, names, attrib):
        for child in self.children:
            if child.name == names[0]:
                break
        else:
            child = XPathTree(names[0], attrib)
            self.children.add(child)

        if len(names) > 1:
            child._insert(names[1:], attrib)

    def insert(self, xpath, attrib):
        if not xpath:
            return
        self._insert(xpath.strip().split('/'), attrib)

    def search(self, xpath):
        if not xpath:
            return None
        return self._search(xpath.strip().split('/'))

    def _search(self, names):
        if not names:
            return None

        for child in self.children:
            if child.name == names[0]:
                if len(names) == 1:
                    return self
                return child._search(names[1:])

        return None