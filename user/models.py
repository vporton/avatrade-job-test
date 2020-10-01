from urllib.parse import quote

import clearbit as clearbit
import requests
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework.exceptions import ValidationError

clearbit.key = settings.CLEARBIT_API_SECRET
clearbit.Person.version = '2019-12-19'


class NetworkUser(AbstractUser):
    birth_date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    lat = models.FloatField(default=float("NAN"))
    lng = models.FloatField(default=float("NAN"))
    bio = models.TextField(blank=True)
    site = models.URLField(blank=True)
    avatar = models.URLField(blank=True)


    def validate_new_user(self):
        url_tmpl = 'https://api.hunter.io/v2/email-verifier?email={}&api_key={}'
        url = url_tmpl.format(quote(self.email), quote(settings.HUNTER_API_KEY))
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Cannot connect to hunter.io for user email verification. Try again.")
        # Consider no ['data']['result'] as an internal error and suffice with KeyNotFound exception as the error signal.
        return response.json()['data']['result'] == 'deliverable'  # my understanding of "verifying email existence" in the technical task

    def fill_data_automatically(self):
        person = clearbit.Person.find(email=self.email, stream=True)  # TODO: Run it in a separate thread.
        # Don't handle errors in details, because error messages may probably contain private information
        if person != None:
            self.first_name = person['name']['givenName']
            self.last_name = person['name']['familyName']
            # ignore person['name']['fullName']
            self.location = person['location']
            self.city = person['geo']['city']
            self.state = person['geo']['state']
            self.country = person['geo']['country']
            self.lat = person['geo']['lat']
            self.lng = person['geo']['lng']
            self.bio = person['bio']
            # Handle exceptions be sure for the case if ClearBit's concept of URL is not the same as ours:
            try:
                self.site = person['site']
            except ValidationError:
                pass
            try:
                self.avatar = person['avatar']
            except ValidationError:
                pass
