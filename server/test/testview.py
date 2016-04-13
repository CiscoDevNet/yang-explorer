"""
    Unit Test Automation for YangExplorer Application

    @author: Neha Kalbhore (neha.Kalbhore@gmail.com)
"""
import os
import logging
import lxml.etree as ET
from django.test import TestCase, Client
from django.contrib.auth import authenticate
from explorer.models import User
from explorer.views import login_handler
from explorer.utils.misc import ServerSettings
from explorer.utils.admin import ModuleAdmin

logging.basicConfig(level=logging.DEBUG)


class UsersTestCase(TestCase):
    def setUp(self):
        demo = User()
        demo.username = 'demo'
        demo.first_name = 'Demo'
        demo.last_name = 'Last'
        demo.set_password('demo123')
        demo.is_staff = False
        demo.save()
        self.user = demo
        self.user_path = os.path.join('data', 'users', 'demo')
        self.chrome = Client()
        self.upload_files = []

    def cleanUp(self):
    	demo.delete()

    def test_01_login(self):
        """Verify user creation"""
       	user = authenticate(username='demo', password='demo123')
       	self.assertTrue(user is not None)
       	self.assertTrue(user.is_active == True)

        user = authenticate(username='demo', password='demo122')
        self.assertTrue(user is None)

        user = authenticate(username='demo', password='')
        self.assertTrue(user is None)

        user = authenticate(username='demo1', password='demo123')
        self.assertTrue(user is None)

        user = authenticate(username='', password='demo123')
        self.assertTrue(user is None)

    def test_02_login_handler(self):
        """Verify login_handler API in views.py"""

        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'login'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)

        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'logout'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)

        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo124', 'action': 'login'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('Authentication Failed' in response.content)

        print("Test: login_handler PASSED")

    def test_03_session_handler(self):
        """Verify session_handler API in views.py"""

        response = self.chrome.get('/explorer/session/')
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)
        self.assertFalse('demo' in response.content)

        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'login'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)

        response = self.chrome.get('/explorer/session/')
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)
        self.assertTrue('demo' in response.content)

        print("Test: session_handler PASSED")

    def test_04_upload_handler(self):
        """ Verify upload_handler API in views.py """

        # 1. Login to django server
        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'login'})
        self.assertTrue(response.status_code == 200)

        # 2. Intialize upload request
        response = self.chrome.get('/explorer/upload', {'mode' : 'init'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)

        # Get path to upload file
        curr = os.getcwd()
        pathlist = curr.split('/')
        while pathlist[-1] != 'yang-explorer': pathlist.pop()
        pathlist.append('default-models')
        root = '/'.join(pathlist)

        # 3. Upload file content
        filelist = ['ietf-inet-types.yang', 'ietf-yang-types.yang', 'ietf-interfaces@2013-12-23.yang']
        for _file in filelist:
            with open(os.path.join(root, _file), 'r') as fp:
                response = self.chrome.post('/explorer/upload-add', {'Filedata' : fp})
                self.assertTrue(response.status_code == 200)
                self.assertTrue('ok' in response.content)
                f = response.content.split('<module>')[1].split('</module>')[0]
                self.upload_files.append(f.strip())

        # 4. Compile file
        for _file in self.upload_files:
            response = self.chrome.get('/explorer/upload', {'mode':'sync', 'file': _file})
            self.assertTrue(response.status_code == 200)
            self.assertTrue('ok' in response.content)

        # 5. Commit file
        response = self.chrome.get('/explorer/upload', {'mode':'commit'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)

        # logout
        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'logout'})
        self.assertTrue(response.status_code == 200)
        self.assertTrue('ok' in response.content)

        # Verify that files are actually uploaded
        yang_path = ServerSettings.yang_path('demo')
        cxml_path = ServerSettings.cxml_path('demo')
        for _file in self.upload_files:
            # check if yang file is uploaded
            self.assertTrue(os.path.exists(os.path.join(yang_path, _file)))

            # check if xml file is created
            xml_name = _file.split('.yang')[0] + '.xml'
            self.assertTrue(os.path.exists(os.path.join(cxml_path, xml_name)))

        print("Test: upload_handler PASSED")

    def test_05_admin_handler(self):
        """ Verify admin handler functionality """

        # 1. Login to django server
        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'login'})
        self.assertTrue(response.status_code == 200)

        # 2 Subscribe invalid module
        modules = ET.Element('modules')
        module = ET.Element('module')
        module.text = 'ietf-yang-types@2013-07-15.yang'
        modules.append(module)

        response = self.chrome.get('/explorer/admin', {'action':'subscribe', 'payload': ET.tostring(modules)})
        self.assertTrue(response.status_code == 200)
        print response.content
        self.assertTrue('error' in response.content)
        self.assertTrue('not a main module' in response.content)

        # 2 Subscribe valid module
        module.text = 'ietf-interfaces@2013-12-23.yang'
        response = self.chrome.get('/explorer/admin', {'action':'subscribe', 'payload': ET.tostring(modules)})
        self.assertTrue(response.status_code == 200)
        print response.content
        self.assertTrue('ok' in response.content)

        # 3. Verify that returned list correct subscription
        modulelist = ET.fromstring(response.content).find('modulelist')
        found = False
        for m in modulelist:
            if m.text == 'ietf-interfaces@2013-12-23.yang':
                found = True
                self.assertTrue(m.get('subscribed', 'false') == 'true')
        self.assertTrue(found)

        # 4. Un-Subscribe ietf-interfaces
        response = self.chrome.get('/explorer/admin', {'action':'unsubscribe', 'payload': ET.tostring(modules)})
        self.assertTrue(response.status_code == 200)
        print response.content
        self.assertTrue('ok' in response.content)

        # 5. Verify that returned list correct subscription
        modulelist = ET.fromstring(response.content).find('modulelist')
        found = False
        for m in modulelist:
            if m.text == 'ietf-interfaces@2013-12-23.yang':
                found = True
                self.assertFalse(m.get('subscribed', 'false') == 'true')
        self.assertTrue(found)

        module.text = 'ietf-yang-types@2013-07-15.yang'
        response = self.chrome.get('/explorer/admin', {'action':'delete', 'payload': ET.tostring(modules)})
        self.assertTrue(response.status_code == 200)
        print response.content
        self.assertTrue('ok' in response.content)

        # 6. Verify delete
        modulelist = ET.fromstring(response.content).find('modulelist')
        found = False
        for m in modulelist:
            self.assertTrue(m.text != 'ietf-yang-types@2013-07-15.yang')

        _file = module.text
        yang_path = ServerSettings.yang_path('demo')
        cxml_path = ServerSettings.cxml_path('demo')
        # check if yang file is deleted
        self.assertFalse(os.path.exists(os.path.join(yang_path, _file)))

        # check if xml file is deleted
        xml_name = _file.split('.yang')[0] + '.xml'
        self.assertFalse(os.path.exists(os.path.join(cxml_path, xml_name)))

        print("Test: admin_handler PASSED")

    def test_06_request_handler(self):
        """ Verify request handler functionality """

        # 1. Login to django server
        response = self.chrome.post('/explorer/login/', {'username': 'demo', 'password': 'demo123', 'action': 'login'})
        self.assertTrue(response.status_code == 200)

        # 2. Verify get collections
        response = self.chrome.get('/explorer/netconf', {'mode': 'get-collection-list'})
        print response.content
        self.assertTrue('ok' in response.content)
        self.assertTrue('<collections/>' in response.content)

        # 3. Verify add collection

        metadata = '''
<metadata>
    <collection>default</collection>
    <author>demo</author>
    <name>test-demo</name>
    <desc>This is test description</desc>
</metadata>'''

        payload = '''
<payload version="3" protocol="netconf" format="xpath" operation="edit-config" target="running">
    <metadata>
        <device-auth profile="" platform="" host="" port="" user="" passwd=""/>
        <netconf-auth host="" port="" user="" passwd=""/>
    </metadata>
    <keyvalue>
        <node path="ietf-interfaces@2013-12-23/interfaces/interface/name">GigabitEthernet0</node>
        <node path="ietf-interfaces@2013-12-23/interfaces/interface/description">Test</node>
        <node path="ietf-interfaces@2013-12-23/interfaces/interface/type">ianaift:ethernetCsmacd</node>
    </keyvalue>
</payload>'''


        response = self.chrome.get('/explorer/netconf', {'mode': 'add-collection',
                                                         'metadata':metadata,
                                                         'payload':payload})
        print response.content
        self.assertTrue('ok' in response.content)
        self.assertTrue('<author>demo</author>' in response.content)
        self.assertTrue('<name>test-demo</name>' in response.content)
        self.assertTrue('<desc>This is test description</desc>' in response.content)

        # Verify load-collection
        response = self.chrome.get('/explorer/netconf', {'mode': 'load-collection', 'metadata':metadata})
        print response.content
        self.assertTrue('ok' in response.content)
        self.assertTrue('<response type="load-collection">' in response.content)
        self.assertTrue('<rpc' in response.content)
        self.assertTrue('<edit-config>' in response.content)
        self.assertTrue('<name>GigabitEthernet0</name>' in response.content)
        self.assertTrue('<type>ianaift:ethernetCsmacd</type>' in response.content)
        self.assertTrue('<description>Test</description>' in response.content)
        self.assertTrue('<target><running/></target>' in response.content)
        self.assertTrue('</rpc>' in response.content)

        # Verify mode rpc
        response = self.chrome.get('/explorer/netconf', {'mode': 'rpc','payload': payload})
        print response.content
        self.assertTrue('ok' in response.content)
        self.assertTrue('<response type="rpc">' in response.content)
        self.assertTrue('<rpc' in response.content)
        self.assertTrue('<edit-config>' in response.content)
        self.assertTrue('<name>GigabitEthernet0</name>' in response.content)
        self.assertTrue('<type>ianaift:ethernetCsmacd</type>' in response.content)
        self.assertTrue('<description>Test</description>' in response.content)
        self.assertTrue('<target><running/></target>' in response.content)
        self.assertTrue('</rpc>' in response.content)

        # Verify delete-collection
        response = self.chrome.get('/explorer/netconf', {'mode': 'delete-collection', 'metadata': metadata})
        print response.content
        self.assertTrue('ok' in response.content)
        self.assertTrue('<collections/>' in response.content)

        print("Test: request_handler PASSED")

