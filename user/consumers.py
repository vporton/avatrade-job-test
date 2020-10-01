import re

import requests
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer


class UserInfoConsumer(WebsocketConsumer):
    consumers = {}

    def connect(self):
        self.user = None
        self.accept()

    def receive(self, *, text_data):
        m = re.match(r'^/auth (.*)$', text_data)
        if not m:
            self.send(text_data="error: syntax")
            return

        token = m[1]
        validator = VerifyJSONWebTokenSerializer()
        try:
            user_info = validator.validate({'token': token})
        except ValidationError:
            self.send(text_data="error: cannot authenticate")
        else:
            self.remove_self()  # possibly switch to different user
            self.user = user_info['user']
            if not self.user.pk in UserInfoConsumer.consumers:
                UserInfoConsumer.consumers[self.user.pk] = {}
            UserInfoConsumer.consumers[self.user.pk].add(self)
            self.send(text_data="ok: user_id={}".format(self.user.pk))

    def disconnect(self, message):
        self.remove_self()
        if self.user and not UserInfoConsumer.consumers[self.user.pk]:
            del UserInfoConsumer.consumers[self.user.pk]

    def remove_self(self):
        if self.user:
            UserInfoConsumer.consumers[self.user.pk].remove(self)

    def notify_user_info_received(self, user_pk, success):
        if not user_pk in UserInfoConsumer.consumers:
            return
        for consumer in UserInfoConsumer.consumers[user_pk]:
            consumer.send("notice: user data received" if success else "error: cannot receive user data")
