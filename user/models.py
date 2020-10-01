import math
from json.decoder import JSONDecodeError
from threading import Thread
from urllib.parse import quote

import clearbit as clearbit
import requests
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework.exceptions import ValidationError

from core.misc import MyErrorResponse

clearbit.key = settings.CLEARBIT_API_SECRET
clearbit.Person.version = '2019-12-19'


class NetworkUser(AbstractUser):
    # Don't rename fields. They are also HTTP params names.
    # username
    # first_name
    # last_name
    # email
    # password
    # is_staff
    # is_active
    # is_superuser
    # last_login
    # date_joined
    birth_date = models.DateField(null=True)
    location = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)    # TODO: To improve performance should be a foreign key
    state = models.CharField(max_length=100, blank=True)   # ditto
    country = models.CharField(max_length=100, blank=True) # ditto
    lat = models.FloatField(null=True)
    lng = models.FloatField(null=True)
    bio = models.TextField(blank=True)
    site = models.URLField(blank=True)
    avatar = models.URLField(blank=True)

    @staticmethod
    def verify_new_user_email(email):
        if settings.SKIP_EXTERNAL_CALLS:
            return

        url_tmpl = 'https://api.hunter.io/v2/email-verifier?email={}&api_key={}'
        url = url_tmpl.format(quote(email), quote(settings.HUNTER_API_KEY))
        response = requests.get(url)
        if response.status_code != 200:
            return MyErrorResponse({"code": "EXT_01",
                                   "message": "Cannot connect to hunter.io for user email verification. Try again.",
                                   "field": "NONE"})
        try:
            if not response.json()['data']['result'] == 'deliverable':  # my understanding of "verifying email existence" in the technical task
                return MyErrorResponse({"code": "USR_03",
                                        "message": "Email does not verify.",
                                        "field": "email"})
        except (JSONDecodeError, KeyError):
            return MyErrorResponse({"code": "EXT_01",
                                    "message": "Cannot parse hunter.io response.",
                                    "field": "NONE"})

    def fill_data_automatically(self):
        Thread(target=self.do_fill_data_automatically, args=()).start()

    def do_fill_data_automatically(self):
        if settings.SKIP_EXTERNAL_CALLS:
            return

        person = clearbit.Person.find(email=self.email, stream=True)
        # Don't handle errors in details, because error messages may probably contain private information.
        if person == None:
            return

        # My interpretation of "additional information" in the tech specification:
        if not self.first_name:
            self.first_name = person['name']['givenName']
        if not self.last_name:
            self.last_name = person['name']['familyName']
        # ignore person['name']['fullName']
        if not self.location:
            self.location = person['location']
        if not self.city:
            self.city = person['geo']['city']
        if not self.state:
            self.state = person['geo']['state']
        if not self.country:
            self.country = person['geo']['country']
        if self.lat is None:
            self.lat = person['geo']['lat']
        if self.lng is None:
            self.lng = person['geo']['lng']
        if not self.bio:
            self.bio = person['bio']
        # Handle exceptions be sure for the case if ClearBit's concept of URL is not the same as ours:
        if not self.site:
            try:
                self.site = person['site']
            except ValidationError:
                pass
        if not self.avatar:
            try:
                self.avatar = person['avatar']
            except ValidationError:
                pass

        self.save()
