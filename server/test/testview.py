"""
    Unit Test Automation for YangExplorer Application

    @author: Neha Kalbhore (neha.Kalbhore@gmail.com)
"""
import os
import logging
from django.test import TestCase, Client
from django.contrib.auth import authenticate
from explorer.models import User
from explorer.views import login_handler
from explorer.utils.misc import ServerSettings

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

    def cleanUp(self):
    	demo.delete()

    def test_login(self):
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

    def test_login_handler(self):
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

    def test_session_handler(self):
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

    def test_upload_handler(self):
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
        upload_file = []
        filelist = ['ietf-inet-types.yang', 'ietf-yang-types.yang', 'ietf-interfaces@2013-12-23.yang']
        for _file in filelist:
            with open(os.path.join(root, _file), 'r') as fp:
                response = self.chrome.post('/explorer/upload-add', {'Filedata' : fp})
                self.assertTrue(response.status_code == 200)
                self.assertTrue('ok' in response.content)
                f = response.content.split('<module>')[1].split('</module>')[0]
                upload_file.append(f.strip())

        # 4. Compile file
        for _file in upload_file:
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
        for _file in upload_file:
            # check if yang file is uploaded
            self.assertTrue(os.path.exists(os.path.join(yang_path, _file)))

            # check if xml file is created
            xml_name = _file.split('.yang')[0] + '.xml'
            self.assertTrue(os.path.exists(os.path.join(cxml_path, xml_name)))

        print("Test: upload_handler PASSED")