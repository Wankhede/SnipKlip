from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from rest_framework.permissions import BasePermission


def in_group(group_name):
    """
    Returns a function that checks if the user is in the specified group.
    """
    def check_group(user):
        if user.is_authenticated:
            return user.groups.filter(name=group_name).exists()
        return False
    return check_group


def group_match(group_name,request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name=group_name).exists() == False:
            response = False
        else:
            response = True
    return response


class UserInGroupPermission(BasePermission):
    """
    Permission class that restricts access to a view based on group membership.
    """
    def __init__(self, group_name):
        self.group_name = group_name

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name=self.group_name).exists()

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return redirect('/login/')

        return True
