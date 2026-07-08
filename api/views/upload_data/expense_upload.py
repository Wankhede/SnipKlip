from rest_framework.response import Response
from backend.models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
import random
import string


def insert_expense(request):
    pass