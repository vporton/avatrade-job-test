import configparser
import itertools
import os
from random import random

import requests
from django.conf import settings
from django.test import TestCase, Client

from user.models import NetworkUser


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
        return {p[0]: int(p[1]) for p in dict(config['numbers']).items()}  # Convert config['numbers'] to numbers.

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

        if numbers['number_of_users'] == 1 and numbers['max_likes_per_user'] != 0:
            print("Contradictory config: Only one user, he cannot like himself.")
            return

        # Sign up users
        # TODO: This format of separate arrays is simple for humans, but is against some basic programming principles.
        passwords = []
        user_ids = []
        for i in range(numbers['number_of_users']):
            passwords.append(NetworkUser.objects.make_random_password())
            response = self.client.post('/user/signup',
                                        {'username': "user{}".format(i), 'password': passwords[i],
                                         'email': 'porton@narod.ru'})
            self.assertEqual(response.json()['code'], 'OK', "Cannot signup user.")
            user_ids.append(response.json()['data']['user_id'])

        # Post posts
        user_posts = []
        for i in range(numbers['number_of_users']):
            user_posts.append([])
            for j in range(int(random(numbers['max_posts_per_user'] + 1))):
                title = "Title{} (user {})".format(j, i)
                text = "Text{} (user {})".format(j, i)
                # TODO: Test posts with no link.
                response = self.client.post('/post/new', {'title': title, 'text': text, 'link': "http://example.com"})
                self.assertEqual(response.json()['code'], 'OK', "Cannot post.")
                user_posts[i].append(response.json()['data']['post_id'])
            assert len(user_posts[i]) <= numbers['max_posts_per_user']

        # To ensure no user has reached max likes yet (not strictly necessary, but simplifies flow analysis):
        if numbers['max_likes_per_user'] == 0:
            return

        # Do likes
        eligible_users = [{'user_number': i, 'user_posts_number': len(user_posts[i])}]
        eligible_users.sort(key=lambda p: p['user_posts_number'])
        users_with_eligible_posts = [{'user_number': i, 'posts_with_zero_likes': len(user_posts[i])}]  # Now all posts are with zero likes.
        while eligible_users:
            # "next user to perform a like is the user who has most posts and has not reached max likes"
            next_user_number = eligible_users.pop()['user_number']

            posts_to_like_by_this_user_grouped_by_author = user_posts.copy()
            posts_to_like_by_this_user_grouped_by_author.pop(next_user_number)  # "users cannot like their own posts"

            posts_to_like_by_this_user = list(itertools.chain(*posts_to_like_by_this_user_grouped_by_author))  # flatten array

            # "user performs “like” activity until he reaches max likes"
            for _ in numbers['max_likes_per_user']:
                if not users_with_eligible_posts:  # "if there is no posts with 0 likes, bot stops"
                    break

                # "user can ... like random posts from users who have at least one post with 0 likes":
                user_with_eligible_posts_index = int(random(len(users_with_eligible_posts)))
                user_with_eligible_posts_info = users_with_eligible_posts[user_with_eligible_posts_index]

                post_to_like = int(random(len(posts_to_like_by_this_user)))
                self.client.post('/post/like', {'post_id': posts_to_like_by_this_user[post_to_like]})
                posts_to_like_by_this_user.pop(post_to_like)  # "one user can like a certain post only once"

                user_with_eligible_posts_info['posts_with_zero_likes'] -= 1
                if user_with_eligible_posts_info['posts_with_zero_likes'] == 0:
                    users_with_eligible_posts.pop(user_with_eligible_posts_index)
