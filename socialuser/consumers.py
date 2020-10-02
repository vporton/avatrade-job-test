import re
from threading import Thread

import clearbit
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer, jwt_get_username_from_payload

from socialuser.models import User


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
        try:
            # TODO: Report bug of djangorestframework-jwt==1.11.0 - it tries to User.objects.get_by_natural_key(username) for wrong user model.
            # user_info = VerifyJSONWebTokenSerializer().validate({'token': token})
            payload = VerifyJSONWebTokenSerializer()._check_payload(token=token)
            username = jwt_get_username_from_payload(payload)
            self.remove_self()  # possibly switch to different socialuser
            with open("/home/porton/t/x.txt", 'w') as f:
                f.write(username)
            self.user = User.objects.get(username=username)
        except (ValidationError, User.DoesNotExist) as e:
            self.send(text_data="error: cannot authenticate" + str(e))
        else:
            if not self.user.pk in UserInfoConsumer.consumers:
                UserInfoConsumer.consumers[self.user.pk] = set()
            UserInfoConsumer.consumers[self.user.pk].add(self)
            self.send(text_data="ok: user_id={}".format(self.user.pk))

    def disconnect(self, message):
        self.remove_self()
        if self.user and not UserInfoConsumer.consumers[self.user.pk]:
            del UserInfoConsumer.consumers[self.user.pk]

    def remove_self(self):
        if self.user:
            UserInfoConsumer.consumers[self.user.pk].remove(self)

    @staticmethod
    def notify_user_info_received(user_pk, success):
        if not user_pk in UserInfoConsumer.consumers:
            return
        for consumer in UserInfoConsumer.consumers[user_pk]:
            consumer.send("notice: socialuser data received" if success else "error: cannot receive socialuser data")


def fill_user_data_automatically(user):
    Thread(target=do_fill_user_data_automatically, args=(user,)).start()


def do_fill_user_data_automatically(user):
    if settings.SKIP_EXTERNAL_CALLS:
        return

    person = clearbit.Person.find(email=user.email, stream=True)
    # Don't handle errors in details, because error messages may probably contain private information.
    if person == None:
        UserInfoConsumer.notify_user_info_received(user.pk, success=False)
        return

    # My interpretation of "additional information" in the tech specification:
    if not user.first_name:
        user.first_name = person['name']['givenName']
    if not user.last_name:
        user.last_name = person['name']['familyName']
    # ignore person['name']['fullName']
    if not user.location:
        user.location = person['location']
    if not user.city:
        user.city = person['geo']['city']
    if not user.state:
        user.state = person['geo']['state']
    if not user.country:
        user.country = person['geo']['country']
    if user.lat is None:
        user.lat = person['geo']['lat']
    if user.lng is None:
        user.lng = person['geo']['lng']
    if not user.bio:
        user.bio = person['bio']
    # Handle exceptions be sure for the case if ClearBit's concept of URL is not the same as ours:
    if not user.site:
        try:
            user.site = person['site']
        except ValidationError:
            pass
    if not user.avatar:
        try:
            user.avatar = person['avatar']
        except ValidationError:
            pass

    user.save()
    UserInfoConsumer.notify_user_info_received(user.pk, success=True)
