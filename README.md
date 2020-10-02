# avatrade-job-test
A test Python task

## Running

Settings are stored in `local_settings.py`:
```python
DEBUG = False
HUNTER_API_KEY = ...
CLEARBIT_API_SECRET = ...
```

You can also configure any Django-supported DB here if SQLite does
not suffice.

To run:
```sh
virtualenv -p python3 venv
source venv/bin/activate
./manage.py migrate
./manage.py runserver
```
or it can be run with uWSGI (see Django docs).

Testing is accomplished by
```sh
./manage.py test
```
or
```sh
REAL_SERVER=1 ./manage.py test
```
where only the second tries to connect to the actual server and
make actual HTTP requests. (The first imitates HTTP protocol features
without actually using it.)

To run only the "automated bot" described in the specification:
```sh
./manage.py test mytest.tests.FullTestCase.test_main
```
(It is implemented using Django tests, because its task is related
to testing.)

More testing is done by JavaScript because with Django it appeared
difficult to test WebSocket interactions.

```sh
yarn upgrade
npm test --recursive "./mytest/*.js"
```

## Used packages

I use `djangorestframework` as a powerful REST framework with easy
debugging.

`requests` for making HTTP(S) requests to external servers.

Because it was said to use JWT but nothing about OAuth/OpenID Connect,
I do it in an easy way using `django-rest-framework-jwt`.

Should use `django-defender` against brute force password guessing,
but it required Cron for proper functionality (otherwise it grows
the DB too quick). I could create a
Debian package or another kind of automatic installer, but I was
not specified the exact operating system.

I use Django channels (not REST) to notify about Crearbit information
retrival asynchronously, because it may be slow.

## Architecture decisions

I use `django.contrib.auth.User` as the base of my User model,
because 1. it is convenient; 2. it provides some useful fields
builtin; 3. it eases integration with Django functions like
authentication. The drawback is unnecessary fields that may take
extra DB storage (what can be solved with data migrations in a
future version).

I retrieve data from Clearbit in a background thread because it
may be time consuming.

Normal responses are passed in the field `data` to differentiate
them from error info and other possible auxiliary information.

For test config I use `.ini` format to be easily understandable
and editable. The bot config is read from the file passed by
`BOT_CONFIG` environment variable (or `mytest/data/config.ini` by
default, see that file for an example bot config).

## API

I use the same POST request params as model field names.

Repeated (un)likes are ignored, because:

- It was not required to detect them in the tech specification.
- Detecting them requires additional DB queries.
