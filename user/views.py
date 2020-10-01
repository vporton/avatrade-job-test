from datetime import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.response import Response

from core.misc import MyAPIView, MyErrorResponse
from user.models import NetworkUser


class SignupView(MyAPIView):
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
        values = [request.POST[field.name] for field in all_fields if field.name in request.POST]
        password = request.POST['password']

        # Convert to the right format:
        year, month, day = values['birth_date'].split('-')  # raises ValueError if wrong quantity of numbers
        values['birth_date'] = datetime.date(year, month, day)  # may raise ValueError
        values['lat'] = float(values['lat'])
        values['lng'] = float(values['lng'])

        user = NetworkUser(*values)

        # TODO: Does set_password already do this validation?
        try:
            validate_password(password, user)  # FIXME: Which validators are used?
        except ValidationError:
            return MyErrorResponse({"code": "USR_04",
                                    "message": "Password too weak.",
                                    "field": "password"})
        user.set_password(password)

        if not NetworkUser.validate_new_user_email(user.email):  # TODO: Rename this function.
            return MyErrorResponse({"code": "USR_03",
                                    "message": "Email does not verify.",
                                    "field": "email"})
        user.save()
        user.fill_data_automatically()  # Will run in background in a separate thread
        return Response({'code': "OK"})
