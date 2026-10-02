from rest_framework import exceptions, generics, serializers, status
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
# from core.modules.permissions import RolePermission
from auth_app.permissions import PriorityRolePermission, DeleteCreateUpdateGetPermission
from rest_framework import views as drf_view

##################################
### Our Base Objects:
##################################
class ViewClassDefine:
    is_view = True
    @property
    def methods(self):
        return [key.upper() for key in ["get", "post", "put", "patch", "delete"] if hasattr(self.__class__, key) and callable(getattr(self.__class__, key))]


##################################
### List Objects:
##################################

class ListCreate(generics.ListCreateAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)
    
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # methods = ["GET", "POST",]

class List(generics.ListAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)
    
    filterset_fields = '__all__'
    ordering_fields = '__all__'
    
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # methods = ["GET",]

class Create(generics.CreateAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    # methods = ["POST",]

##################################
### Retrive Destroy and Update:
##################################

class Retrieve(generics.RetrieveAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'
    # methods = ["GET",]

class Update(generics.UpdateAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'
    # methods = ["PUT", "PATCH",]

class Destroy(generics.DestroyAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'
    # methods = ["DELETE",]

class RetrieveUpdate(generics.RetrieveUpdateAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'
    # methods = ["GET", "PUT", "PATCH",]

class RetrieveDestroy(generics.RetrieveDestroyAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'
    # methods = ["GET", "DELETE",]

class RetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
    lookup_field = 'id'
    # methods = ["GET", "PUT", "PATCH", "DELETE",]

##################################
### Generic:
##################################

class Generic(generics.GenericAPIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

class APIView(drf_view.APIView, ViewClassDefine):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
