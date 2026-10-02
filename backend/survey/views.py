from django.shortcuts import render, get_object_or_404
from survey.models import *
from rest_framework import exceptions, generics, serializers
from core.storage import ArvanStorage
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from rest_framework.pagination import LimitOffsetPagination
from core.exceptions import *
from django.db.models import Max
from django.db.models import Count
from django.db.models import F
from django.db import transaction
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from visit.views import AnswerTypeSerializer, AnswerChoiceSerializer, UserSerializer
from rest_framework.response import Response

from auth_app.views import CityAPISerializer, ProvinceAPISerializer
from datetime import timedelta
import secrets
from hmac import compare_digest
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework.throttling import ScopedRateThrottle

from core.generics import BaseView, BaseLimiter
from auth_app.permissions import *
from visit.asset_access import AssetAccess


def accessible_fillouts(request, view):
    """Survey records reachable through this action's active project grant."""
    access = AssetAccess(request, view)
    rows = SurveyFillOut.objects.filter(survey__project_id=access.project_id, is_deleted=False)
    if access.project_wide:
        return rows
    return rows.filter(Q(user=request.user) | Q(visit_id__in=access.assigned_visits.values('pk')))


# Create your views here.
########################################
# Survey:
########################################
class SurveyReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyReportCategory
        fields = '__all__'


class SurveyQuestionTypeSerializer(serializers.ModelSerializer):
    survey_report_category = SurveyReportCategorySerializer()

    class Meta:
        model = SurveyQuestionType
        fields = '__all__'


from auth_app.views import FieldValidationSerializer

from auth_app.views import QuestionAnswerTypeValidationSerializer
from auth_app.models import QuestionAnswerTypeValidation


class SurveyQuestionSerializer(serializers.ModelSerializer):
    survey_question_type = SurveyQuestionTypeSerializer()
    validation = FieldValidationSerializer()
    answer_type = AnswerTypeSerializer(many=True)
    answer_choices = AnswerChoiceSerializer(many=True)
    dropdown_choices = AnswerChoiceSerializer(many=True)
    radio_choices = AnswerChoiceSerializer(many=True)
    survey_report_category = SurveyReportCategorySerializer()
    answer_params = serializers.SerializerMethodField()

    def get_answer_params(self, obj):
        data = QuestionAnswerTypeValidation.objects.filter(survey_question=obj)
        return QuestionAnswerTypeValidationSerializer(data, many=True).data

    class Meta:
        model = SurveyQuestion
        fields = '__all__'


class SurveySerializer(serializers.ModelSerializer):
    # survey_questions = SurveyQuestionSerializer(many=True)
    class Meta:
        model = Survey
        fields = '__all__'


class SurveyFillOutSerializer(serializers.ModelSerializer):
    survey = SurveySerializer()
    user = UserSerializer()
    city = CityAPISerializer()
    province = ProvinceAPISerializer()

    class Meta:
        model = SurveyFillOut
        fields = '__all__'


class SurveyAnswerSerializer(serializers.ModelSerializer):
    survey_fill_out = SurveyFillOutSerializer()
    survey_question = SurveyQuestionSerializer()
    multichoice = AnswerChoiceSerializer(many=True)
    dropdown = AnswerChoiceSerializer()
    radio = AnswerChoiceSerializer()

    class Meta:
        model = SurveyAnswer
        fields = '__all__'


class SurveyPhotoTypeSerializer(serializers.ModelSerializer):
    survey_question = SurveyQuestionSerializer()
    survey_report_category = SurveyReportCategorySerializer()

    class Meta:
        model = SurveyPhotoType
        fields = '__all__'


class SurveyPhotoSerializer(serializers.ModelSerializer):
    survey_photo_type = SurveyPhotoTypeSerializer()
    survey_fill_out = SurveyFillOutSerializer()
    link = serializers.SerializerMethodField()

    class Meta:
        model = SurveyPhoto
        fields = '__all__'

    def get_link(self, obj):
        from core.media_access import media_read_url
        return media_read_url(obj.link, self.context.get('request'))


########################
# Only:
########################

class SurveyReportCategoryOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyReportCategory
        fields = '__all__'


class SurveyQuestionTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestionType
        fields = '__all__'


class SurveyQuestionOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = '__all__'


class SurveyOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'


class SurveyFillOutOnlySerializer(serializers.ModelSerializer):
    final_score = serializers.ReadOnlyField()
    final_result = serializers.ReadOnlyField()
    
    class Meta:
        model = SurveyFillOut
        fields = '__all__'


class SurveyAnswerOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyAnswer
        fields = '__all__'


class SurveyPhotoTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyPhotoType
        fields = '__all__'

    def validate(self, attrs):
        survey = attrs.get('survey', getattr(self.instance, 'survey', None))
        question = attrs.get('survey_question', getattr(self.instance, 'survey_question', None))
        if question and (survey is None or question.survey_id != survey.pk):
            raise serializers.ValidationError({'survey_question': 'سؤال باید متعلق به همین پرسشنامه باشد.'})
        return attrs


class SurveyPhotoOnlySerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    class Meta:
        model = SurveyPhoto
        fields = '__all__'
        read_only_fields = ('id', 'creator', 'survey_photo_type', 'survey_fill_out', 'link',
                            'longitude', 'latitude', 'datetime_created', 'datetime_last_change',
                            'is_deleted')

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


#######################
# Only Ends!
#######################


class SurveyReportCategoryListCreateView(generics.ListCreateAPIView, BaseLimiter):
    def get_queryset(self):
        if self.request.GET.get('survey_fill_out_id') is not None:
            survey_fill_out = SurveyFillOut.objects.get(id=self.request.GET.get('survey_fill_out_id'))
            return self.limit_queryset( SurveyReportCategory.objects.filter(
                id__in=SurveyQuestion.objects.filter(survey=survey_fill_out.survey).values_list(
                    'survey_report_category__id', flat=True)).order_by('id'))
        else:
            return self.limit_queryset(SurveyReportCategory.objects.all().order_by('id'))

    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyReportCategorySerializer
        else:
            return SurveyReportCategoryOnlySerializer

    # serializer_class = SurveyReportCategorySerializer

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


class SurveyQuestionTypeListCreateView(generics.ListCreateAPIView, BaseLimiter):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    def get_queryset(self):
        return self.limit_queryset(SurveyQuestionType.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyQuestionTypeSerializer
        else:
            return SurveyQuestionTypeOnlySerializer

    # serializer_class = SurveyQuestionTypeSerializer

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


class SurveyQuestionListCreateView(generics.ListCreateAPIView, BaseView, BaseLimiter):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    project_path = 'survey__project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(SurveyQuestion.objects.filter(is_active=True)))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyQuestionSerializer
        else:
            return SurveyQuestionOnlySerializer

    # serializer_class = SurveyQuestionSerializer

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


class SurveyListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    project_path = 'project'

    def get_queryset(self):
        visit_id = self.request.query_params.get('visit', None)
        if visit_id is not None:
            from visit.models import Visit
            visit = Visit.objects.get(id=visit_id)
            visit_type = visit.type
            return self.limit_queryset(self.get_projectified_queryset(visit_type.surveys.all()))
        return self.limit_queryset( self.get_projectified_queryset(Survey.objects.all()))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveySerializer
        else:
            return SurveyOnlySerializer

    # serializer_class = SurveySerializer

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


class SurveyFillOutListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    project_path = 'survey__project'

    def get_queryset(self):
        return self.limit_queryset(accessible_fillouts(self.request, self))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyFillOutSerializer
        else:
            return SurveyFillOutOnlySerializer

    # serializer_class = SurveyFillOutSerializer

    permission_classes = [DeleteCreateUpdateGetPermission]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    # filterset_fields = '__all__'
    filterset_fields = {
        "visit": ['exact', ],
        "survey": ['exact', ],
        "user": ['exact', ],
        "province": ['exact', ],
        "city": ['exact', ],
        "longitude": ['exact', ],
        "latitude": ['exact', ],
        "phone_verified": ['exact', ],
        "phone_number": ['exact', ],
        "is_closed": ['exact', ],
        "is_deleted": ['exact', ],
        "status": ['exact', ],
        "datetime_created": ['exact', 'gte', 'lte', ],
        "datetime_last_change": ['exact', 'gte', 'lte', ]
    }
    ordering_fields = '__all__'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        survey = serializer.validated_data.get('survey')
        access = AssetAccess(request, self)
        if survey is None or survey.project_id != access.project_id:
            raise serializers.ValidationError({'survey': 'پرسشنامه باید متعلق به پروژه انتخاب‌شده باشد.'})
        visit = serializer.validated_data.get('visit')
        if visit and not (access.project_wide or access.assigned_visits.filter(pk=visit.pk).exists()):
            raise exceptions.PermissionDenied('بازدید در دامنه شما نیست.')
        existing = accessible_fillouts(request, self).filter(
            user=request.user, survey=survey, is_closed=False).first()
        if existing:
            return Response(SurveyFillOutSerializer(existing).data, status=200)
        self.perform_create(serializer)
        return Response(SurveyFillOutSerializer(serializer.instance).data, status=201)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SurveyAnswerListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    project_path = 'survey_fill_out__survey__project'

    def get_queryset(self):
        return self.limit_queryset(SurveyAnswer.objects.filter(
            survey_fill_out__in=accessible_fillouts(self.request, self),
            survey_question__survey_id=F('survey_fill_out__survey_id'),
        ).order_by('survey_question__priority'))

    def perform_create(self, serializer):
        fillout = serializer.validated_data.get('survey_fill_out')
        question = serializer.validated_data.get('survey_question')
        if fillout is None or not accessible_fillouts(self.request, self).filter(pk=fillout.pk).exists():
            raise exceptions.PermissionDenied('پرسشنامه در دامنه شما نیست.')
        if question is None or question.survey_id != fillout.survey_id:
            raise serializers.ValidationError({'survey_question': 'سؤال متعلق به این پرسشنامه نیست.'})
        if fillout.is_closed or fillout.status == SurveyFillOut.CONFIRMED:
            raise serializers.ValidationError({'survey_fill_out': 'پرسشنامه بسته قابل تغییر نیست.'})
        serializer.save()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyAnswerSerializer
        else:
            return SurveyAnswerOnlySerializer

    # serializer_class = SurveyAnswerSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = '__all__'
    ordering_fields = [
        "survey_fill_out",
        "survey_question",
        "survey_question__priority",
        "score",
        "number",
        "bool",
        "text",
        "description",
        "price",
        "multichoice",
        "dropdown",
        "radio",
        "bool_is_expected",
        "datetime_created",
        "datetime_last_change",
    ]

class SurveyPhotoTypeListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    project_path = 'survey_project'

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(SurveyPhotoType.objects.filter(is_active=True)))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyPhotoTypeSerializer
        else:
            return SurveyPhotoTypeOnlySerializer

    def perform_create(self, serializer):
        access = AssetAccess(self.request, self)
        if not access.project_wide:
            raise exceptions.PermissionDenied('ساخت نوع عکس نیازمند نقش مدیریتی پروژه است.')
        survey = serializer.validated_data.get('survey')
        if survey is None or survey.project_id != access.project_id:
            raise serializers.ValidationError({'survey': 'پرسشنامه باید متعلق به پروژه انتخاب‌شده باشد.'})
        serializer.save()

    # serializer_class = SurveyPhotoTypeSerializer

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


class SurveyPhotoListCreateView(BaseLimiter, generics.ListCreateAPIView, BaseView):
    http_method_names = ['get', 'head', 'options']
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    project_path = 'survey_photo_type__survey__project'

    def get_queryset(self):
        rows = self.get_projectified_queryset(SurveyPhoto.objects.filter(
            is_deleted=False, survey_fill_out__is_deleted=False,
            survey_photo_type__survey_id=F('survey_fill_out__survey_id'),
        ))
        scopes = set(authorized_role_views(self.request, self).values_list('role__asset_scope', flat=True))
        if 'project' not in scopes:
            assigned = AssetAccess(self.request, self).assigned_visits.values('pk')
            rows = rows.filter(Q(creator=self.request.user) |
                               Q(survey_fill_out__visit_id__in=assigned))
        return self.limit_queryset(rows)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyPhotoSerializer
        else:
            return SurveyPhotoOnlySerializer

    filterset_fields = {
        'survey_photo_type': ['exact', ],
        'survey_fill_out__survey': ['exact', ],
        'survey_fill_out__visit': ['exact', ],
        'survey_fill_out__user': ['exact', ],
        'survey_fill_out__province': ['exact', ],
        'survey_fill_out__city': ['exact', ],
        'survey_fill_out__longitude': ['exact', 'gte', 'lte', ],
        'survey_fill_out__latitude': ['exact', 'gte', 'lte', ],
        'survey_fill_out__phone_verified': ['exact', ],
        'survey_fill_out__phone_number': ['exact', ],
        'survey_fill_out__is_closed': ['exact', ],
        'survey_fill_out__is_deleted': ['exact', ],
        'survey_fill_out__status': ['exact', 'in', ],
        'survey_fill_out__datetime_created': ['exact', 'gte', 'lte', ],
        'survey_fill_out__datetime_last_change': ['exact', 'gte', 'lte', ],
        'survey_fill_out': ['exact', ],
        'link': ['exact', ],
        'longitude': ['exact', 'gte', 'lte', ],
        'latitude': ['exact', 'gte', 'lte', ],
        'datetime_created': ['exact', 'gte', 'lte', ],
        'datetime_last_change': ['exact', 'gte', 'lte', ],
        'recognition_status': ['exact', ],
        'supervision_location_confirm': ['exact', ],
        'supervision_confirm': ['exact', ],
        'is_deleted': ['exact', ],
        'is_checked': ['exact', ],
    }
    # serializer_class = SurveyPhotoSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    filter_backends = [
        SearchFilter,
        OrderingFilter,
        DjangoFilterBackend,
    ]

    filterset_fields = {
        'survey_photo_type': ['exact'],
        'survey_photo_type__name': ['in', 'exact', ],
        # 'survey_photo_type__outlet_category': ['exact'],
        # 'survey_photo_type__report_category': ['exact'],
        'link': ['exact'],
        'survey_fill_out': ['in', 'exact'],
        'survey_fill_out__survey': ['exact'],
        'survey_fill_out__status': ['exact'],
        'survey_fill_out__user': ['exact'],
        # 'survey_fill_out__outlet__code': ['exact'],
        'survey_fill_out__city': ['exact'],
        'survey_fill_out__province': ['exact'],
        'survey_fill_out': ['exact'],
        'longitude': ['exact'],
        'latitude': ['exact'],
        'datetime_created': ['gte', 'lte', 'exact'],
        'datetime_last_change': ['gte', 'lte', 'exact'],
        'is_deleted': ['exact'],
        'is_checked': ['exact'],
        'is_favourite': ['exact'],
    }

    # filterset_fields = '__all__'
    ordering_fields = '__all__'


class SurveyReportCategoryEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(SurveyReportCategory.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyReportCategorySerializer
        else:
            return SurveyReportCategoryOnlySerializer

    lookup_field = 'id'


class SurveyQuestionTypeEditsView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(SurveyQuestionType.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyQuestionTypeSerializer
        else:
            return SurveyQuestionTypeOnlySerializer

    lookup_field = 'id'


class SurveyQuestionEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(SurveyQuestion.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyQuestionSerializer
        else:
            return SurveyQuestionOnlySerializer

    lookup_field = 'id'


class SurveyEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(Survey.objects.all())

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveySerializer
        else:
            return SurveyOnlySerializer

    lookup_field = 'id'


class SurveyFillOutEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(accessible_fillouts(self.request, self))

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyFillOutSerializer
        else:
            return SurveyFillOutOnlySerializer

    lookup_field = 'id'

    def perform_update(self, serializer):
        if set(self.request.data) & {'survey', 'visit', 'user', 'outer_entry',
                                     'outer_entry_int_user_id', 'device_id', 'is_deleted'}:
            raise serializers.ValidationError('هویت و مالک پرسشنامه از این مسیر قابل تغییر نیست.')
        if (serializer.instance.is_closed or serializer.instance.status == SurveyFillOut.CONFIRMED) and not AssetAccess(
                self.request, self).project_wide:
            raise exceptions.PermissionDenied('پرسشنامه بسته فقط با نقش مدیریتی قابل تغییر است.')
        if self.request.method == 'PATCH':
            if 'is_closed' in self.request.data.keys():
                if self.request.data['is_closed'] == True:
                    serializer.save(status='1', is_closed=True)
                else:
                    serializer.save(status='0', is_closed=False)
            else:
                return super().perform_update(serializer)
        else:
            return super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not AssetAccess(self.request, self).project_wide:
            raise exceptions.PermissionDenied('حذف پرسشنامه نیازمند نقش مدیریتی پروژه است.')
        photos = SurveyPhoto.objects.filter(survey_fill_out=instance)
        for photo in photos:
            photo.delete()
        return super().perform_destroy(instance)


class SurveyAnswerEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(SurveyAnswer.objects.filter(
            survey_fill_out__in=accessible_fillouts(self.request, self),
            survey_question__survey_id=F('survey_fill_out__survey_id'),
        ))

    def perform_update(self, serializer):
        if set(self.request.data) & {'survey_fill_out', 'survey_question'}:
            raise serializers.ValidationError('پرسشنامه و سؤال پاسخ قابل جابه‌جایی نیستند.')
        fillout = serializer.instance.survey_fill_out
        if fillout.is_closed or fillout.status == SurveyFillOut.CONFIRMED:
            raise serializers.ValidationError('پرسشنامه بسته قابل تغییر نیست.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.survey_fill_out.is_closed or instance.survey_fill_out.status == SurveyFillOut.CONFIRMED:
            raise serializers.ValidationError('پرسشنامه بسته قابل تغییر نیست.')
        instance.delete()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyAnswerSerializer
        else:
            return SurveyAnswerOnlySerializer

    lookup_field = 'id'


class SurveyPhotoTypeEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView, BaseView):
    project_path = 'survey__project'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(self.get_projectified_queryset(SurveyPhotoType.objects.all()))

    def perform_update(self, serializer):
        if not AssetAccess(self.request, self).project_wide:
            raise exceptions.PermissionDenied('ویرایش نوع عکس نیازمند نقش مدیریتی پروژه است.')
        survey = serializer.validated_data.get('survey')
        if survey is not None and survey.pk != serializer.instance.survey_id:
            raise serializers.ValidationError({'survey': 'انتقال نوع عکس به پرسشنامه دیگر مجاز نیست.'})
        serializer.save()

    def perform_destroy(self, instance):
        if not AssetAccess(self.request, self).project_wide:
            raise exceptions.PermissionDenied('حذف نوع عکس نیازمند نقش مدیریتی پروژه است.')
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyPhotoTypeSerializer
        else:
            return SurveyPhotoTypeOnlySerializer

    lookup_field = 'id'


class SurveyPhotoEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView, BaseView):
    project_path = 'survey_photo_type__survey__project'
    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        rows = self.get_projectified_queryset(SurveyPhoto.objects.filter(
            is_deleted=False, survey_fill_out__is_deleted=False,
            survey_photo_type__survey_id=F('survey_fill_out__survey_id'),
        ))
        scopes = set(authorized_role_views(self.request, self).values_list('role__asset_scope', flat=True))
        if 'project' not in scopes:
            if self.request.method == 'GET':
                assigned = AssetAccess(self.request, self).assigned_visits.values('pk')
                rows = rows.filter(Q(creator=self.request.user) |
                                   Q(survey_fill_out__visit_id__in=assigned))
            else:
                rows = rows.filter(creator=self.request.user, survey_fill_out__is_closed=False,
                                   survey_fill_out__status__in=(SurveyFillOut.INITIAL, SurveyFillOut.COMPLETED))
        return self.limit_queryset(rows)

    def perform_update(self, serializer):
        scopes = set(authorized_role_views(self.request, self).values_list('role__asset_scope', flat=True))
        if 'project' not in scopes and set(serializer.validated_data) - {'is_favourite'}:
            raise exceptions.PermissionDenied('بررسی عکس نیازمند نقش مدیریتی پروژه است.')
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SurveyPhotoSerializer
        else:
            return SurveyPhotoOnlySerializer

    lookup_field = 'id'


class SurveyAnswerSubmittedSerializer(serializers.ModelSerializer):
    survey_fill_out = SurveyFillOutSerializer()
    survey_question = SurveyQuestionSerializer()
    dropdown = AnswerChoiceSerializer()
    radio = AnswerChoiceSerializer()

    class Meta:
        model = SurveyAnswer
        fields = '__all__'


class SurveyQuestionListForVisitsSerializer(serializers.Serializer):
    question = SurveyQuestionSerializer()
    submitted_answer = SurveyAnswerSubmittedSerializer()


# from core.json_renderer import RegexSafeJSONRenderer
class PromoterSurveyQuestionList(BaseLimiter, generics.ListAPIView):
    def get_queryset(self, *args, **kwargs):
        # visit_id = int(kwargs.get('visit_id', 0))
        # print("q", kwargs, args)
        # visit = Visit.objects.get(id=1)
        return self.limit_queryset(SurveyQuestion.objects.none())

    # renderer_classes = [RegexSafeJSONRenderer]
    serializer_class = SurveyQuestionSerializer

    permission_classes = [DeleteCreateUpdateGetPermission]

    def list(self, request, *args, **kwargs):
        # project_id = self.request.query_params.get('p', None)
        survey_fill_out = get_object_or_404(accessible_fillouts(request, self),
                                            pk=kwargs.get('survey_fill_out'))
        query_param = self.request.GET.get('survey_question_type')
        if query_param is None:
            queryset = SurveyQuestion.objects.filter(
                survey=survey_fill_out.survey, is_active=True).order_by('priority')
        else:
            queryset = SurveyQuestion.objects.filter(
                survey=survey_fill_out.survey, survey_question_type=query_param, is_active=True).order_by('priority')
        # queryset = self.get_queryset()
        output = []
        for q in queryset:
            answers = SurveyAnswer.objects.filter(survey_fill_out=survey_fill_out, survey_question=q)
            if len(answers) == 0:
                answer = SurveyAnswer()
                answer.id = None
                # answer = None
            else:
                answer = answers[0]
            output.append(
                {
                    "question": q,
                    "submitted_answer": answer
                }
            )

        return Response(SurveyQuestionListForVisitsSerializer(output, many=True).data)


class SurveyQuestionTypeWithStatusSerializer(SurveyQuestionTypeSerializer):
    progress = serializers.CharField()
    status = serializers.BooleanField()
    disabled = serializers.BooleanField()
    total_score = serializers.IntegerField()



class SurveyPhotoTypeWithStatusSerializer(SurveyPhotoTypeSerializer):
    progress = serializers.CharField()
    status = serializers.BooleanField()

from config.views import AddInSerializer
class FrontSurveyPageSettingsSerializer(serializers.Serializer):
    survey_fill_out = SurveyFillOutSerializer()
    questions = SurveyQuestionTypeWithStatusSerializer(many=True)
    photos = SurveyPhotoTypeWithStatusSerializer(many=True)
    add_ins = AddInSerializer(many=True)



class FrontSurveyPageSettingsView(BaseLimiter, generics.GenericAPIView):
    serializer_class = FrontSurveyPageSettingsSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.limit_queryset(User.objects.none())

    def get(self, request, *args, **kwargs):
        survey_fill_out_id = kwargs.get('survey_fill_out_id', 0)
        survey_fill_out = get_object_or_404(accessible_fillouts(request, self), pk=survey_fill_out_id)

        questions = SurveyQuestion.objects.filter(
            survey=survey_fill_out.survey, is_active=True).order_by('id')
        question_types = []
        for q in questions:
            if q.survey_question_type is not None and q.survey_question_type not in question_types:
                question_types.append(q.survey_question_type)
        for question_type in question_types:
            question_type.status = False
            question_type.total_score = 0
            questions = SurveyQuestion.objects.filter(
                survey=survey_fill_out.survey, survey_question_type=question_type, is_active=True, is_mandatory=True)
            answered_questions_count = 0
            for question in questions:
                q = SurveyAnswer.objects.filter(survey_fill_out=survey_fill_out, survey_question=question)
                if len(q) > 0:
                    answered_questions_count += 1
                    answer_fields = set(question.answer_type.values_list('field', flat=True))
                    if question_type.has_score:
                        if 'radio' in answer_fields:
                            choice = q.first().radio
                            question_type.total_score += (choice.score or 0) if choice else 0
                        elif 'dropdown' in answer_fields:
                            choice = q.first().dropdown
                            question_type.total_score += (choice.score or 0) if choice else 0
            if answered_questions_count < len(questions):
                question_type.status = False
            else:
                question_type.status = True
            if len(questions) == 0:
                question_type.progress = '100%'
            else:
                question_type.progress = str(
                    (answered_questions_count / len(questions)) * 100) + '%'

        for qt1 in question_types:
            if qt1.score_depends_on is not None:
                for qt2 in question_types:
                    if qt2.id == qt1.score_depends_on.id:
                        if qt2.total_score >= qt1.score_min and qt2.total_score <= qt1.score_max:
                            qt1.disabled = False
                        else:
                            qt1.disabled = True
            else:
                qt1.disabled = False

        photos = SurveyPhotoType.objects.filter(
            survey=survey_fill_out.survey, is_active=True).order_by('id')
        for photo in photos:
            photo.status = False
            q = SurveyPhoto.objects.filter(survey_photo_type=photo, survey_fill_out=survey_fill_out, is_deleted=False)

            if len(q) < photo.min:
                photo.status = False
            else:
                photo.status = True
            if photo.min == 0:
                photo.progress = '100%'
            else:
                photo.progress = str((len(q) / photo.min) * 100) + '%'

        r = {
            "survey_fill_out": survey_fill_out,
            "questions": question_types,
            "photos": photos,
            "add_ins": survey_fill_out.survey.add_ins.all()
        }
        return Response(FrontSurveyPageSettingsSerializer(r, many=False).data)


class FieldSurveyAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyAnswer
        fields = ('survey_fill_out', 'survey_question', 'bool', 'number', 'text',
                  'description', 'price', 'multichoice', 'dropdown', 'radio',
                  'longitude', 'latitude')

    def validate(self, attrs):
        unexpected = set(self.initial_data) - set(self.fields)
        if unexpected:
            raise serializers.ValidationError({key: 'این فیلد قابل ثبت نیست.' for key in unexpected})
        return attrs


class PromoterAnswersSurveyQuestionsView(BaseLimiter, generics.GenericAPIView):
    serializer_class = FieldSurveyAnswerSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.limit_queryset(SurveyAnswer.objects.none())

    def post(self, request):
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        with transaction.atomic():
            fillout = get_object_or_404(accessible_fillouts(request, self).select_for_update(),
                                        pk=values['survey_fill_out'].pk)
            question = values['survey_question']
            if question.survey_id != fillout.survey_id or not question.is_active:
                raise serializers.ValidationError({'survey_question': 'سؤال متعلق به این پرسشنامه نیست.'})
            if fillout.is_closed or fillout.status == SurveyFillOut.CONFIRMED:
                raise serializers.ValidationError({'survey_fill_out': 'پرسشنامه بسته قابل تغییر نیست.'})
            answer = SurveyAnswer.objects.filter(survey_fill_out=fillout,
                                                 survey_question=question).first()
            values = {key: value for key, value in values.items()
                      if key not in ('survey_fill_out', 'survey_question', 'multichoice')}
            if answer is None:
                answer = SurveyAnswer(survey_fill_out=fillout, survey_question=question)
            for key, value in values.items():
                setattr(answer, key, value)
            answer.save()
            if 'multichoice' in payload.validated_data:
                answer.multichoice.set(payload.validated_data['multichoice'])
        return Response(SurveyAnswerSerializer(answer).data)


########################
# SurveyPhoto Upload:
########################


class SurveyPhotoCreateSerializer(serializers.ModelSerializer):
    link = serializers.FileField()

    class Meta:
        model = SurveyPhoto
        fields = ('longitude', 'latitude', 'survey_photo_type', 'survey_fill_out', 'link', 'is_favourite')


class PromoterUploadSurveyImageAPIView(generics.GenericAPIView, BaseLimiter):

    serializer_class = SurveyPhotoCreateSerializer

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]

    def get_queryset(self):
        return self.limit_queryset(SurveyPhoto.objects.none())

    def post(self, request, *args, **kwargs):
        from PIL import Image, UnidentifiedImageError
        data = request.data.copy()
        for field in ('longitude', 'latitude'):
            if data.get(field) in ('null', 'None', 'NULL', '', ' '):
                data[field] = None
        payload = self.get_serializer(data=data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        try:
            project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            raise serializers.ValidationError({'p': 'پروژه معتبر لازم است.'})
        if project_id <= 0:
            raise serializers.ValidationError({'p': 'پروژه معتبر لازم است.'})
        upload = values['link']
        if upload.size > 10 * 1024 * 1024:
            raise serializers.ValidationError({'link': 'حداکثر اندازه عکس ۱۰ مگابایت است.'})
        try:
            with Image.open(upload) as image:
                if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 40000000:
                    raise ValueError('Unsupported image format or dimensions')
                image.verify()
            upload.seek(0)
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise serializers.ValidationError({'link': 'فایل باید تصویر JPEG، PNG یا WebP معتبر باشد.'})
        with transaction.atomic():
            fillout = SurveyFillOut.objects.select_for_update().filter(
                pk=values['survey_fill_out'].pk, survey__project_id=project_id,
                is_deleted=False,
            ).first()
            if fillout is None:
                raise exceptions.PermissionDenied('پرسشنامه در محدوده پروژه نیست.')
            photo_type = values['survey_photo_type']
            if photo_type.survey_id != fillout.survey_id or not photo_type.is_active:
                raise serializers.ValidationError({'survey_photo_type': 'نوع عکس به این پرسشنامه تعلق ندارد.'})
            assets = AssetAccess(request, self)
            if not (assets.project_wide or fillout.user_id == request.user.pk
                    or (fillout.visit_id and assets.assigned_visits.filter(pk=fillout.visit_id).exists())):
                raise exceptions.PermissionDenied('ثبت عکس برای این پرسشنامه مجاز نیست.')
            if fillout.is_closed or fillout.status == SurveyFillOut.CONFIRMED:
                raise serializers.ValidationError({'survey_fill_out': 'پرسشنامه تأییدشده یا بسته قابل تغییر نیست.'})
            if photo_type.max is not None and SurveyPhoto.objects.filter(
                    survey_fill_out=fillout, survey_photo_type=photo_type, is_deleted=False).count() >= photo_type.max:
                raise serializers.ValidationError({'survey_photo_type': 'سقف تعداد عکس این بخش پر شده است.'})
            link = ArvanStorage().put_file(upload)
            if not link:
                raise serializers.ValidationError({'link': 'ذخیره عکس انجام نشد؛ دوباره تلاش کنید.'})
            photo = SurveyPhoto.objects.create(
                creator=request.user, survey_photo_type=photo_type, survey_fill_out=fillout,
                link=link, latitude=values.get('latitude'), longitude=values.get('longitude'),
                is_favourite=values.get('is_favourite', False),
            )
        return Response(SurveyPhotoSerializer(photo, context={'request': request}).data, status=201)


########################
# SurveyPhoto Upload Ends!
########################


######################
# Phone Verification:
######################

class FillOutPhoneVerificationSerializer(serializers.Serializer):
    survey_fill_out = serializers.PrimaryKeyRelatedField(queryset=SurveyFillOut.objects.all())
    phone_number = serializers.RegexField(r'^\+?\d{10,15}$', max_length=16)


from django.db.models import Q


class FillOutPhoneVerificationRequestView(generics.GenericAPIView, BaseLimiter):
    serializer_class = FillOutPhoneVerificationSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_request'

    def get_queryset(self):
        return self.limit_queryset(FillOutPhoneVerification.objects.none())

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fillout = get_object_or_404(accessible_fillouts(request, self),
                                    pk=serializer.validated_data['survey_fill_out'].pk)
        if fillout.is_closed or not fillout.survey.has_phone_verification:
            raise serializers.ValidationError('تأیید تلفن برای این پرسشنامه فعال نیست.')
        phone = serializer.validated_data['phone_number']
        if SurveyFillOut.objects.filter(survey=fillout.survey, phone_number=phone,
                                        phone_verified=True, is_deleted=False).exclude(pk=fillout.pk).exists():
            raise serializers.ValidationError({'phone_number': 'شماره تلفن قبلاً تأیید شده است.'})
        now = timezone.now()
        recent = FillOutPhoneVerification.objects.filter(survey_fill_out=fillout)
        latest = recent.order_by('-datetime_requested').first()
        if latest and latest.datetime_requested and now - latest.datetime_requested < timedelta(seconds=30):
            return Response({'detail': 'برای ارسال دوباره کمی صبر کنید.'}, status=429)
        if recent.filter(datetime_requested__gte=now - timedelta(hours=1)).count() >= 5:
            return Response({'detail': 'تعداد درخواست کد بیش از حد مجاز است.'}, status=429)
        code = str(secrets.randbelow(90000) + 10000)
        with transaction.atomic():
            recent.filter(consumed_at__isnull=True).update(consumed_at=now, code='', verification_token='')
            challenge = FillOutPhoneVerification.objects.create(
                survey_fill_out=fillout, phone_number=phone, code=make_password(code),
                verification_token=secrets.token_urlsafe(32),
            )
        from notification.modules.notification import Notification
        Notification(to=phone, message_template_key=fillout.survey.sms_text or 'FILLOUT', code=code)
        return Response({'id': challenge.pk, 'verification_token': challenge.verification_token,
                         'phone_number': phone}, status=201)


class FillOutPhoneVerificationCheckCodeSerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True, min_value=1, required=True)
    verification_token = serializers.CharField(write_only=True, required=True)
    code = serializers.RegexField(r'^\d{5}$', write_only=True, required=True)
    phone_number = serializers.RegexField(r'^\+?\d{10,15}$', write_only=True, required=True)
    is_verified = serializers.BooleanField(read_only=True)


class FillOutPhoneVerificationCheckCodeView(generics.GenericAPIView, BaseLimiter):
    serializer_class = FillOutPhoneVerificationCheckCodeSerializer
    permission_classes = [DeleteCreateUpdateGetPermission]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'otp_verify'

    def get_queryset(self):
        return self.limit_queryset(FillOutPhoneVerification.objects.none())

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data
        result = 'invalid'
        with transaction.atomic():
            challenge = FillOutPhoneVerification.objects.select_for_update().filter(pk=fields['id']).first()
            if challenge and challenge.consumed_at is None and challenge.failed_attempts < 3:
                fillout = accessible_fillouts(request, self).filter(
                    pk=challenge.survey_fill_out_id, is_closed=False,
                    survey__has_phone_verification=True).first()
                if fillout:
                    if (challenge.datetime_requested is None or
                            timezone.now() - challenge.datetime_requested > timedelta(minutes=2)):
                        result = 'expired'
                    elif (challenge.phone_number == fields['phone_number'] and
                          compare_digest(challenge.verification_token, fields['verification_token']) and
                          check_password(fields['code'], challenge.code)):
                        fillout.phone_number = challenge.phone_number
                        fillout.phone_verified = True
                        fillout.save(update_fields=['phone_number', 'phone_verified', 'datetime_last_change'])
                        challenge.consumed_at = timezone.now()
                        challenge.code = ''
                        challenge.verification_token = ''
                        challenge.save(update_fields=['consumed_at', 'code', 'verification_token'])
                        result = 'accepted'
                    else:
                        challenge.failed_attempts += 1
                        challenge.save(update_fields=['failed_attempts'])
        if result == 'expired':
            return Response({'detail': 'کد منقضی شده است.'}, status=419)
        if result != 'accepted':
            raise serializers.ValidationError('کد تأیید معتبر نیست.')
        return Response({'is_verified': True})


######################
# Phone Verification Ends!
######################


######################
# change photo location!
######################


class SurveyChangePhotoLocationsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    longitude = serializers.DecimalField(max_digits=22, decimal_places=16)
    latitude = serializers.DecimalField(max_digits=22, decimal_places=16)


class SurveyChangePhotoLocations(generics.GenericAPIView, BaseLimiter):
    serializer_class = SurveyChangePhotoLocationsSerializer

    permission_classes = [DeleteCreateUpdateGetPermission]

    def get_queryset(self):
        return self.limit_queryset(SurveyPhoto.objects.none())

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if not AssetAccess(request, self).project_wide:
            raise exceptions.PermissionDenied('ویرایش گروهی موقعیت عکس نیازمند نقش مدیریتی پروژه است.')
        if len(set(values['ids'])) != len(values['ids']):
            raise serializers.ValidationError({'ids': 'شناسه‌ها باید یکتا باشند.'})
        with transaction.atomic():
            photos = SurveyPhoto.objects.select_for_update().filter(
                pk__in=values['ids'], is_deleted=False,
                survey_photo_type__survey__project_id=AssetAccess(request, self).project_id,
                survey_photo_type__survey_id=F('survey_fill_out__survey_id'),
                survey_fill_out__is_deleted=False,
            )
            if photos.count() != len(values['ids']):
                raise serializers.ValidationError({'ids': 'بخشی از عکس‌ها در پروژه مجاز وجود ندارند.'})
            photos.update(longitude=values['longitude'], latitude=values['latitude'],
                          datetime_last_change=timezone.now())
        return Response({"detail": "ok"})


########################################
# Survey ends!
########################################


########################################
# Public surveys:
########################################

class OuterEntryConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = OuterEntryConfig
        fields = '__all__'
        read_only_fields = ('project',)

    def validate(self, attrs):
        project_id = AssetAccess(self.context['request'], self.context['view']).project_id
        incoming_project = self.context['request'].data.get('project')
        if incoming_project is not None and str(incoming_project) != str(project_id):
            raise serializers.ValidationError({'project': 'پروژه بدنه با پروژه انتخاب‌شده یکسان نیست.'})
        survey = attrs.get('survey', getattr(self.instance, 'survey', None))
        building = attrs.get('building', getattr(self.instance, 'building', None))
        if survey is not None and survey.project_id != project_id:
            raise serializers.ValidationError({'survey': 'پرسشنامه باید در پروژه انتخاب‌شده باشد.'})
        if building is not None and building.project_id != project_id:
            raise serializers.ValidationError({'building': 'ساختمان باید در پروژه انتخاب‌شده باشد.'})
        return attrs


class GenerateQRcodeForOuterSurveyView(generics.RetrieveAPIView):
    def get_queryset(self):
        return OuterEntryConfig.objects.all()

    serializer_class = OuterEntryConfigSerializer

    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        from core.qr import QRCode
        from io import BytesIO
        qr = QRCode(logo_url=self.request.data['logo_url'], code_data=self.request.data['code_data'])
        pill_img = qr.generate_qr_code()
        buffered = BytesIO()
        pill_img.save(buffered, format='PNG')
        from django.http import HttpResponse
        response = HttpResponse(buffered.getvalue(), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="' + str(instance.id) + '.png"'
        return response


class OuterEntryConfigListCreateView(BaseLimiter, generics.ListCreateAPIView):
    def get_queryset(self):
        access = AssetAccess(self.request, self)
        if not access.project_wide:
            return OuterEntryConfig.objects.none()
        return self.limit_queryset(OuterEntryConfig.objects.filter(project_id=access.project_id))

    def perform_create(self, serializer):
        access = AssetAccess(self.request, self)
        if not access.project_wide:
            raise exceptions.PermissionDenied('مدیریت تنظیمات پرسشنامه بیرونی به نقش مدیریتی پروژه نیاز دارد.')
        serializer.save(project_id=access.project_id)

    serializer_class = OuterEntryConfigSerializer

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


class OuterEntryConfigEditsView(BaseLimiter, generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        access = AssetAccess(self.request, self)
        if not access.project_wide:
            return OuterEntryConfig.objects.none()
        return self.limit_queryset(OuterEntryConfig.objects.filter(project_id=access.project_id))

    serializer_class = OuterEntryConfigSerializer

    lookup_field = 'id'

    permission_classes = [
        DeleteCreateUpdateGetPermission,
    ]
