"""Store records for the existing admin store screens.

The former Outlet model was removed in visit migration 0075. These records
are independent of building-based visits; no legacy visit relation is restored.
"""
from rest_framework import generics, serializers
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from auth_app.permissions import DeleteCreateUpdateGetPermission
from auth_app.views import CityAPISerializer
from visit.models import Store, StoreCategory


class StoreCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreCategory
        fields = '__all__'


class StoreWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = '__all__'
        read_only_fields = ['project', 'datetime_created']

    def validate_category(self, value):
        if value and str(value.project_id) != self.context['request'].query_params.get('p'):
            raise serializers.ValidationError('Category belongs to a different project.')
        return value

    def validate(self, attrs):
        code = attrs.get('code', self.instance.code if self.instance else None)
        duplicates = Store.objects.filter(project_id=self.context['request'].query_params.get('p'), code=code)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError({'code': 'This code already exists in this project.'})
        return attrs


class StoreSerializer(StoreWriteSerializer):
    city = CityAPISerializer(read_only=True)
    category = StoreCategorySerializer(read_only=True)
    district = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()

    def get_district(self, obj):
        return None

    def get_region(self, obj):
        return None


class StoreProjectMixin:
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.model.objects.filter(project_id=self.request.query_params.get('p')).order_by('id')

    def get_serializer_class(self):
        return StoreSerializer if self.request.method == 'GET' else StoreWriteSerializer

    def perform_create(self, serializer):
        serializer.save(project_id=int(self.request.query_params['p']))


class AdminStoreListCreateView(StoreProjectMixin, generics.ListCreateAPIView):
    model = Store
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['city', 'city__province', 'category', 'is_active', 'is_visiting', 'code', 'visit_count']
    ordering_fields = ['id', 'name', 'datetime_created', 'visit_count']
    search_fields = ['name', 'code', 'customer_code', 'address', 'owner_name']


class AdminStoreDetailView(StoreProjectMixin, generics.RetrieveUpdateAPIView):
    model = Store
    lookup_field = 'id'


class AdminStoreCategoryListView(StoreProjectMixin, generics.ListAPIView):
    model = StoreCategory

    def get_serializer_class(self):
        return StoreCategorySerializer
