from django.shortcuts import render

# Create your views here.
from warehouse.serializers import (UnitSerializer, WareVisitTypeOnlySerializer, WareVisitTypeOnlyListSerializer,
                                   WareTypeSerializer, WareVisitTypeSerializer, WareSerializer,
                                   WarehouseLocationSerializer, WarehouseTransactionSerializer,
                                   TransactionLineTypeSerializer, WarehouseTransactionLineSerializer,
                                   WareOnlySerializer, WarehouseLocationOnlySerializer,
                                   WarehouseTransactionOnlySerializer, TransactionLineTypeOnlySerializer,
                                   WarehouseTransactionLineOnlySerializer, WareAggregatedListSerializer,
                                   WarehouseAggregatedLocationSerializer, StockUserSerializer,
                                   WareDistributionByUserSerializer, WareDistributionByLocationSerializer,
                                   WareTransactionEzCreateSerializer, WareVisitSettingsSerializer, WarehouseLocationPersonnelSerializer, WarehouseLocationPersonnelNestedSerializer)
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from django.utils.translation import gettext_lazy as _
from core.generics import BaseView, BaseLimiter
from core.exceptions import *
from django.db.models import F, Max
from django.db.models import Count
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import exceptions, generics, serializers, status
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from warehouse.models import (Unit, WareType, Ware, WarehouseLocation, WarehouseTransaction,
                              TransactionLineType, WarehouseTransactionLine, WareVisitType, WarehouseLocationPersonnel,)
from auth_app.permissions import *
from warehouse.stock import StockTransferInput, create_stock_transfer
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from auth_app.models import Project


def warehouse_project_id(request):
    try:
        project_id = int(request.query_params.get('p'))
    except (TypeError, ValueError):
        raise ValidationError({'p': 'پروژه معتبر لازم است.'})
    if project_id <= 0:
        raise ValidationError({'p': 'پروژه معتبر لازم است.'})
    return project_id


def require_warehouse_manager(request, view):
    if 'project' not in set(authorized_role_views(request, view).values_list('role__asset_scope', flat=True)):
        raise PermissionDenied('مدیریت انبار به نقش مدیریتی پروژه نیاز دارد.')


class WareTypeListCreateView(BaseLimiter, generics.ListCreateAPIView):
    # project_path = ''
    def get_queryset(self):
        return self.limit_queryset(WareType.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareTypeSerializer
        else:
            return WareTypeSerializer

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


class WareVisitTypeListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    project_path = 'ware__project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(WareVisitType.objects.all()))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareVisitTypeSerializer
        else:
            return WareVisitTypeOnlySerializer

            # if type(self.request.data) == list:
            #     return WareVisitTypeOnlySerializer
            # else:
            #     return WareVisitTypeOnlySerializer

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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        require_warehouse_manager(request, self)
        project_id = warehouse_project_id(request)
        items = request.data if isinstance(request.data, list) else [request.data]
        for item in items:
            if not Ware.objects.filter(pk=item.get('ware'), project_id=project_id).exists():
                raise ValidationError({'ware': 'کالا در پروژه انتخاب‌شده نیست.'})
            visit_type = item.get('visit_type')
            if visit_type is not None:
                from visit.models import VisitType
                if not VisitType.objects.filter(pk=visit_type, project_id=project_id).exists():
                    raise ValidationError({'visit_type': 'نوع بازدید در پروژه انتخاب‌شده نیست.'})
            visit = item.get('visit')
            if visit is not None:
                from visit.models import Visit
                if not Visit.objects.filter(pk=visit, type__project_id=project_id).exists():
                    raise ValidationError({'visit': 'بازدید در پروژه انتخاب‌شده نیست.'})
        if type(self.request.data) == list:
            response = []
            for obj in self.request.data:
                serializer = self.get_serializer(data=obj)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                response.append(serializer.data)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            response = serializer.data
        headers = self.get_success_headers(serializer.data)
        return Response(response, status=status.HTTP_201_CREATED, headers=headers)


class WareListCreateView(generics.ListCreateAPIView, BaseView, BaseLimiter):  # ask
    project_path = 'project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(Ware.objects.all()))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareSerializer
        else:
            return WareOnlySerializer

    def perform_create(self, serializer):
        require_warehouse_manager(self.request, self)
        project_id = warehouse_project_id(self.request)
        project = serializer.validated_data.get('project')
        if project is not None and project.pk != project_id:
            raise ValidationError({'project': 'پروژه کالا باید با پروژه انتخاب‌شده یکسان باشد.'})
        serializer.save(project_id=project_id)

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


class WarehouseLocationListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    project_path = 'projects'  # ask

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(WarehouseLocation.objects.all()))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseLocationSerializer
        else:
            return WarehouseLocationOnlySerializer

    def perform_create(self, serializer):
        require_warehouse_manager(self.request, self)
        project_id = warehouse_project_id(self.request)
        supplied = serializer.validated_data.get('projects')
        if supplied and {item.pk for item in supplied} != {project_id}:
            raise ValidationError({'projects': 'انبار تازه فقط به پروژه انتخاب‌شده متصل می‌شود.'})
        serializer.save(projects=[Project.objects.get(pk=project_id)])

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


class WarehouseTransactionListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    http_method_names = ['get', 'head', 'options']
    project_path = 'project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(WarehouseTransaction.objects.all()))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseTransactionSerializer
        else:
            return WarehouseTransactionOnlySerializer

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


class TransactionLineTypeListCreateView(BaseLimiter, generics.ListCreateAPIView):
    http_method_names = ['get', 'head', 'options']
    # project_path = 'project'

    def get_queryset(self):
        return self.limit_queryset(TransactionLineType.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransactionLineTypeSerializer
        else:
            return TransactionLineTypeOnlySerializer

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


class WarehouseTransactionLineListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    http_method_names = ['get', 'head', 'options']
    project_path = 'transaction__project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(
            WarehouseTransactionLine.objects.filter(ware__project_id=F('transaction__project_id'))))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseTransactionLineSerializer
        else:
            return WarehouseTransactionLineOnlySerializer

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = '__all__'
    ordering_fields = '__all__'

    ordering_fields = [
        "ware",
        "transaction",
        "transaction__datetime_created",
        "amount",
        "type",
        "location",
        "user",
    ]

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


######################
# Edits:
######################


class WareTypeEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return self.limit_queryset(WareType.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareTypeSerializer
        else:
            return WareTypeSerializer

    # serializer_class = WareSerializer

    lookup_field = 'id'


class WareVisitTypeEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView, BaseView):
    project_path = 'ware__project'
    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(WareVisitType.objects.all()))

    def perform_update(self, serializer):
        require_warehouse_manager(self.request, self)
        project_id = warehouse_project_id(self.request)
        ware = serializer.validated_data.get('ware')
        visit_type = serializer.validated_data.get('visit_type')
        visit = serializer.validated_data.get('visit')
        if ((ware and ware.project_id != project_id)
                or (visit_type and visit_type.project_id != project_id)
                or (visit and visit.type.project_id != project_id)):
            raise ValidationError('ارتباط کالا و بازدید باید در همین پروژه باشد.')
        serializer.save()

    def perform_destroy(self, instance):
        require_warehouse_manager(self.request, self)
        instance.delete()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareVisitTypeSerializer
        else:
            return WareVisitTypeOnlySerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'


class WareEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView, BaseView):
    project_path = 'project'
    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(Ware.objects.all()))

    def perform_update(self, serializer):
        require_warehouse_manager(self.request, self)
        if 'project' in serializer.validated_data and serializer.validated_data['project'].pk != warehouse_project_id(self.request):
            raise ValidationError({'project': 'انتقال کالا بین پروژه‌ها مجاز نیست.'})
        serializer.save(project_id=warehouse_project_id(self.request))

    def perform_destroy(self, instance):
        require_warehouse_manager(self.request, self)
        if WarehouseTransactionLine.objects.filter(ware=instance).exists():
            raise ValidationError({'ware': 'کالای دارای سابقه موجودی باید غیرفعال شود.'})
        instance.delete()

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareSerializer
        else:
            return WareOnlySerializer

    # serializer_class = WareSerializer

    lookup_field = 'id'


class WarehouseLocationEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView, BaseView):
    project_path = 'projects'
    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(WarehouseLocation.objects.all()))

    def perform_update(self, serializer):
        require_warehouse_manager(self.request, self)
        if 'projects' in serializer.validated_data:
            raise ValidationError({'projects': 'اتصال انبار به پروژه‌ها از این فرم قابل تغییر نیست.'})
        serializer.save()

    def perform_destroy(self, instance):
        require_warehouse_manager(self.request, self)
        if WarehouseTransactionLine.objects.filter(location=instance).exists():
            raise ValidationError({'location': 'انبار دارای سابقه موجودی قابل حذف نیست.'})
        instance.delete()

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseLocationSerializer
        else:
            return WarehouseLocationOnlySerializer

    # serializer_class = WarehouseLocationSerializer

    lookup_field = 'id'


class WarehouseTransactionEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'head', 'options']
    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            project_id = None
        return self.limit_queryset(WarehouseTransaction.objects.filter(project_id=project_id)) if project_id and project_id > 0 else WarehouseTransaction.objects.none()

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseTransactionSerializer
        else:
            return WarehouseTransactionOnlySerializer

    # serializer_class = WarehouseTransactionSerializer

    lookup_field = 'id'


class TransactionLineTypeEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'head', 'options']
    def get_queryset(self):
        return self.limit_queryset(TransactionLineType.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransactionLineTypeSerializer
        else:
            return TransactionLineTypeOnlySerializer

    # serializer_class = TransactionLineTypeSerializer

    lookup_field = 'id'


class WarehouseTransactionLineEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'head', 'options']
    def get_queryset(self):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            project_id = None
        return self.limit_queryset(WarehouseTransactionLine.objects.filter(
            transaction__project_id=project_id, ware__project_id=project_id)) if project_id and project_id > 0 else WarehouseTransactionLine.objects.none()

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseTransactionLineSerializer
        else:
            return WarehouseTransactionLineOnlySerializer

    # serializer_class = WarehouseTransactionLineSerializer

    lookup_field = 'id'


###################
# Aggregated:
###################


class WareAggregatedListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    http_method_names = ['get', 'head', 'options']
    project_path = 'project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(Ware.objects.all()))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WareAggregatedListSerializer
        else:
            return WareOnlySerializer

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


class WarehouseLocationAggregatedListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    http_method_names = ['get', 'head', 'options']
    project_path = 'projects'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(WarehouseLocation.objects.all()))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseAggregatedLocationSerializer
        else:
            return WarehouseLocationOnlySerializer

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


class WarehouseStockAggregatedByUserListView(BaseLimiter, generics.ListAPIView, BaseView):
    project_path = 'ware__project'

    def get_queryset(self):
        from auth_app.models import User
        from django.db.models import Q
        me = self.request.query_params.get('me', False)
        if me:
            base_queryset = User.objects.filter(id=self.request.user.id)
        else:
            base_queryset = User.objects.filter(id__in=self.get_projectified_queryset(
                WarehouseTransactionLine.objects.filter(~Q(user=None))).values_list('user', flat=True))
        return self.limit_queryset(base_queryset)

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    serializer_class = StockUserSerializer

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


class WareDistributionView(BaseLimiter, generics.RetrieveAPIView, BaseView):
    project_path = 'project'
    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(Ware.objects.all()))

    lookup_field = 'id'

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        based_on = self.request.query_params.get('based_on', None)
        if based_on is not None and based_on == 'user':
            return WareDistributionByUserSerializer
        else:
            return WareDistributionByLocationSerializer


##############################
# Create Ez Ware Transaction:
##############################


class WareTransactionEzCreateView(BaseLimiter, generics.GenericAPIView):
    def get_queryset(self):
        return self.limit_queryset(WarehouseTransaction.objects.none())

    serializer_class = StockTransferInput

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry, replayed = create_stock_transfer(request, self, serializer.validated_data)
        return Response({'detail': 'ok', 'transaction_id': entry.id, 'replayed': replayed})

    """
    {
        "lines": [
            {
                "ware": null,
                "amount": null,
                "location": null,
                "user": null,
                "side": "",
                "involved": ""
            },
            {
                "ware": null,
                "amount": null,
                "location": null,
                "user": null,
                "side": "",
                "involved": ""
            }
        ],
        "description": "",
        "datetime_created": null,
        "datetime_last_change": null,
        "creator": null
    }
    """


"""   
{
    "lines": [
        {
            "ware": 1,
            "amount": 1,
            "location": 1,
            "side": "FROM",
            "involved": "LOCATION"
        },
        {
            "ware": 1,
            "amount": 1,
            "user": 4,
            "side": "TO",
            "involved": "USER"
        }
    ],
    "description": "nadarad"
}
"""


# ####################
# # TMP
# ###################


# WareListCreateView
# WarehouseLocationListCreateView
# WarehouseTransactionListCreateView
# TransactionLineTypeListCreateView
# WarehouseTransactionLineListCreateView
# # Edits:
# WareEditsView
# WarehouseLocationEditsView
# WarehouseTransactionEditsView
# TransactionLineTypeEditsView
# WarehouseTransactionLineEditsView


#############################
# Unit APIs:
#############################

class UnitListCreateView(BaseLimiter, generics.ListCreateAPIView):
    def get_queryset(self):
        return self.limit_queryset(Unit.objects.all())

    serializer_class = UnitSerializer
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    filterset_fields = '__all__'
    ordering_fields = '__all__'

    pagination_class = LimitOffsetPagination

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)


class UnitEditsView(BaseLimiter, generics.ListCreateAPIView):
    def get_queryset(self):
        return self.limit_queryset(Unit.objects.all())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    serializer_class = UnitSerializer
    lookup_field = 'id'


##############################
# Ware VisitType Connection:
# WareVisitSettings:
##########################


class WareVisitSettingsView(BaseLimiter, generics.GenericAPIView):
    def get_queryset(self):
        return self.limit_queryset(Ware.objects.none())

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    serializer_class = WareVisitSettingsSerializer

    def get(self, request, *args, **kwargs):
        try:
            visit_id = int(self.request.query_params.get('visit'))
        except (TypeError, ValueError):
            raise ValidationError({'visit': 'بازدید معتبر لازم است.'})
        if visit_id <= 0:
            raise ValidationError({'visit': 'بازدید معتبر لازم است.'})
        from visit.models import Visit
        from django.db.models import Sum
        from visit.asset_access import AssetAccess
        visit = AssetAccess(request, self).visits.filter(pk=visit_id).first()
        if visit is None:
            raise PermissionDenied('بازدید در محدوده دسترسی نیست.')
        response = {
            "has_wares": WareVisitType.objects.filter(visit_type=visit.type, ware__project_id=warehouse_project_id(request), ware__is_for_use=True).exists(),
            "total_count": WarehouseTransactionLine.objects.filter(user=self.request.user,
                                                                   ware__id__in=WareVisitType.objects.filter(
                                                                       visit_type=visit.type,
                                                                       ware__is_for_use=True).values_list('ware',
                                                                                                          flat=True),
                                                                   ware__project=visit.type.project,
                                                                   ware__is_for_use=True).aggregate(Sum('amount'))[
                'amount__sum'],
        }
        serializer = self.get_serializer(response)
        return Response(serializer.data)



class WarehouseLocationPersonnelListCreateView(BaseLimiter, generics.ListCreateAPIView):
    http_method_names = ['get', 'head', 'options']
    project_path = 'location__projects'

    def get_queryset(self):
        return self.limit_queryset(WarehouseLocationPersonnel.objects.filter(user=self.request.user, location__projects__id=self.request.query_params.get('p')))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseLocationPersonnelSerializer
        else:
            return WarehouseLocationPersonnelNestedSerializer

class WarehouseLocationPersonnelEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'head', 'options']
    project_path = 'location__projects'

    def get_queryset(self):
        return self.limit_queryset(WarehouseLocationPersonnel.objects.filter(user=self.request.user, location__projects__id=self.request.query_params.get('p')))

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WarehouseLocationPersonnelSerializer
        else:
            return WarehouseLocationPersonnelNestedSerializer
    
    lookup_field = 'id'
    
