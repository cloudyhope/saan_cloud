from rest_framework import serializers
from .models import (
    Country,
    Province,
    City,
    Config,
)

from main.modules.serializers import AdditionalSerializer

from django.forms import IntegerField, UUIDField
from django.utils.translation import gettext_lazy as _
from pkg_resources import require
from rest_framework import exceptions, serializers, validators
from rest_framework.exceptions import ValidationError
from main.modules.exceptions import *
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, SlidingToken, UntypedToken
from rest_framework_simplejwt.serializers import TokenObtainSerializer

from .models import *
from main.modules.serializers import AdditionalSerializer
from django.db import transaction
from django.contrib.auth.validators import UnicodeUsernameValidator
#############################
# Health Check:
#############################

class HealthCheckSerializer(serializers.Serializer):
    detail = serializers.CharField(allow_null=True, allow_blank=True)

    class Meta:
        fields = '__all__'

#############################
# Region:
#############################

class CountrySerializer(AdditionalSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class ProvinceSerializer(AdditionalSerializer):
    class Meta:
        model = Province
        fields = '__all__'

class NestedProvinceSerializer(AdditionalSerializer):
    country = CountrySerializer()
    class Meta:
        model = Province
        fields = '__all__'


class CitySerializer(AdditionalSerializer):
    class Meta:
        model = City
        fields = '__all__'


class NestedCitySerializer(AdditionalSerializer):
    province = ProvinceSerializer()

    class Meta:
        model = City
        fields = '__all__'

#############################
# Config:
#############################

class ConfigSerializer(AdditionalSerializer):
    class Meta:
        model = Config
        fields = '__all__'

class SpecificationTypeSerializer(AdditionalSerializer):
    class Meta:
        model = SpecificationType
        fields = '__all__'

#############################
# Auth:
#############################



class PasswordField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['write_only'] = True

        super().__init__(*args, **kwargs)


class TokenObtainPhoneNumberOTPSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD
    default_error_messages = {
        'no_active_account': _('No active account found with the given credentials')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
        }
        self.user = authenticate()
        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        return {}

    @classmethod
    def get_token(cls, user):
        raise NotImplementedError(
            'Must implement `get_token` method for `TokenObtainSerializer` subclasses')


class MyTokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.username_password_auth:
            raise exceptions.AuthenticationFailed(
                _('Not Permitted!')
            )
        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data

class UserSerializer(AdditionalSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',)


class PhoneOTPVerifyAPISerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True, required=True)
    verification_token = serializers.CharField(write_only=True, required=True)
    code = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(write_only=True, required=True)
    access = serializers.CharField(read_only=True)
    resresh = serializers.CharField(read_only=True)


class RequestOTPSerializer(AdditionalSerializer):
    class Meta:
        model = PhoneOTP
        fields = '__all__'

class RoleSerializer(AdditionalSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class ProfileSerializer(AdditionalSerializer):
    # roles = RoleSerializer(many=True)
    city = CitySerializer()
    class Meta:
        model = Profile
        # fields = '__all__'
        exclude = ('roles',)


class ProfileWithUserSerializer(AdditionalSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        exclude = ['roles']


class ProfileSafeSerializer(AdditionalSerializer):
    class Meta:
        model = Profile
        exclude = ['roles', 'user',]


class LiteProfileSerializer(AdditionalSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class LiteUserSerializer(AdditionalSerializer):
    extended = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'extended',)
    
    def get_extended(self, obj):
        query = Profile.objects.filter(user = obj)
        if len(query) > 0:
            return LiteProfileSerializer(query[0], many=False).data
        else:
            return LiteProfileSerializer(Profile(), many=False).data


class ExtendedUserSerializer(AdditionalSerializer):
    extended = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = '__all__'

    def get_extended(self, obj):
        query = Profile.objects.filter(user = obj)
        if len(query) > 0:
            return ProfileSerializer(query[0], many=False).data
        else:
            return ProfileSerializer(Profile(), many=False).data
            return ReferralCodeBaseSerializer(code, many=False).data




######################################
# Users Utils:
######################################

class ViewMethodSerializer(AdditionalSerializer):
    class Meta:
        model = ViewMethod
        fields = '__all__'

class NestedRoleSerializer(AdditionalSerializer):
    permissions = ViewMethodSerializer(many=True)
    class Meta:
        model = Role
        fields = '__all__'

class FullNestedProfile(AdditionalSerializer):
    user = UserSerializer()
    roles = RoleSerializer(many=True)

    class Meta:
        model = Profile
        fields = '__all__'



class AddressSerializer(AdditionalSerializer):
    class Meta:
        model = Address 
        fields = '__all__'

class NestedAddressSerializer(AdditionalSerializer):
    city = CitySerializer()
    type = SpecificationTypeSerializer()
    class Meta:
        model = Address 
        fields = '__all__'


class ProfileChangeRoleSerializer(serializers.Serializer):
    do_delete = serializers.BooleanField(allow_null=True, default=False)
    do_add = serializers.BooleanField(allow_null=True, default=False)
    roles_list = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)


class RoleChangeProfileSerializer(serializers.Serializer):
    do_delete = serializers.BooleanField(allow_null=True, default=False)
    do_add = serializers.BooleanField(allow_null=True, default=False)
    Profiles = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)


class UserCreateSerializer(AdditionalSerializer):
    password = serializers.SerializerMethodField(allow_null=True)
    email = serializers.SerializerMethodField(allow_null=True)

    def get_password(self, obj):
        return None

    def get_email(self, obj):
        return '<EMAIL>'

    def create(self, validated_data):
        instance, _ = User.objects.get_or_create(
            username=validated_data['username'],
            defaults={'password': make_password(None)},
        )
        return instance

    class Meta:
        model = User
        fields = ('username', 'password', 'email', )
        extra_kwargs = {
            'username': {
                'validators': [UnicodeUsernameValidator()],
            }
        }


class ProfileFullSerializer(AdditionalSerializer):
    user = UserCreateSerializer()

    class Meta:
        model = Profile
        exclude = ['roles',]

    def create(self, validated_data):
        instance, _ = Profile.objects.get_or_create(**validated_data)
        return instance


class BulkAdminMultiUserCreateSerializer(serializers.Serializer):
    users = ProfileFullSerializer(many=True)

    def create(self, validated_data):
        users_data = validated_data['users']
        created_users = {'users': []}

        for user_data in users_data:
            with transaction.atomic():
                user_info = user_data.pop('user')
                user_serializer = UserCreateSerializer(data=user_info)
                is_valid = user_serializer.is_valid(raise_exception=False)
                if not is_valid:
                    continue

                user = user_serializer.save()

                profile = Profile.objects.filter(user=user)
                if not profile.first():
                    profile, _ = Profile.objects.get_or_create(user=user, **user_data)
                    profile.roles.set([Role.objects.filter(role_title="endUser").order_by("-id").first()])
                    profile.save()
                    from utils.modules.farapayamak import FaraPayamak
                    user_client = FaraPayamak(user.username)
                    user_client.type_send("USER_FIRST_LOGIN_BY_ADMIN", **user_client.flatten_dict(ProfileSerializer(profile, many=False).data))
                    del user_client

                    created_users['users'].append(profile)

                if not api_settings.USER_AUTHENTICATION_RULE(user):
                    raise exceptions.AuthenticationFailed(
                        self.error_messages['no_active_account'],
                        'no_active_account',
                    )
                from wallet.core import WalletCore
                core = WalletCore()
                general_wallet = core.check_general_wallet_for_user(user)

        return created_users


class EasyProfileFullSerializer(AdditionalSerializer):
    user = serializers.CharField()

    class Meta:
        model = Profile
        exclude = ['roles', ]

    def create(self, validated_data):
        username = validated_data.pop('user')
        user = UserCreateSerializer(data=username)
        user.save()
        user, _ = User.objects.get_or_create(username=username)
        profile, _ = Profile.objects.get_or_create(user=user, **validated_data)
        return profile


class EasyBulkAdminMultiUserCreateSerializer(serializers.Serializer):
    users = EasyProfileFullSerializer(many=True)

    def create(self, validated_data):
        users_data = validated_data['users']
        created_users = {'users': []}

        for user_data in users_data:
            with transaction.atomic():
                username = user_data.pop('user')
                user_serializer = UserCreateSerializer(data={'username': username})
                is_valid = user_serializer.is_valid(raise_exception=False)
                if not is_valid:
                    continue

                user = user_serializer.save()

                profile = Profile.objects.filter(user=user).first()
                if not profile:
                    profile = Profile.objects.create(user=user, **user_data)
                    profile.roles.set([Role.objects.filter(role_title="endUser").order_by("-id").first()])
                    profile.save()

                    # Send the notification to the user
                    from utils.modules.farapayamak import FaraPayamak
                    user_client = FaraPayamak(user.username)
                    user_client.type_send("USER_FIRST_LOGIN_BY_ADMIN",
                                          **user_client.flatten_dict(ProfileSerializer(profile, many=False).data))
                    del user_client

                    if not api_settings.USER_AUTHENTICATION_RULE(user):
                        raise exceptions.AuthenticationFailed(
                            self.error_messages['no_active_account'],
                            'no_active_account',
                        )

                    # Create general wallet for the user
                    from wallet.core import WalletCore
                    core = WalletCore()
                    general_wallet = core.check_general_wallet_for_user(user)

                    created_users['users'].append(profile)

        return created_users


###############################
# Company APIs:
###############################

class CompanySerializer(AdditionalSerializer):
    class Meta:
        model = Company
        fields = '__all__'


###############################
# RequestLog APIs: 
###############################


from .models import RequestLog


class RequestLogSerializer(AdditionalSerializer):
    class Meta:
        model = RequestLog
        fields = '__all__'

class RoleAssignmentSerializer(AdditionalSerializer):
    user = UserSerializer()
    role = RoleSerializer()

    class Meta:
        model = RoleAssignment
        fields = '__all__'


class UserManagementSerializer(AdditionalSerializer):
    # extended = ExtendedUser() 

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name',)
        extra_kwargs = {'password': {'write_only': True}}


class RoleAssignmentCreateSerializer(AdditionalSerializer):
    change_password = serializers.BooleanField()
    user = UserManagementSerializer()

    class Meta:
        model = RoleAssignment
        fields = '__all__'

