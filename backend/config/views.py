from django.shortcuts import render
from config.models import AddIn
# Create your views here.
from rest_framework import exceptions, generics, serializers
from auth_app.views import RoleSerializer, ProjectSerializer
from auth_app.models import RoleAssignment
from config.serializers import HealCheckSerializer
# from core.generics import BaseView
from core.generics import BaseView, BaseLimiter

from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from rest_framework.response import Response
from auth_app.permissions import *



class FrResultSerializer(serializers.Serializer):
    is_for = serializers.CharField()
    for_id = serializers.IntegerField()
    recognition_status = serializers.IntegerField()


class FrResultView(generics.GenericAPIView): #todo ask for permission
    serializer_class = FrResultSerializer

    def get_queryset(self):
        return RoleAssignment.objects.none()
    def post(self, request, *args, **kwargs):
        is_for = self.request.data['is_for']
        for_id = self.request.data['for_id']
        if is_for == 'S':
            from survey.models import SurveyPhoto
            obj = SurveyPhoto.objects.get(id=for_id)
        else:
            from visit.models import Photo
            obj = Photo.objects.get(id=for_id)
        obj.recognition_status = self.request.data['recognition_status']
        obj.save()
        return Response({"detail": "ok"})


class GenerateQRcodeSerializer(serializers.Serializer):
    logo_url = serializers.CharField()
    code_data = serializers.CharField()


class GenerateQRcodeView(generics.GenericAPIView): #todo ask for permissions

    serializer_class = GenerateQRcodeSerializer

    def get_queryset(self):
        return RoleAssignment.objects.none()

    def post(self, request, *args, **kwargs):
        from core.qr import QRCode
        from io import BytesIO
        qr = QRCode(logo_url=self.request.data['logo_url'], code_data=self.request.data['code_data'])
        pill_img = qr.generate_qr_code()
        buffered = BytesIO()
        pill_img.save(buffered, format='PNG')
        from django.http import HttpResponse
        response = HttpResponse(buffered.getvalue(), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="downded_image.png"'
        return response


class CustomBulkEditSerializer(serializers.Serializer):
    app = serializers.CharField()
    model = serializers.CharField()
    ids = serializers.ListSerializer(child=serializers.IntegerField())
    is_active = serializers.BooleanField(required=False)
    is_deleted = serializers.BooleanField(required=False)
    real_delete = serializers.BooleanField(required=False)


class CustomBulkEditView(BaseLimiter, generics.GenericAPIView): #todo ask for it

    serializer_class = CustomBulkEditSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(RoleAssignment.objects.none())

    def post(self, request, *args, **kwargs):
        allowed_model_name = [
            'Visit',
            'RoleAssignment',
        ]
        model_name = self.request.data['model']
        app_name = self.request.data['app']
        ids = self.request.data['ids']

        if not model_name in allowed_model_name:
            from core.exceptions import NotAcceptable
            raise NotAcceptable("not allowed!")
        from django.apps import apps
        model = apps.get_model(app_name, model_name)
        d = {}
        if 'is_active' in self.request.data.keys():
            d['is_active'] = self.request.data['is_active']
        if 'is_deleted' in self.request.data.keys():
            d['is_deleted'] = self.request.data['is_deleted']

        model.objects.filter(id__in=ids).update(**d)
        return Response({"detail": "ok"})


class AddInSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddIn
        fields = (
            "key",
            "name",
            "verbose_name",
            "app_model_name",
        )


class HealthCheck(generics.GenericAPIView):
    serializer_class = HealCheckSerializer

    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        data = {'detail': 'healthy'}
        return Response(data, status=200)


from rest_framework.response import Response

from rest_framework import generics

from core.modules.views import (
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
from config.models import (
    Config,
    MediaManager,
    NavMenu,
    TagType,
    TagManager,
    MediaType,
)

from config.serializers import (
    ConfigSerializer,
    MediaManagerSerializer,
    NavMenuSerializer,
    NavMenuOnlySerializer,
    TagTypeSerializer,
    TagManagerSerializer,
    OnlyTagManagerSerializer,
    MediaTypeSerializer, 
    HealCheckSerializer,
    OnlyMediaManagerSerializer,
)

from visit.views import CitySerializer, ProvinceSerializer
from visit.models import City, Province

from rest_framework.permissions import AllowAny

from auth_app.models import Role, ExtendedUser
from django.db.models import Q


###################################
# Config CR:
###################################


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


#######################
# NavBar and Media    #
#######################


class NavMenuList(List):

    def get_queryset(self):
        grants = authorized_role_views(self.request, self)
        if not grants.exists():
            return NavMenu.objects.none()
        return NavMenu.objects.filter(Q(role_id__in=grants.values('role_id')) | Q(role=None)).distinct()

    serializer_class = NavMenuSerializer


class NavMenuRetrieveUpdate(RetrieveUpdate):

    def get_queryset(self):
        return NavMenu.objects.all()

    serializer_class = NavMenuOnlySerializer


class MediaManagerList(List):
    def get_queryset(self):
        return MediaManager.objects.all()

    serializer_class = MediaManagerSerializer

class MediaManagerCreate(Create):
    def get_queryset(self):
        return MediaManager.objects.all()

    serializer_class = OnlyMediaManagerSerializer

class MediaTypeList(List):
    def get_queryset(self):
        return MediaType.objects.all()

    serializer_class = MediaTypeSerializer


class MediaManagerRetrieveUpdateDestroy(RetrieveUpdateDestroy):

    def get_queryset(self):
        return MediaManager.objects.all()

    serializer_class = MediaManagerSerializer




class TagManagerDetailView(RetrieveUpdateDestroy):
    serializer_class = OnlyTagManagerSerializer
    queryset = TagManager.objects.all()


class TagManagerListCreateView(ListCreate):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TagManagerSerializer
        else:
            return OnlyTagManagerSerializer

    def get_queryset(self):
        return TagManager.objects.filter(is_active=True)

    filterset_fields = {
        'title': ['exact', 'in',],
        'title_fa': ['exact',  'in',],
        'datetime_created': ['exact', 'gte', 'lte', ],
        'datetime_last_change': ['exact', ],
        'type': ['exact',  'in',],
        'type__id': ['exact', ],
        'type__name': ['exact',  'in',],
        'type__verbose': ['exact', ],
        'store__category__id': ['exact',  'in',],
        'store__category__name_en': ['exact',  'in',],
        'store__category__name_fa': ['exact',  'in',],
        'store__category': ['exact',  'in',],
        'is_active': ['exact', ],
        'is_visible': ['exact', ],
    }
    ordering_fields = [
        'title',
        'title_fa',
        'datetime_created',
        'datetime_last_change',
    ]
    search_fields = ['title', 'title_fa']


class MediaTypeListCreateView(ListCreate):
    serializer_class = MediaTypeSerializer
    queryset = MediaType.objects.all()


class MediaTypeDetailView(RetrieveUpdateDestroy):
    serializer_class = MediaTypeSerializer
    queryset = MediaType.objects.all()


class TagTypeListCreateView(ListCreate):
    serializer_class = TagTypeSerializer
    queryset = TagType.objects.all()


class TagTypeDetailView(RetrieveUpdateDestroy):
    serializer_class = TagTypeSerializer
    queryset = TagType.objects.all()


class HealthCheck(generics.GenericAPIView):
    serializer_class = HealCheckSerializer

    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        data = {'detail': 'healthy'}
        return Response(data, status=200)

