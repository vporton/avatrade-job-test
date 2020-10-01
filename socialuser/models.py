from json.decoder import JSONDecodeError
from urllib.parse import quote

import clearbit as clearbit
import requests
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

from core.misc import MyErrorResponse

clearbit.key = settings.CLEARBIT_API_SECRET
clearbit.Person.version = '2019-12-19'


class User(AbstractUser):
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
                                   "message": "Cannot connect to hunter.io for socialuser email verification. Try again.",
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
