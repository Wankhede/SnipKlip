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
        user, auth = jwt_auth.authenticate(request)
        if user is not None:
            # User is authenticated, call the view function
            return view_func(request, *args, **kwargs)
        else:
            # User is not authenticated
            return JsonResponse(
                {"message": "Authentication failed"},
                status=status.HTTP_401_UNAUTHORIZED
            )

    return _wrapped_view
