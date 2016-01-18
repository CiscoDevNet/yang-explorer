"""
    Unit Test Automation for YangExplorer Application

    @author: Neha Kalbhore (neha.Kalbhore@gmail.com)
"""

import logging
from django.test import TestCase, Client
from django.contrib.auth import authenticate
from explorer.models import User
from explorer.views import login_handler

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
        
