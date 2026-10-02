from collections import OrderedDict

from django.shortcuts import render

from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import exceptions, generics, serializers, status, authentication, permissions
# from address_app.serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from rest_framework.views import APIView

from auth_app.models import *

# from auth_service.exceptions import *
from django.utils.translation import gettext_lazy as _
import copy

from django.forms import IntegerField, UUIDField
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, generics, serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.contrib.auth.models import User
# from auth_app.serializers import *
# from address_app.models import *
from core.farapayamak import FaraPayamak
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.views import TokenViewBase

from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from rest_framework.pagination import LimitOffsetPagination

import hashlib
import secrets
from hmac import compare_digest
from datetime import datetime, timedelta
from random import randint
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.throttling import ScopedRateThrottle
from core.exceptions import *

# from core.generics import BaseView
from config.models import *
from core.generics import BaseView, BaseLimiter
from auth_app.permissions import *
from auth_app.user_serializers import SafeUserSerializer, UserSerializer
from core import settings


# City and Province List:

class ProvinceAPISerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'


class CityAPISerializer(serializers.ModelSerializer):
    province = ProvinceAPISerializer()

    class Meta:
        model = City
        fields = '__all__'


class ProviceListAPIView(generics.ListAPIView):
    serializer_class = ProvinceAPISerializer

    def get_queryset(self):
        return Province.objects.all()


    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = '__all__'
    ordering_fields = '__all__'


class CityListAPIView(BaseLimiter, generics.ListAPIView):
    serializer_class = CityAPISerializer

    def get_queryset(self):
        return City.objects.filter(is_active=True)

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = '__all__'
    ordering_fields = '__all__'


# User create by Us:

#################################
### Generating JWT Tokens:
#################################


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    update_last_login(None, user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class AuthUserOnlySerializer(SafeUserSerializer):
    pass


class RegisterAPISerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    fullname = serializers.CharField()
    city_id = serializers.IntegerField(required=False)
    province_id = serializers.IntegerField(required=False)
    national_code = serializers.CharField()
    role = serializers.CharField(required=False)


class RegisterAPISerializer(generics.GenericAPIView): #todo ask for it
    serializer_class = RegisterAPISerializer

    def get_queryset(self):
        return User.objects.none()

    def post(self, request):
        phone_number = self.request.data['phone_number']
        full_name = self.request.data['fullname']
        national_code = self.request.data['national_code']
        q = User.objects.filter(username=phone_number)
        if len(q) > 0:
            return Response(AuthUserOnlySerializer(q[0], many=False).data)
        new_user = User.objects.create(username=phone_number, first_name=full_name, password='thisuserspasswords',
                                       email=str(phone_number) + '@kavoshsystemyar.ir')
        ex_user = ExtendedUser()
        ex_user.user = new_user
        ex_user.national_code = national_code
        if 'role' in self.request.data.keys():
            ex_user.role = self.request.data['role']
        if 'province_id' in self.request.data.keys():
            ex_user.province = Province.objects.get(id=self.request.data['province_id'])
        if 'city_id' in self.request.data.keys():
            ex_user.province = City.objects.get(id=self.request.data['city_id'])
        ex_user.save()
        return Response(AuthUserOnlySerializer(new_user, many=False).data)


# OTP login:

class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.RegexField(r'^\+?\d{10,15}$', max_length=16)


class RequestOTP(generics.CreateAPIView):
    serializer_class = RequestOTPSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_request'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data['phone_number']
        if not User.objects.filter(username=phone_number, is_active=True).exists():
            raise BadRequest('کاربر یافت نشد.')
        now = timezone.now()
        latest = OTP.objects.filter(phone_number=phone_number).order_by('-datetime_requested').first()
        if latest and latest.datetime_requested and now - latest.datetime_requested < timedelta(seconds=30):
            return Response({'detail': 'برای ارسال دوباره کد کمی صبر کنید.'}, status=429)
        if OTP.objects.filter(phone_number=phone_number, datetime_requested__gte=now - timedelta(hours=1)).count() >= 5:
            return Response({'detail': 'تعداد درخواست کد بیش از حد مجاز است.'}, status=429)

        code = str(secrets.randbelow(90000) + 10000)
        with transaction.atomic():
            OTP.objects.filter(phone_number=phone_number, consumed_at__isnull=True).update(consumed_at=now)
            obj = OTP.objects.create(
                phone_number=phone_number,
                otp=make_password(code),
                verification_token=secrets.token_urlsafe(32),
            )
        from notification.modules.notification import Notification
        Notification(to=phone_number, message_template_key='OTP', code=code)
        return Response({'id': obj.pk, 'verification_token': obj.verification_token}, status=201)


class PhoneOTPVerifyAPISerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True, min_value=1, required=True)
    verification_token = serializers.CharField(write_only=True, required=True)
    code = serializers.RegexField(r'^\d{5}$', write_only=True, required=True)
    phone_number = serializers.RegexField(r'^\+?\d{10,15}$', write_only=True, required=True)


class ExtendedUserSerializer(serializers.ModelSerializer):
    city = CityAPISerializer()

    class Meta:
        model = ExtendedUser
        fields = '__all__'


class VerifyPhoneNumberOTPAPIView(generics.GenericAPIView):
    serializer_class = PhoneOTPVerifyAPISerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_verify'

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data
        user_object = User.objects.filter(username=fields['phone_number'], is_active=True).first()
        if user_object is None or not api_settings.USER_AUTHENTICATION_RULE(user_object):
            raise exceptions.AuthenticationFailed('حساب کاربری فعال نیست.')

        result = 'invalid'
        with transaction.atomic():
            obj = OTP.objects.select_for_update().filter(pk=fields['id']).first()
            if obj and obj.consumed_at is None and obj.failed_attempts < 3:
                if obj.datetime_requested and timezone.now() - obj.datetime_requested > timedelta(minutes=2):
                    result = 'expired'
                elif (obj.phone_number == fields['phone_number']
                      and compare_digest(obj.verification_token, fields['verification_token'])
                      and check_password(fields['code'], obj.otp)):
                    obj.consumed_at = timezone.now()
                    obj.otp = ''
                    obj.verification_token = ''
                    obj.save(update_fields=['consumed_at', 'otp', 'verification_token'])
                    result = 'accepted'
                else:
                    obj.failed_attempts += 1
                    obj.save(update_fields=['failed_attempts'])
        if result == 'expired':
            raise TooLate('کد منقضی شده است.')
        if result != 'accepted':
            raise BadRequest('کد تأیید معتبر نیست.')

        ext = ExtendedUser.objects.filter(user=user_object).first()
        return Response({
            'user': AuthUserOnlySerializer(user_object).data,
            'role': ExtendedUserSerializer(ext).data if ext else None,
            'tokens': get_tokens_for_user(user_object),
        })


class UserDetailView(BaseLimiter, generics.ListAPIView):
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id) 

    serializer_class = UserSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


###############################
# Company APIs:
###############################

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class CompanyListCreateView(BaseLimiter, generics.ListCreateAPIView):

    def get_queryset(self):
        return self.limit_queryset(Company.objects.all())

    serializer_class = CompanySerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class CompanyEditsView(BaseLimiter, generics.RetrieveUpdateAPIView):
    def get_queryset(self):
        return self.limit_queryset(Company.objects.all())

    serializer_class = CompanySerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


###############################
# Role:
###############################

from auth_app.serializers import RoleSerializer


class ProjectSerializer(serializers.ModelSerializer):
    company = CompanySerializer()

    class Meta:
        model = Project
        exclude = ('key',)


class RoleAssignmentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    role = RoleSerializer()
    project = ProjectSerializer()

    class Meta:
        model = RoleAssignment
        fields = '__all__'


class RoleAssignmentListView(BaseLimiter, generics.ListAPIView):
    serializer_class = RoleAssignmentSerializer

    def get_queryset(self):
        return RoleAssignment.objects.filter(is_deleted=False, user=self.request.user,
                                             user__is_active=True, role__is_active=True,
                                             project__is_active=True).select_related('user', 'role', 'project')

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


class RoleListView(BaseLimiter, generics.ListAPIView):
    serializer_class = RoleSerializer

    def get_queryset(self):
        return self.limit_queryset(Role.objects.all())

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    permission_classes = [
        DeleteCreateUpdateGetPermission,
                          ]

    filterset_fields = {
        "id": ['exact'],
        "title": ['exact', ],
        "title_abbreviation": ['exact', ],
        "verbose_name": ['exact', ],
        "description": ['exact', ],
        "priority": ['exact', 'gte', 'lte', ],
        # "is_active": ['exact',],
    }
    # filterset_fields = '__all__'
    ordering_fields = '__all__'


class AdminMenuRawSerializer(serializers.ModelSerializer):
    # children = serializers.SerializerMethodField()
    class Meta:
        model = AdminMenu
        fields = '__all__'


class AdminMenuSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = AdminMenu
        fields = '__all__'

    def get_children(self, obj):
        return (AdminMenuRawSerializer(
            AdminMenu.objects.filter(parent=obj, role=obj.role, project=obj.project, is_active=True).order_by(
                'priority'), many=True).data)


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class AdminMenuListView(BaseLimiter, generics.ListAPIView):
    serializer_class = AdminMenuSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('p', in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Project ID')])
    def get_queryset(self):
        project_id = self.request.GET.get('p', None)
        if project_id is None:
            return AdminMenu.objects.none()
        project = Project.objects.get(id=project_id)
        role_assignment = RoleAssignment.objects.filter(user=self.request.user, project=project, is_deleted=False)[0]
        return self.limit_queryset( AdminMenu.objects.filter(parent=None, role=role_assignment.role, project=project,
                                        is_active=True).order_by('priority'))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        "id": ['exact'],
        #     "title": ['exact',],
        #     "title_abbreviation": ['exact',],
        #     "verbose_name": ['exact',],
        #     "description": ['exact',],
        #     "priority": ['exact', 'gte', 'lte',],
        #     # "is_active": ['exact',],
    }
    # filterset_fields = '__all__'
    ordering_fields = '__all__'


class AdminMenuRetriveUpdateDestroyView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminMenuRawSerializer
    lookup_field = 'id'
    def get_queryset(self):
        return self.limit_queryset(AdminMenu.objects.filter(is_active=True))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class ProjectRoleAssignmentListView(BaseLimiter, generics.ListAPIView):
    serializer_class = RoleAssignmentSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return self.limit_queryset(RoleAssignment.objects.filter(user=self.request.user, is_deleted=False))


class ActiveCitySerializer(serializers.ModelSerializer):
    city = CityAPISerializer()

    class Meta:
        model = ActiveCity
        fields = '__all__'


class ActiveCityListView(BaseLimiter, generics.ListAPIView):
    serializer_class = ActiveCitySerializer

    def get_queryset(self):
        project_id = self.request.GET.get('p', None)
        project = Project.objects.get(id=project_id)
        return self.limit_queryset(ActiveCity.objects.filter(project=project))

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        "id": ['exact'],
        "city": ['exact'],
        'city__province': ['exact'],
        'project': ['exact'],
    }
    ordering_fields = '__all__'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class ActiveProjectRetriveView(BaseLimiter, generics.RetrieveAPIView):
    serializer_class = RoleAssignmentSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(RoleAssignment.objects.filter(user=self.request.user, is_deleted=False))

    lookup_field = 'project'


# from visit.views import AnswerTypeSerializer
# from auth_app.models import FieldValidation
class FieldValidationSerializer(serializers.ModelSerializer):
    # regex = serializers.URLField()

    # def get_regex(Self, obj):
    #     return obj.regex
    class Meta:
        model = FieldValidation
        fields = '__all__'


class AuthAnswerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerType
        fields = '__all__'


class QuestionAnswerTypeValidationSerializer(serializers.ModelSerializer):
    validation = FieldValidationSerializer()
    answer_type = AuthAnswerTypeSerializer()

    class Meta:
        model = QuestionAnswerTypeValidation
        fields = '__all__'


#########################
# Parse Excel File:
#########################

class ParseXLSXAPISerializer(serializers.Serializer):
    file = serializers.FileField()


class ParseXLSXResponseAPISerializer(serializers.Serializer):
    data = serializers.ListField(child=serializers.DictField(), min_length=0)


from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema


class ParseXlsxAPIView(generics.GenericAPIView):
    parser_classes = [MultiPartParser]
    serializer_class = ParseXLSXAPISerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.none()

    @swagger_auto_schema(request_body=ParseXLSXAPISerializer, responses={200: ParseXLSXResponseAPISerializer})
    def post(self, request):
        grants = authorized_role_views(request, self, view_name='AdminActionPlanCreate')
        if not grants.filter(role__asset_scope__in=('project', 'supervised')).exists():
            raise PermissionDenied('دسترسی به واردکردن برنامه مجاز نیست.')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from auth_app.action_plan_import import parse_action_plan_rows
        return Response({'data': parse_action_plan_rows(serializer.validated_data['file'])})


class UploadedFileListSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    def get_file(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.file, self.context.get('request'))

    def get_icon(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.icon, self.context.get('request'))

    class Meta:
        model = UploadedFile
        fields = '__all__'


class UploadedFileCreateSerializer(UploadedFileListSerializer):
    file = serializers.FileField()
    icon = serializers.FileField()


class UploadedFileMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ('name', 'type', 'description', 'priority')


def validate_uploaded_resource(upload, *, icon=False):
    limit = 2 * 1024 * 1024 if icon else 50 * 1024 * 1024
    if upload.size <= 0 or upload.size > limit:
        raise DRFValidationError({'icon' if icon else 'file': 'اندازه فایل معتبر نیست.'})
    header = upload.read(16)
    upload.seek(0)
    name = (upload.name or '').lower()
    image = ((name.endswith('.png') and header.startswith(b'\x89PNG\r\n\x1a\n')) or
             (name.endswith(('.jpg', '.jpeg')) and header.startswith(b'\xff\xd8\xff')) or
             (name.endswith('.webp') and header.startswith(b'RIFF') and header[8:12] == b'WEBP'))
    document = name.endswith('.pdf') and header.startswith(b'%PDF-')
    video = name.endswith('.mp4') and len(header) >= 12 and header[4:8] == b'ftyp'
    if not image and (icon or not (document or video)):
        raise DRFValidationError({'icon' if icon else 'file': 'فرمت فایل مجاز نیست.'})


from core.storage import ArvanStorage


class UploadedFileListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    project_path = 'project'

    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return UploadedFile.objects.none()
        rows = UploadedFile.objects.filter(is_deleted=False)
        if self.request.method == 'GET' and self.request.query_params.get('project__isnull') == 'true':
            rows = rows.filter(Q(project_id=project_id) | Q(project__isnull=True))
        else:
            rows = rows.filter(project_id=project_id)
        return self.limit_queryset(rows)

    serializer_class = UploadedFileCreateSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UploadedFileListSerializer
        else:
            return UploadedFileCreateSerializer

    def create(self, request, *args, **kwargs):
        if not authorized_role_views(request, self).filter(role__asset_scope='project').exists():
            raise PermissionDenied('بارگذاری فایل به دسترسی مدیریت پروژه نیاز دارد.')
        allowed = {'file', 'icon', 'project', 'name', 'type', 'description', 'priority'}
        if set(request.data) - allowed:
            raise DRFValidationError({'fields': 'فیلد غیرمجاز در درخواست وجود دارد.'})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise DRFValidationError({'project': 'پروژه معتبر لازم است.'})
        if ('project' in serializer.validated_data and
                serializer.validated_data['project'].pk != project_id):
            raise DRFValidationError({'project': 'پروژه فایل باید با پروژه انتخاب‌شده برابر باشد.'})
        project = Project.objects.filter(pk=project_id, is_active=True).first()
        if project is None:
            raise DRFValidationError({'project': 'پروژه فعال پیدا نشد.'})
        upload, icon = serializer.validated_data['file'], serializer.validated_data['icon']
        validate_uploaded_resource(upload)
        validate_uploaded_resource(icon, icon=True)
        storage = ArvanStorage()
        url = storage.put_file(upload)
        icon_url = storage.put_file(icon) if url else None
        if not url or not icon_url:
            return Response({'detail': 'ذخیره فایل انجام نشد.'}, status=502)
        values = serializer.validated_data
        obj = UploadedFile.objects.create(
            file=url, icon=icon_url, project=project, uploaded_by=request.user,
            name=values.get('name'), type=values.get('type'),
            description=values.get('description'), priority=values.get('priority', 0),
        )
        return Response(UploadedFileListSerializer(obj, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = {
        "file": ['exact', ],
        "name": ['exact', ],
        "type": ['exact', ],
        "description": ['exact', ],
        "icon": ['exact', ],
        "uploaded_by": ['exact', ],
        "project": ['exact', 'isnull', ],
        "is_deleted": ['exact', ],
    }
    ordering_fields = '__all__'


class UploadedFileEditView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UploadedFileMetadataSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return UploadedFile.objects.none()
        return self.limit_queryset(UploadedFile.objects.filter(
            project_id=project_id, is_deleted=False))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UploadedFileListSerializer
        else:
            return UploadedFileMetadataSerializer

    lookup_field = 'id'

    def perform_update(self, serializer):
        if not authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            raise PermissionDenied('ویرایش فایل به دسترسی مدیریت پروژه نیاز دارد.')
        if set(self.request.data) - {'name', 'type', 'description', 'priority'}:
            raise DRFValidationError({'fields': 'فقط اطلاعات نمایشی فایل قابل ویرایش است.'})
        serializer.save()

    def perform_destroy(self, instance):
        if not authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            raise PermissionDenied('حذف فایل به دسترسی مدیریت پروژه نیاز دارد.')
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


##############################
# Supervisor:
##############################


class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = '__all__'


class SupervisorNestedSerializer(serializers.ModelSerializer):
    supervisor = UserSerializer()
    promoter = UserSerializer()
    project = ProjectSerializer()

    class Meta:
        model = Supervisor
        fields = '__all__'


class SupervisorOfPromoterCheckView(BaseLimiter, generics.ListAPIView): #todo ask
    serializer_class = SupervisorNestedSerializer

    def get_queryset(self):
        promoter = self.request.query_params.get('promoter', None)
        project = self.request.query_params.get('p', None)
        if promoter and project:
            return Supervisor.objects.filter(promoter=promoter, project=project, is_active=True).all()
        else:
            raise ValidationError('promoter and p should be in params!')

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = '__all__'
    ordering_fields = '__all__'


class SupervisorListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView): #todo ask permission
    project_path = 'project'

    def get_queryset(self):
        base_query = Supervisor.objects.filter(is_active=True)
        if self.request.query_params.get('me', False):
            base_query = base_query.filter(supervisor=self.request.user)
        return self.limit_queryset(self.get_projectified_queryset(base_query))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SupervisorNestedSerializer
        return SupervisorSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = '__all__'
    ordering_fields = '__all__'

    def create(self, request, *args, **kwargs):
        # serializer.is_valid(raise_exception=True)
        # serializer = self.get_serializer(data=request.data)
        try:
            supervisor = User.objects.get(id=self.request.data['supervisor'])
            promoter = User.objects.get(id=self.request.data['promoter'])
            project = Project.objects.get(id=self.request.data['project'])
        except:
            raise BadRequest("data is not correct!")

        active_supervisors = Supervisor.objects.filter(promoter=promoter, project=project, is_active=True).all()
        if active_supervisors.exists():
            for active_supervisor in active_supervisors:
                active_supervisor.is_active = False
                active_supervisor.save()
        #     for supervisor in active_supervisors:
        #         supervisor.is_active = False
        # Supervisor.objects.bulk_update(active_supervisors, ['is_active'])

        queries = Supervisor.objects.filter(
            supervisor=supervisor,
            promoter=promoter,
            project=project,
        )
        if queries.exists():
            obj = queries[0]
            obj.is_active = True
        else:
            obj = Supervisor()
            obj.supervisor = supervisor
            obj.promoter = promoter
            obj.project = project
            obj.is_active = True
        obj.save()
        # headers = self.get_success_headers(serializer.data)
        return Response({"detail": "OK"}, status=status.HTTP_201_CREATED)

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class SupervisorEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return self.limit_queryset(Supervisor.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SupervisorNestedSerializer
        return SupervisorSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    lookup_field = 'id'


#############################################
# AuthenticationImage:                      #
#############################################

class AuthenticationImageOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticationImage
        fields = '__all__'


class AuthenticationImageInputSerializer(AuthenticationImageOutputSerializer):
    image = serializers.FileField()


def register_into_face_recognition(user_id, image):
    import requests
    import json
    if settings.production:
        base_url = 'https://face.koosha.ir'
    else:
        base_url = 'https://testface.koosha.ir'
    profile_url = base_url + '/recognize/profile/list_create/'
    known_image_url = base_url + '/recognize/known_image/list_create/'
    gotten_profiles = requests.get(url=profile_url, params={"matching_id": user_id, "limit": 1, "offset": 0})
    if json.loads(gotten_profiles.text)["count"] == 0:
        create_profile = requests.post(url=profile_url, data={"matching_id": user_id})
        profile_id = json.loads(create_profile.text)['id']
    else:
        profile_id = json.loads(gotten_profiles.text)["results"][0]["id"]
    adding_known_img = requests.post(known_image_url, data={"url": image, "profile": profile_id, "is_active": True})


class AuthenticationImageListCreateView(BaseLimiter, generics.ListCreateAPIView):
    def get_queryset(self):
        return self.limit_queryset(AuthenticationImage.objects.filter(user=self.request.user))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AuthenticationImageOutputSerializer
        else:
            return AuthenticationImageInputSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = '__all__'
    ordering_fields = '__all__'

    def perform_create(self, serializer):
        client = ArvanStorage()
        image_url = client.put_file(self.request.FILES.get("image"))
        obj = AuthenticationImage()
        obj.user = self.request.user
        obj.image = image_url
        obj.save()
        # serializer.save(image=image_url)
        register_into_face_recognition(self.request.user.id, image_url)


class AuthenticationImageEditView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView): #todo ask permission
    def get_queryset(self):
        return self.limit_queryset(AuthenticationImage.objects.filter(user=self.request.user))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AuthenticationImageOutputSerializer
        else:
            return AuthenticationImageInputSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    lookup_field = 'id'

    def perform_update(self, serializer):
        url = self.request.build_absolute_uri().split('?')[0]
        if url.split('/')[-1] == '':
            id = int(url.split('/')[-2])
        else:
            id = int(url.split('/')[-1])
        obj = AuthenticationImage.objects.get(id=id)
        client = ArvanStorage()
        image_url = client.put_file(self.request.FILES.get("image"))
        obj.user = self.request.user
        obj.image = image_url
        obj.save()
        # serializer.save(image=image_url)
        register_into_face_recognition(self.request.user.id, image_url)


##########################################
# paswword authentication:               #
########################################## 

class UsernamePasswordAPISerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)


class SetPasswordForUser(BaseLimiter, generics.GenericAPIView):
    serializer_class = UsernamePasswordAPISerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def post(self, request):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        project_id = int(request.query_params['p'])
        grants = authorized_role_views(request, self).filter(role__asset_scope='project')
        if not grants.exists():
            raise PermissionDenied('تغییر رمز به نقش مدیریتی پروژه نیاز دارد.')
        actor_rank = RoleAssignment.objects.filter(
            user=request.user, project_id=project_id, is_deleted=False,
            role_id__in=grants.values('role_id'), role__is_active=True,
        ).order_by('role__priority').values_list('role__priority', flat=True).first()
        with transaction.atomic():
            project_users = RoleAssignment.objects.filter(
                project_id=project_id, is_deleted=False, role__is_active=True,
            ).values('user_id')
            user = User.objects.select_for_update().filter(
                username=payload.validated_data['username'], is_active=True,
                pk__in=project_users,
            ).first()
            if user is None:
                raise NotFound('کاربر در پروژه انتخاب‌شده پیدا نشد.')
            if RoleAssignment.objects.filter(
                user=user, is_deleted=False, role__is_active=True,
                project__is_active=True,
            ).exclude(project_id=project_id).exists():
                raise PermissionDenied('تغییر رمز حساب چندپروژه‌ای از پنل پروژه مجاز نیست.')
            target_rank = RoleAssignment.objects.filter(
                user=user, project_id=project_id, is_deleted=False, role__is_active=True,
            ).order_by('role__priority').values_list('role__priority', flat=True).first()
            if (actor_rank is None or user.is_superuser
                    or (user.is_staff and not request.user.is_superuser)
                    or (not request.user.is_superuser and target_rank <= actor_rank)):
                raise PermissionDenied('تغییر رمز این حساب مجاز نیست.')
            try:
                validate_password(payload.validated_data['password'], user=user)
            except DjangoValidationError as error:
                raise DRFValidationError({'password': error.messages})
            user.set_password(payload.validated_data['password'])
            user.save(update_fields=['password'])
        return Response({'status': 'password_changed'})


############################################
# Authentication Management Services:
############################################
from auth_app.permissions import PriorityRolePermission


class UserInquiryView(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'project'
    serializer_class = RoleAssignmentSerializer

    def get_queryset(self):
        if not authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            raise PermissionDenied('فهرست کاربران به مدیریت پروژه نیاز دارد.')
        from django.db.models import Q
        return_val = self.get_projectified_queryset(RoleAssignment.objects.filter(~Q(role__priority=0)))
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
        return self.limit_queryset(return_val)

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
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


class UserManagementSerializer(serializers.ModelSerializer):
    extended = ExtendedUser()

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name',)
        extra_kwargs = {'password': {'write_only': True}}


class RoleAssignmentCreateSerializer(serializers.ModelSerializer):
    change_password = serializers.BooleanField()
    user = UserManagementSerializer()

    class Meta:
        model = RoleAssignment
        fields = '__all__'


class UserManagementView(BaseLimiter, generics.GenericAPIView):
    queryset = User.objects.none()
    class InputSerializer(serializers.Serializer):
        id = serializers.IntegerField(min_value=1, required=False)
        username = serializers.RegexField(r'^09\d{9}$', required=False)
        first_name = serializers.CharField(max_length=150, required=False, trim_whitespace=True)
        last_name = serializers.CharField(max_length=150, required=False, trim_whitespace=True)
        email = serializers.EmailField(required=False, allow_blank=True)
        national_code = serializers.RegexField(r'^\d{10}$', required=False, allow_blank=True)
        city = serializers.IntegerField(min_value=1, required=False, allow_null=True)
        project = serializers.IntegerField(min_value=1)
        role = serializers.IntegerField(min_value=1)

        def validate(self, attrs):
            editing = 'id' in attrs
            allowed = ({'id', 'project', 'role'} if editing else
                       {'username', 'first_name', 'last_name', 'email',
                        'national_code', 'city', 'project', 'role'})
            unexpected = set(self.initial_data) - allowed
            if unexpected:
                raise DRFValidationError({'detail': 'فیلد غیرمجاز در درخواست تغییر نقش.'})
            if not editing and not {'username', 'first_name', 'last_name'} <= attrs.keys():
                raise DRFValidationError({'detail': 'شماره همراه، نام و نام خانوادگی لازم‌اند.'})
            code = attrs.get('national_code')
            if code:
                check = int(code[9])
                remainder = sum(int(code[index]) * (10 - index) for index in range(9)) % 11
                if len(set(code)) == 1 or check != (remainder if remainder < 2 else 11 - remainder):
                    raise DRFValidationError({'national_code': 'کد ملی معتبر نیست.'})
            return attrs

    serializer_class = InputSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def post(self, request):
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        project_id = int(request.query_params['p'])
        if values['project'] != project_id:
            raise DRFValidationError({'project': 'پروژه نقش باید با پروژه انتخاب‌شده یکسان باشد.'})
        grants = authorized_role_views(request, self).filter(role__asset_scope='project')
        if not grants.exists():
            raise PermissionDenied('تغییر نقش به مدیریت پروژه نیاز دارد.')
        actor_rank = RoleAssignment.objects.filter(
            user=request.user, project_id=project_id, is_deleted=False,
            role_id__in=grants.values('role_id'), role__is_active=True,
        ).order_by('role__priority').values_list('role__priority', flat=True).first()
        desired_role = Role.objects.filter(pk=values['role'], is_active=True).first()
        if desired_role is None:
            raise DRFValidationError({'role': 'نقش فعال پیدا نشد.'})
        if 'id' not in values:
            if actor_rank is None or (not request.user.is_superuser
                                      and desired_role.priority <= actor_rank):
                raise PermissionDenied('افزودن این نقش مجاز نیست.')
            with transaction.atomic():
                city = None
                if values.get('city'):
                    city = City.objects.filter(pk=values['city']).first()
                    if city is None:
                        raise DRFValidationError({'city': 'شهر پیدا نشد.'})
                user, created = User.objects.get_or_create(
                    username=values['username'], defaults={
                        'password': make_password(None),
                        'first_name': values['first_name'],
                        'last_name': values['last_name'],
                        'email': values.get('email', ''),
                    },
                )
                if not created:
                    raise DRFValidationError({'username': 'این حساب از قبل وجود دارد؛ افزودن آن به پروژه به دعوت و تأیید صاحب حساب نیاز دارد.'})
                ExtendedUser.objects.create(
                    user=user, national_code=values.get('national_code') or None,
                    city=city,
                )
                assignment = RoleAssignment.objects.create(
                    user=user, project_id=project_id, role=desired_role,
                )
            return Response(RoleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)
        with transaction.atomic():
            assignment = RoleAssignment.objects.select_for_update().select_related('user', 'role').filter(
                pk=values['id'], project_id=project_id, is_deleted=False,
                user__is_active=True, role__is_active=True,
            ).first()
            if assignment is None:
                raise NotFound('عضویت در پروژه انتخاب‌شده پیدا نشد.')
            target_rank = RoleAssignment.objects.filter(
                user=assignment.user, project_id=project_id, is_deleted=False,
                role__is_active=True,
            ).order_by('role__priority').values_list('role__priority', flat=True).first()
            if (actor_rank is None or assignment.user_id == request.user.pk
                    or assignment.user.is_superuser
                    or (assignment.user.is_staff and not request.user.is_superuser)
                    or (not request.user.is_superuser
                        and (target_rank <= actor_rank
                             or desired_role.priority <= actor_rank))):
                raise PermissionDenied('تغییر این نقش مجاز نیست.')
            if RoleAssignment.objects.filter(
                user=assignment.user, project_id=project_id, role=desired_role,
                is_deleted=False,
            ).exclude(pk=assignment.pk).exists():
                raise DRFValidationError({'role': 'این کاربر همین نقش را در پروژه دارد.'})
            assignment.role = desired_role
            assignment.save(update_fields=['role'])
        return Response(RoleAssignmentSerializer(assignment).data)


class RolesAssignmentCustomizableListView(BaseLimiter, generics.ListAPIView, BaseView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    project_path = 'project'

    def get_queryset(self):
        if not authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            raise PermissionDenied('فهرست عضویت‌ها به مدیریت پروژه نیاز دارد.')
        role_assignments = RoleAssignment.objects.filter(is_deleted=False)
        return self.limit_queryset(self.get_projectified_queryset(role_assignments))

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


class RolesAssignmentDeleteListView(BaseLimiter, generics.DestroyAPIView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    project_path = 'project'
    lookup_field = 'id'

    def get_queryset(self):
        project_id = self.request.query_params.get('p')
        return self.limit_queryset(RoleAssignment.objects.filter(
            project_id=project_id, is_deleted=False,
        ))

    serializer_class = RoleAssignmentSerializer

    def perform_destroy(self, assignment):
        project_id = int(self.request.query_params['p'])
        grants = authorized_role_views(self.request, self).filter(role__asset_scope='project')
        if not grants.exists():
            raise PermissionDenied('حذف عضویت به مدیریت پروژه نیاز دارد.')
        actor_rank = RoleAssignment.objects.filter(
            user=self.request.user, project_id=project_id, is_deleted=False,
            role_id__in=grants.values('role_id'), role__is_active=True,
        ).order_by('role__priority').values_list('role__priority', flat=True).first()
        with transaction.atomic():
            locked = RoleAssignment.objects.select_for_update().select_related('user').filter(
                pk=assignment.pk, project_id=project_id, is_deleted=False,
            ).first()
            if locked is None:
                raise NotFound('عضویت در پروژه انتخاب‌شده پیدا نشد.')
            target_rank = RoleAssignment.objects.filter(
                user=locked.user, project_id=project_id, is_deleted=False,
                role__is_active=True,
            ).order_by('role__priority').values_list('role__priority', flat=True).first()
            if (actor_rank is None or locked.user_id == self.request.user.pk
                    or locked.user.is_superuser
                    or (locked.user.is_staff and not self.request.user.is_superuser)
                    or (not self.request.user.is_superuser
                        and (target_rank is None or target_rank <= actor_rank))):
                raise PermissionDenied('حذف این عضویت مجاز نیست.')
            locked.is_deleted = True
            locked.save(update_fields=['is_deleted'])


###############################
# Region and District:
###############################

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class NestedRegionSerializer(serializers.ModelSerializer):
    city = CityAPISerializer()

    class Meta:
        model = Region
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class NestedDistrictSerializer(serializers.ModelSerializer):
    city = CityAPISerializer()

    class Meta:
        model = District
        fields = '__all__'


class RegionListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        return Region.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedRegionSerializer
        else:
            return RegionSerializer

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
    filterset_fields = '__all__'
    # filterset_fields = {
    #     "id": ['exact'],
    #     "ticket_message": ['exact'],
    #     "link": ['exact'],
    #     "is_deleted": ['exact'],        
    # }
    ordering_fields = '__all__'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class RegionEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return self.limit_queryset(Region.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedRegionSerializer
        else:
            return RegionSerializer

    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class DistrictListCreateView(BaseLimiter, generics.ListCreateAPIView):
    def get_queryset(self):
        return self.limit_queryset(District.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedDistrictSerializer
        else:
            return DistrictSerializer

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = '__all__'
    # filterset_fields = {
    #     "id": ['exact'],
    #     "ticket_message": ['exact'],
    #     "link": ['exact'],
    #     "is_deleted": ['exact'],        
    # }
    ordering_fields = '__all__'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class DistrictEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return self.limit_queryset(District.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedDistrictSerializer
        else:
            return DistrictSerializer

    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


from auth_app.serializers import *
#todo these permissions ask for business


class DocumentsListCreteView(BaseLimiter, generics.ListAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return self.limit_queryset(Document.objects.all())

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    filterset_fields = '__all__'
    ordering_fields = '__all__'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class DocumentEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    lookup_field = 'id'

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(Document.objects.all())


class DocumentsPhotoListCreateView(generics.ListCreateAPIView, BaseView, BaseLimiter):

    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return DocumentPhoto.objects.none()
        if authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            users = RoleAssignment.objects.filter(
                project_id=project_id, project__is_active=True, is_deleted=False,
                role__is_active=True, user__is_active=True).values('user_id')
            rows = DocumentPhoto.objects.filter(user_id__in=users, is_deleted=False)
        else:
            rows = DocumentPhoto.objects.filter(user=self.request.user, is_deleted=False)
        return self.limit_queryset(rows.order_by('-datetime_created'))

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DocumentPhotoInputSerializer
        else:
            return DocumentPhotoOnlyInputSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data['file']
        if upload.size > 10 * 1024 * 1024:
            raise DRFValidationError({'file': 'حداکثر اندازه فایل ۱۰ مگابایت است.'})
        header = upload.read(16)
        upload.seek(0)
        if not (header.startswith(b'%PDF-') or header.startswith(b'\xff\xd8\xff')
                or header.startswith(b'\x89PNG\r\n\x1a\n')
                or (header.startswith(b'RIFF') and header[8:12] == b'WEBP')):
            raise DRFValidationError({'file': 'فقط PDF، JPEG، PNG یا WebP معتبر پذیرفته می‌شود.'})
        url = ArvanStorage(storage='docs').put_file(upload)
        if not url:
            return Response({'detail': 'ذخیره سند انجام نشد.'}, status=502)
        obj = DocumentPhoto.objects.create(file=url, user=request.user,
                                           document=serializer.validated_data['document'])
        return Response(DocumentPhotoSerializer(obj, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = {
    #     "url": ['exact', ],
    #     "name": ['exact', ],
    #     "document": ['exact', ],
    #     "user": ['exact', ],
    #     "is_deleted": ['exact', ],
    # }
    ordering_fields = '__all__'

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


class DocumentPhotoEditAPIView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):

    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return DocumentPhoto.objects.none()
        grants = authorized_role_views(self.request, self)
        if grants.filter(role__asset_scope='project').exists():
            users = RoleAssignment.objects.filter(
                project_id=project_id, project__is_active=True, is_deleted=False,
                role__is_active=True, user__is_active=True).values('user_id')
            rows = DocumentPhoto.objects.filter(user_id__in=users, is_deleted=False)
        elif self.request.method == 'GET':
            rows = DocumentPhoto.objects.filter(user=self.request.user, is_deleted=False)
        else:
            rows = DocumentPhoto.objects.none()
        return self.limit_queryset(rows)

    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DocumentPhotoSerializer
        else:
            return DocumentPhotoReviewSerializer

    # def update(self, request, *args, **kwargs):  # todo not allow change req
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=self.request.data)
    #     serializer.is_valid(raise_exception=True)
    #     # status = instance.get_status()
    #     # user = User.objects.get(user=self.request.user.id)
    #     # ext_user = ExtendedUser.objects.get(user=user)
    #     # if not (self.request.user) or not (ext_user.status):
    #     #     return Response({'auth error': 'you are not allowed'}) #todo no status yet
    #     self.perform_update(serializer)
    #     return Response(serializer.data)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ] #ask

    lookup_field = 'id'


class UserStatusView(APIView, BaseLimiter):
    def get(self):
        extended_user = ExtendedUser.objects.filter(user=self.request.user).first()
        # todo statuses
        if extended_user.status == 'FORM_COMPLETE' or extended_user.status == 'F_C':
            return [True]
        else:
            return [False]

    # serializer_class = UserSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    #
    # filterset_fields = '__all__'
    # ordering_fields = '__all__'


class ExtendedUseListView(generics.ListAPIView, BaseLimiter):
    serializer_class = SingInExtendedUserOnlySerializer

    def get_queryset(self):
        return self.limit_queryset(ExtendedUser.objects.all())

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    # authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filterset_fields = '__all__'
    ordering_fields = '__all__'


class ExtendedUserEditsView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
                          ]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SingInExtendedUserOnlySerializer
        else:
            return SingInExtendedUserSerializer

    def get_queryset(self):
        return self.limit_queryset(ExtendedUser.objects.all())

    # def update(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=self.request.data)
    #     serializer.is_valid(raise_exception=True)
    #     # user = User.objects.get(user=self.request.user.id)
    #     # ext_user = ExtendedUser.objects.get(user=user)
    #     # if self.request.user or ext_user.status:  # todo set status !!! not given yet
    #     #     return Response({'auth error': 'you are not allowed'})
    #     self.perform_update(serializer)
    #     return Response(serializer.data)


class UserEditAPIView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
                          ]
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        else:
            return AuthUserOnlySerializer

    def get_queryset(self):
        return self.limit_queryset(User.objects.all())


class ProfileEditAPIView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
                          ]
    serializer_class = SingInExtendedUserSerializer

    def get_queryset(self):
        return self.limit_queryset(ExtendedUser.objects.all())

    # def get_object(self):
    #     user = User.objects.filter(id=self.request.user.id).first()
    #     obj = ExtendedUser.objects.filter(user__id=user.id).all()
    #     return obj

    def update(self, request, *args, **kwargs):
        first_name = request.data.get('first_name', None)
        last_name = request.data.get('last_name', None)
        email = request.data.get('email', None)

        user_obj = User.objects.get(id=self.request.user.id)
        if first_name:
            user_obj.first_name = first_name
        if last_name:
            user_obj.last_name = last_name
        if email:
            user_obj.email = email
        user_obj.save()

        partial = kwargs.pop('partial', False)
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


from auth_app.modules.uidshahkar import *


class ConfigValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Config
        fields = ['value']


class UserDataValidationSerializer(serializers.ModelSerializer):

    response = serializers.SerializerMethodField(required=False)

    def get_response(self, obj):
        return obj.message.value if obj.message else ''

    class Meta:
        model = AuthenticationValidationLog
        fields = ('id', 'survey_fillout', 'visit', 'phone_number', 'national_id', 'birth_date', 'sheba_number', 'response')


class AuthenticationValidationLogSerializer(serializers.ModelSerializer):
    message = ConfigValueSerializer()

    class Meta:
        model = AuthenticationValidationLog
        fields = '__all__'


def accessible_validation_logs(request, view):
    """Keep identity-check results inside the granted project and work scope."""
    from visit.asset_access import AssetAccess
    access = AssetAccess(request, view)
    project_id = access.project_id
    if project_id is None:
        return AuthenticationValidationLog.objects.none()
    rows = AuthenticationValidationLog.objects.filter(
        Q(visit__building__project_id=project_id, visit__type__project_id=project_id)
        | Q(survey_fillout__survey__project_id=project_id)
    )
    if access.project_wide:
        return rows
    if not {'assigned', 'supervised'} & access.scopes:
        return rows.none()
    assigned = access.assigned_visits.values('pk')
    return rows.filter(
        Q(visit_id__in=assigned)
        | Q(survey_fillout__visit_id__in=assigned)
        | Q(survey_fillout__user=request.user, survey_fillout__visit__isnull=True)
    )


class UserDataValidationAPI(generics.ListCreateAPIView):
    permission_classes = [DeleteCreateUpdateGetPermission]
    serializer_class = UserDataValidationSerializer
    filterset_fields = ('survey_fillout', 'visit', 'is_main')

    def get_queryset(self):
        return accessible_validation_logs(self.request, self)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AuthenticationValidationLogSerializer
        else:
            return UserDataValidationSerializer

    def perform_create(self, serializer):
        from visit.asset_access import AssetAccess
        access = AssetAccess(self.request, self)
        visit = serializer.validated_data.get('visit')
        fillout = serializer.validated_data.get('survey_fillout')
        if (visit is None) == (fillout is None):
            raise DRFValidationError('دقیقاً یک بازدید یا پرسشنامه باید مشخص شود.')
        if visit is not None:
            allowed = (visit.building.project_id == access.project_id
                       and visit.type.project_id == access.project_id
                       and (access.project_wide or access.assigned_visits.filter(pk=visit.pk).exists()))
        else:
            allowed = (fillout.survey.project_id == access.project_id
                       and (access.project_wide
                            or (fillout.visit_id is not None
                                and access.assigned_visits.filter(pk=fillout.visit_id).exists())
                            or (fillout.visit_id is None and fillout.user_id == self.request.user.pk
                                and bool({'assigned', 'supervised'} & access.scopes))))
        if not allowed:
            raise PermissionDenied('پرونده اعتبارسنجی در دامنه شما نیست.')
        survey_fillout_id = None
        visit_id = None
        if 'survey_fillout' in self.request.data.keys():
            survey_fillout_id = self.request.data['survey_fillout']
        if 'visit' in self.request.data.keys():
            visit_id = self.request.data['visit']
        
        national_id=self.request.data['national_id']
        phone_number=self.request.data['phone_number']
        sheba_number=self.request.data['sheba_number']
        birth_date=self.request.data['birth_date']

        logs = self.get_queryset().filter(
            national_id = national_id,
            phone_number = phone_number,
            sheba_number = sheba_number,
            birth_date = birth_date
        )
        if logs.exists():
            if survey_fillout_id is not None:
                query = logs.filter(survey_fillout__id=survey_fillout_id)
            elif visit_id is not None:
                query = logs.filter(visit__id=visit_id)
            if query.exists():
                raise CustomResponse(UserDataValidationSerializer(query.first(), many=False).data)
            else:
                q= logs.first()
                log = AuthenticationValidationLog()
                log.creator = self.request.user
                log.survey_fillout = None if survey_fillout_id is None else SurveyFillOut.objects.get(id=survey_fillout_id)
                log.visit = None if visit_id is None else Visit.objects.get(id=visit_id)
                log.national_id = q.national_id
                log.phone_number = q.phone_number
                log.sheba_number = q.sheba_number
                log.sheba_message = q.sheba_message
                log.phone_message = q.phone_message
                log.birth_date = q.birth_date
                log.message = q.message
                log.is_sheba_valid = q.is_sheba_valid
                log.is_phone_valid = q.is_phone_valid
                log.is_valid = q.is_valid
                log.save()
                raise CustomResponse(UserDataValidationSerializer(log, many=False).data)
            

        shahkar = UIDShahkar(national_id=self.request.data['national_id'])
        
        phone_with_national, from_shahkar_1 = shahkar.phone_with_national_id(
            phone_number=self.request.data['phone_number'])
        
        sheba_with_national, from_shahkar_2 = shahkar.sheba_with_national_id(
            sheba_number=self.request.data['sheba_number'],
            birth_date=self.request.data['birth_date'])

        messages = Config.objects.filter(category='SHAHKAR').all()

        data_dict = {
            "creator": self.request.user,
            "is_phone_valid": phone_with_national,
            "is_sheba_valid": sheba_with_national,
            "sheba_message": from_shahkar_2,
            "phone_message": from_shahkar_1,
            "is_new": True
        }

        # serializer.save()

        del shahkar

        if from_shahkar_1 == 'U-id error' or from_shahkar_2 == 'U-id error':
            message = messages.filter(key='NoService').first()
            data_dict["message"]=message
            data_dict["is_valid"]=False
        elif phone_with_national and sheba_with_national:
            message = messages.filter(key='FullMatch').first()
            data_dict["message"]=message
            data_dict["is_valid"]=True
        elif not phone_with_national and not sheba_with_national:
            message = messages.filter(key='NoMatch').first()
            data_dict["message"]=message
            data_dict["is_valid"]=False
        elif not phone_with_national:
            message = messages.filter(key='PhoneNotMatch').first()
            data_dict["message"]=message
            data_dict["is_valid"]=False
        else:
            message = messages.filter(key='ShebaNotMatch').first()
            data_dict["message"]=message
            data_dict["is_valid"]=False
        serializer.save(**data_dict)


class ConfigValueAPI(generics.RetrieveAPIView):
    serializer_class = ConfigValueSerializer
    queryset = Config.objects.all()
    lookup_field = 'id'

class AuthenticationValidationLogIsMainEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticationValidationLog
        fields = ('is_main', )

class AuthenticationValidationLogIsMainEditView(generics.UpdateAPIView):
    lookup_field = 'id'
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return accessible_validation_logs(self.request, self)

    serializer_class = AuthenticationValidationLogIsMainEditSerializer

    def perform_update(self, serializer):
        if serializer.validated_data.get('is_main') is not True:
            return serializer.save()
        obj = serializer.instance
        with transaction.atomic():
            query = self.get_queryset().filter(
                visit_id=obj.visit_id
            ) if obj.visit_id is not None else self.get_queryset().filter(
                survey_fillout_id=obj.survey_fillout_id
            )
            locked = AuthenticationValidationLog.objects.filter(pk__in=query.values('pk'))
            list(locked.select_for_update().values_list('pk', flat=True))
            locked.exclude(pk=obj.pk).update(is_main=False)
            return serializer.save()
