"""Uniform API error envelope: {"error": {"detail": ..., "status": ...}}."""
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"error": {"detail": response.data, "status": response.status_code}}
    return response
