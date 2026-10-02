from rest_framework.response import Response

from rest_framework import generics

from main.modules.views import (
    List,
    Create,
    ListCreate,
    Retrieve,
    Update,
    Destroy,
    RetrieveDestroy,
    RetrieveUpdate,
    RetrieveUpdateDestroy,
    Generic,
)
from .models import *
from .serializers import *

from rest_framework.permissions import AllowAny
from main.modules.permissions import RolePermission
from .models import *
from django.db.models import Q

class HealthCheck(generics.GenericAPIView):
    serializer_class = HealthCheckSerializer

    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        data = {'detail': 'healthy'}
        return Response(data, status=200)


###################################
# Config CR:
###################################

class CountryList(List):
    def get_queryset(self):
        return Province.objects.all()

    serializer_class = ProvinceSerializer

    permission_classes = [
        AllowAny,
    ]


class ProvinceList(List):
    def get_queryset(self):
        return Province.objects.all()

    serializer_class = ProvinceSerializer

    permission_classes = [
        AllowAny,
    ]


class CityList(List):
    def get_queryset(self):
        return City.objects.all()

    serializer_class = CitySerializer

    permission_classes = [
        AllowAny,
    ]


###################################
# Config RUD:
###################################

class ProvinceRetrieve(Retrieve):
    def get_queryset(self):
        return Province.objects.all()

    serializer_class = ProvinceSerializer


class CityRetrieve(Retrieve):
    def get_queryset(self):
        return City.objects.all()

    serializer_class = CitySerializer


#####################################
# Terms and Conditions:
#####################################

class TermsAndConditionsList(List):
    def get_queryset(self):
        return Config.objects.filter(category='TERMS_AND_CONDITIONS')

    serializer_class = ConfigSerializer

#####################################
# Auth:
#####################################


from datetime import datetime, date, timedelta
from math import prod
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
# from rest_framework import exceptions, generics, serializers, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from rest_framework.views import APIView
from main.modules.exceptions import *
from django.utils.translation import gettext_lazy as _
# from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from django.db.models import Min, Sum, F, BigIntegerField
import os
import requests
import json
import hashlib

from django.conf import settings

from .models import *

from django.contrib.auth import get_user_model

User = get_user_model()
from random import randint

from .authentication_backends import get_tokens_for_user

from .serializers import *

from main.modules.views import (
    List, 
    Create,
    ListCreate,
    Retrieve,
    Update,
    Destroy,
    RetrieveDestroy,
    RetrieveUpdate,
    RetrieveUpdateDestroy,
    Generic,
    )


###################################################
# Checks that if A User is authenticated or not:
###################################################


class CheckAuthenticationView(Generic):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        AllowAny,
    ]
    def get(self, request):
        if request.user.is_authenticated:
            return Response({"is_authenticated": True})
        else:
            return Response({"is_authenticated": False})



######################################################
# OTP Request:
######################################################

class RequestOTP(Create):
    serializer_class = RequestOTPSerializer
    queryset = PhoneOTP.objects.none()

    permission_classes = [
        AllowAny,
    ]

    def perform_create(self, serializer):
        # Generate Code:
        # try:
        #     user = User.objects.get(username=self.request.data['phone_number'])
        # except:
        #     raise NotFound("No user found with this credentials!")
        code = str(randint(10000, 99999))
        print(code)
        hash = hashlib.sha256()
        hash.update((str(datetime.utcnow()) +
                    str(self.request.data["phone_number"]) + str(code)).encode('UTF-8'))
        verification_token = hash.hexdigest().lower()
        # Send SMS
        if 'notification' in settings.PROJECT_APPS:
            from notification.modules.otp import SendOTP
            sms = SendOTP(destination=self.request.data['phone_number'], code=code)
        obj = serializer.save(code=code, verification_token=verification_token)
        instance_serialized = RequestOTPSerializer(obj, many=False).data
        if settings.PRODUCTION:
            instance_serialized.pop("code", None)
        print(instance_serialized)
        raise CustomResponse(instance_serialized)




######################################################
# OTP Verify and Authenticate:
######################################################


class VerifyPhoneNumberOTPAPIView(Generic):
    serializer_class = PhoneOTPVerifyAPISerializer
    queryset = PhoneOTP.objects.all()
    permission_classes = [AllowAny, ]

    def post(self, request):
        id = request.data['id']
        code = request.data['code']
        verification_token = request.data['verification_token']
        phone_number = request.data['phone_number']
        first_login = False
        try:
            obj = PhoneOTP.objects.get(id=id)
        except:
            raise BadRequest
        if obj.code == code and obj.verification_token == verification_token and obj.phone_number == phone_number and obj.wrong_answers_count < 3:
            if timedelta(minutes=2) >= datetime.utcnow() - obj.datetime_requested.replace(tzinfo=None):
                # Authenticate user:
                user_objects = User.objects.filter(username=phone_number)
                if len(user_objects) == 0:
                    # raise NotFound("no user found with this credentials")
                    user_object = User.objects.create_user(username=phone_number, password='9C4mkZbX9ScVvZVJ8igPIzgpW1n3ovBr7W0Ypo0b', email=None)
                    profile_obj = Profile()
                    profile_obj.user = user_object
                    profile_obj.save()
                    profile_obj.roles.add(Role.objects.filter(role_title="endUser").order_by("-id")[0])
                    profile_obj.save()
                    first_login = True
                    # from utils.modules.farapayamak import SMS
                    # user_client = SMS(phone_number)
                    # user_client.type_send("USER_FIRST_LOGIN", **user_client.flatten_dict(ProfileSerializer(profile_obj, many=False).data))
                    # del user_client
                else:
                    user_object = user_objects[0]
                    profile_obj = Profile.objects.get(user=user_object)
                user = UserSerializer(user_object, many=False).data
                if not api_settings.USER_AUTHENTICATION_RULE(user_object):
                    raise exceptions.AuthenticationFailed(
                        self.error_messages['no_active_account'],
                        'no_active_account',
                    )
                tokens = get_tokens_for_user(user_object)
                role = ProfileSerializer(profile_obj, many=False).data
                # if not ReferralCode.objects.filter(user=user_object).exists():
                #     referral_code = ReferralCode()
                #     referral_code.user = user_object
                #     referral_code.save()
                # else:
                #     referral_code = ReferralCode.objects.filter(user=user_object)[0]
                # from wallet.core import WalletCore
                # core = WalletCore()
                # general_wallet = core.check_general_wallet_for_user(user_object)
                response = {
                    "user": user,
                    "role": role,
                    "tokens": tokens,
                    "first_login": first_login,
                    # "referral_code": ReferralCodeBaseSerializer(referral_code, many=False).data,
                    # "general_wallet_public_address": general_wallet.public_address
                }
                return Response(response)
            else:
                raise TooLate
        else:
            raise NotAcceptable

class MeView(ListCreate):
    permission_classes = [
        IsAuthenticated,
    ]
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ExtendedUserSerializer
        else:
            return ProfileSafeSerializer
    
    def get_queryset(self):
        if self.request.method == 'GET':
            return User.objects.filter(username=self.request.user.username)
        else:
            return Profile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # print(serializer, type(serializer), str(serializer))
        # return
        query = Profile.objects.filter(user=self.request.user)
        if len(query) > 0:
            extended_user = query[0]
            for i in self.request.data.keys():
                if i in ['roles', 'user']:
                    raise PermissionDenied
                setattr(extended_user, i, self.request.data[i])
            extended_user.save()
            return Response({"detail": "ok"})
        return serializer.save(user=self.request.user)




######################################
# Users List:
######################################


class ProfileList(List):
    def get_queryset(self):
        return Profile.objects.all()

    def get_serializer_class(self):
        return FullNestedProfile

    filterset_fields = {
        'user': ['exact',],
        'user__username': ['exact',],
        'first_name': ['exact',],
        'last_name': ['exact',],
        'national_code': ['exact',],
        'birth_date': ['exact',],
        'job': ['exact',],
        'sheba': ['exact',],
        'user__first_name': ['exact',],
        'user__last_name': ['exact',],
    }    

    search_fields = ['first_name', 'last_name']


class ProfileUpdate(Generic):
    def get_queryset(self):
        base = Profile.objects.filter(user=self.request.user)
        if not base.exists():
            obj = Profile()
            obj.user = self.request.user
            obj.save()
        return base
    
    serializer_class = ProfileSafeSerializer

    def post(self, request, *args, **kwargs):
        instance = self.get_queryset().first()
        safe_fields = [
            "first_name",
            "last_name",
            "national_code",
            "birth_date",
            "job",
            "sheba",
        ]
        for key in self.request.data.keys():
            if key not in safe_fields:
                continue
            setattr(instance, key, self.request.data[key])
        instance.save()
        return Response(ProfileSafeSerializer(instance, many=False).data)


###################################
# Admin:
###################################


class ProfileRetrieve(Retrieve):
    def get_queryset(self):
        return Profile.objects.all()

    def get_serializer_class(self):
        return FullNestedProfile

    lookup_field = 'user'


class AdminMultiUserCreate(ListCreate):

    queryset = Profile.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BulkAdminMultiUserCreateSerializer
        return ProfileFullSerializer


class AddOrRemoveRoleFromProfile(RetrieveUpdate):

    permission_classes = [AllowAny]

    queryset = Profile.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProfileSerializer
        return ProfileChangeRoleSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        profile_obj = self.get_object()
        roles_to_do = filter(lambda x: x is not None and x.isdigit(), serializer.validated_data.get('roles_list', []))

        if self.request.data['do_delete']:
            for role in roles_to_do:
                try:
                    role_obj = Role.objects.filter(id=role).first()
                    profile_obj.roles.remove(role_obj)
                except ValueError:
                    pass

        elif self.request.data['do_add']:
            for role in roles_to_do:
                role_obj = Role.objects.filter(id=role).first()
                has_role = profile_obj.roles.filter(role_title=role_obj.role_title).first()
                if not has_role:
                    role_obj = Role.objects.filter(id=role).first()
                    profile_obj.roles.add(role_obj)

        profile_obj.save()

        return Response(ProfileSerializer(profile_obj, many=False).data)


class EasyAdminMultiUserCreate(ListCreate):

    queryset = Profile.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EasyBulkAdminMultiUserCreateSerializer
        return ProfileFullSerializer


class AddOrRemoveProfilesFromRole(RetrieveUpdate):


    queryset = Role.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RoleSerializer
        return RoleChangeProfileSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        role_obj = self.get_object()
        profiles_data = serializer.validated_data.get('Profiles', [])
        profiles_changed = []

        print(profiles_data)

        if self.request.data['do_delete']:
            for profile in profiles_data:
                print(profile)
                try:
                    profile = Profile.objects.get(id=profile)
                    has_role = profile.roles.filter(role_title=role_obj.role_title).first()
                    if has_role:
                        profile.roles.remove(role_obj)
                        profile.save()
                        profiles_changed.append(profile)
                except ValueError:
                    pass

        elif self.request.data['do_add']:
            for profile in profiles_data:
                print(profile)
                try:
                    profile = Profile.objects.get(id=profile)
                    print(profile)
                    has_role = profile.roles.filter(role_title=role_obj.role_title).first()
                    print(has_role)
                    if not has_role:
                        profile.roles.add(role_obj)
                        profile.save()
                        print("hi")
                        profiles_changed.append(profile)
                        print(profiles_changed)
                except ValueError:
                    pass

        return Response(ProfileSerializer(profiles_changed, many=True).data)


class RoleAssignmentListView(List):
    serializer_class = RoleAssignmentSerializer

    def get_queryset(self):
        return RoleAssignment.objects.filter(is_deleted=False, user=self.request.user, role__is_active=True)

    permission_classes = [
        IsAuthenticated,
    ]

    pagination_class = LimitOffsetPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        "id": ['exact'],
        "user": ['exact'],
        'role': ['exact'],
        'is_deleted': ['exact'],
    }
    ordering_fields = '__all__'


class RoleAssignmentListView(List):
    serializer_class = RoleAssignmentSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return RoleAssignment.objects.filter(user=self.request.user, is_deleted=False)

class RoleAssignmentCreateSerializer(serializers.ModelSerializer):
    change_password = serializers.BooleanField()
    user = UserManagementSerializer()

    class Meta:
        model = RoleAssignment
        fields = '__all__'


class UserInquiryView(List): #todo ask permission
    project_path = 'project'
    serializer_class = RoleAssignmentSerializer

    def get_queryset(self):
        from django.db.models import Q
        return_val = RoleAssignment.objects.filter(~Q(role__priority=0)) 
        city_id = self.request.query_params.get('city', None)
        province_id = self.request.query_params.get('province', None)
        if city_id is not None and city_id != '':
            city = City.objects.get(id=city_id)
            return_val = return_val.filter(
                user__in=User.objects.filter(id__in=ExtendedUser.objects.filter(city=city).values_list('user')))
        elif province_id is not None and province_id != '':
            province = Province.objects.get(id=province_id)
            return_val = return_val.filter(
                user__in=User.objects.filter(id__in=ExtendedUser.objects.filter(province=province).values_list('user')))
        return return_val

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        RolePermission, #ask
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        'user': ['exact', ],
        'role': ['exact', ],
        'project': ['exact', ],
        'user__username': ['exact', ],
        'role__priority': ['exact', ],
        'is_deleted': ['exact', ],
        "user__first_name": ['exact', 'in'],
        "user__last_name": ['exact', 'in'],
    }

    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'role']
    ordering_fields = '__all__'



class UserManagementView(Generic): #todo permission ask business
    queryset = User.objects.none()
    serializer_class = RoleAssignmentCreateSerializer
    permission_classes = [
        RolePermission,
    ]

    def post(self, serializer):
        # Request Data
        project = Project.objects.get(id=self.request.data['project'])
        role = Role.objects.get(id=self.request.data['role'])
        users = User.objects.filter(username=self.request.data['user']['username'])
        city = City.objects.get(id=self.request.data['user']['extended']['city'])

        # Request User
        request_roles = RoleAssignment.objects.filter(user=self.request.user, project=project, is_deleted=False)
        request_roles_count = request_roles.count()

        if request_roles_count < 1 or request_roles_count > 1:
            raise NotAcceptable("any user can have only one role in every project!")
        request_role = request_roles[0]
        if request_role.role.priority > role.priority:
            raise NotAcceptable("You must have a higher role to do this!")

        if users.exists():
            user = users[0]
            role_assignments = RoleAssignment.objects.filter(user=user, project=project, is_deleted=False)
            extended_users = ExtendedUser.objects.filter(user=user)
            if extended_users.exists():
                extended_user = extended_users[0]
            else:
                extended_user = ExtendedUser()
                extended_user.user = user
            extended_user.national_code = self.request.data['user']['extended']['national_code']
            extended_user.role = 'M'
            extended_user.city = city
            extended_user.province = city.province
            extended_user.save()
            if role_assignments.filter(role=role).exists():
                user.first_name = self.request.data['user']['first_name']
                user.last_name = self.request.data['user']['last_name']
                user.email = self.request.data['user']['email']
                user.save()
                return Response(RoleAssignmentSerializer(role_assignments[0], many=False).data)
            elif role_assignments.exists():
                role_assignment = role_assignments[0]
                role_assignment.role = role
                role_assignment.save()
            else:
                role_assignment = RoleAssignment()
                role_assignment.role = role
                role_assignment.project = project
                role_assignment.user = user
                role_assignment.is_deleted = False
                role_assignment.save()
            if self.request.data['change_password']:
                user.set_password(self.request.data['user']['password'])
        else:
            user = User.objects.create_user(username=self.request.data['user']['username'], email=None,
                                            password=self.request.data['user']['username'])
            extended_user = ExtendedUser()
            city = City.objects.get(id=self.request.data['user']['extended']['city'])
            extended_user.user = user
            extended_user.national_code = self.request.data['user']['extended']['national_code']
            extended_user.role = 'M'
            extended_user.city = city
            extended_user.province = city.province
            extended_user.save()
            role_assignment = RoleAssignment()
            role_assignment.role = role
            role_assignment.user = user
            role_assignment.project = project
            role_assignment.save()
        user.first_name = self.request.data['user']['first_name']
        user.last_name = self.request.data['user']['last_name']
        user.email = self.request.data['user']['email']
        user.save()
        return Response(RoleAssignmentSerializer(role_assignment, many=False).data)


class RolesAssignmentCustomizableListView(List):
    permission_classes = [
        RolePermission,
    ]
    project_path = 'project'

    def get_queryset(self):
        role_assignments = RoleAssignment.objects.filter(is_deleted=False)
        return role_assignments

    serializer_class = RoleAssignmentSerializer

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = {
        'user': ['in', 'exact', ],
        'user__username': ['in', 'exact', ],
        'role': ['in', 'exact', ],
        'role__title_abbreviation': ['in', 'exact', ],
        'project': ['in', 'exact', ],
        'is_deleted': ['in', 'exact', ],
    }
    ordering_fields = '__all__'


class RolesAssignmentDeleteListView(Destroy):
    permission_classes = [
        RolePermission,
    ]
    project_path = 'project'
    lookup_field = 'id'

    def get_queryset(self):
        return RoleAssignment.objects.filter(is_deleted=False)

    serializer_class = RoleAssignmentSerializer

###############################
# Company APIs:
###############################

class CompanyListCreateView(ListCreate):

    def get_queryset(self):
        return Company.objects.all()

    serializer_class = CompanySerializer
    permission_classes = [
        RolePermission,
    ]


class CompanyEditsView(RetrieveUpdate): 
    def get_queryset(self):
        return Company.objects.all()

    serializer_class = CompanySerializer
    permission_classes = [
        RolePermission,
    ]


####################################
# Address:
####################################
class AddressListCreate(ListCreate):
    def get_queryset(self):
        if self.request.user.is_staff:
            return Address.objects.all()
        return Address.objects.filter(is_deleted=False, user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedAddressSerializer
        else:
            return AddressSerializer

class AddressRetrieveUpdateDestroy(RetrieveUpdateDestroy):
    def get_queryset(self):
        return Address.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedAddressSerializer
        else:
            return AddressSerializer
    permission_classes = [
        RolePermission,
    ]

####################################
# SpecificationType:
####################################
class SpecificationTypeListCreate(ListCreate):
    def get_queryset(self):
        return SpecificationType.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SpecificationTypeSerializer
        else:
            return SpecificationTypeSerializer

class SpecificationTypeRetrieveUpdateDestroy(RetrieveUpdateDestroy):
    def get_queryset(self):
        return SpecificationType.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SpecificationTypeSerializer
        else:
            return SpecificationTypeSerializer


    permission_classes = [
        RolePermission,
    ]


