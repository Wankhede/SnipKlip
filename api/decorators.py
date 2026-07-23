from functools import wraps
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.decorators import user_passes_test

def group_required(group_name):
    def decorator(view_func):
        @user_passes_test(lambda user: user.groups.filter(name=group_name).exists())
        def wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def jwt_authentication_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        jwt_auth = JWTAuthentication()
        try:
            auth_result = jwt_auth.authenticate(request)
        except Exception:
            auth_result = None
        if auth_result is None:
            return JsonResponse(
                {"message": "Authentication failed", "status": 401},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user, auth = auth_result
        request.user = user
        return view_func(request, *args, **kwargs)

    return _wrapped_view
