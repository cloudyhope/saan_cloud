from django.db import connection, transaction
# from excel_response import ExcelView
import json
import requests
from rest_framework.permissions import BasePermission
from rest_framework import permissions
from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import exceptions, generics, serializers, status
# from address_app.serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from auth_app.models import *
from visit.models import *
# from auth_service.exceptions import *
from django.utils.translation import gettext_lazy as _
import copy

from django.forms import IntegerField, UUIDField
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, generics, serializers
from rest_framework.exceptions import ValidationError as DRFValidationError, NotFound as DRFNotFound
from core.storage import ArvanStorage
# from auth_app.serializers import *
# from address_app.models import *

from core.generics import BaseView

from core.exceptions import *
from django.db.models import Max
from django.db.models import Count, Q, F

from rest_framework.pagination import LimitOffsetPagination

from auth_app.views import *
from auth_app.permissions import authorized_role_views
from visit.management import current_management_q, client_visible_visits
from visit.bulk_scope import locked_project_batch
from visit.ticket_access import TicketAccess


# class TestSer(serializers.Serializer):
#     file = serializers.ImageField()


# class Test(generics.GenericAPIView):
#     queryset = User.objects.none()
#     serializer_class = TestSer

#     def post(self, request):
#         q = ArvanStorage()
#         l = q.put_file(self.request.FILES['file'])
#         return Response({"hi": l})


#################################
# Start
#################################
class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategory
        fields = '__all__'


class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'


class ExtendedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtendedUser
        fields = '__all__'


from auth_app.views import UserSerializer
from visit.asset_access import AssetAccess
from visit.service_requests import ServiceRequestInputSerializer, submit_service_request


# class UserSerializer(serializers.ModelSerializer):
#     extended = serializers.SerializerMethodField()

#     class Meta:
#         model = User
#         fields = '__all__'

#     def get_extended(self, obj):
#         query = ExtendedUser.objects.filter(user=obj)
#         if len(query) > 0:
#             return ExtendedUserSerializer(query[0], many=False).data
#         else:
#             return {}




class MoreInfoKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = MoreInfoKey
        fields = '__all__'


class MoreInfoKeyListCreateView(generics.ListCreateAPIView, BaseLimiter):
    serializer_class = MoreInfoKeySerializer
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

    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return self.queryset.all(MoreInfoKey.objects.all())

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class MoreInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoreInfo
        fields = '__all__'


class NestedMoreInfoSerializer(serializers.ModelSerializer):
    key = MoreInfoKeySerializer()

    class Meta:
        model = MoreInfo
        fields = '__all__'


class MoreInfoListCreateView(generics.ListCreateAPIView, BaseLimiter):

    def get_queryset(self):
        return self.limit_queryset(MoreInfo.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NestedMoreInfoSerializer
        else:
            return MoreInfoSerializer

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

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class AnswerTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerType
        fields = '__all__'


class AnswerChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = '__all__'




######################################################################
# NEWS:
######################################################################


class OnlyClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        exclude = ('legacy_visits',)


class OnlyUserClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserClient
        fields = '__all__'


class OnlyProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'


class OnlyProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OnlyElevatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Elevator
        fields = '__all__'


class OnlyProductElevatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductElevator
        fields = ('id', 'product', 'elevator')
        read_only_fields = ('id',)


class ProductElevatorEndSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductElevator
        fields = ('is_active', 'removal_reason')


class OnlyBuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'


class OnlyBuildingElevatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingElevator
        fields = '__all__'


class OnlyBuildingClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingClient
        fields = '__all__'
        read_only_fields = ('start_at', 'end_at', 'started_by', 'ended_by', 'start_reason', 'end_reason')

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        exclude = ('legacy_visits',)
    


class UserClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserClient
        fields = '__all__'
    
    client = ClientSerializer()
    user = UserSerializer()

class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'
    
   
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
    
    model = ProductModelSerializer()
    
class ElevatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Elevator
        fields = '__all__'
    
    

class ProductElevatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductElevator
        fields = '__all__'
    
    product = ProductSerializer()
    elevator = ElevatorSerializer()
    
class OnlyBuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'
    
    # city = CitySerializer()

    
class BuildingElevatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingElevator
        fields = '__all__'
    
    building = OnlyBuildingSerializer()
    elevator = ElevatorSerializer()

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'
    
    city = CitySerializer()
    # building = BuildingSerializer()
    elevators = serializers.SerializerMethodField()
    def get_elevators(self, obj):
        rows = BuildingElevator.objects.filter(building=obj)
        access = self.context.get('asset_access')
        if access is not None:
            rows = access.filter(rows)
        return BuildingElevatorSerializer(rows, many=True, context=self.context).data


class BuildingClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildingClient
        fields = '__all__'
    
    building = BuildingSerializer()
    client = ClientSerializer()


class EntityPermissionMixin:
    """Require project membership and a method grant for asset/client CRUD."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    @property
    def asset_access(self):
        if not hasattr(self, '_asset_access'):
            self._asset_access = AssetAccess(self.request, self)
        return self._asset_access

    def filter_queryset(self, queryset):
        rows = self.asset_access.filter(super().filter_queryset(queryset))
        return BaseLimiter.limit_queryset(self, rows)

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'asset_access': self.asset_access}

    def perform_create(self, serializer):
        self.asset_access.validate_write(serializer, creating=True)
        if serializer.Meta.model in (Client, Building, Elevator, Product, ProductModel):
            serializer.save(project_id=self.asset_access.project_id)
        elif serializer.Meta.model is BuildingClient:
            serializer.save(started_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        self.asset_access.validate_write(serializer)
        serializer.save()


class ClientListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    search_fields = ['name', 'name_fa']
    def get_queryset(self):
        return Client.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClientSerializer
        else:
            return OnlyClientSerializer
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class ClientEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Client.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClientSerializer
        else:
            return OnlyClientSerializer
    
    lookup_field = 'id'


class UserClientListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return UserClient.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserClientSerializer
        else:
            return OnlyUserClientSerializer
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class UserClientEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return UserClient.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserClientSerializer
        else:
            return OnlyUserClientSerializer
    
    lookup_field = 'id'


class ProductModelListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return ProductModel.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductModelSerializer
        else:
            return OnlyProductModelSerializer
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class ProductModelEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return ProductModel.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductModelSerializer
        else:
            return OnlyProductModelSerializer
    
    lookup_field = 'id'


class ProductListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return Product.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductSerializer
        else:
            return OnlyProductSerializer
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class ProductEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Product.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductSerializer
        else:
            return OnlyProductSerializer
    
    lookup_field = 'id'


class ElevatorListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return Elevator.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ElevatorSerializer
        else:
            return OnlyElevatorSerializer
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class ElevatorEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Elevator.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ElevatorSerializer
        else:
            return OnlyElevatorSerializer
    
    lookup_field = 'id'


class ProductElevatorListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return ProductElevator.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductElevatorSerializer
        else:
            return OnlyProductElevatorSerializer

    def perform_create(self, serializer):
        self.asset_access.validate_write(serializer, creating=True)
        product = serializer.validated_data['product']
        with transaction.atomic():
            Product.objects.select_for_update().get(pk=product.pk)
            if ProductElevator.objects.filter(product=product, is_active=True).exists():
                raise DRFValidationError({'product': 'این قطعه هم‌اکنون روی آسانسور نصب است.'})
            serializer.save(is_active=True, installed_at=timezone.now(), installed_by=self.request.user)
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class ProductElevatorEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return ProductElevator.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProductElevatorSerializer
        else:
            return ProductElevatorEndSerializer

    def perform_update(self, serializer):
        if not self.asset_access.project_wide:
            raise exceptions.PermissionDenied('تغییر نصب قطعه نیازمند دسترسی کل پروژه است.')
        if serializer.validated_data.get('is_active') is not False or not serializer.instance.is_active:
            raise DRFValidationError({'is_active': 'برای نصب مجدد، سابقه نصب تازه ایجاد کنید.'})
        with transaction.atomic():
            Product.objects.select_for_update().get(pk=serializer.instance.product_id)
            serializer.save(removed_at=timezone.now(), removed_by=self.request.user)

    def perform_destroy(self, instance):
        if not self.asset_access.project_wide:
            raise exceptions.PermissionDenied('تغییر نصب قطعه نیازمند دسترسی کل پروژه است.')
        if not instance.is_active:
            raise DRFValidationError({'product': 'این نصب قبلاً پایان یافته است.'})
        with transaction.atomic():
            Product.objects.select_for_update().get(pk=instance.product_id)
            instance.is_active = False
            instance.removed_at = timezone.now()
            instance.removed_by = self.request.user
            instance.removal_reason = 'پایان نصب از پنل'
            instance.save(update_fields=['is_active', 'removed_at', 'removed_by', 'removal_reason'])
    
    lookup_field = 'id'


class BuildingListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return Building.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BuildingSerializer
        else:
            return OnlyBuildingSerializer
    # filterset_fields = '__all__'
    filterset_fields = {
        'name': ['exact',],
        'verbose_name': ['exact',],
        'type': ['exact',],
        'parent': ['exact', 'isnull',],
        'address': ['exact',],
        'longitude': ['exact',],
        'latitude': ['exact',],
        'city': ['exact',],
        'is_visiting': ['exact',],
        'code': ['exact',],
    }
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class BuildingEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return Building.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BuildingSerializer
        else:
            return OnlyBuildingSerializer
    
    lookup_field = 'id'


class BuildingElevatorListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    def get_queryset(self):
        return BuildingElevator.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BuildingElevatorSerializer
        else:
            return OnlyBuildingElevatorSerializer
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

class BuildingElevatorEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return BuildingElevator.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BuildingElevatorSerializer
        else:
            return OnlyBuildingElevatorSerializer
    
    lookup_field = 'id'


class BuildingClientListCreateAPIView(EntityPermissionMixin, generics.ListCreateAPIView):
    search_fields = ['building__name', 'building__verbose_name', 'building__code', 'building__address', 'client__name_fa']
    def get_queryset(self):
        if str(self.request.query_params.get('me', '')).lower() in ('true', '1'):
            return BuildingClient.objects.filter(
                client__in=UserClient.objects.filter(user=self.request.user).values_list('client', flat=True),
            ).filter(current_management_q())
        return BuildingClient.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BuildingClientSerializer
        else:
            return OnlyBuildingClientSerializer
    filterset_fields = {
        "building": ['exact'],
        "building__name": ['exact',],
        "building__verbose_name": ['exact',],
        "building__type": ['exact',],
        "building__parent": ['exact', 'isnull',],
        "building__address": ['exact',],
        "building__longitude": ['exact',],
        "building__latitude": ['exact',],
        "building__city": ['exact',],
        "building__city__province": ['exact',],
        "building__is_visiting": ['exact',],
        "building__code": ['exact',],
        "client": ['exact'],
        "client__name": ['exact',],
        "client__name_fa": ['exact',],
        "client__avatar_photo": ['exact',],
        "client__description": ['exact',],
        # "client__visit_types": ['exact',],
        "client__type": ['exact',],
        "end_at": ['isnull',],
    }
    ordering_fields = '__all__'
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

class BuildingClientEditsAPIView(EntityPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return BuildingClient.objects.all()
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BuildingClientSerializer
        else:
            return OnlyBuildingClientSerializer
    
    lookup_field = 'id'

    def perform_destroy(self, instance):
        if not self.asset_access.project_wide:
            raise exceptions.PermissionDenied('پایان مدیریت ساختمان نیازمند دسترسی کل پروژه است.')
        if instance.end_at is None:
            instance.end_at = timezone.now()
            instance.ended_by = self.request.user
            instance.save(update_fields=['end_at', 'ended_by'])




######################################################################
# NEWS:
######################################################################





from auth_app.views import QuestionAnswerTypeValidationSerializer


class VisitTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitType
        fields = '__all__'


class VisitSerializer(serializers.ModelSerializer):
    # UserSerializer()
    creator = UserSerializer()
    promoter = UserSerializer()
    expert_details = UserSerializer(source='expert', read_only=True)
    elevator = ElevatorSerializer(many=True)
    type = VisitTypeOnlySerializer()
    checked_by = UserSerializer()
    building = BuildingSerializer()
    comment_publisher = UserSerializer()
    supervisors = serializers.SerializerMethodField()
    rate = serializers.SerializerMethodField()
    is_pending_request = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    assignment = serializers.SerializerMethodField()

    def get_priority(self, obj):
        from visit.priority import visit_priority
        return visit_priority(obj)

    def get_assignment(self, obj):
        from visit.field_ops import assignment_state
        return assignment_state(obj)

    def get_is_pending_request(self, obj):
        return (not obj.is_active and obj.status == Visit.NOTVISITED
                and obj.service_submissions.exists())

    def get_rate(self, obj):
        rate = VisitRate.objects.filter(visit=obj).order_by('-datetime_created').first()
        return rate.rate if rate else rate

    def get_supervisors(self, obj):
        supervisors = Supervisor.objects.filter(promoter=obj.promoter, project=obj.type.project, is_active=True)
        return SupervisorNestedSerializer(supervisors, many=True).data

    class Meta:
        model = Visit
        exclude = ('completion_code', 'completion_code_failures', 'completion_code_locked_until')  # only the client app shows the code


class VisitOnlySerializer(serializers.ModelSerializer):
    # UserSerializer()
    # creator = UserSerializer()
    # promoter = UserSerializer()
    # checked_by = UserSerializer()
    # building = BuildingSerializer()
    # comment_publisher = UserSerializer()
    class Meta:
        model = Visit
        exclude = ('completion_code', 'completion_code_failures', 'completion_code_locked_until')  # only the client app shows the code

class QuestionTypeSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    class Meta:
        model = QuestionType
        fields = '__all__'


class QuestionSerializer(serializers.ModelSerializer):
    question_type = QuestionTypeSerializer()
    # validation = FieldValidationSerializer()
    answer_type = AnswerTypeSerializer(many=True)
    answer_choices = AnswerChoiceSerializer(many=True)
    dropdown_choices = AnswerChoiceSerializer(many=True)
    radio_choices = AnswerChoiceSerializer(many=True)
    report_category = ReportCategorySerializer()
    answer_params = serializers.SerializerMethodField()

    def get_answer_params(self, obj):
        data = QuestionAnswerTypeValidation.objects.filter(visit_question=obj)
        return QuestionAnswerTypeValidationSerializer(data, many=True).data

    class Meta:
        model = Question
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    visit = VisitSerializer()
    question = QuestionSerializer()
    dropdown = AnswerChoiceSerializer()
    radio = AnswerChoiceSerializer()

    class Meta:
        model = Answer
        fields = '__all__'


class FieldAnswerSerializer(serializers.ModelSerializer):
    """Compact answer for the field questionnaire; the visit is already known to the caller."""
    dropdown = AnswerChoiceSerializer()
    radio = AnswerChoiceSerializer()

    class Meta:
        model = Answer
        fields = ('id', 'question', 'bool', 'score', 'number', 'text', 'description', 'price',
                  'multichoice', 'dropdown', 'radio', 'datetime_last_change')


class PhotoTypeSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()
    report_category = ReportCategorySerializer()

    class Meta:
        model = PhotoType
        fields = '__all__'


class PhotoSerializer(serializers.ModelSerializer):
    type = PhotoTypeSerializer()
    visit = VisitSerializer()
    distance = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = '__all__'

    def get_link(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.link, self.context.get('request'))

    def get_distance(self, obj):
        from decimal import Decimal
        building = obj.visit.building
        if building is None or building.longitude is None or building.latitude is None:
            return -1
        elif obj.longitude is None or obj.latitude is None:
            return -2
        elif obj.longitude == Decimal(0) or obj.latitude == Decimal(0):
            return -3
        else:
            from geopy.distance import great_circle as GRC
            try:
                return GRC((obj.latitude, obj.longitude), (building.latitude, building.longitude)).m
            except:
                return -4


########################################
# APIs:
########################################


class ReportCategoryListAPIView(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'project'

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('visit_id') is not None:
            return self.limit_queryset(self.get_projectified_queryset(ReportCategory.objects.filter(
                visit_type=Visit.objects.get(id=self.request.GET.get('visit_id')).type).order_by('id')))
        else:
            return self.get_projectified_queryset(ReportCategory.objects.all().order_by('id'))

    serializer_class = ReportCategorySerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = '__all__'
    ordering_fields = '__all__'


class PromoterVisitsAPIView(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'type__project'

    def get_queryset(self):
        from django.db.models import Q
        today = timezone.localdate()
        rows = Visit.objects.filter(
            Q(promoter=self.request.user) | Q(expert=self.request.user),
            status__in=[Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND],
            is_deleted=False, is_active=True, building__project_id=self.request.query_params.get('p'),
        )
        schedule = self.request.query_params.get('schedule')
        if schedule == 'overdue':
            rows = rows.filter(has_due_date=True, due_date__lt=today)
        elif schedule == 'today':
            rows = rows.filter(has_due_date=True, due_date=today)
        elif schedule == 'upcoming':
            rows = rows.filter(has_due_date=True, due_date__gt=today)
        elif schedule == 'unscheduled':
            rows = rows.filter(Q(has_due_date=False) | Q(due_date__isnull=True))
        from visit.priority import annotate_visits
        # Higher service priority first (client tier, building sensitivity...), then the nearest due date.
        rows = annotate_visits(self.limit_queryset(self.get_projectified_queryset(rows)).distinct())
        return rows.order_by(F('priority_value').desc(nulls_last=True), '-has_due_date', 'due_date', 'id')

    serializer_class = VisitSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = (
        "creator",
        "promoter",
        "building",
        "building__city",
        "building__city__province",
        "status",
        "is_deleted",
        "checked_by",
        "rejection_reason",
        "datetime_created",
        "datetime_last_change",
        "start_datetime",
    )
    ordering_fields = '__all__'
    search_fields = ['building__verbose_name', 'building__address', 'building__name', 'building__parent__name',]

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class PromoterVisitStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=(Visit.INPROGRESS, Visit.COMPLETED), required=False)
    supervision_status = serializers.ChoiceField(choices=(Visit.INPROGRESS, Visit.COMPLETED), required=False)
    client_code = serializers.RegexField(r'^\d{6}$', required=False,
                                         error_messages={'invalid': 'کد تأیید شش رقمی است.'})


class PromoterVisitStatusChangeAPIView(generics.GenericAPIView):
    serializer_class = PromoterVisitStatusChangeSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def put(self, request, id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if 'status' not in serializer.validated_data or set(serializer.validated_data) - {'status', 'client_code'}:
            raise DRFValidationError({'status': 'فقط وضعیت مأموریت قابل تغییر است.'})
        visit = assigned_field_visit(request, id)
        new_status = serializer.validated_data['status']
        with transaction.atomic():
            visit = Visit.objects.select_for_update().get(pk=visit.pk)
            if new_status == Visit.INPROGRESS:
                if visit.status not in [Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND]:
                    raise DRFValidationError({'status': 'این مأموریت قابل شروع نیست.'})
            elif visit.status != Visit.INPROGRESS:
                raise DRFValidationError({'status': 'فقط مأموریت شروع‌شده قابل پایان است.'})
            if new_status == Visit.COMPLETED:
                from visit.field_completion import completion_gaps
                gaps = completion_gaps(visit)
                if any(gaps.values()):
                    return Response({'requirements': gaps}, status=400)
                if visit.type.requires_client_code:
                    from visit.field_ops import CodeRejected, check_completion_code
                    try:
                        check_completion_code(visit, serializer.validated_data.get('client_code') or '')
                    except CodeRejected as error:
                        # Returning (not raising) commits the failure counter.
                        return Response({'client_code': [str(error)]}, status=400)
            visit.status = new_status
            fields = ['status', 'datetime_last_change']
            if new_status == Visit.INPROGRESS and visit.start_datetime is None:
                visit.start_datetime = timezone.now()  # first start of the field work
                fields.append('start_datetime')
            visit.save(update_fields=fields)
            if new_status == Visit.INPROGRESS:
                from visit.field_ops import record_acceptance
                record_acceptance(visit, request.user)  # starting the work accepts the assignment
            if new_status == Visit.COMPLETED:
                from notification.in_app import notify_visit_completed
                from visit.report_snapshot import capture_report_snapshot
                # A corrected re-completion keeps earlier versions and publishes the next one.
                snapshot = capture_report_snapshot(visit, request.user, new_version=True)
                actor_id = request.user.id
                transaction.on_commit(lambda: notify_visit_completed(visit, snapshot.version, actor_id))
            if visit.building_id:
                building = visit.building
                building.is_visiting = Visit.objects.filter(
                    building=building, status=Visit.INPROGRESS,
                    is_active=True, is_deleted=False,
                ).exists()
                building.save(update_fields=['is_visiting'])
        return Response(VisitSerializer(visit).data)

    def patch(self, request, id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if set(serializer.validated_data) != {'supervision_status'}:
            raise DRFValidationError({'supervision_status': 'فقط وضعیت نظارت قابل تغییر است.'})
        visit = assigned_field_visit(request, id, view=self, allow_supervised=True)
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise DRFNotFound()
        if not authorized_role_views(request, self).filter(role__asset_scope='supervised').exists():
            raise DRFNotFound()
        if not Supervisor.objects.filter(
            supervisor=request.user, promoter_id=visit.promoter_id,
            project_id=project_id, is_active=True,
        ).exists():
            raise DRFNotFound()
        new_status = serializer.validated_data['supervision_status']
        with transaction.atomic():
            visit = Visit.objects.select_for_update().get(pk=visit.pk)
            if visit.status not in [Visit.COMPLETED, Visit.APPROVED]:
                raise DRFValidationError({'status': 'بازدید کارشناس هنوز پایان نیافته است.'})
            if new_status == Visit.INPROGRESS:
                if visit.supervision_status not in [Visit.NOTVISITED, Visit.INPROGRESS]:
                    raise DRFValidationError({'supervision_status': 'نظارت بسته شده است.'})
            elif visit.supervision_status != Visit.INPROGRESS:
                raise DRFValidationError({'supervision_status': 'نظارت باید ابتدا شروع شود.'})
            if new_status == Visit.COMPLETED:
                from visit.field_completion import completion_gaps
                gaps = completion_gaps(visit, supervision=True)
                if any(gaps.values()):
                    return Response({'requirements': gaps}, status=400)
            visit.supervision_status = new_status
            visit.save(update_fields=['supervision_status', 'datetime_last_change'])
        return Response(VisitSerializer(visit).data)


class QuestionListForVisitsSerializer(serializers.Serializer):
    question = QuestionSerializer()
    submitted_answer = FieldAnswerSerializer()


def assigned_field_visit(request, visit_id, editable=False, view=None, allow_supervised=False,
                         allow_project_read=False):
    """Resolve a field visit without exposing another project's or worker's record.

    allow_project_read lets project-wide roles read (never edit) any visit of the project, so
    reviewers can open a report they did not perform.
    """
    try:
        project_id = int(request.query_params.get('p'))
        visit_id = int(visit_id)
    except (TypeError, ValueError):
        raise DRFNotFound()
    if project_id <= 0 or visit_id <= 0:
        raise DRFNotFound()
    visits = Visit.objects.filter(
        pk=visit_id, type__project_id=project_id, building__project_id=project_id,
        is_deleted=False, is_active=True,
    )
    visit = visits.first()
    if visit is None:
        raise DRFNotFound()
    assigned = visit.promoter_id == request.user.id or visit.expert_id == request.user.id
    supervised = (allow_supervised and view is not None
                  and authorized_role_views(request, view).filter(role__asset_scope='supervised').exists()
                  and Supervisor.objects.filter(
                      supervisor=request.user, promoter_id=visit.promoter_id,
                      project_id=project_id, is_active=True,
                  ).exists())
    project_reader = (allow_project_read and not editable and view is not None
                      and authorized_role_views(request, view).filter(role__asset_scope='project').exists())
    if not assigned and not supervised and not project_reader:
        raise DRFNotFound()
    if editable:
        field_open = assigned and visit.status in [Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND]
        supervision_open = (supervised and visit.status in [Visit.COMPLETED, Visit.APPROVED]
                            and visit.supervision_status in [Visit.NOTVISITED, Visit.INPROGRESS])
        if not (field_open or supervision_open):
            raise DRFNotFound()
    return visit


class QuestionListForVisitsAPIView(generics.ListAPIView):
    def get_queryset(self, *args, **kwargs):
        # visit_id = int(kwargs.get('visit_id', 0))
        # print("q", kwargs, args)
        # visit = Visit.objects.get(id=1)
        return Question.objects.none()

    serializer_class = QuestionSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def list(self, request, *args, **kwargs):
        supervision_flag = request.query_params.get('question_type__is_for_supervision')
        if supervision_flag not in (None, 'true', 'True', 'false', 'False'):
            raise DRFValidationError({'question_type__is_for_supervision': 'مقدار نامعتبر است.'})
        supervised = supervision_flag in ('true', 'True')
        if supervised and not authorized_role_views(request, self).filter(role__asset_scope='supervised').exists():
            raise DRFNotFound()
        visit = assigned_field_visit(
            request, kwargs.get('visit_id'), view=self, allow_supervised=supervised,
        )
        project_id = visit.type.project_id
        queryset = Question.objects.filter(
            question_type__visit_type=visit.type, question_type__project_id=project_id,
            question_type__is_active=True, is_active=True,
        ).order_by('priority', 'id')
        question_type = request.query_params.get('question_type')
        if question_type is not None:
            if not question_type.isdecimal():
                raise DRFValidationError({'question_type': 'شناسه نامعتبر است.'})
            queryset = queryset.filter(question_type_id=int(question_type))
        question_family = request.query_params.get('type')
        if question_family is not None:
            if question_family not in dict(Question.QUESTIONS_CHOICES):
                raise DRFValidationError({'type': 'نوع سؤال نامعتبر است.'})
            queryset = queryset.filter(type=question_family)
        if supervision_flag is not None:
            queryset = queryset.filter(question_type__is_for_supervision=supervised)
        if supervised and visit.promoter_id != request.user.id and visit.expert_id != request.user.id:
            queryset = queryset.filter(question_type__is_for_supervision=True)
        report_category_id = request.query_params.get('report_category')
        if report_category_id is not None:
            if not report_category_id.isdecimal():
                raise DRFValidationError({'report_category': 'شناسه نامعتبر است.'})
            queryset = queryset.filter(
                report_category_id=int(report_category_id),
                report_category__project_id=project_id,
                report_category__visit_type=visit.type,
            )
        questions = list(queryset)
        answers = {
            answer.question_id: answer for answer in
            Answer.objects.filter(visit=visit, question_id__in=[q.pk for q in questions]).order_by('id')
        }
        output = []
        for question in questions:
            answer = answers.get(question.pk)
            if report_category_id is not None and answer is not None:
                continue
            output.append({
                'question': question,
                'submitted_answer': answer if answer is not None else Answer(),
            })
        return Response(QuestionListForVisitsSerializer(output, many=True).data)


class PhotoCreateSerializer(serializers.Serializer):
    visit = serializers.IntegerField(min_value=1)
    type = serializers.IntegerField(min_value=1)
    link = serializers.FileField()
    longitude = serializers.DecimalField(required=False, allow_null=True, max_digits=22, decimal_places=16)
    latitude = serializers.DecimalField(required=False, allow_null=True, max_digits=22, decimal_places=16)


class PromoterUploadImageAPIView(generics.GenericAPIView):
    serializer_class = PhotoCreateSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, *args, **kwargs):
        from PIL import Image, UnidentifiedImageError

        payload = request.data.copy()
        for coordinate in ('longitude', 'latitude'):
            if str(payload.get(coordinate, '')).strip().lower() in ('', 'null', 'none'):
                payload[coordinate] = None
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise DRFNotFound()
        photo_type = PhotoType.objects.filter(
            pk=data['type'], project_id=project_id, is_active=True,
        ).first()
        if photo_type is None:
            raise DRFNotFound()
        visit = assigned_field_visit(
            request, data['visit'], editable=True, view=self,
            allow_supervised=photo_type.is_for_supervision,
        )
        if photo_type.visit_type_id != visit.type_id:
            raise DRFNotFound()
        if photo_type.is_for_supervision and not authorized_role_views(request, self).filter(role__asset_scope='supervised').exists():
            raise DRFNotFound()
        if photo_type.is_for_supervision and visit.status not in [Visit.COMPLETED, Visit.APPROVED]:
            raise DRFNotFound()
        upload = data['link']
        if upload.size > 10 * 1024 * 1024:
            raise DRFValidationError({'link': 'حجم عکس باید حداکثر ۱۰ مگابایت باشد.'})
        try:
            with Image.open(upload) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise DRFValidationError({'link': 'قالب عکس مجاز نیست.'})
                image.verify()
            upload.seek(0)
        except (UnidentifiedImageError, OSError, ValueError):
            raise DRFValidationError({'link': 'فایل عکس معتبر نیست.'})
        if photo_type.max and Photo.objects.filter(visit=visit, type=photo_type, is_deleted=False).count() >= photo_type.max:
            raise DRFValidationError({'type': 'حداکثر تعداد عکس این بخش ثبت شده است.'})
        try:
            link = ArvanStorage().put_file(upload)
        except Exception:
            return Response({'detail': 'ذخیره عکس انجام نشد.'}, status=502)
        if not link:
            return Response({'detail': 'ذخیره عکس انجام نشد.'}, status=502)
        with transaction.atomic():
            visit = Visit.objects.select_for_update().get(pk=visit.pk)
            obj = Photo.objects.create(
                creator=request.user, visit=visit, type=photo_type, link=link,
                longitude=data.get('longitude'), latitude=data.get('latitude'),
            )
            if visit.start_datetime is None and photo_type.name == 'StoreFront':
                visit.start_datetime = timezone.now()
                visit.save(update_fields=['start_datetime', 'datetime_last_change'])
        return Response(PhotoSerializer(obj, context={'request': request}).data)


class PromoterAnswerCommitmentSerializer(serializers.Serializer):
    visit = serializers.IntegerField(min_value=1)
    question = serializers.IntegerField(min_value=1)
    bool = serializers.BooleanField(required=False, allow_null=True)
    score = serializers.IntegerField(required=False, allow_null=True)
    number = serializers.IntegerField(required=False, allow_null=True)
    text = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    multichoice = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True,
    )
    dropdown = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    radio = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    longitude = serializers.DecimalField(required=False, allow_null=True, max_digits=22, decimal_places=16)
    latitude = serializers.DecimalField(required=False, allow_null=True, max_digits=22, decimal_places=16)


class PromoterAnswersQuestionsView(generics.GenericAPIView):
    serializer_class = PromoterAnswerCommitmentSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return Answer.objects.none()

    def post(self, request):
        unknown = set(request.data) - set(self.get_serializer().fields)
        if unknown:
            raise DRFValidationError({'fields': 'فیلد غیرمجاز در پاسخ وجود دارد.'})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        answer_fields = {
            'bool', 'score', 'number', 'text', 'description', 'price',
            'multichoice', 'dropdown', 'radio',
        }
        submitted = answer_fields.intersection(data)
        if not submitted:
            raise DRFValidationError({'answer': 'حداقل یک مقدار پاسخ لازم است.'})
        question = Question.objects.filter(
            pk=data['question'], is_active=True, question_type__is_active=True,
            question_type__isnull=False,
        ).first()
        if question is None:
            raise DRFNotFound()
        supervisor_question = question.question_type.is_for_supervision
        visit = assigned_field_visit(
            request, data['visit'], editable=True, view=self,
            allow_supervised=supervisor_question,
        )
        if (question.question_type.project_id != visit.type.project_id
                or question.question_type.visit_type_id != visit.type_id):
            raise DRFNotFound()
        if supervisor_question and not authorized_role_views(request, self).filter(role__asset_scope='supervised').exists():
            raise DRFNotFound()
        if (visit.promoter_id != request.user.id and visit.expert_id != request.user.id
                and not supervisor_question):
            raise DRFNotFound()
        allowed_fields = set(question.answer_type.values_list('field', flat=True))
        if not submitted.issubset(allowed_fields):
            raise DRFValidationError({'answer': 'نوع پاسخ با سؤال سازگار نیست.'})
        for field, relation in (
            ('multichoice', question.answer_choices),
            ('dropdown', question.dropdown_choices),
            ('radio', question.radio_choices),
        ):
            if field not in data or data[field] is None:
                continue
            submitted_ids = set(data[field]) if field == 'multichoice' else {data[field]}
            valid_ids = set(relation.filter(pk__in=submitted_ids).values_list('pk', flat=True))
            if submitted_ids != valid_ids:
                raise DRFValidationError({field: 'گزینه انتخابی به این سؤال تعلق ندارد.'})

        with transaction.atomic():
            locked = Visit.objects.select_for_update().get(pk=visit.pk)
            field_open = not supervisor_question and locked.status in [Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND]
            supervision_open = (supervisor_question and locked.status in [Visit.COMPLETED, Visit.APPROVED]
                                and locked.supervision_status in [Visit.NOTVISITED, Visit.INPROGRESS])
            if not (field_open or supervision_open):
                raise DRFValidationError({'visit': 'این مأموریت برای ثبت پاسخ باز نیست.'})
            answer = Answer.objects.filter(visit=locked, question=question).order_by('id').first()
            if answer is None:
                answer = Answer(visit=locked, question=question)
            for field in submitted - {'multichoice', 'dropdown', 'radio'}:
                setattr(answer, field, data[field])
            for field in ('dropdown', 'radio'):
                if field in data:
                    setattr(answer, field + '_id', data[field])
            for field in ('longitude', 'latitude'):
                if field in data:
                    setattr(answer, field, data[field])
            answer.save()
            if 'multichoice' in data:
                answer.multichoice.set(data['multichoice'])
        return Response(FieldAnswerSerializer(answer).data)


class PromoterVisistsHistory(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'type__project'

    def get_queryset(self):
        return self.limit_queryset( self.get_projectified_queryset(
            Visit.objects.filter(Q(promoter=self.request.user) | Q(expert=self.request.user),
                                 status__in=['2', '3', '4', '5'], is_deleted=False,
                                 building__project_id=self.request.query_params.get('p'),
                                 ).order_by('-datetime_last_change', '-id')))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    serializer_class = VisitSerializer

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset) #ask for paginate


class PhotoTypeSettingsSerializer(PhotoTypeSerializer):
    progress = serializers.CharField()
    status = serializers.BooleanField()
    count = serializers.IntegerField(default=0)


class QuestionTypeSettingsSerializer(serializers.ModelSerializer):
    report_category = ReportCategorySerializer()
    progress = serializers.CharField()
    status = serializers.BooleanField()
    
    final_score = serializers.ReadOnlyField()
    final_result = serializers.ReadOnlyField()
    answered_count = serializers.IntegerField(default=0)
    question_count = serializers.IntegerField(default=0)
    required_count = serializers.IntegerField(default=0)
    missing_required = serializers.IntegerField(default=0)

    # question_type = serializers.SerializerMethodField()

    class Meta:
        model = QuestionType
        fields = '__all__'

    # def get_question_type(self, obj):
    # return obj.name


from survey.views import SurveySerializer

from config.views import AddInSerializer
class FrontVisitPageSettingsSerializer(serializers.Serializer):
    visit = VisitSerializer()
    start_time = serializers.DateTimeField()
    questions = QuestionTypeSettingsSerializer(many=True)
    photos = PhotoTypeSettingsSerializer(many=True)
    surveys = SurveySerializer(many=True)
    add_ins = AddInSerializer(many=True)
    is_assignee = serializers.BooleanField(default=False)
    editable = serializers.BooleanField(default=False)
    requirements = serializers.DictField(default=dict)
    report_version = serializers.IntegerField(allow_null=True, default=None)


def calculate_final_score(visit: Visit, question_type: QuestionType) -> int:
    """Sum up scores in questions dropdown/radio answers and return the result"""
    result = 0

    questions = Question.objects.filter(question_type=question_type, is_active=True)
    answers = Answer.objects.filter(visit=visit, question__in=questions)
    
    for answer in answers:
        if answer.dropdown is not None:
            result += (answer.dropdown.score or 0)
        elif answer.radio is not None:
            result += (answer.radio.score or 0)
            
    return result

def get_result(visit: Visit, final_score: int):
    try:
        rule = VisitRule.objects.get(visit=visit, score_begin__lte=final_score, score_end__gt=final_score)
        return rule.result

    except VisitRule.DoesNotExist:
        return None

class FrontVisitPageSettingsView(generics.GenericAPIView):
    serializer_class = FrontVisitPageSettingsSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request, *args, **kwargs):
        from visit.field_completion import _has_answer

        flag = request.query_params.get('s', 'false').lower()
        if flag not in ('true', 'false'):
            raise DRFValidationError({'s': 'مقدار نامعتبر است.'})
        supervision = flag == 'true'
        if supervision and not authorized_role_views(request, self).filter(role__asset_scope='supervised').exists():
            raise DRFNotFound()
        visit = assigned_field_visit(
            request, kwargs.get('visit_id'), view=self, allow_supervised=supervision,
            allow_project_read=True,
        )
        project_id = visit.type.project_id
        question_types = list(QuestionType.objects.filter(
            visit_type=visit.type, project_id=project_id,
            is_active=True, is_for_supervision=supervision,
        ).order_by('id'))
        for question_type in question_types:
            questions = list(Question.objects.filter(
                question_type=question_type, is_active=True,
            ).prefetch_related('answer_type'))
            answers = {answer.question_id: answer for answer in Answer.objects.filter(
                visit=visit, question__in=questions,
            ).prefetch_related('multichoice').order_by('id')}
            answered = sum(
                _has_answer(answers.get(question.pk), question.answer_type.values_list('field', flat=True))
                for question in questions
            )
            question_type.status = bool(questions) and answered == len(questions)
            question_type.progress = f'{(answered / len(questions) * 100):g}%' if questions else '0%'
            question_type.answered_count = answered
            question_type.question_count = len(questions)
            required = [question for question in questions if question_type.is_mandatory or question.is_mandatory]
            question_type.required_count = len(required)
            question_type.missing_required = sum(
                not _has_answer(answers.get(question.pk), question.answer_type.values_list('field', flat=True))
                for question in required)
            question_type.final_score = calculate_final_score(visit, question_type)
            question_type.final_result = get_result(visit, question_type.final_score)

        photo_types = list(PhotoType.objects.filter(
            visit_type=visit.type, project_id=project_id,
            is_active=True, is_for_supervision=supervision,
        ).order_by('id'))
        start_time = None
        for photo_type in photo_types:
            rows = Photo.objects.filter(visit=visit, type=photo_type, is_deleted=False).order_by('id')
            count = rows.count()
            target = max(photo_type.min or 0, 1)
            photo_type.status = count >= target
            photo_type.progress = f'{(min(count / target, 1) * 100):g}%'
            photo_type.count = count
            if photo_type.name == 'StoreFront':
                first = rows.first()
                start_time = first.datetime_created if first else None

        from visit.field_completion import completion_gaps
        assigned = request.user.id in (visit.expert_id, visit.promoter_id)
        open_states = [Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND]
        result = {
            'visit': visit,
            'questions': question_types,
            'photos': photo_types,
            'start_time': start_time,
            'add_ins': visit.type.add_ins.all(),
            'surveys': visit.type.surveys.all(),
            'is_assignee': assigned,
            'editable': assigned and not supervision and visit.status in open_states,
            'requirements': completion_gaps(visit, supervision=supervision),
            'report_version': visit.report_snapshots.order_by('-version').values_list('version', flat=True).first(),
        }
        return Response(FrontVisitPageSettingsSerializer(result).data)


class ListPhotoForVisitSerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = '__all__'

    def get_link(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.link, self.context.get('request'))


class ListPhotoForVisitView(BaseLimiter, generics.ListAPIView, BaseView):
    serializer_class = ListPhotoForVisitSerializer
    project_path = 'type__project'

    def get_queryset(self):
        access = AssetAccess(self.request, self)
        rows = Photo.objects.filter(is_deleted=False, type__project_id=access.project_id,
                                    visit__type__project_id=access.project_id,
                                    visit__building__project_id=access.project_id,
                                    visit__in=access.visits)
        return self.limit_queryset(rows)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = (
        'id',
        'type',
        'link',
        'visit',
        'longitude',
        'latitude',
        'datetime_created',
        'datetime_last_change',
    )
    ordering_fields = '__all__'
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)



class PromoterDeletePhotoView(BaseLimiter, generics.RetrieveDestroyAPIView):
    serializer_class = PhotoSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        access = AssetAccess(self.request, self)
        rows = Photo.objects.filter(Q(visit__promoter=self.request.user) | Q(visit__expert=self.request.user),
                                    is_deleted=False,
                                    type__project_id=access.project_id,
                                    visit__type__project_id=access.project_id,
                                    visit__building__project_id=access.project_id,
                                    visit__in=access.assigned_visits,
                                    visit__status__in=(Visit.NOTVISITED, Visit.INPROGRESS,
                                                      Visit.RETRY, Visit.SUSPEND))
        return self.limit_queryset(rows)

    lookup_field = 'id'

    # is deleted is handled in models!

    # def perform_destroy(self, instance):
    #     instance.is_deleted = True
    #     instance.save()
    #     return super().perform_destroy(instance)


#######################################
# Census APIs:
#######################################


class CensusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Census
        fields = '__all__'


class CensusListView(BaseLimiter, generics.ListAPIView):
    serializer_class = CensusSerializer

    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return self.limit_queryset(Census.objects.all())

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


class CountPerCitySerializer(serializers.Serializer):
    city = serializers.CharField()
    city_count = serializers.IntegerField()


class CensusAggregateSerializer(serializers.Serializer):
    count_per_city = serializers.ListField(child=CountPerCitySerializer())
    all_count = serializers.IntegerField()
    hamkari_avalaible_count = serializers.IntegerField()


class CensusAggregateView(BaseLimiter, generics.GenericAPIView):
    serializer_class = CensusAggregateSerializer

    def get_queryset(self):
        return self.limit_queryset(Census.objects.all())

    def get(self, request):
        province_city = Census.objects.values_list('province', 'city')
        result = Census.objects.values('city').annotate(
            city_count=Count('city')).order_by('city')
        all_count = Census.objects.all().count()
        hamkari_count = Census.objects.filter(
            hamakri=True, isavailable=True).count()

        print(province_city)
        print(result)
        print(all_count)
        print(hamkari_count)
        response = {
            # "province_city": province_city,
            "count_per_city": result,
            "all_count": all_count,
            "hamkari_avalaible_count": hamkari_count
        }
        return Response(CensusAggregateSerializer(response).data)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    # filter_backends = [
    #     SearchFilter,
    #     OrderingFilter,
    #     DjangoFilterBackend,
    # ]
    # filterset_fields = '__all__'
    # ordering_fields = '__all__'


#######################################
# Admin panel:
#######################################
# from product_app.models import *
# from order_service.settings import SERVICE_NAME


class AllAdminsPermission(BasePermission):  # ask to move?
    """
    check Role and Permission
    # TODO Needs Test
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        ext = ExtendedUser.objects.filter(user=request.user)
        if len(ext) == 0:
            return False
        elif ext[0].role in ['S', 'M', 'C']:
            return True
        else:
            return False


class CustomerPermission(BasePermission):  # ask
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        ext = ExtendedUser.objects.filter(user=request.user)
        if len(ext) == 0:
            return False
        elif ext[0].role in ['S', 'M', 'C']:
            return True
        else:
            return False


from auth_app.serializers import UserOnlySerializer


class ExtendedUserWithUserSerializer(serializers.ModelSerializer):
    user = UserOnlySerializer()
    city = CitySerializer()
    province = ProvinceSerializer()

    class Meta:
        model = ExtendedUser
        fields = '__all__'


# class AdminPromotersList(generics.ListAPIView):

#     permission_classes = [
#         IsAuthenticated,
#         AllAdminsPermission,
#     ]

#     queryset = ExtendedUser.objects.filter(role='P')

#     serializer_class = ExtendedUserWithUserSerializer

#     pagination_class = LimitOffsetPagination

#     def paginate_queryset(self, queryset):
#         if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
#             return None
#         return super().paginate_queryset(queryset)

#     filter_backends = [
#         SearchFilter,
#         OrderingFilter,
#         DjangoFilterBackend,
#     ]
#     filterset_fields = '__all__'
#     ordering_fields = '__all__'

class AdminPromotersList(BaseLimiter, generics.ListAPIView):
    permission_classes = [
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        project_id = self.request.query_params.get('p', None)
        role_assignments = RoleAssignment.objects.filter(
            role__title_abbreviation__in=['P', 'M', 'S', 'V', 'L', 'H', 'W', 'F', 'C', ], is_deleted=False)
        if project_id is not None:
            role_assignments = role_assignments.filter(project__id=project_id)
        users = role_assignments.values_list('user')
        return self.limit_queryset(ExtendedUser.objects.filter(user__in=users))

    serializer_class = ExtendedUserWithUserSerializer

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
    #     'user': ['in', 'exact',],
    #     'user__username': ['in', 'exact',],
    #     'role': ['in', 'exact',],
    #     'role__title_abbreviation':  ['in', 'exact',],
    #     'project': ['in', 'exact',],
    #     'is_deleted': ['in', 'exact',],
    # }
    ordering_fields = '__all__'


class AdminCreateVisitsSerializer(serializers.Serializer):
    buildings = serializers.ListField(
        child=serializers.IntegerField()
    )
    promoter = IntegerField()


# Deprecated!
class AdminCreateVisitsView(BaseLimiter, generics.GenericAPIView):
    serializer_class = AdminCreateVisitsSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
        AllAdminsPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(Visit.objects.none())

    def post(self, request, *args, **kwargs):
        building_ids = self.request.data['buildings']
        expert = User.objects.get(id=self.request.data['expert'])
        ext = ExtendedUser.objects.get(user=promoter, role='P')
        buildings = Building.objects.filter(id__in=building_ids, is_visiting=False)
        if buildings.count() != len(building_ids):
            raise BadRequest

        # created_visits = []
        for building in buildings:
            visit = Visit()
            visit.creator = self.request.user
            visit.status = '0'
            visit.expert = expert
            visit.building = building
            visit.is_deleted = False
            visit.checked_by = None
            visit.visit_turn = Visit.objects.filter(
                building=building, is_deleted=False).aggregate(Max('visit_turn')) + 1
            visit.save()
            # created_visits.append(visit)

        return Response({"detail": "ok"})


class AdminVisitSerializer(VisitSerializer):
    start_datetime = serializers.SerializerMethodField()

    def get_start_datetime(self, obj):
        enter_photos = Photo.objects.filter(visit=obj, type__name='StoreFront')
        if len(enter_photos) == 0:
            return None
        else:
            return enter_photos[0].datetime_created


class AdminVisitsListView(BaseLimiter, generics.ListAPIView, BaseView):
    serializer_class = VisitSerializer
    # project_path = 'building'
    project_path = 'type__project'

    def get_queryset(self):
        base_query = Visit.objects.filter(is_deleted=False)
        supervisor_id = self.request.query_params.get('supervisor', None)
        project_id = self.request.query_params.get('p', None)
        if supervisor_id is not None and supervisor_id != '' and project_id is not None:
            base_query = base_query.filter(promoter__in=Supervisor.objects.filter(supervisor__id=supervisor_id,
                                                                                  project__id=project_id).values_list(
                'promoter', flat=True))
        if supervisor_id is not None and supervisor_id != '':
            base_query = base_query.filter(
                promoter__in=Supervisor.objects.filter(supervisor__id=supervisor_id).values_list('promoter', flat=True))
        from visit.priority import annotate_visits
        # `ordering=-priority_value` lists the most sensitive work first for planning and assignment.
        return annotate_visits(self.limit_queryset(self.get_projectified_queryset(base_query)))

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = {
        'creator': ['exact'],
        'promoter': ['exact'],
        'building': ['exact'],
        'visit_turn': ['exact', 'gte', 'lte', ],
        'status': ['exact', 'gte', 'lte', ],
        'is_deleted': ['exact'],
        'is_active': ['exact'],
        'checked_by': ['exact'],
        'rejection_reason': ['exact'],
        'datetime_created': ['gte', 'lte', ],
        'datetime_last_change': ['gte', 'lte', ],
        'building__city': ['exact'],
        'building__city__province': ['exact'],
        'start_datetime': ['gte', 'lte', ],
        'due_date': ['exact', 'gte', 'lte', ],
        'visit_comment': ['isnull', ],
        'type__has_supervision': ['exact', ],
        'supervision_status': ['exact', 'in', 'gte', 'lte', ],
    }
    # filterset_fields = '__all__'
    ordering_fields = '__all__'


class AdminUpdateVisitView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):

    def get_queryset(self):
        return self.limit_queryset(Visit.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return VisitSerializer
        else:
            return VisitOnlySerializer

    permission_classes = [
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    lookup_field = 'id'

    def perform_destroy(self, instance):
        url = self.request.build_absolute_uri().split('?')[0]
        if url.split('/')[-1] == '':
            id = int(url.split('/')[-2])
        else:
            id = int(url.split('/')[-1])
        photos = Photo.objects.filter(visit__id=id)
        for photo in photos:
            photo.delete()
        return super().perform_destroy(instance)


class AdminUpdateVisitStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ['status', 'checked_by', 'rejection_reason', ]


class AdminUpdateVisitStatusView(BaseLimiter, generics.UpdateAPIView):
    serializer_class = AdminUpdateVisitStatusSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
        AllAdminsPermission,
    ]

    lookup_field = 'id'

    def get_queryset(self):
        return self.limit_queryset(AssetAccess(self.request, self).visits)

    def check_alarms(self, visit):
        from django.db.models import Q
        visit_answers = Answer.objects.filter(visit=visit)
        for obj in visit_answers:
            if obj.question.has_bool_expected_value:
                if not (obj.bool == obj.question.bool_unexpected_value):
                    obj.bool_is_expected = True
                    obj.save()
                    FoulAlarm.objects.filter(
                        building=obj.visit.building, question=obj.question).delete()
                else:
                    obj.bool_is_expected = False
                    obj.save()
                    query = Answer.objects.filter(
                        ~Q(bool_is_expected=None), question=obj.question, visit__building=obj.visit.building).order_by(
                        '-id')[0:3]
                    if len(query) < 3:
                        continue
                    flag = True
                    for q in query:
                        flag = flag and (q.bool_is_expected == False)
                    if flag:
                        FoulAlarm.objects.filter(
                            building=obj.visit.building, question=obj.question).delete()
                        alarm = FoulAlarm()
                        alarm.question = obj.question
                        alarm.building = obj.visit.building
                        alarm.is_deleted = False
                        alarm.save()
                        # alarm.answers.add(obj)
                        for q in query:
                            alarm.answers.add(q)

    def perform_update(self, serializer):
        if not AssetAccess(self.request, self).project_wide:
            raise exceptions.PermissionDenied('تأیید ویزیت نیازمند نقش مدیریتی پروژه است.')
        new_status = serializer.validated_data.get('status')
        if new_status is None:
            raise DRFValidationError({'status': 'وضعیت جدید لازم است.'})
        if new_status not in (Visit.APPROVED, Visit.REJECTED, Visit.RETRY):
            raise DRFValidationError({'status': 'بررسی فقط می‌تواند تأیید، رد یا بازگشت برای اصلاح باشد.'})
        if serializer.instance.status != Visit.COMPLETED:
            raise DRFValidationError({'status': 'فقط خدمت پایان‌یافته قابل بررسی نهایی است.'})
        if new_status in (Visit.REJECTED, Visit.RETRY) and not str(
                serializer.validated_data.get('rejection_reason') or '').strip():
            raise DRFValidationError({'rejection_reason': 'دلیل رد یا اصلاح لازم است.'})
        with transaction.atomic():
            if new_status == Visit.APPROVED:
                self.check_alarms(serializer.instance)
                Photo.objects.filter(visit=serializer.instance, type__is_for_supervision=False).update(
                    supervision_location_confirm='CONFIRMED', supervision_confirm='CONFIRMED')
                from visit.report_snapshot import capture_report_snapshot
                capture_report_snapshot(serializer.instance, self.request.user, source='legacy_approval')
            visit = serializer.save(checked_by=self.request.user)
            from notification.in_app import notify_visit_reviewed
            actor_id = self.request.user.id
            transaction.on_commit(lambda: notify_visit_reviewed(visit, actor_id))


class AdminAnswerSerializer(AnswerSerializer):
    multichoice = AnswerChoiceSerializer(many=True)


class AdminAnswerListView(BaseLimiter, generics.ListAPIView, BaseView):
    serializer_class = AdminAnswerSerializer
    project_path = 'visit__type__project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(Answer.objects.all()))

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [  # ask
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = {
        "id": ['in', 'exact', ],
        "visit": ['exact', ],
        "question": ['exact', ],
        "score": ['exact', ],
        "number": ['exact', ],
        "bool": ['exact', ],
        "description": ['exact', ],
        "price": ['exact', ],
        "multichoice": ['exact', ],
        "bool_is_expected": ['exact', ],
        "question__question_type__is_for_supervision": ['exact', ],
        "question__question_type__is_active": ['exact', ],
    }
    ordering_fields = [
        "id",
        "visit",
        "question",
        "score",
        "number",
        "bool",
        "description",
        "price",
        "multichoice",
        "bool_is_expected",
        "question__question_type__is_for_supervision",
        "question__question_type__is_active",
        "question__priority",
    ]


class AnswerOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'


class AdminAnswerEdistsView(BaseLimiter, generics.RetrieveUpdateAPIView):
    serializer_class = AnswerOnlySerializer

    def get_queryset(self):
        return self.limit_queryset(Answer.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AnswerSerializer
        else:
            return AnswerOnlySerializer

    permission_classes = [
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    lookup_field = 'id'

    def perform_update(self, serializer):
        url = self.request.build_absolute_uri().split('?')[0]
        if url.split('/')[-1] == '':
            id = int(url.split('/')[-2])
        else:
            id = int(url.split('/')[-1])
        if 'multichoice' in self.request.data.keys():
            answer_before = Answer.objects.get(id=id)
            choices_before = answer_before.multichoice.all()  # .clear()
            for c in choices_before:
                answer_before.multichoice.remove(c)
            for choice in self.request.data['multichoice']:
                answer_before.multichoice.add(
                    AnswerChoice.objects.get(id=choice))

        return super().perform_update(serializer)


class AdminPhotoListView(BaseLimiter, generics.ListAPIView, BaseView):
    serializer_class = PhotoSerializer
    project_path = 'type__project'

    def get_queryset(self):
        rows = Photo.objects.filter(
            is_deleted=False, type__project_id=F('visit__type__project_id'),
            visit__building__project_id=F('visit__type__project_id'),
        )
        return self.limit_queryset(self.get_projectified_queryset(rows))

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [  # ask
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = {
        'type': ['exact'],
        'type__name': ['in', 'exact', ],
        'type__report_category': ['exact'],
        'type__report_category__is_for_supervision': ['exact'],
        'type__is_for_supervision': ['exact'],
        'link': ['exact'],
        'visit': ['in', 'exact'],
        'visit__visit_turn': ['exact'],
        'visit__status': ['exact'],
        'visit__promoter': ['exact'],
        'visit__building__city': ['exact'],
        'visit__building__city__province': ['exact'],
        'visit': ['exact'],
        'longitude': ['exact'],
        'latitude': ['exact'],
        'datetime_created': ['gte', 'lte', 'exact'],
        'datetime_last_change': ['gte', 'lte', 'exact'],
        'is_deleted': ['exact'],
    }

    ordering_fields = '__all__'


class PhotoOnlySerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = '__all__'
        read_only_fields = ('id', 'creator', 'type', 'link', 'visit', 'longitude', 'latitude',
                            'datetime_created', 'datetime_last_change', 'is_deleted')

    def get_link(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.link, self.context.get('request'))

    def validate(self, attrs):
        allowed = {'is_checked', 'is_favourite', 'supervision_location_confirm',
                   'supervision_confirm', 'recognition_status'}
        unexpected = set(self.initial_data) - allowed
        if unexpected:
            raise serializers.ValidationError({field: 'این فیلد از این مسیر قابل ویرایش نیست.'
                                               for field in unexpected})
        return attrs


class AdminPhotoEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView, BaseView):
    project_path = 'type__project'
    serializer_class = PhotoOnlySerializer

    permission_classes = [
        AllAdminsPermission,
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        rows = Photo.objects.filter(
            is_deleted=False, type__project_id=F('visit__type__project_id'),
            visit__building__project_id=F('visit__type__project_id'),
        )
        return self.limit_queryset(self.get_projectified_queryset(rows))

    def perform_update(self, serializer):
        if not authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            raise exceptions.PermissionDenied('ویرایش عکس نیازمند نقش مدیریتی پروژه است.')
        serializer.save()

    def perform_destroy(self, instance):
        if not authorized_role_views(self.request, self).filter(role__asset_scope='project').exists():
            raise exceptions.PermissionDenied('حذف عکس نیازمند نقش مدیریتی پروژه است.')
        instance.delete()

    lookup_field = 'id'


class PhotoTypeListView(BaseLimiter, generics.ListAPIView, BaseView):
    serializer_class = PhotoTypeSerializer
    project_path = 'project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(PhotoType.objects.all()))

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = '__all__'
    ordering_fields = '__all__'


class CensusValuesSerializer(serializers.Serializer):
    cities = serializers.ListField(child=serializers.CharField(), min_length=0)
    store_situation = serializers.ListField(child=serializers.CharField(), min_length=0)
    start_date = serializers.ListField(child=serializers.CharField(), min_length=0)


class CensusValuesView(BaseLimiter, generics.GenericAPIView):
    serializer_class = CensusValuesSerializer

    def get_queryset(self):
        return self.limit_queryset(Census.objects.none())

    def get(self, request, *args, **kwargs):
        cities_q = Census.objects.values('city').distinct()
        cities = []
        for q in cities_q:
            cities.append(q['city'])
        store_situation_q = Census.objects.values('store_situation').distinct()
        store_situation = []
        for q in store_situation_q:
            store_situation.append(q['store_situation'])
        start_date_q = Census.objects.values('start_date').distinct()
        start_date = []
        for q in start_date_q:
            start_date.append(q['start_date'])
        response = {
            "cities": cities,
            "store_situation": store_situation,
            "start_date": start_date
        }
        return Response(CensusValuesSerializer(response).data)



#######################
# Test:
#######################


class Test(generics.GenericAPIView):
    queryset = Building.objects.none()

    def get(self, request, *args, **kwargs):
        from core.qr import QRCode
        import base64
        from io import BytesIO
        x = QRCode(
            logo_url="",
            code_data="https://www.mamad.com")
        y = x.generate_qr_code()
        buffered = BytesIO()
        print("inja", y)
        y.save(buffered, format='PNG')
        from django.http import HttpResponse
        response = HttpResponse(buffered.getvalue(), content_type='image/jpeg')
        response['Content-Disposition'] = 'attachment; filename="downded_image.png"'
        return response
        # return Response(base64.b64encode(buffered.getvalue()).decode('utf-8'), headers=headers)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    # def get(self, request, *args, **kwargs):
    #     with connection.cursor() as cursor:
    #         # raw_query = "select vv.id , vo.name as store_name, vo.address, vo.code , vv.status, aap.name as province, aac.name as city , au.first_name||' '||au.last_name as promoter_name , vq.text, va.bool as YesNo_answer, va.description, va.score from visit_answer va left join visit_visit vv on va.visit_id = vv.id left join visit_building vo on vv.building_id = vo.id left join auth_app_city aac on vo.city_id = aac.id left join auth_app_province aap on aac.province_id = aap.id left join auth_user au on vv.promoter_id = au.id left join visit_question vq on va.question_id = vq.id where vv.status = '2' order by va.visit_id, va.question_id ;"
    #         raw_query = "select * from visit_building;"
    #         cursor.execute(raw_query)
    #         data = cursor.fetchall()

    #     print(data)
    #     return Response(data)


####################################
# Photo Type Retrive:
####################################

class PhotoTypeRetrieveView(BaseLimiter, generics.RetrieveAPIView, BaseView):
    project_path = 'project'
    serializer_class = PhotoTypeSerializer

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(PhotoType.objects.all()))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    lookup_field = 'id'


####################################
# FO Answers List:
####################################

class FOAnswerList(BaseLimiter, generics.ListAPIView, BaseView):

    project_path = 'visit__type__project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(
            Answer.objects.filter(question__question_type__name="FO", visit__status="3", visit__is_deleted=False)))

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    serializer_class = AnswerSerializer
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = (
        "visit__creator",
        "visit__promoter",
        "visit__building__id",
        "visit__building__name",
        "visit__building__address",
        "visit__building__city",
        "visit__building__city__province",
        "visit__building__longitude",
        "visit__building__latitude",
        "visit__building__is_visiting",
        "visit__id",
        "visit__visit_turn",
        # "visit__status",
        # "visit__is_deleted",
        "visit__checked_by",
        "visit__rejection_reason",
        "visit__datetime_created",
        "visit__datetime_last_change",
        "visit__start_datetime",
        "question",
        "score",
        "number",
        "bool",
        "description",
        "price",
    )
    # ordering_fields = '__all__'
    ordering_fields = (
        "visit__start_datetime",
    )


class PlaceVisitCommentEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ['visit_comment', 'comment_publisher']


class PlaceVisitCommentSerializer(serializers.ModelSerializer):
    comment_publisher = UserSerializer()

    class Meta:
        model = Visit
        fields = ['visit_comment', 'comment_publisher']


class PlaceVisitCommentView(BaseLimiter, generics.RetrieveUpdateAPIView):
    # serializer_class = PlaceVisitCommentSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PlaceVisitCommentSerializer
        else:
            return PlaceVisitCommentEditSerializer

    def get_queryset(self):
        return self.limit_queryset(Visit.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'

    def perform_update(self, serializer):
        return serializer.save(comment_publisher=self.request.user, visit_comment=self.request.data['visit_comment'])
        # return super().perform_update(serializer)


#####################################
# Foul Alarm:
#####################################


class FoulAlarmSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()
    answers = AnswerSerializer(many=True)

    class Meta:
        model = FoulAlarm
        fields = '__all__'


class FoulAlarmListView(generics.ListAPIView, BaseView):
    serializer_class = FoulAlarmSerializer
    project_path = 'project'

    def get_queryset(self):
        return self.get_projectified_queryset(FoulAlarm.objects.filter(is_deleted=False))

    # def get_queryset(self):
    #     queryset = FoulAlarm.objects.filter(is_deleted=False)
    #     result = []
    #     for q in queryset:
    #         flag = True
    #         answers = q.answers.all()
    #         if len(answers) < 3:
    #             break
    #         for a in answers:
    #               if a.visit.status not in ['3',]:
    #                   flag = False
    #                   break
    #         if flag:
    #             result.append(q)
    #     return queryset

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    pagination_class = LimitOffsetPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = (
    #     "id",
    #     # "building",
    #     # "question",
    #     # "is_deleted",
    #     "building__name",
    #     # "building__category__id",
    #     # "building__category__name",
    #     # "building__category__icon",
    #     "building__address",
    #     "building__city",
    #     "building__city__province",
    #     "building__longitude",
    #     "building__latitude",
    #     # "building__is_active",
    #     # "building__postal_code",
    #     # "building__phone",
    #     # "building__mobile_phone",
    #     # "building__owner_national_code",
    #     # "building__owner_name",
    #     # "building__period",
    #     # "building__visit_count",
    #     "building__code",
    #     "building__is_visiting",
    #     # "question",
    # )
    ordering_fields = '__all__'
    # ordering_fields = (
    #     "datetime_created",
    # )


class FoulAlarmRetriveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FoulAlarmSerializer

    def get_queryset(self):
        return self.limit_queryset(FoulAlarm.objects.filter(is_deleted=False))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'


class FixAlarms(generics.GenericAPIView):
    serializer_class = FoulAlarmSerializer

    def get_queryset(self):
        return FoulAlarm.objects.filter(is_deleted=False)

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):
        self.fix_alarms()
        return Response({})

    def fix_alarms(self):
        from django.db.models import Q
        FoulAlarm.objects.all().delete()
        buildings = Building.objects.all()
        questions = Question.objects.filter(~Q(has_bool_expected_value=False))
        for building in buildings:
            for question in questions:
                answers = Answer.objects.filter(
                    ~Q(bool_is_expected=None), visit__building=building, question=question).order_by('-id')[0:3]
                flag = False
                ff = False
                if len(answers) < 3:
                    continue
                for q in answers:
                    ff = True
                    flag = flag or (q.bool_is_expected == True)
                if not flag and ff:
                    FoulAlarm.objects.filter(
                        building=building, question=question).delete()
                    alarm = FoulAlarm()
                    alarm.question = question
                    alarm.building = building
                    alarm.is_deleted = False
                    alarm.save()
                    for q in answers:
                        alarm.answers.add(q)


###############################
# Ticketing:
###############################

class TicketSerializer(serializers.ModelSerializer):
    visit = VisitSerializer()
    creator = UserSerializer()
    role_assignee = RoleSerializer()

    class Meta:
        model = Ticket
        fields = '__all__'


class TicketOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('id', 'project', 'visit', 'building', 'role_assignee', 'title', 'subject')
        read_only_fields = ('id',)
        extra_kwargs = {'project': {'required': False}}


class TicketStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ('status',)


class TicketMessageSerializer(serializers.ModelSerializer):
    ticket = TicketSerializer()
    created_by = UserSerializer()

    class Meta:
        model = TicketMessage
        fields = '__all__'


class TicketMessageOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ('ticket', 'parent', 'body')


class TicketMessageBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessage
        fields = ('body',)


class TicketMessageAttachmentSerializer(serializers.ModelSerializer):
    ticket_message = TicketMessageSerializer()
    link = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessageAttachment
        fields = '__all__'

    def get_link(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.link, self.context.get('request'))


class TicketMessageAttachmentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessageAttachment
        fields = ('ticket_message', 'link')


class TicketMessageAttachmentEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketMessageAttachment
        fields = ('link',)


class TicketListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TicketSerializer
        else:
            return TicketOnlySerializer

    project_path = 'project'

    def get_queryset(self):
        return self.limit_queryset(TicketAccess(self.request, self).tickets)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    pagination_class = LimitOffsetPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        "id": ['exact'],
        "visit": ['exact'],
        'visit__visit_turn': ['exact'],
        'visit__status': ['exact'],
        'visit__promoter': ['exact'],
        'building__city': ['exact'],
        'building__city__province': ['exact'],
        "building": ['exact'],
        "creator": ['exact'],
        "title": ['exact'],
        "subject": ['exact'],
        "status": ['exact', 'in'],
        "is_deleted": ['exact'],
        "role_assignee": ['exact'],
        "datetime_created": ['exact'],
        "datetime_last_change": ['exact'],
    }
    ordering_fields = '__all__'

    def perform_create(self, serializer):
        access = TicketAccess(self.request, self)
        access.validate_ticket(serializer.validated_data)
        serializer.save(creator=self.request.user, project_id=access.assets.project_id,
                        status=Ticket.WAITING)


class TicketMessageListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TicketMessageSerializer
        else:
            return TicketMessageOnlySerializer

    project_path = 'ticket__project'

    def get_queryset(self):
        return self.limit_queryset(TicketAccess(self.request, self).messages)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    pagination_class = LimitOffsetPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        "id": ['exact'],
        "ticket": ['exact'],
        "created_by": ['exact'],
        "body": ['exact'],
        "is_deleted": ['exact'],
        "parent": ['exact'],
        "datetime_created": ['exact'],
        "datetime_last_change": ['exact'],
    }
    ordering_fields = '__all__'

    def perform_create(self, serializer):
        TicketAccess(self.request, self).validate_message(serializer.validated_data)
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().get(pk=serializer.validated_data['ticket'].pk)
            if ticket.is_deleted or ticket.status == Ticket.CLOSED:
                raise DRFValidationError({'ticket': 'گفتگو بسته شده است.'})
            message = serializer.save(created_by=self.request.user)
            ticket.status = Ticket.WAITING if ticket.creator_id == self.request.user.pk else Ticket.ANSWERED
            ticket.save(update_fields=['status', 'datetime_last_change'])
            from notification.in_app import notify_support_reply, notify_support_staff
            if ticket.creator_id == self.request.user.pk:
                notify_support_staff(ticket, message)
            else:
                notify_support_reply(ticket, message)


class TicketMessageAttachmentListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    def get_serializer_class(self):
        return TicketMessageAttachmentSerializer if self.request.method == 'GET' else TicketMessageAttachmentLinkSerializer
    project_path = 'ticket_message__ticket__project'

    def get_queryset(self):
        return self.limit_queryset(TicketAccess(self.request, self).attachments)

    def perform_create(self, serializer):
        raise DRFValidationError({'link': 'پیوست فقط از مسیر بارگذاری معتبر ثبت می‌شود.'})

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    pagination_class = LimitOffsetPagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = {
        "id": ['exact'],
        "ticket_message": ['exact'],
        "link": ['exact'],
        "is_deleted": ['exact'],
    }
    ordering_fields = '__all__'


class TicketRetriveUpdateDestroyView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        return TicketSerializer if self.request.method == 'GET' else TicketStatusSerializer
    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        access = TicketAccess(self.request, self)
        rows = access.tickets if self.request.method == 'GET' else access.writable_tickets
        return self.limit_queryset(rows)


class TicketMessageRetriveUpdateDestroyView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        return TicketMessageSerializer if self.request.method == 'GET' else TicketMessageBodySerializer
    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        access = TicketAccess(self.request, self)
        rows = access.messages if self.request.method == 'GET' else access.writable_messages
        return self.limit_queryset(rows)


class TicketMessageAttachmentRetriveUpdateDestroyView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_serializer_class(self):
        return TicketMessageAttachmentSerializer if self.request.method == 'GET' else TicketMessageAttachmentEditSerializer
    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        access = TicketAccess(self.request, self)
        rows = access.attachments if self.request.method == 'GET' else access.writable_attachments
        return self.limit_queryset(rows)

    def perform_update(self, serializer):
        raise DRFValidationError({'link': 'نشانی فایل ثبت‌شده قابل تغییر نیست.'})


class TicketMessageAttachmentUploadSerializer(serializers.ModelSerializer):
    link = serializers.FileField()

    class Meta:
        model = TicketMessageAttachment
        fields = ('ticket_message', 'link',)


class TicketUploadAttachmentAPIView(BaseLimiter, generics.GenericAPIView):
    serializer_class = TicketMessageAttachmentUploadSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(TicketAccess(self.request, self).attachments)

    def post(self, request, *args, **kwargs):
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        message = payload.validated_data['ticket_message']
        if not TicketAccess(request, self).writable_messages.filter(pk=message.pk).exists():
            raise exceptions.PermissionDenied('این گفتگو در دسترس نیست.')
        if message.ticket.status == Ticket.CLOSED:
            raise DRFValidationError({'ticket_message': 'گفتگو بسته شده است.'})
        file = payload.validated_data['link']
        if file.size > 10 * 1024 * 1024:
            raise DRFValidationError({'link': 'حجم فایل باید حداکثر ۱۰ مگابایت باشد.'})
        header = file.read(16)
        file.seek(0)
        valid = (header.startswith(b'%PDF-') or header.startswith(b'\xff\xd8\xff')
                 or header.startswith(b'\x89PNG\r\n\x1a\n')
                 or (header.startswith(b'RIFF') and header[8:12] == b'WEBP'))
        if not valid:
            raise DRFValidationError({'link': 'فقط PDF، JPEG، PNG یا WebP معتبر پذیرفته می‌شود.'})
        url = ArvanStorage().put_file(file)
        if not url:
            raise DRFValidationError({'link': 'ذخیره فایل ناموفق بود؛ دوباره تلاش کنید.'})
        obj = TicketMessageAttachment.objects.create(ticket_message=message, link=url)
        return Response(TicketMessageAttachmentSerializer(obj, context={'request': request}).data, status=status.HTTP_201_CREATED)


class VisitForActionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        exclude = ('completion_code', 'completion_code_failures', 'completion_code_locked_until')  # only the client app shows the code


class IncomingSingleActionPlanSerializer(serializers.Serializer):
    building_code = serializers.CharField()
    expert_phone_number = serializers.CharField(required=False, allow_blank=True)
    elevator_ids = serializers.ListField(child=serializers.IntegerField(min_value=1),
                                         required=False, allow_empty=True)
    visit_turn = serializers.IntegerField(required=False)
    is_last_day = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False, default=False)


class IncommingWrappedActionPlanSerializer(serializers.Serializer):
    actions = IncomingSingleActionPlanSerializer(many=True, allow_empty=False)
    project = serializers.IntegerField(min_value=1)
    visit_type = serializers.IntegerField(min_value=1)
    has_due_date = serializers.BooleanField()
    due_date = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs['has_due_date'] and not attrs.get('due_date'):
            raise serializers.ValidationError({'due_date': 'برای برنامه زمان‌دار، تاریخ اجرا لازم است.'})
        return attrs


class OutgoingWrappedActionPlanSerializer(serializers.Serializer):
    errors = serializers.ListField()
    successfuls = VisitSerializer(many=True)


class AdminActionPlanCreate(BaseLimiter, generics.GenericAPIView):
    serializer_class = IncommingWrappedActionPlanSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.limit_queryset(Visit.objects.filter(is_deleted=False, creator=self.request.user))

    def post(self, request, *args, **kwargs):
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        project_id = values['project']
        if str(project_id) != request.query_params.get('p'):
            raise serializers.ValidationError({'project': 'پروژه برنامه باید با پروژه انتخاب‌شده یکسان باشد.'})
        access = AssetAccess(request, self)
        if not access.project_wide and 'supervised' not in access.scopes:
            raise exceptions.PermissionDenied('ثبت برنامه به دسترسی مدیریتی یا سرپرستی نیاز دارد.')
        visit_type = VisitType.objects.filter(pk=values['visit_type'], project_id=project_id,
                                              is_active=True).first()
        if visit_type is None:
            raise serializers.ValidationError({'visit_type': 'نوع خدمت فعال در این پروژه پیدا نشد.'})

        valid = []
        errors = []
        for index, row in enumerate(values['actions']):
            building = Building.objects.filter(code=row['building_code'], project_id=project_id).first()
            if building is None:
                errors.append({'index': index, 'building_code': row['building_code'],
                               'message': 'ساختمان در پروژه انتخاب‌شده پیدا نشد.'})
                continue
            expert = None
            if row.get('expert_phone_number'):
                assignment = RoleAssignment.objects.filter(
                    user__username=row['expert_phone_number'], user__is_active=True,
                    project_id=project_id, is_deleted=False, role__is_active=True,
                    role__asset_scope='assigned',
                ).select_related('user').first()
                if assignment is None:
                    errors.append({'index': index, 'building_code': row['building_code'],
                                   'message': 'کارشناس فعال در این پروژه پیدا نشد.'})
                    continue
                expert = assignment.user
            if not access.project_wide and (expert is None or not Supervisor.objects.filter(
                    supervisor=request.user, promoter=expert, project_id=project_id,
                    is_active=True).exists()):
                errors.append({'index': index, 'building_code': row['building_code'],
                               'message': 'کارشناس انتخاب‌شده زیرمجموعه این سرپرست نیست.'})
                continue
            elevator_ids = row.get('elevator_ids', [])
            if len(elevator_ids) != len(set(elevator_ids)) or (elevator_ids and
                    BuildingElevator.objects.filter(
                        building=building, elevator_id__in=elevator_ids,
                        elevator__project_id=project_id,
                    ).values('elevator_id').distinct().count() != len(elevator_ids)):
                errors.append({'index': index, 'building_code': row['building_code'],
                               'message': 'آسانسور انتخابی به این ساختمان و پروژه تعلق ندارد.'})
                continue
            valid.append((building, expert, row))

        created = []
        if valid:
            from django.db import transaction
            with transaction.atomic():
                for building, expert, row in valid:
                    visit = Visit.objects.create(
                        type=visit_type, creator=request.user, building=building,
                        expert=expert, promoter=expert, visit_turn=row.get('visit_turn'),
                        is_last_day=row.get('is_last_day', False), is_active=row.get('is_active', False),
                        has_due_date=values['has_due_date'],
                        due_date=values['due_date'].date() if values['has_due_date'] else None,
                        start_datetime=values['due_date'] if values['has_due_date'] else None,
                    )
                    if row.get('elevator_ids'):
                        visit.elevator.set(row['elevator_ids'])
                    if visit.is_active:
                        from notification.in_app import notify_visit_assignment
                        notify_visit_assignment(visit, f'visit-created:{visit.pk}')
                    created.append(visit)
        return Response({'errors': errors, 'successfuls': VisitSerializer(created, many=True).data})


class DepthIncommingWrappedServiceRequestSerializer(serializers.Serializer):
    building = serializers.IntegerField()
    elevators = serializers.ListField(child=(serializers.IntegerField())) 
class IncommingWrappedServiceRequestSerializer(serializers.Serializer):
    buildings = serializers.ListField(child=serializers.ListField(child=DepthIncommingWrappedServiceRequestSerializer()))
    type = serializers.IntegerField()

class ServiceRequestCreate(generics.GenericAPIView):
    serializer_class = ServiceRequestInputSerializer

    def get_queryset(self):
        return Visit.objects.filter(is_deleted=False, creator=self.request.user)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission, replayed = submit_service_request(request, self, serializer.validated_data)
        return Response({
            'request_key': str(submission.request_key), 'replayed': replayed, 'errors': [],
            'successfuls': VisitSerializer(submission.visits.order_by('pk'), many=True,
                                          context=self.get_serializer_context()).data,
        }, status=status.HTTP_200_OK if replayed else status.HTTP_201_CREATED)




class AdminActionPlanList(BaseLimiter, generics.ListAPIView, BaseView):
    serializer_class = VisitSerializer
    project_path = 'type__project'

    def get_queryset(self):
        me = self.request.query_params.get('me', False)
        project_id = self.request.query_params.get('p', None)
        is_my_promoters = self.request.query_params.get('my_promoters', False)  # ask
        is_today = self.request.query_params.get('today', False)

        visits_list = Visit.objects.filter(is_deleted=False)

        from django.db.models import Q
        if me:
            visits_list = visits_list.filter(creator=self.request.user)
        if is_today:
            visits_list = visits_list.filter(Q(has_due_date=False) | Q(due_date=timezone.now().date()))
        if is_my_promoters:
            my_promoters = Supervisor.objects.filter(supervisor=self.request.user, project__id=project_id,
                                                     is_active=True).values_list('promoter', flat=True)
            visits_list = visits_list.filter(promoter__id__in=my_promoters)
        return self.limit_queryset(self.get_projectified_queryset(visits_list))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    # def perform_create(self, serializer):
    #     return serializer.save(creator=self.request.user, is_active=False)

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


class AdminActionPlanEdits(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VisitForActionPlanSerializer
    http_method_names = ['get', 'delete', 'head', 'options']

    def get_queryset(self):
        return self.limit_queryset(Visit.objects.filter(is_deleted=False, creator=self.request.user))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    lookup_field = 'id'

    def perform_destroy(self, instance):
        if (instance.status != Visit.NOTVISITED or instance.is_active or
                instance.report_snapshots.exists()):
            raise DRFValidationError({'detail': 'برنامه شروع‌شده یا دارای گزارش قابل حذف نیست.'})
        instance.delete()


#################################
# Visit Type :
#################################
# class VisitTypeOnlySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VisitType
#         fields = '__all__'


class VisitTypeNestedSerializer(serializers.ModelSerializer):
    surveys = SurveySerializer(many=True)

    class Meta:
        model = VisitType
        fields = '__all__'


class VisitTypeListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    project_path = 'project'

    def get_queryset(self):
        rows = VisitType.objects.all()
        # The service-type settings page also lists retired types so they can be reactivated.
        if not (self.request.query_params.get('include_inactive') == '1' and AssetAccess(self.request, self).project_wide):
            rows = rows.filter(is_active=True)
        return self.limit_queryset(self.get_projectified_queryset(rows))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return VisitTypeNestedSerializer
        else:
            return VisitTypeOnlySerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = '__all__'
    ordering_fields = '__all__'


class VisitTypeSettingsSerializer(serializers.ModelSerializer):
    """Service-type settings an admin may change; project and questionnaire links stay fixed."""
    class Meta:
        model = VisitType
        fields = ('id', 'title', 'verbose_name', 'description', 'default_wage', 'requires_client_code',
                  'show_wage_in_report', 'is_active')
        read_only_fields = ('id', 'title')


class VisitTypeEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):

    def get_queryset(self):
        # Scoped to the selected project; writes need a project-wide role.
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return VisitType.objects.none()
        if self.request.method != 'GET' and not AssetAccess(self.request, self).project_wide:
            return VisitType.objects.none()
        return self.limit_queryset(VisitType.objects.filter(project_id=project_id))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return VisitTypeNestedSerializer
        else:
            return VisitTypeSettingsSerializer

    def perform_destroy(self, instance):
        # Visits cascade from their type, so a type is only ever deactivated.
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]


##################################
# SupervisionVisitsListView
##################################


class SupervisionVisitsListView(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'type__project'

    def get_queryset(self):
        promoter_id = self.request.query_params.get('promoter', None)
        is_today = self.request.query_params.get('today', False)
        if promoter_id == '':
            promoter_id = None
        project_id = self.request.query_params.get('p', None)
        # if not Supervisor.objects.filter(promoter__id=promoter_id, supervisor=self.request.user, project__id=project_id).exists():
        #     return Visit.objects.none()
        from django.db.models import Q
        visits_list = Visit.objects.filter(supervision_status__in=['0', '1'], is_active=True,
                                           type__has_supervision=True, status__in=['0', '1', '2', '3'])
        if promoter_id is not None:
            visits_list = visits_list.filter(promoter__id=promoter_id)
        else:
            my_promoters = Supervisor.objects.filter(supervisor=self.request.user, project__id=project_id,
                                                     is_active=True).values_list('promoter', flat=True)
            visits_list = visits_list.filter(promoter__id__in=my_promoters)
        if is_today:
            visits_list = visits_list.filter(Q(has_due_date=False) | Q(due_date=timezone.now().date()))
        return self.limit_queryset(self.get_projectified_queryset(visits_list))

    serializer_class = VisitSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = {
        "creator": ['exact', ],
        "promoter": ['exact', ],
        "building": ['exact', ],
        "building__city": ['exact', ],
        "building__city__province": ['exact', ],
        "visit_turn": ['exact', ],
        "status": ['exact', 'in'],
        "is_deleted": ['exact', ],
        "checked_by": ['exact', ],
        "rejection_reason": ['exact', ],
        "datetime_created": ['exact', ],
        "datetime_last_change": ['exact', ],
        "start_datetime": ['exact', ],
        "has_due_date": ['exact', ],
        "supervision_status": ['exact', 'in', 'gte', 'lte', ],
        "due_date": ['exact', 'gte', 'lte', ],
    }
    ordering_fields = '__all__'
    # search_fields = ['^building__code']
    search_fields = ['building__code', 'building__address', 'building__name', ]

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class AdminUpdateSupervisionVisitStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ('supervision_status',)


class AdminUpdateSupervisionVisitStatusView(BaseLimiter, generics.UpdateAPIView):
    def get_queryset(self):
        return self.limit_queryset(Visit.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    serializer_class = AdminUpdateSupervisionVisitStatusSerializer

    lookup_field = 'id'


###############################
# AdminActionPlanBulkEdits
###############################

class AdminActionPlanBulkEditsSerializer(serializers.Serializer):
    id = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    is_active = serializers.BooleanField()
    is_deleted = serializers.BooleanField(required=False, default=False)
    # class Meta:
    #     model = Visit
    #     fields = '__all__'


class AdminActionPlanBulkEdits(BaseLimiter, generics.GenericAPIView):
    serializer_class = AdminActionPlanBulkEditsSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.limit_queryset(Visit.objects.none())

    def post(self, request, *args, **kwargs):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if values['is_active'] and values['is_deleted']:
            raise DRFValidationError({'is_deleted': 'رکورد حذف‌شده نمی‌تواند فعال باشد.'})
        with transaction.atomic():
            query = locked_project_batch(request, self, Visit, values['id'],
                                         allow_supervised_creator=True)
            update_visit_activation(query, is_active=values['is_active'], is_deleted=values['is_deleted'])
        return Response({"detail": "ok"})


####################################
# change photo location:
####################################

class VisitChangePhotoLocationsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    longitude = serializers.DecimalField(max_digits=22, decimal_places=16)
    latitude = serializers.DecimalField(max_digits=22, decimal_places=16)


class VisitChangePhotoLocations(BaseLimiter, generics.GenericAPIView):
    serializer_class = VisitChangePhotoLocationsSerializer

    def get_queryset(self):
        return self.limit_queryset(Photo.objects.none())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def post(self, request):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        with transaction.atomic():
            photos = locked_project_batch(request, self, Photo, values['ids'])
            photos.update(longitude=values['longitude'], latitude=values['latitude'],
                          datetime_last_change=timezone.now())
        return Response({"detail": "ok"})


#######################################
# Create Visit Answer:
#######################################

class RawAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'


class AdminAnswerCreateAPIView(BaseLimiter, generics.CreateAPIView):
    serializer_class = RawAnswerSerializer
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(Answer.objects.all())

    # def post(self, request):
    #     data = self.request.data
    #     visit = Visit.objects.get(id=data['visit'])
    #     question = Question.objects.get(id=data['question'])
    #     query = Answer.objects.filter(visit=visit, question=question)
    #     if len(query) == 0:
    #         obj = Answer()
    #         obj.question = question
    #         obj.visit = visit
    #     else:
    #         obj = query[0]
    #     for key in data.keys():
    #         if key in ['question', 'visit', 'multichoice', 'dropdown', 'radio']:
    #             continue
    #         setattr(obj, key, data[key])
    #     obj.save()
    #     if 'multichoice' in data.keys():
    #         for choice in data['multichoice']:
    #             obj.multichoice.add(AnswerChoice.objects.get(id=int(choice)))
    #     if 'dropdown' in data.keys():
    #         obj.dropdown = AnswerChoice.objects.get(id=data['dropdown'])
    #     if 'radio' in data.keys():
    #         obj.radio = AnswerChoice.objects.get(id=data['radio'])
    #     # self.check_alarms(obj)
    #     obj.save()
    #     return Response(AnswerSerializer(obj, many=False).data)


################################
# VisitRate
################################

class QuestionTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionType
        fields = '__all__'


class VisitRateSerializer(serializers.ModelSerializer):
    created_by = UserSerializer()
    visit = VisitSerializer()
    question_type = QuestionTypeOnlySerializer()
    photo_type = PhotoTypeSerializer()

    class Meta:
        model = VisitRate
        fields = '__all__'


class VisitRateOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitRate
        fields = '__all__'
        read_only_fields = ('id', 'created_by', 'datetime_created', 'datetime_last_change')

    def validate(self, attrs):
        visit = attrs.get('visit', getattr(self.instance, 'visit', None))
        question_type = attrs.get('question_type', getattr(self.instance, 'question_type', None))
        photo_type = attrs.get('photo_type', getattr(self.instance, 'photo_type', None))
        if visit is None or visit.type_id is None:
            raise DRFValidationError({'visit': 'ویزیت معتبر لازم است.'})
        if question_type and (question_type.visit_type_id != visit.type_id or
                              question_type.project_id != visit.type.project_id):
            raise DRFValidationError({'question_type': 'نوع سؤال به این ویزیت تعلق ندارد.'})
        if photo_type and (photo_type.visit_type_id != visit.type_id or
                           photo_type.project_id != visit.type.project_id):
            raise DRFValidationError({'photo_type': 'نوع عکس به این ویزیت تعلق ندارد.'})
        return attrs


class VisitRateListCreateView(BaseLimiter, generics.ListCreateAPIView):
    def get_queryset(self):
        return self.limit_queryset(VisitRate.objects.filter(
            visit__in=AssetAccess(self.request, self).visits))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return VisitRateSerializer
        return VisitRateOnlySerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def perform_create(self, serializer):
        access = AssetAccess(self.request, self)
        visit = serializer.validated_data['visit']
        if not access.visits.filter(pk=visit.pk).exists():
            raise exceptions.PermissionDenied('ویزیت در دامنه شما نیست.')
        if not access.project_wide and visit.status not in (Visit.COMPLETED, Visit.APPROVED):
            raise DRFValidationError({'visit': 'ثبت امتیاز پس از پایان خدمت ممکن است.'})
        serializer.save(created_by=self.request.user)


class VisitRateEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'id'

    def get_queryset(self):
        rows = VisitRate.objects.filter(visit__in=AssetAccess(self.request, self).visits)
        if self.request.method != 'GET':
            rows = rows.filter(created_by=self.request.user)
        return self.limit_queryset(rows)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return VisitRateSerializer
        return VisitRateOnlySerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def perform_update(self, serializer):
        if set(self.request.data) & {'visit', 'question_type', 'photo_type', 'created_by',
                                     'datetime_created', 'datetime_last_change'}:
            raise DRFValidationError('هویت ویزیت یا نوع امتیاز قابل جابه‌جایی نیست.')
        serializer.save(created_by=self.request.user)


class VisitActivationEditsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    is_active = serializers.BooleanField()
    is_deleted = serializers.BooleanField()


def update_visit_activation(query, *, is_active, is_deleted):
    now = timezone.now()
    newly_active = list(query.filter(is_active=False)) if is_active and not is_deleted else []
    query.update(is_active=is_active, is_deleted=is_deleted, datetime_last_change=now)
    if newly_active:
        from notification.in_app import notify_visit_assignment
        for visit in newly_active:
            notify_visit_assignment(visit, f'visit-activated:{visit.pk}:{now.isoformat()}')


class VisitBulkEditsView(generics.GenericAPIView):

    serializer_class = VisitActivationEditsSerializer
    queryset = Visit.objects.none()
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, *args, **kwargs):
        data = self.get_serializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if values['is_active'] and values['is_deleted']:
            raise DRFValidationError({'is_deleted': 'رکورد حذف‌شده نمی‌تواند فعال باشد.'})
        with transaction.atomic():
            query = locked_project_batch(request, self, Visit, values['ids'])
            update_visit_activation(query, is_active=values['is_active'], is_deleted=values['is_deleted'])
        return Response({"detail": "ok"})


class VisitDetailRetriveAPIView(BaseLimiter, generics.RetrieveAPIView):
    serializer_class = VisitSerializer
    lookup_field = 'id'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(AssetAccess(self.request, self).visits)

class ClientVisitsAPIView(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'type__project'

    def get_queryset(self):
        from django.db.models import Q

        access = AssetAccess(self.request, self)
        rows = Visit.objects.filter(type__project_id=access.project_id,
                                   building__project_id=access.project_id, is_deleted=False)
        rows = client_visible_visits(rows, access.own_clients).prefetch_related('service_submissions')
        # Pending requests and future/overdue visits stay visible to their client.
        return self.limit_queryset(rows)


    serializer_class = VisitSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # filterset_fields = '__all__'
    filterset_fields = (
        "creator",
        "promoter",
        "building",
        "building__city",
        "building__city__province",
        "status",
        "is_deleted",
        "checked_by",
        "rejection_reason",
        "datetime_created",
        "datetime_last_change",
        "start_datetime",
    )
    ordering_fields = '__all__'
    search_fields = ['building__verbose_name', 'building__address', 'building__name', 'building__parent__name',]

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)
