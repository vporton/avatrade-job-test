from datetime import datetime
from sqlite3 import DatabaseError

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.misc import MyAPIView, MyErrorResponse
from user.models import User


class SignupView(MyAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        all_fields = ['username',
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

        # may raise an exception
        values = {field: request.POST[field] for field in all_fields if field in request.POST}
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


class RetrieveUserDataView(MyAPIView):
    def post(self, request):
        request.user.fill_data_automatically()  # Will run in background in a separate thread
