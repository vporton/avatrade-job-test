from rest_framework.response import Response

from core.misc import MyAPIView, MyErrorResponse
from user.models import NetworkUser


class SignupView(MyAPIView):
    def post(self, request):
        all_fields = ['username',
                      'first_name',
                      'last_name',
                      'email',
                      'birth_date',  # FIXME: DateField
                      'location',
                      'city',
                      'state',
                      'country',
                      'lat',  # FIXME: FloatField
                      'lng',  # FIXME: FloatField
                      'bio',
                      'site',
                      'avatar']
        user = NetworkUser(*(request.POST[field.name] for field in all_fields if field.name in request.POST))  # TODO: validate fields
        if not NetworkUser.validate_new_user_email(user.email):  # TODO: Rename this function.
            return MyErrorResponse({"code": "USR_03",
                                    "message": "Email does not verify.",
                                    "field": "email"})
        user.save()
        user.fill_data_automatically()  # Will run in background in a separate thread
        return Response({'code': "OK"})  # FIXME # TODO: Also set password correctly (may be None)
