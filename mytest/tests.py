import configparser
import itertools
import os
import re
from random import randrange

import requests
from django.conf import settings
from django.test import TestCase, Client

from socialuser.models import User


class RealClient():
    """Interface similar to `django.test.Client`, but working with a real HTTP server.

    This class is kept simple with only a minimum set of features."""

    def __init__(self, server):
        self.server = server

    def get(self, path, params=None, **kwargs):
        headers = {re.sub(r'^HTTP_', '', p[0]): p[1] for p in kwargs.items() if p[0].startswith('HTTP_')}
        kwargs = {p[0]: p[1] for p in kwargs.items() if not p[0].startswith('HTTP_')}
        return requests.get(self.server + path, params, headers=headers, **kwargs)

    def post(self, path, params=None, **kwargs):
        headers = {re.sub(r'^HTTP_', '', p[0]): p[1] for p in kwargs.items() if p[0].startswith('HTTP_')}
        kwargs = {p[0]: p[1] for p in kwargs.items() if not p[0].startswith('HTTP_')}
        return requests.post(self.server + path, params, headers=headers, **kwargs)


class FullTestCase(TestCase):
    def setUp(self):
        if os.environ.get('REAL_SERVER', ''):
            self.client = RealClient(settings.PROXIED_SERVER_URL)
        else:
            self.client = Client()

    @staticmethod
    def get_config():
        config = configparser.ConfigParser()
        config_file = os.environ.get('BOT_CONFIG', None) or 'mytest/data/config.ini'
        config.read(config_file)
        return {p[0]: int(p[1]) for p in dict(config['numbers']).items()}  # Convert config['numbers'] to numbers.

    def test_auth(self):
        self.assertEqual(self.client.post('/user/data', {'username': 'aa', 'password': 'xx'}).json(),
                         {'code': 'PAR_01', 'field': 'email', 'message': 'Missing HTTP param.'},
                         "Missing email not detected.")
        self.assertEqual(self.client.post('/user/data', {'username': 'aa', 'email': 'tbray@textuality.com'}).json(),
                         {'code': 'PAR_01', 'field': 'password', 'message': 'Missing HTTP param.'},
                         "Missing password not detected.")
        self.assertEqual(self.client.post('/user/data', {'password': 'xx', 'email': 'tbray@textuality.com'}).json(),
                         {'code': 'PAR_01', 'field': 'username', 'message': 'Missing HTTP param.'},
                         "Missing username not detected.")

        self.assertEqual(self.client.post('/user/data', {'username': 'aa', 'password': 'xx', 'email': 'tbray@textuality.com'}).json(),
                         {'code': 'USR_04', 'message': 'Password too weak.', 'field': 'password'},
                         "Weak password not detected.")

        # Test signing up twice with the same username:
        response = self.client.post('/user/data',
                                    {'username': 'duplicate', 'password': User.objects.make_random_password(), 'email': 'tbray@textuality.com'})
        self.assertEqual(response.json()['code'], 'OK', "Cannot signup user: {}".format(response.json().get('message')))
        response = self.client.post('/user/data',
                                    {'username': 'duplicate', 'password': User.objects.make_random_password(), 'email': 'tbray@textuality.com'})
        self.assertEqual(response.json(),
                         {'code': 'USR_05', 'message': 'User with this username already exists.', 'field': 'username'},
                         "Allowed to use the same username twice.")

        # Bill Gates apparently does not read this email.
        response = self.client.post('/user/data',
                                    {'username': 'billgates', 'password': User.objects.make_random_password(), 'email': 'billgates@microsoft.com'})
        self.assertEqual(response.json(),
                         {'code': "USR_03", 'message': "Email does not verify.", 'field': "email"},
                         "This man does not read his email.")

    def test_main(self):
        """The test described in the tech specification."""
        # seed(1)

        numbers = FullTestCase.get_config()

        if numbers['number_of_users'] == 1 and numbers['max_likes_per_user'] != 0:
            print("Contradictory config: Only one user, he cannot like himself.")
            return

        # Sign up users
        passwords = []
        for i in range(numbers['number_of_users']):
            username = "socialuser{}".format(i)
            password = User.objects.make_random_password()
            passwords.append({'username': username, 'password': password})
            response = self.client.post('/user/data',
                                        {'username': username, 'password': password, 'email': 'tbray@textuality.com'})
            self.assertEqual(response.json()['code'], 'OK', "Cannot signup user: {}".format(response.json().get('message')))
            user_id = response.json()['data']['user_id']
            print("Signed up user {} (ID {})".format(username, user_id))

        # Post posts
        user_posts = []
        for i in range(numbers['number_of_users']):
            # See https://jpadilla.github.io/django-rest-framework-jwt/
            auth_token = self.client.post('/api-token-auth/', passwords[i]).json()['token']
            auth_header = "JWT {}".format(auth_token)

            user_posts.append([])
            for j in range(int(randrange(numbers['max_posts_per_user'] + 1))):
                title = "Title{} (user {})".format(j, i)
                text = "Text{} (user {})".format(j, i)
                post_data = {'title': title, 'text': text}
                if randrange(2) != 0:
                    post_data['link'] = "http://example.com"
                response = self.client.post('/post/data', post_data, HTTP_AUTHORIZATION=auth_header)
                self.assertEqual(response.json()['code'], 'OK', "Cannot post: {}".format(response.json().get('message')))
                post_id = response.json()['data']['post_id']
                user_posts[i].append(post_id)
                print("Posted by socialuser {} (post_id {})".format(passwords[i]['username'], post_id))
            assert len(user_posts[i]) <= numbers['max_posts_per_user']

        # To ensure no socialuser has reached max likes yet (not strictly necessary, but simplifies flow analysis):
        if numbers['max_likes_per_user'] == 0:
            return

        # Do likes
        eligible_users_unsorted = ({'user_number': i, 'user_posts_number': len(user_posts[i])} for i in range(numbers['number_of_users']))
        eligible_users = sorted(eligible_users_unsorted, key=lambda p: p['user_posts_number'], reverse=True)

        # Now all posts are with zero likes.
        users_with_eligible_posts = [{'user_number': i, 'posts_with_zero_likes': len(user_posts[i])} for i in range(numbers['number_of_users'])]

        for eligible_user in eligible_users:
            # "next socialuser to perform a like is the socialuser who has most posts and has not reached max likes"
            next_user_number = eligible_user['user_number']

            # See https://jpadilla.github.io/django-rest-framework-jwt/
            auth_token = self.client.post('/api-token-auth/', passwords[next_user_number]).json()['token']
            auth_header = "JWT {}".format(auth_token)

            posts_to_like_by_this_user_grouped_by_author = user_posts.copy()
            posts_to_like_by_this_user_grouped_by_author.pop(next_user_number)  # "users cannot like their own posts"

            posts_to_like_by_this_user = list(itertools.chain(*posts_to_like_by_this_user_grouped_by_author))  # flatten array

            # "socialuser performs “like” activity until he reaches max likes"
            for _ in range(numbers['max_likes_per_user']):
                # print(' '.join(["socialuser={}/posts_with_zero_likes={}".format(h['user_number'], h['posts_with_zero_likes']) \
                #                 for h in users_with_eligible_posts]))
                if not users_with_eligible_posts:  # "if there is no posts with 0 likes, bot stops"
                    break

                # "socialuser can ... like randrange posts from users who have at least one post with 0 likes":
                user_with_eligible_posts_index = int(randrange(len(users_with_eligible_posts)))
                user_with_eligible_posts_info = users_with_eligible_posts[user_with_eligible_posts_index]

                if not posts_to_like_by_this_user:
                    # The tech specification does not tell what to do in this case. Let's stop for this socialuser:
                    break

                post_to_like = int(randrange(len(posts_to_like_by_this_user)))
                post_id = posts_to_like_by_this_user[post_to_like]
                response = self.client.post('/post/like',
                                 {'post_id': post_id},
                                 HTTP_AUTHORIZATION=auth_header)
                self.assertEqual(response.json()['code'], 'OK', "Cannot like: {}".format(response.json().get('message')))
                print("User {} liked post_id {}".format(next_user_number, post_id))
                posts_to_like_by_this_user.pop(post_to_like)  # "one socialuser can like a certain post only once"

                user_with_eligible_posts_info['posts_with_zero_likes'] -= 1
                if user_with_eligible_posts_info['posts_with_zero_likes'] == 0:
                    users_with_eligible_posts.pop(user_with_eligible_posts_index)
