from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class MyErrorResponse(Response):
    def __init__(self, data=None, status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        # USR_01 object not found
        # USR_02 invalid data
        # AUT_01 not authorized
        # PAR_01 parameter is missing
        status = {
            'USR': 400,
            'AUT': 401,
            'PAR': 404,
        }.get(data['code'][:3])
        super().__init__(data, status, template_name, headers, exception, content_type)


class MyAPIView(APIView):
    # This code would probably be correct for View but does not work for APIView
    # def dispatch(self, request, *args, **kwargs):
    #     try:
    #         response = super().dispatch(request, *args, **kwargs)
    #     except MultiValueDictKeyError as e:
    #         # It is an unwise assumption that this is necessarily missing HTTP param,
    #         # but rewriting it in other way would be time consuming (and maybe even more error prone).
    #         return MyErrorResponse({"code": "PAR_01",
    #                          "message": "Missing HTTP param.",
    #                          "field": e.args[0]})
    #     return response

    def handle_exception(self, exc):
        if isinstance(exc, NotAuthenticated):
            return MyErrorResponse({"code": "AUT_01",
                                    "message": "The apikey is invalid.",
                                    "field": "API-KEY"})
        if isinstance(exc, MultiValueDictKeyError):
            # It is an unwise assumption that this is necessarily a missing HTTP param,
            # but rewriting it in other way would be time consuming (and maybe even more error prone).
            return MyErrorResponse({"code": "PAR_01",
                                    "message": "Missing HTTP param.",
                                    "field": exc.args[0]})
        if isinstance(exc, ObjectDoesNotExist):
            return MyErrorResponse({"code": "USR_01",
                                    "message": "Object not found.",
                                    "field": "none"})
        return super().handle_exception(exc)
