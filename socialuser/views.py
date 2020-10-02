from datetime import datetime
from sqlite3 import DatabaseError

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.misc import MyAPIView, MyErrorResponse
from socialuser.consumers import fill_user_data_automatically
from socialuser.models import User


class UserView(MyAPIView):
    permission_classes = [AllowAny]

    the_fields = ['username',
                  'first_name',
                  'last_name',
                  'email',
                  'birth_date',
                  'location',
                  'city',
                  'state',
                  'country',
                  'lat',
                  'lng',
                  'bio',
                  'site',
                  'avatar']

    def post(self, request):
        """Sign up with a username and password."""

        # may raise an exception
        values = {field: request.POST[field] for field in UserView.the_fields if field in request.POST}
        password = request.POST['password']
        request.POST['username']
        request.POST['email']

        # Convert to the right format:
        if 'birth_date' in values:
            year, month, day = values['birth_date'].split('-')  # raises ValueError if wrong quantity of numbers
            values['birth_date'] = datetime.date(year, month, day)  # may raise ValueError
        if 'lat' in values and 'lng' in values:
            values['lat'] = float(values['lat'])
            values['lng'] = float(values['lng'])

        user = User(**values)

        try:
            validate_password(password, user)
        except ValidationError:
            return MyErrorResponse({"code": "USR_04",
                                    "message": "Password too weak.",
                                    "field": "password"})
        user.set_password(password)

        email_verificiation_result = User.verify_new_user_email(user.email)
        if email_verificiation_result is not None:
            return email_verificiation_result

        try:
            with transaction.atomic():
                if User.objects.filter(username=user.username):
                    return MyErrorResponse({"code": "USR_05",
                                            "message": "User with this username already exists.",
                                            "field": "username"})
                user.save()
        except DatabaseError:
            return MyErrorResponse({"code": "OFF_01",
                                    "message": "Server overloaded, try again.",
                                    "field": "NONE"})

        return Response({'code': "OK", 'data': {'user_id': user.pk}})

    def get(self, request):
        user = User.objects.get(pk=request.GET['user_id'])
        data = {field: getattr(user, field) for field in UserView.the_fields}
        data['birth_date'] = data['birth_date'].isoformat() if data['birth_date'] else None

        return Response({'code': "OK", 'data': data})

class RetrieveUserDataView(MyAPIView):
    def post(self, request):
        fill_user_data_automatically(request.user)  # Will run in background in a separate thread
        return Response({'code': "PENDING"})
