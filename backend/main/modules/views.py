from rest_framework import exceptions, generics, serializers, status
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from main.modules.permissions import RolePermission
from main.modules.filters import SmartAutoFilterMixin, ConfigurableAutoFilterMixin
from rest_framework import status

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

class ListCreate(ConfigurableAutoFilterMixin, generics.ListCreateAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)
    
    # filterset_fields = '__all__'
    ordering_fields = '__all__'
    
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # methods = ["GET", "POST",]
    # filter_max_depth = 3  # Only go 3 levels deep in relations
    # filter_excluded_field_names = []
    # filter_include_text_search = False  # Exclude text field searching

class List(ConfigurableAutoFilterMixin, generics.ListAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            # If no limit parameter and queryset is large (650+ items)
            if queryset.count() >= 650:
                # Force pagination with limit=50
                self.paginator.page_size = 50
                return self.paginator.paginate_queryset(queryset, self.request, view=self)
            return None # Return None to use default pagination behavior
        # Otherwise use default pagination behavior
        return super().paginate_queryset(queryset)
    
    # filterset_fields = '__all__'
    ordering_fields = '__all__'
    
    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]
    # methods = ["GET",]

class Create(generics.CreateAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    # methods = ["POST",]

class BulkCreate(generics.CreateAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    def create(self, request, *args, **kwargs):
        # Check if data is a list
        is_many = isinstance(request.data, list)
        
        if not is_many:
            return super().create(request, *args, **kwargs)
            
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

##################################
### Retrive Destrot and Update:
##################################

class Retrieve(generics.RetrieveAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    lookup_field = 'id'
    # methods = ["GET",]

class Update(generics.UpdateAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    lookup_field = 'id'
    # methods = ["PUT", "PATCH",]

class Destroy(generics.DestroyAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    lookup_field = 'id'
    # methods = ["DELETE",]

class RetrieveUpdate(generics.RetrieveUpdateAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    lookup_field = 'id'
    # methods = ["GET", "PUT", "PATCH",]

class RetrieveDestroy(generics.RetrieveDestroyAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    lookup_field = 'id'
    # methods = ["GET", "DELETE",]

class RetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]
    lookup_field = 'id'
    # methods = ["GET", "PUT", "PATCH", "DELETE",]

##################################
### Retrive Destroy and Update:
##################################

class Generic(generics.GenericAPIView, ViewClassDefine):
    permission_classes = [
        RolePermission,
    ]