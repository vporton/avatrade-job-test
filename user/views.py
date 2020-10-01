from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import NetworkUser


class Signup(APIView):
    def post(self, request):
        all_fields = NetworkUser._meta.fields
        user = NetworkUser(*(request.POST[field.name] for field in all_fields if field.name in request.POST))  # TODO: validate fields
        if not NetworkUser.validate_new_user_email(user.email):
            return Response({})  # FIXME
        user.save()
        user.fill_data_automatically()  # Will run in background in a separate thread
        return Response({})  # FIXME # TODO: Also set password correctly (may be None) and return here the JWT
