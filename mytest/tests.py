from django.test import TestCase, Client


class FullTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_auth(self):
        self.assertEqual(self.client.post('/user/signup', {'username': 'aa', 'password': 'xx'}).json(),
                         {'code': 'USR_04', 'message': 'Password too weak.', 'field': 'password'},
                         "Weak password not detected.")

    def test_main(self):
        """The test described in the tech specification."""
        pass