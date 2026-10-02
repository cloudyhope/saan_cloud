from django.urls import path
from url_utility.views import *

URLurlpatterns = [
    path('url_utility/api/v1/plan/list_create/', PlanListCreateView.as_view(), name="PlanListCreateView"),
    path('url_utility/api/v1/short_url/list_create/', ShortUrlListCreateView.as_view(), name="ShortUrlListCreateView"),
    path('url_utility/api/v1/user_plan/list_create/', UserPlanListCreateAPIView.as_view(),
         name="UserPlanListCreateAPIView"),
    path('url_utility/api/v1/click_log/list_create/', ClickLogListCreateAPIView.as_view(),
         name="ClickLogCreateAPIView"),
    path('url_utility/api/v1/plan/edits/<id>/', PlanEditView.as_view(), name="PlanEditView"),
    path('url_utility/api/v1/short_url/edits/<id>/', ShortUrlEditView.as_view(), name="ShortUrlEditView"),
    path('url_utility/api/v1/user_plan/edits/<id>/', UserPlanEditView.as_view(), name="UserPlanEditView"),
    path('url_utility/api/v1/click_log/edits/<id>/', ClickLogEditView.as_view(), name="ClickLogEditView"),
    path('s/<str:short_url>/', GetOriginalUrl.as_view(), name='get_original_url'),
]
