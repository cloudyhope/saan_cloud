from django.shortcuts import redirect
from rest_framework.views import APIView

from url_utility.serializers import *
from url_utility.models import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import generics
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from core.generics import BaseLimiter


class PlanListCreateView(generics.ListCreateAPIView, BaseLimiter):
    serializer_class = PlanSerializer
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    def get_queryset(self):
        return Plan.objects.all()

    permission_classes = [
        IsAuthenticated
    ]

    filterset_fields = '__all__'
    ordering_fields = '__all__'


class ShortUrlListCreateView(generics.ListCreateAPIView, BaseLimiter):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        userplan = UserPlan.objects.filter(user=self.request.user).first()
        return ShortUrl.objects.filter(user_plan=userplan).all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ShortUrlSerializer
        else:
            return ShortUrlOnlySerializer

    filterset_fields = '__all__'
    ordering_fields = '__all__'


class UserPlanListCreateAPIView(generics.ListCreateAPIView, BaseLimiter):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return UserPlan.objects.filter(user=self.request.user).all()

    filterset_fields = '__all__'
    ordering_fields = '__all__'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserPlanSerializer
        else:
            return UserPlanOnlySerializer


class ClickLogListCreateAPIView(generics.ListCreateAPIView, BaseLimiter):
    pagination_class = LimitOffsetPagination

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return ClickLog.objects.all()

    filterset_fields = '__all__'
    ordering_fields = '__all__'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClickLogSerializer
        else:
            return ClickLogOnlySerializer


class PlanEditView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()

    permission_classes = [
        IsAuthenticated
    ]

    lookup_field = 'id'


class ShortUrlEditView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    serializer_class = ShortUrlOnlySerializer
    queryset = ShortUrl.objects.filter(is_deleted=False)

    queryset = ShortUrl.objects.filter(is_deleted=False)

    permission_classes = [
        IsAuthenticated,
    ]

    lookup_field = 'id'


class UserPlanEditView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    serializer_class = UserPlanSerializer

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        IsAuthenticated,
    ]
    queryset = UserPlan.objects.filter(is_deleted=False)

    lookup_field = 'id'


class ClickLogEditView(generics.RetrieveUpdateDestroyAPIView, BaseLimiter):
    serializer_class = ClickLogOnlySerializer

    def paginate_queryset(self, queryset):
        print(self.paginator)
        if self.paginator and self.request.query_params.get(self.paginator.limit_query_param, None) is None:
            return None
        return super().paginate_queryset(queryset)

    permission_classes = [
        IsAuthenticated,
    ]
    queryset = ClickLog.objects.all()

    lookup_field = 'id'


class GetOriginalUrl(APIView, BaseLimiter):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request, short_url: str):
        short_url = short_url.replace('/', '')
        ip_address = request.META.get('REMOTE_ADDR')
        agent = request.META.get('HTTP_USER_AGENT')
        user = User.objects.filter(id=request.user.id).first()
        userplan = UserPlan.objects.filter(user_plan=user).first()
        try:
            short_url_obj = ShortUrl.objects.filter(url=short_url, is_deleted=False, is_active=True).first()
            ClickLog.objects.create(user_plan=userplan, short_url=short_url_obj, ip_address=ip_address,
                                    user_agent=agent).save()
            long = short_url_obj.long_url
            return redirect(f"{long}")
        except:
            return redirect("https://koosha.ir/")


class ShortUrlMicroListCreateView(generics.CreateAPIView):
    serializer_class = ShortURLMicroServiceGetSerializer

    def post(self, request, *args, **kwargs):
        request.data['user_plan'] = UserPlan.objects.filter(user=None).first().id
        return self.create(request, *args, **kwargs)

    permission_classes = [
        AllowAny,
    ]

    ordering_fields = '__all__'