from django.shortcuts import render
from rest_framework.generics import *
# Create your views here.
import requests
import json
# from main.models import Config
from .models import MessageTemplate
from django.conf import settings
from string import Template
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.permissions import IsAdminUser
from rest_framework import serializers
from auth_app.user_serializers import SafeUserSerializer

class UserSerializer(SafeUserSerializer):
    pass


class Test(ListAPIView):
    queryset = User.objects.all()

    permission_classes = [
        IsAdminUser,
    ]
    serializer_class = UserSerializer


