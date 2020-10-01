from django.test import TestCase, Client


class FullTestCase(TestCase):
    def setUp(self):
        self.client = Client()

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

    def test_main(self):
        """The test described in the tech specification."""
        pass