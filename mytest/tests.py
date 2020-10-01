import configparser
import os

import requests
from django.conf import settings
from django.test import TestCase, Client


class RealClient():
    """Interface similar to `django.test.Client`, but working with a real HTTP server.

    This class is kept simple with only a minimum set of features."""

    def __init__(self, server):
        self.server = server

    def get(self, path, params=None):
        return requests.get(self.server + path, params)

    def post(self, path, params=None):
        return requests.post(self.server + path, params)


class FullTestCase(TestCase):
    def setUp(self):
        if os.environ.get('REAL_SERVER', ''):
            self.client = RealClient(settings.SERVER_URL)
        else:
            self.client = Client()

    @staticmethod
    def get_config():
        config = configparser.ConfigParser()
        config_file = os.environ.get('BOT_CONFIG', None) or 'mytest/data/config.ini'
        config.read(config_file)
        return config['numbers']

    def test_auth(self):
        self.assertEqual(self.client.post('/user/signup', {'username': 'aa', 'password': 'xx'}).json(),
                         {'code': 'PAR_01', 'field': 'email', 'message': 'Missing HTTP param.'},
                         "Missing email not detected.")
        self.assertEqual(self.client.post('/user/signup', {'username': 'aa', 'email': 'porton@narod.ru'}).json(),
                         {'code': 'PAR_01', 'field': 'password', 'message': 'Missing HTTP param.'},
                         "Missing password not detected.")
        self.assertEqual(self.client.post('/user/signup', {'password': 'xx', 'email': 'porton@narod.ru'}).json(),
                         {'code': 'PAR_01', 'field': 'username', 'message': 'Missing HTTP param.'},
                         "Missing username not detected.")

        self.assertEqual(self.client.post('/user/signup', {'username': 'aa', 'password': 'xx', 'email': 'porton@narod.ru'}).json(),
                         {'code': 'USR_04', 'message': 'Password too weak.', 'field': 'password'},
                         "Weak password not detected.")

        # TODO: Test signing up with the same username or the same email.

    def test_main(self):
        """The test described in the tech specification."""
        numbers = FullTestCase.get_config()
