from datetime import datetime

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
        values = [request.POST[field.name] for field in all_fields if field.name in request.POST]

        # Convert to the right format:
        year, month, day = values['birth_date'].split('-')  # raises ValueError if wrong quantity of numbers
        values['birth_date'] = datetime.date(year, month, day)  # may raise ValueError
        values['lat'] = float(values['lat'])
        values['lng'] = float(values['lng'])

        user = NetworkUser(*values)
        if not NetworkUser.validate_new_user_email(user.email):  # TODO: Rename this function.
            return MyErrorResponse({"code": "USR_03",
                                    "message": "Email does not verify.",
                                    "field": "email"})
        user.save()
        user.fill_data_automatically()  # Will run in background in a separate thread
        return Response({'code': "OK"})  # TODO: Also set password correctly (may be None)
