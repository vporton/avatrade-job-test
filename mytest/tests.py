from django.test import TestCase, Client


class FullTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_auth(self):
        print(self.client.post('/user/signup', {'username': 'aa', 'password': 'xx'}).json())

    def test_main(self):
        """The test described in the tech specification."""
        pass