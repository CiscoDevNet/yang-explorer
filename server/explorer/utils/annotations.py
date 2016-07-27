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
import json
from django.core.cache import cache
from explorer.utils.misc import ServerSettings
from explorer.utils.xpath import XPathTree


def get_annotation_tree():
    ann_path = ServerSettings.annotation_path(None)
    filename = os.path.join(ann_path, 'covered.json')
    if not os.path.exists(filename):
        return None

    tree = cache.get('ui_ann', None)
    if tree is None:
        tree = XPathTree('/', None)
        with open(filename, 'r') as f:
            profile = json.load(f)
            for line in profile.get('data', []):
                tree.insert(line, profile.get('annotate', None))
            cache.set('ui_ann', tree)
    else:
        print 'From cache..'
    return tree


def annotate(nodes, tree=None):
    """
    Args:
        nodes: list lxml element tree nodes with lazy tree instance
    Returns:
        Annotated nodes with attribute and value specified in annotation file
    """
    if not tree:
        tree = get_annotation_tree()

    if tree and nodes:
        for node in nodes:
            xpath = node.get('path', '')
            instance = tree.search(xpath)
            if not instance:
                continue
            for attr, value in instance.attrib.items():
                node.set(attr, value)
            annotate(list(node), tree)
    return nodes