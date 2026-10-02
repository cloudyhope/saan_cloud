from django.urls import path
from .views import *

app_name = 'main'

urlpatterns = [
     # health:
     path('health/', HealthCheck.as_view(), name='HealthCheck'),
     # auth validations:
     path('auth/authentication_check/', CheckAuthenticationView.as_view(), name="CheckAuthenticationView"),
     path('auth/otp/request/', RequestOTP.as_view(), name="RequestOTP"),
     path('auth/otp/verify/', VerifyPhoneNumberOTPAPIView.as_view(), name="VerifyPhoneNumberOTPAPIView"),
     path('auth/me/', MeView.as_view(), name="MeView"),
     # Admin:
     path('auth/user_info/update/', ProfileUpdate.as_view(), name="ProfileUpdate"),
     path('auth/user_info/retrieve/<user>/', ProfileRetrieve.as_view(), name="ProfileRetrieve"),
     # users:
     path('auth/users/list_create/', ProfileList.as_view(), name="ProfileList"),
     # admin helpers
     path('auth/users/admin_multi_user_add/', AdminMultiUserCreate.as_view(), name="AdminMultiUserCreate"),
     path('auth/users/admin_add_or_remove_roles/<id>/', AddOrRemoveRoleFromProfile.as_view(), name="AddOrRemoveRoleFromProfile"),
     path('auth/users/easy_admin_user_add/', EasyAdminMultiUserCreate.as_view(), name="EasyAdminMultiUserCreate"),
     path('auth/users/admin_add_users_to_role/<id>/', AddOrRemoveProfilesFromRole.as_view(), name="AddOrRemoveProfilesFromRole"),
     # term:
     path('config/terms_and_conditions/list/', TermsAndConditionsList.as_view(), name="TermsAndConditionsList"),
     # Config:
     path('config/province/list_create/', ProvinceList.as_view(), name="ProvinceList"),
     path('config/city/list_create/', CityList.as_view(), name="CityList"),
     path('config/province/retrieve/<id>/', ProvinceRetrieve.as_view(), name="ProvinceRetrieve"),
     path('config/city/retrieve/<id>/', CityRetrieve.as_view(), name="CityRetrieve"),
     path('config/terms_and_conditions/list/', TermsAndConditionsList.as_view(), name="TermsAndConditionsList"),
     # role
     path('admin/role_assignment/list/', RolesAssignmentCustomizableListView.as_view(), name="RolesAssignmentCustomizableListView"),
     path('admin/role_assignment/delete/<id>/', RolesAssignmentDeleteListView.as_view(), name="RolesAssignmentDeleteListView"),
     path('auth/me/', RoleAssignmentListView.as_view(), name="RoleAssignmentListView"),
     # address
     path('address/list_create/', AddressListCreate.as_view(), name="AddressListCreate"),
     path('address/edits/<id>/', AddressRetrieveUpdateDestroy.as_view(), name="AddressRetrieveUpdateDestroy"),
     # specification type
     path('specification_type/list_create/', SpecificationTypeListCreate.as_view(), name="SpecificationTypeListCreate"),
     path('specification_type/edits/<id>/', SpecificationTypeRetrieveUpdateDestroy.as_view(), name="SpecificationTypeRetrieveUpdateDestroy"),
]