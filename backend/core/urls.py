"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from visit.views import *
from visit.client_dashboard import ClientDashboardAPIView
from visit.client_visit_detail import ClientVisitDetailAPIView
from visit.client_feedback import ClientVisitFeedbackAPIView
from visit.client_support import (
    ClientSupportTicketsAPIView, ClientSupportTicketDetailAPIView,
    ExpertSupportTicketsAPIView, ExpertSupportTicketDetailAPIView,
)
from visit.report_pdf import ClientVisitReportPDFAPIView
from notification.in_app import (
    InAppNotificationListView, InAppNotificationReadView,
    InAppNotificationReadAllView,
)
from core.media_access import local_uploaded_media_read
from visit.management_api import BuildingManagementTransferAPIView
from visit.dashboard_api import AdminDashboardView
from visit.field_ops import (AdminVisitFieldOpsView, ClientVisitChatView, PromoterEarningsView, PromoterVisitChatView,
                             VisitAssetContextView, VisitAssignmentResponseView)
from visit.maintenance import MaintenancePlanDetailView, MaintenancePlanListCreateView
from visit.assignment_api import (AssignmentApplyView, AssignmentExpertView, AssignmentOverviewView,
                                  AssignmentPlanView, AssignmentRequirementView, AssignmentSettingView,
                                  AssignmentSkillDetailView, AssignmentSkillListView, AssignmentTimeOffDetailView,
                                  AssignmentTimeOffView)
from warehouse.part_requests import (PartRequestDecisionView, PartRequestListView, PromoterPartRequestCancelView,
                                     PromoterPartRequestView)
from visit.priority_api import (PriorityEntityView, PriorityFactorDetailView, PriorityFactorListCreateView,
                                PriorityRankingView)
from visit.service_case_api import (
    WarrantyContractListCreateView, WarrantyEligibleProductsView, WarrantyClaimListCreateView,
    WarrantyClaimDecisionView, RepairCaseListCreateView, RepairCaseDetailView,
    RepairCaseTransitionView, RepairCaseLoanerView, RepairCaseMaterialView,
)
from auth_app.views import *
from survey.views import *
from config.views import *
from core import settings
from utils.views import *
from wallet.views import *


from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

from warehouse.views import *
from warehouse.opening import WareOpeningStockView

schema_view = get_schema_view(
    openapi.Info(
        title="core API",
        default_version='v1 ',
        description="",
        contact=openapi.Contact(email="mmzadfalah@gmail.com"),
        USE_X_FORWARDED_HOST = True,
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('core/api/admin/dashboard/', AdminDashboardView.as_view(), name='AdminDashboardView'),
    path('core/api/promoter/visit/<int:id>/assignment/', VisitAssignmentResponseView.as_view(), name='VisitAssignmentResponseView'),
    path('core/api/promoter/visit/<int:id>/assets/', VisitAssetContextView.as_view(), name='VisitAssetContextView'),
    path('core/api/promoter/visit/<int:id>/chat/', PromoterVisitChatView.as_view(), name='PromoterVisitChatView'),
    path('core/api/promoter/visit/<int:id>/parts/', PromoterPartRequestView.as_view(), name='PromoterPartRequestView'),
    path('core/api/promoter/part_request/<int:id>/cancel/', PromoterPartRequestCancelView.as_view(), name='PromoterPartRequestCancelView'),
    path('core/api/promoter/visit/earnings/', PromoterEarningsView.as_view(), name='PromoterEarningsView'),
    path('core/api/client/visits/<int:id>/chat/', ClientVisitChatView.as_view(), name='ClientVisitChatView'),
    path('core/api/admin/visit/<int:id>/field_ops/', AdminVisitFieldOpsView.as_view(), name='AdminVisitFieldOpsView'),
    path('core/api/admin/assignment/overview/', AssignmentOverviewView.as_view(), name='AssignmentOverviewView'),
    path('core/api/admin/assignment/plan/', AssignmentPlanView.as_view(), name='AssignmentPlanView'),
    path('core/api/admin/assignment/apply/', AssignmentApplyView.as_view(), name='AssignmentApplyView'),
    path('core/api/admin/assignment/experts/<int:user_id>/', AssignmentExpertView.as_view(), name='AssignmentExpertView'),
    path('core/api/admin/assignment/experts/<int:user_id>/time_off/', AssignmentTimeOffView.as_view(), name='AssignmentTimeOffView'),
    path('core/api/admin/assignment/time_off/<int:id>/', AssignmentTimeOffDetailView.as_view(), name='AssignmentTimeOffDetailView'),
    path('core/api/admin/assignment/skills/', AssignmentSkillListView.as_view(), name='AssignmentSkillListView'),
    path('core/api/admin/assignment/skills/<int:id>/', AssignmentSkillDetailView.as_view(), name='AssignmentSkillDetailView'),
    path('core/api/admin/assignment/requirements/<int:visit_type_id>/', AssignmentRequirementView.as_view(), name='AssignmentRequirementView'),
    path('core/api/admin/assignment/settings/', AssignmentSettingView.as_view(), name='AssignmentSettingView'),
    path('core/api/admin/maintenance_plans/', MaintenancePlanListCreateView.as_view(), name='MaintenancePlanListCreateView'),
    path('core/api/admin/maintenance_plans/<int:id>/', MaintenancePlanDetailView.as_view(), name='MaintenancePlanDetailView'),
    path('api/warehouse/v1/part_requests/', PartRequestListView.as_view(), name='PartRequestListView'),
    path('api/warehouse/v1/part_requests/<int:id>/decision/', PartRequestDecisionView.as_view(), name='PartRequestDecisionView'),
    path('core/api/admin/priority/factors/', PriorityFactorListCreateView.as_view(), name='PriorityFactorListCreateView'),
    path('core/api/admin/priority/factors/<int:id>/', PriorityFactorDetailView.as_view(), name='PriorityFactorDetailView'),
    path('core/api/admin/priority/entity/<str:target>/<int:id>/', PriorityEntityView.as_view(), name='PriorityEntityView'),
    path('core/api/admin/priority/ranking/', PriorityRankingView.as_view(), name='PriorityRankingView'),
    path('core/api/notifications/', InAppNotificationListView.as_view(), name='InAppNotificationListView'),
    path('core/api/notifications/read-all/', InAppNotificationReadAllView.as_view(), name='InAppNotificationReadAllView'),
    path('core/api/notifications/<int:id>/read/', InAppNotificationReadView.as_view(), name='InAppNotificationReadView'),
    path('core/api/client/visits/<id>/report.pdf', ClientVisitReportPDFAPIView.as_view(), name='ClientVisitReportPDFAPIView'),
    path('core/api/media/<str:token>/', local_uploaded_media_read, name='LocalUploadedMediaReadView'),
    path('core/api/client/support/tickets/', ClientSupportTicketsAPIView.as_view(), name='ClientSupportTicketsAPIView'),
    path('core/api/client/support/tickets/<id>/', ClientSupportTicketDetailAPIView.as_view(), name='ClientSupportTicketDetailAPIView'),
    path('core/api/expert/support/tickets/', ExpertSupportTicketsAPIView.as_view(), name='ExpertSupportTicketsAPIView'),
    path('core/api/expert/support/tickets/<id>/', ExpertSupportTicketDetailAPIView.as_view(), name='ExpertSupportTicketDetailAPIView'),
    path('core/api/warranty/contracts/', WarrantyContractListCreateView.as_view(), name='WarrantyContractListCreateView'),
    path('core/api/warranty/eligible_products/', WarrantyEligibleProductsView.as_view(), name='WarrantyEligibleProductsView'),
    path('core/api/warranty/claims/', WarrantyClaimListCreateView.as_view(), name='WarrantyClaimListCreateView'),
    path('core/api/warranty/claims/<id>/decision/', WarrantyClaimDecisionView.as_view(), name='WarrantyClaimDecisionView'),
    path('core/api/repair/cases/', RepairCaseListCreateView.as_view(), name='RepairCaseListCreateView'),
    path('core/api/repair/cases/<id>/', RepairCaseDetailView.as_view(), name='RepairCaseDetailView'),
    path('core/api/repair/cases/<id>/materials/', RepairCaseMaterialView.as_view(), name='RepairCaseMaterialView'),
    path('core/api/repair/cases/<id>/transition/', RepairCaseTransitionView.as_view(), name='RepairCaseTransitionView'),
    path('core/api/repair/cases/<id>/loaner/', RepairCaseLoanerView.as_view(), name='RepairCaseLoanerView'),
    path('coreadminurl/', admin.site.urls),

]

project_urlpatterns = [
    path('core/api/admin/building_management/transfer/', BuildingManagementTransferAPIView.as_view()),
    #health
    path('health/', HealthCheck.as_view(), name='HealthCheck'),

    path('core/api/province/list/', ProviceListAPIView.as_view(), name="ProviceListAPIView"),
    path('core/api/city/list/', CityListAPIView.as_view(), name="CityListAPIView"),
    path('core/api/active_city/list/', ActiveCityListView.as_view(), name="ActiveCityListView"),

    path('core/api/region/list_create/', RegionListCreateView.as_view(), name="RegionListCreateView"),
    path('core/api/region/edits/<id>/', RegionEditsView.as_view(), name="RegionEditsView"),
    path('core/api/district/list_create/', DistrictListCreateView.as_view(), name="DistrictListCreateView"),
    path('core/api/district/edits/<id>/', DistrictEditsView.as_view(), name="DistrictEditsView"),






    path('core/api/auth/otp/request/', RequestOTP.as_view(), name="RequestOTP"),
    path('core/api/auth/otp/verify/', VerifyPhoneNumberOTPAPIView.as_view(), name="VerifyPhoneNumberOTPAPIView"),

    path('core/api/auth/user_detail/', UserDetailView.as_view(), name="UserDetailView"),

    path('core/api/auth/me/', RoleAssignmentListView.as_view(), name="RoleAssignmentListView"),
    path('core/api/auth/roles/list_create/', RoleListView.as_view(), name="RoleListView"),

    path('core/api/conf/report_cat_list/', ReportCategoryListAPIView.as_view(), name="ReportCategoryListAPIView"),


    #signIn
    path('core/api/auth/document_photo_edits/<id>/', DocumentPhotoEditAPIView.as_view(), name="DocumentPhotoEditAPIView"),
    path('core/api/auth/document_photo/list_create/', DocumentsPhotoListCreateView.as_view(), name="DocumentsPhotoListCreateView"),
    path('core/api/auth/document/list_create/', DocumentsListCreteView.as_view(), name="DocumentsListCreteView"),
    #end signIn


    path('core/api/visit/retrieve/<id>/', VisitDetailRetriveAPIView.as_view(), name="VisitDetailRetriveAPIView"),

    path('core/api/promoter/open_visits/list/', PromoterVisitsAPIView.as_view(), name="PromoterVisitsAPIView"),
    path('core/api/promoter/open_visit/change_status/<id>/', PromoterVisitStatusChangeAPIView.as_view(), name="PromoterVisitStatusChangeAPIView"),

    path('core/api/promoter/open_visit/upload_image/', PromoterUploadImageAPIView.as_view(), name="PromoterUploadImageAPIView"),

    path('core/api/promoter/questions/list/visit/<visit_id>/', QuestionListForVisitsAPIView.as_view(), name="QuestionListForVisitsAPIView"),


    path('core/api/promoter/visit_page_settings/<visit_id>/', FrontVisitPageSettingsView.as_view(), name="FrontVisitPageSettingsView"),

    # Survey:
    path('core/api/promoter/survey_question/list/<survey_fill_out>/', PromoterSurveyQuestionList.as_view(), name="PromoterSurveyQuestionList"),

    path('core/api/promoter/survey_page_settings/<survey_fill_out_id>/', FrontSurveyPageSettingsView.as_view(), name="FrontSurveyPageSettingsView"),
    path('core/api/promoter/answer_to_survey_question/', PromoterAnswersSurveyQuestionsView.as_view(), name="PromoterAnswersSurveyQuestionsView"),
    path('core/api/promoter/upload_survey_photo/', PromoterUploadSurveyImageAPIView.as_view(), name="PromoterUploadSurveyImageAPIView"),

    path('core/api/promoter/verification_code/request/', FillOutPhoneVerificationRequestView.as_view(), name="FillOutPhoneVerificationRequestView"),
    path('core/api/promoter/verification_code/validate/', FillOutPhoneVerificationCheckCodeView.as_view(), name="FillOutPhoneVerificationCheckCodeView"),



    path('core/api/promoter/survey_report_category/list_create/', SurveyReportCategoryListCreateView.as_view(), name="SurveyReportCategoryListCreateView"),
    path('core/api/admin/survey_report_category/list_create/', SurveyReportCategoryListCreateView.as_view(), name="SurveyReportCategoryListCreateView"),
    path('core/api/promoter/survey_question_type/list_create/', SurveyQuestionTypeListCreateView.as_view(), name="SurveyQuestionTypeListCreateView"),
    path('core/api/admin/survey_question_type/list_create/', SurveyQuestionTypeListCreateView.as_view(), name="SurveyQuestionTypeListCreateView"),
    path('core/api/promoter/survey_question/list_create/', SurveyQuestionListCreateView.as_view(), name="SurveyQuestionListCreateView"),
    path('core/api/admin/survey_question/list_create/', SurveyQuestionListCreateView.as_view(), name="SurveyQuestionListCreateView"),
    path('core/api/promoter/survey/list_create/', SurveyListCreateView.as_view(), name="SurveyListCreateView"),
    path('core/api/admin/survey/list_create/', SurveyListCreateView.as_view(), name="SurveyListCreateView"),
    path('core/api/promoter/survey_fill_out/list_create/', SurveyFillOutListCreateView.as_view(), name="SurveyFillOutListCreateView"),
    path('core/api/admin/survey_fill_out/list_create/', SurveyFillOutListCreateView.as_view(), name="SurveyFillOutListCreateView"),
    path('core/api/promoter/survey_answer/list_create/', SurveyAnswerListCreateView.as_view(), name="SurveyAnswerListCreateView"),
    path('core/api/admin/survey_answer/list_create/', SurveyAnswerListCreateView.as_view(), name="SurveyAnswerListCreateView"),
    path('core/api/promoter/survey_photo_type/list_create/', SurveyPhotoTypeListCreateView.as_view(), name="SurveyPhotoTypeListCreateView"),
    path('core/api/admin/survey_photo_type/list_create/', SurveyPhotoTypeListCreateView.as_view(), name="SurveyPhotoTypeListCreateView"),
    path('core/api/promoter/survey_photo/list_create/', SurveyPhotoListCreateView.as_view(), name="SurveyPhotoListCreateView"),
    path('core/api/admin/survey_photo/list_create/', SurveyPhotoListCreateView.as_view(), name="SurveyPhotoListCreateView"),
    path('core/api/promoter/survey_report_category/edits/<id>/', SurveyReportCategoryEditsView.as_view(), name="SurveyReportCategoryEditsView"),
    path('core/api/admin/survey_report_category/edits/<id>/', SurveyReportCategoryEditsView.as_view(), name="SurveyReportCategoryEditsView"),
    path('core/api/promoter/survey_question_type/edits/<id>/', SurveyQuestionTypeEditsView.as_view(), name="SurveyQuestionTypeEditsView"),
    path('core/api/admin/survey_question_type/edits/<id>/', SurveyQuestionTypeEditsView.as_view(), name="SurveyQuestionTypeEditsView"),
    path('core/api/promoter/survey_question/edits/<id>/', SurveyQuestionEditsView.as_view(), name="SurveyQuestionEditsView"),
    path('core/api/admin/survey_question/edits/<id>/', SurveyQuestionEditsView.as_view(), name="SurveyQuestionEditsView"),
    path('core/api/promoter/survey/edits/<id>/', SurveyEditsView.as_view(), name="SurveyEditsView"),
    path('core/api/admin/survey/edits/<id>/', SurveyEditsView.as_view(), name="SurveyEditsView"),
    path('core/api/promoter/survey_fill_out/edits/<id>/', SurveyFillOutEditsView.as_view(), name="SurveyFillOutEditsView"),
    path('core/api/admin/survey_fill_out/edits/<id>/', SurveyFillOutEditsView.as_view(), name="SurveyFillOutEditsView"),
    path('core/api/promoter/survey_answer/edits/<id>/', SurveyAnswerEditsView.as_view(), name="SurveyAnswerEditsView"),
    path('core/api/admin/survey_answer/edits/<id>/', SurveyAnswerEditsView.as_view(), name="SurveyAnswerEditsView"),
    path('core/api/promoter/survey_photo_type/edits/<id>/', SurveyPhotoTypeEditsView.as_view(), name="SurveyPhotoTypeEditsView"),
    path('core/api/admin/survey_photo_type/edits/<id>/', SurveyPhotoTypeEditsView.as_view(), name="SurveyPhotoTypeEditsView"),
    path('core/api/promoter/survey_photo/edits/<id>/', SurveyPhotoEditsView.as_view(), name="SurveyPhotoEditsView"),
    path('core/api/admin/survey_photo/edits/<id>/',SurveyPhotoEditsView.as_view(), name="SurveyPhotoEditsView"),

    # Survey Ends!

    path('core/api/admin/retrive_photo_type/<id>/', PhotoTypeRetrieveView.as_view(), name="PhotoTypeRetrieveView"),



    path('core/api/promoter/answer_to_question/', PromoterAnswersQuestionsView.as_view(), name="PromoterAnswersQuestionsView"),

    path('core/api/promoter/visit/history/', PromoterVisistsHistory.as_view(), name="PromoterVisistsHistory"),

    path('core/api/promoter/visit/photo_history/', ListPhotoForVisitView.as_view(), name="ListPhotoForVisitView"),

    path('core/api/promoter/visit/delete_photo/<id>/', PromoterDeletePhotoView.as_view(), name="PromoterDeletePhotoView"),

#     path('core/api/admin/outlet_list/', AdminOutletListView.as_view(), name="AdminOutletListView"),
    path('core/api/admin/promoter_list/', AdminPromotersList.as_view(), name="AdminPromotersList"),
    path('core/api/admin/create_visits/', AdminCreateVisitsView.as_view(), name="AdminCreateVisitsView"),
    path('core/api/admin/visit_list/', AdminVisitsListView.as_view(), name="AdminVisitsListView"),
    path('core/api/admin/visit_edit/<id>/', AdminUpdateVisitView.as_view(), name="AdminUpdateVisitView"),
    path('core/api/admin/visit_status_change/<id>/', AdminUpdateVisitStatusView.as_view(), name="AdminUpdateVisitStatusView"),
    path('core/api/admin/answer_list/', AdminAnswerListView.as_view(), name="AdminAnswerListView"),
    path('core/api/admin/answer_edit/<id>/', AdminAnswerEdistsView.as_view(), name="AdminAnswerEdistsView"),
    path('core/api/admin/photo_list', AdminPhotoListView.as_view(), name="AdminPhotoListView"),
    path('core/api/admin/photo_edit/<id>/', AdminPhotoEditsView.as_view(), name="AdminPhotoEditsView"),

    path('core/api/admin/fo_answers_list/', FOAnswerList.as_view(), name="FOAnswerList"),

    path('core/api/admin/supervision_visit_status_change/<id>/', AdminUpdateSupervisionVisitStatusView.as_view(), name="AdminUpdateSupervisionVisitStatusView"),


    path('core/api/admin/vist/place_comment/<id>/', PlaceVisitCommentView.as_view(), name="PlaceVisitCommentView"),


    # action_plan

    path('core/api/admin/action_plan/create/', AdminActionPlanCreate.as_view(), name="AdminActionPlanCreate"),
    path('core/api/service_request/create/', ServiceRequestCreate.as_view(), name="ServiceRequestCreate"),
    path('core/api/admin/action_plan/list/', AdminActionPlanList.as_view(), name="AdminActionPlanList"),
    path('core/api/admin/action_plan/edits/<id>/', AdminActionPlanEdits.as_view(), name="AdminActionPlanEdits"),
    path('core/api/admin/action_plan/bulk_update/', AdminActionPlanBulkEdits.as_view(), name="AdminActionPlanBulkEdits"),


    # visit type:
    path('core/api/admin/visit_type/list_create/', VisitTypeListCreateView.as_view(), name="VisitTypeListCreateView"),
    path('core/api/admin/visit_type/edits/<id>/', VisitTypeEditsView.as_view(), name="VisitTypeEditsView"),


#     path('core/api/admin/outlet_cat_list/', AdminOutletCategoryListView.as_view(), name="AdminOutletCategoryListView"),
    # path('core/api/admin/outlet_list/', AdminOutletListView.as_view(), name="AdminPhotoEditsView"),


    path('core/api/census/list/', CensusListView.as_view(), name="CensusListView"),
    path('core/api/census/aggregate/', CensusAggregateView.as_view(), name="CensusAggregateView"),

    path('core/api/admin/photo_type_list/', PhotoTypeListView.as_view(), name="PhotoTypeListView"),

    path('core/api/admin/census/filter_values/', CensusValuesView.as_view(), name="CensusValuesView"),
    # path('core/api/admin/census/xlsx_export/', CensusExportView.as_view(), name="CensusExportView"),

    path('core/api/admin/alarm_list/', FoulAlarmListView.as_view(), name="FoulAlarmListView"),
    path('core/api/admin/alarm_edit/<id>/', FoulAlarmRetriveUpdateDestroyView.as_view(), name="FoulAlarmRetriveUpdateDestroyView"),


    path('core/api/admin/ticket/list_create/', TicketListCreateView.as_view(), name="TicketListCreateView"),
    path('core/api/admin/ticket_message/list_create/', TicketMessageListCreateView.as_view(), name="TicketMessageListCreateView"),
    path('core/api/admin/ticket_message_attachment/list_create/', TicketMessageAttachmentListCreateView.as_view(), name="TicketMessageAttachmentListCreateView"),

    path('core/api/admin/ticket/edits/<id>/', TicketRetriveUpdateDestroyView.as_view(), name="TicketRetriveUpdateDestroyView"),
    path('core/api/admin/ticket_message/edits/<id>/', TicketMessageRetriveUpdateDestroyView.as_view(), name="TicketMessageRetriveUpdateDestroyView"),
    path('core/api/admin/ticket_message_attachment/edits/<id>/', TicketMessageAttachmentRetriveUpdateDestroyView.as_view(), name="TicketMessageAttachmentRetriveUpdateDestroyView"),

    path('core/api/admin/ticket_message_attachment/upload/', TicketUploadAttachmentAPIView.as_view(), name="TicketUploadAttachmentAPIView"),


    # Admin Menu:
    path('core/api/admin/menu/list/', AdminMenuListView.as_view(), name="AdminMenuListView"),
    path('core/api/admin/menu/edits/<id>/', AdminMenuRetriveUpdateDestroyView.as_view(), name="AdminMenuRetriveUpdateDestroyView"),

    # Project List:
    path('core/api/admin/project_list/', ProjectRoleAssignmentListView.as_view(), name="ProjectRoleAssignmentListView"),
    path('core/api/promoter/project_list/', ProjectRoleAssignmentListView.as_view(), name="ProjectRoleAssignmentListView"),

    path('core/api/active_project/retrieve/<project>/', ActiveProjectRetriveView.as_view(), name="ActiveProjectRetriveView"),

    path('core/api/admin/role_assignment/list/', RolesAssignmentCustomizableListView.as_view(), name="RolesAssignmentCustomizableListView"),
    path('core/api/admin/role_assignment/delete/<id>/', RolesAssignmentDeleteListView.as_view(), name="RolesAssignmentDeleteListView"),


    path('config/parse_excel/', ParseXlsxAPIView.as_view(), name="ParseXlsxAPIView"),
    path('config/files/list_create/', UploadedFileListCreateView.as_view(), name="UploadedFileListCreateView"),
    path('core/api/config/files/edits/<id>/', UploadedFileEditView.as_view(), name="UploadedFileEditView"),

    path('core/api/auth/supervisor/list_create/', SupervisorListCreateView.as_view(), name="SupervisorListCreateView"),
    path('core/api/auth/supervisor/edits/<id>/', SupervisorEditsView.as_view(), name="SupervisorEditsView"),
    path('core/api/auth/active_supervisors/',SupervisorOfPromoterCheckView.as_view(), name="SupervisorOfPromoterCheckView"),

    path('core/api/supervisor/supervision_visits/list/', SupervisionVisitsListView.as_view(), name="SupervisionVisitsListView"),


    path('core/api/admin/visit_answer/create/', AdminAnswerCreateAPIView.as_view(), name="AdminAnswerCreateAPIView"),



    # change photos locations:
    path('core/api/admin/survey/change_photo_location/', SurveyChangePhotoLocations.as_view(), name="SurveyChangePhotoLocations"),
    path('core/api/admin/visit/change_photo_location/', VisitChangePhotoLocations.as_view(), name="VisitChangePhotoLocations"),

    path('core/api/promoter/known_image/list_create/', AuthenticationImageListCreateView.as_view(), name="AuthenticationImageListCreateView"),
    path('core/api/promoter/known_image/edits/<id>/', AuthenticationImageEditView.as_view(), name="AuthenticationImageEditView"),

    # path('test/', Test.as_view(), name="test"),

    # QR Code:



    path('config/outer_survey_config/list_create/', OuterEntryConfigListCreateView.as_view(), name="OuterEntryConfigListCreateView"),
    path('config/outer_survey_config/edits/<id>/', OuterEntryConfigEditsView.as_view(), name="OuterEntryConfigEditsView"),


#

    path('core/api/admin/more_info_key/list_create/', MoreInfoKeyListCreateView.as_view(), name="MoreInfoKeyListCreateView"),
    path('core/api/admin/outlet_more_info/list_create/', MoreInfoListCreateView.as_view(), name="MoreInfoListCreateView"),

#     path('core/api/admin/outlet_with_more_info/create/', AdminOutletCreateView.as_view(), name="AdminOutletCreateView"),
#     path('core/api/admin/outlet_with_more_info/edits/<id>/', AdminOutletEditsView.as_view(), name="AdminOutletEditsView"),

    #PASSWORD ATHENTICATION:
    path('auth/api/v1/auth/set-password/', SetPasswordForUser.as_view(), name="SetPasswordForUser"),

    path('api/v1/username/password/token/', TokenObtainPairView.as_view(), name='TokenObtainPairView'),
    path('api/v1/username/password/refresh/', TokenRefreshView.as_view(), name='TokenRefreshView'),
    path('api/v1/username/password/logout/', TokenBlacklistView.as_view(), name='TokenBlacklistView'),



    # Face Recognition Result:


    # Authentication Management Services:
    path('api/auth/v1/user/inquiry/', UserInquiryView.as_view(), name='UserInquiryView'),
    path('api/auth/v1/user/management/', UserManagementView.as_view(), name='UserManagementView'),
    # path('api/auth/v1/user/result/', FrResultView.as_view(), name='FrResultView'),


        # Wallet:
    path('wallet/currency/list_create/', CurrencyListCreateView.as_view(), name="CurrencyListCreateView"),
    path('wallet/layer/list_create/', LayerListCreateView.as_view(), name="LayerListCreateView"),
    path('wallet/wallet_type/list_create/', WalletTypeListCreateView.as_view(), name="WalletTypeListCreateView"),
    path('wallet/transaction_type/list_create/', TransactionTypeListCreateView.as_view(),
         name="TransactionTypeListCreateView"),
    path('wallet/allowed_transaction_rule/list_create/', AllowedTransactionRuleListCreateView.as_view(),
         name="AllowedTransactionRuleListCreateView"),

    path('wallet/transaction_line_type/list_create/', WalletTransactionLineTypeListCreateView.as_view(),
         name="WalletTransactionLineTypeListCreateView"),

    path('wallet/currency/edits/<id>/', CurrencyEditsView.as_view(), name="CurrencyEditsView"),
    path('wallet/layer/edits/<id>/', LayerEditsView.as_view(), name="LayerEditsView"),
    path('wallet/wallet_type/edits/<id>/', WalletTypeEditsView.as_view(), name="WalletTypeEditsView"),
    path('wallet/transaction_type/edits/<id>/', TransactionTypeEditsView.as_view(), name="TransactionTypeEditsView"),
    path('wallet/allowed_transaction_rule/edits/<id>/', AllowedTransactionRuleEditsView.as_view(),
         name="AllowedTransactionRuleEditsView"),

    path('wallet/transaction_line_type/edits/<id>/', WalletTransactionLineTypeEditsView.as_view(),
         name="WalletTransactionLineTypeEditsView"),

    path('wallet/get_signature/', WalletGetSignatureView.as_view(), name="WalletGetSignatureView"),


    # Wallet tools:


    path('wallet/transaction/user_balance/', WalletTransactionUserBalance.as_view(),
         name="WalletTransactionUserBalanceView"),

    # invoice:
    path('wallet/invoice/expert/list_create/', WalletInvoiceExpertListCreateView.as_view(),
         name="WalletInvoiceExpertListCreateView"),
    path('wallet/invoice/get_qr_code/<id>/', WalletInvoiceGetQRCodeView.as_view(), name="WalletInvoiceGetQRCodeView"),
    path('wallet/invoice/client/retrieve/<id>/', WalletInvoiceClientRetrieveView.as_view(),
         name="WalletInvoiceClientRetrieve"),
    path('wallet/invoice/code_request/', WalletInvoiceCodeRequestView.as_view(), name="WalletInvoiceCodeRequestView"),
    path('wallet/invoice/code_validate/', WalletInvoiceCodeValidateView.as_view(),
         name="WalletInvoiceCodeValidateView"),

    # WalletReceipt
    path('wallet/api/v1/wallet_receipt/retrieve/<id>/', WalletReceiptRetrieve.as_view(), name="WalletReceiptRetrieve"),

    # wallet transaction line list
    path('wallet/api/user_wallet_transaction_line/list/', UserWalletTransactionLineList.as_view(),
         name='UserWalletTransactionLineList'),



    # WareHouse
    path('api/warehouse/v1/unit/list_create/', UnitListCreateView.as_view(), name='UnitListCreateView'),
    path('api/warehouse/v1/ware/list_create/', WareListCreateView.as_view(), name='WareListCreateView'),
    path('api/warehouse/v1/ware/opening_stock/', WareOpeningStockView.as_view(), name='WareOpeningStockView'),
    path('api/warehouse/v1/location/list_create/', WarehouseLocationListCreateView.as_view(), name='WarehouseLocationListCreateView'),
    path('api/warehouse/v1/transaction/list_create/', WarehouseTransactionListCreateView.as_view(), name='WarehouseTransactionListCreateView'),
    path('api/warehouse/v1/transaction_line_type/list_create/', TransactionLineTypeListCreateView.as_view(), name='TransactionLineTypeListCreateView'),
    path('api/warehouse/v1/transaction_line/list_create/', WarehouseTransactionLineListCreateView.as_view(), name='WarehouseTransactionLineListCreateView'),
    path('api/warehouse/v1/ware_type/list_create/', WareTypeListCreateView.as_view(), name='WareTypeListCreateView'),
    path('api/warehouse/v1/ware_visit_type/list_create/', WareVisitTypeListCreateView.as_view(), name='WareVisitTypeListCreateView'),
    path('api/warehouse/v1/location_personnel/list_create/', WarehouseLocationPersonnelListCreateView.as_view(), name='WarehouseLocationPersonnelListCreateView'),
    path('api/warehouse/v1/location_personnel/edits/<id>/', WarehouseLocationPersonnelEditsView.as_view(), name='WarehouseLocationPersonnelEditsView'),


    # Aggregated
    path('api/warehouse/v1/aggregated/ware/list_create/', WareAggregatedListCreateView.as_view(), name='WareAggregatedListCreateView'),
    path('api/warehouse/v1/aggregated/location/list_create/', WarehouseLocationAggregatedListCreateView.as_view(), name='WarehouseLocationAggregatedListCreateView'),
    path('api/warehouse/v1/aggregated/user/list/', WarehouseStockAggregatedByUserListView.as_view(), name='WarehouseStockAggregatedByUserListView'),
    path('api/warehouse/v1/aggregated/user_or_location/retrieve/<id>/', WareDistributionView.as_view(), name='WareDistributionView'),
    path('api/warehouse/v1/aggregated/visit_page_settings/', WareVisitSettingsView.as_view(), name='WareVisitSettingsView'),


    # Edits:

    path('api/warehouse/v1/unit/edits/<id>/', UnitEditsView.as_view(), name='UnitEditsView'),
    path('api/warehouse/v1/ware/edits/<id>/', WareEditsView.as_view(), name='WareEditsView'),
    path('api/warehouse/v1/location/edits/<id>/', WarehouseLocationEditsView.as_view(), name='WarehouseLocationEditsView'),
    path('api/warehouse/v1/transaction/edits/<id>/', WarehouseTransactionEditsView.as_view(), name='WarehouseTransactionEditsView'),
    path('api/warehouse/v1/transaction_line_type/edits/<id>/', TransactionLineTypeEditsView.as_view(), name='TransactionLineTypeEditsView'),
    path('api/warehouse/v1/transaction_line/edits/<id>/', WarehouseTransactionLineEditsView.as_view(), name='WarehouseTransactionLineEditsView'),
    path('api/warehouse/v1/ware_type/edits/<id>/', WareTypeEditsView.as_view(), name='WareTypeEditsView'),
    path('api/warehouse/v1/ware_visit_type/edits/<id>/', WareVisitTypeEditsView.as_view(), name='WareVisitTypeEditsView'),


    path('api/warehouse/v1/ware_transaction/ez_create/', WareTransactionEzCreateView.as_view(), name='WareTransactionEzCreateView'),

    # End WareHouse

    #VISIT RATE:

    path('core/api/v1/visit_rate/list_create/', VisitRateListCreateView.as_view(), name='VisitRateListCreateView'),
    path('core/api/v1/visit_rate/edits/<id>/', VisitRateEditsView.as_view(), name='VisitRateEditsView'),


    #Custom Bulk Delete:
    path('core/api/v1/custom_bulk_edit/', CustomBulkEditView.as_view(), name='CustomBulkEdit'),

    #Shakar
    path('api/micro/personalinfo/validate/', UserDataValidationAPI.as_view(), name='UserDataValidationAPI'),

    path('api/micro/personalinfo/set_main/<id>/', AuthenticationValidationLogIsMainEditView.as_view(), name='AuthenticationValidationLogIsMainEditView'),

    # visit activation change
    path('core/api/v1/visit_activation_edit/', VisitBulkEditsView.as_view(), name='VisitBulkEditsView'),

     #news:
    path('api/visit/ClientListCreate/', ClientListCreateAPIView.as_view(), name='ClientListCreateAPIView'),
    path('api/visit/ClientEdits/<id>/', ClientEditsAPIView.as_view(), name='ClientEditsAPIView'),
    path('api/visit/UserClientListCreate/', UserClientListCreateAPIView.as_view(), name='UserClientListCreateAPIView'),
    path('api/visit/UserClientEdits/<id>/', UserClientEditsAPIView.as_view(), name='UserClientEditsAPIView'),
    path('api/visit/ProductModelListCreate/', ProductModelListCreateAPIView.as_view(), name='ProductModelListCreateAPIView'),
    path('api/visit/ProductModelEdits/<id>/', ProductModelEditsAPIView.as_view(), name='ProductModelEditsAPIView'),
    path('api/visit/ProductListCreate/', ProductListCreateAPIView.as_view(), name='ProductListCreateAPIView'),
    path('api/visit/ProductEdits/<id>/', ProductEditsAPIView.as_view(), name='ProductEditsAPIView'),
    path('api/visit/ElevatorListCreate/', ElevatorListCreateAPIView.as_view(), name='ElevatorListCreateAPIView'),
    path('api/visit/ElevatorEdits/<id>/', ElevatorEditsAPIView.as_view(), name='ElevatorEditsAPIView'),
    path('api/visit/ProductElevatorListCreate/', ProductElevatorListCreateAPIView.as_view(), name='ProductElevatorListCreateAPIView'),
    path('api/visit/ProductElevatorEdits/<id>/', ProductElevatorEditsAPIView.as_view(), name='ProductElevatorEditsAPIView'),
    path('api/visit/BuildingListCreate/', BuildingListCreateAPIView.as_view(), name='BuildingListCreateAPIView'),
    path('api/visit/BuildingEdits/<id>/', BuildingEditsAPIView.as_view(), name='BuildingEditsAPIView'),
    path('api/visit/BuildingElevatorListCreate/', BuildingElevatorListCreateAPIView.as_view(), name='BuildingElevatorListCreateAPIView'),
    path('api/visit/BuildingElevatorEdits/<id>/', BuildingElevatorEditsAPIView.as_view(), name='BuildingElevatorEditsAPIView'),
    path('api/visit/BuildingClientListCreate/', BuildingClientListCreateAPIView.as_view(), name='BuildingClientListCreateAPIView'),
    path('api/visit/BuildingClientEdits/<id>/', BuildingClientEditsAPIView.as_view(), name='BuildingClientEditsAPIView'),


    # term:
    path('config/terms_and_conditions/list/', TermsAndConditionsList.as_view(), name="TermsAndConditionsList"),

    # Config:
    path('config/province/list_create/', ProvinceList.as_view(), name="ProvinceList"),
    path('config/city/list_create/', CityList.as_view(), name="CityList"),
    path('config/province/retrieve/<id>/', ProvinceRetrieve.as_view(), name="ProvinceRetrieve"),
    path('config/city/retrieve/<id>/', CityRetrieve.as_view(), name="CityRetrieve"),
    path('config/terms_and_conditions/list/', TermsAndConditionsList.as_view(), name="TermsAndConditionsList"),

    # media and Navbar
    path('config/Media/List/', MediaManagerList.as_view(), name="MediaManagerList"),
    path('config/Media/Create/', MediaManagerCreate.as_view(), name="MediaManagerCreate"),
    path('config/MediaType/List/', MediaTypeList.as_view(), name="MediaTypeList"), 

    path('config/media/edits/<id>', MediaManagerRetrieveUpdateDestroy.as_view(),
         name="MediaManagerRetrieveUpdateDestroy"),
    path('config/navbar/List/', NavMenuList.as_view(), name="NavMenuList"),
    path('config/navbar/edits/<id>/', NavMenuRetrieveUpdate.as_view(), name="NavMenuRetrieveUpdate"),

     # Client
    path('core/api/client/open_visits/list/', ClientVisitsAPIView.as_view(), name="ClientVisitsAPIView"),
    path('core/api/client/dashboard/', ClientDashboardAPIView.as_view(), name="ClientDashboardAPIView"),
    path('core/api/client/visits/<int:id>/', ClientVisitDetailAPIView.as_view(), name="ClientVisitDetailAPIView"),
    path('core/api/client/visits/<int:id>/feedback/', ClientVisitFeedbackAPIView.as_view(), name="ClientVisitFeedbackAPIView"),
]
docs_urlpatterns = [

    path('api-auth/', include('rest_framework.urls')),
    path('redoc/', schema_view.with_ui('redoc',
                                       cache_timeout=0), name='schema-redoc'),
    path('swagger/', schema_view.with_ui('swagger',
                                         cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('postman/', schema_view.without_ui(cache_timeout=0),
         name='schema-swagger-postman'),
]

urlpatterns += project_urlpatterns

# Local uploads are served only through short-lived URLs issued by scoped APIs.


if settings.DEBUG:
    urlpatterns += docs_urlpatterns

from core.initial import init_permissions,init_model

# try:
#     if init_permissions():
#         print("initiated views successfully")
#     if init_model():
#         print("initiated models successfully")
# except:
#     print("cannot try initial!")
# Existing admin store routes use project-scoped store records.
from visit.store_api import AdminStoreListCreateView, AdminStoreDetailView, AdminStoreCategoryListView
urlpatterns += [
    path('core/api/admin/outlet_list/', AdminStoreListCreateView.as_view()),
    path('core/api/admin/outlet_with_more_info/create/', AdminStoreListCreateView.as_view()),
    path('core/api/admin/outlet_with_more_info/edits/<int:id>/', AdminStoreDetailView.as_view()),
    path('core/api/admin/outlet_cat_list/', AdminStoreCategoryListView.as_view()),
]
