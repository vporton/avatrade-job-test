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

Used Node.js for testing WebSockets, see above.

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

I use the same POST/GET request params as model field names.
Non-essential fields can be omitted.

### Errors

Error responses follow the format like:
```json
{
  "code": "USR_04",
  "message": "Password too weak.",
  "field": "password"
}
```
(Here `code` is the error code (see `core/misc.py`), `message` is
the error message, and `field` is sometimes the information about
the HTTP param name with an error.)

For non-error responses, `code` is `OK` (`PENDING` for
`/user/request-retrieve-data`) and the data is under `data`
subdictionary.

### API endpoints

* `/api-token-auth/` does password authentication (`username` and
`password` HTTP params).

* `/api-token-verify/` (not used) performs token verification.

* `/user/data` performs user signup (with POST) or getting
  user data (GET)

* `/user/request-retrieve-data` (POST) initiates requesting user
  data from Clearbit. It returns `{"code": "PENDING"}` immediately
  and if a WebSocket connection is already opened, this connection
  will be notified when the data is retrieved.

* `/post/data` (POST) post a post.

* `/post/read` (GET) read a post.

### WebSocket

Endpoint `user-watch`.

First send `/auth <TOKEN>` to authenticate and receive back
`ok: user_id=<NUMBER>` or `error: cannot authenticate`.

Then we will receive notices `notice: socialuser data received`
or `error: cannot receive socialuser data` (if Clearbit retrieval
fails).

## Other notes

Repeated (un)likes are ignored, because:

- It was not required to detect them in the tech specification.
- Detecting them requires additional DB queries.

Password authentication may be somehow insecure, but there is
no other way to accomplish the tech specification as it is
given.
