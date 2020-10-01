from django.db import models
from django.contrib.auth.models import AbstractUser


class NetworkUser(AbstractUser):
    birth_date = models.DateField()
