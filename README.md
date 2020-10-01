# avatrade-job-test
A test Python task

## Used packages

I use djangorestframework as a powerful REST framework with easy
debugging.

## Architecture decisions

I use `django.contrib.auth.User` as the base of my User model,
because 1. it is convenient; 2. it provides some useful fields
builtin; 3. it eases integration with Django functions like
authentication. The drawback is unnecessary fields that may take
extra DB storage (what can be solved with data migrations in a
future version).
