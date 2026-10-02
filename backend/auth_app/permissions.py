from rest_framework.permissions import BasePermission
from auth_app.models import *
from django.conf import settings


METHOD_CAPABILITIES = {
    'GET': 'can_view',
    'HEAD': 'can_view',
    'OPTIONS': 'can_view',
    'POST': 'can_create',
    'PUT': 'can_update',
    'PATCH': 'can_update',
    'DELETE': 'can_delete',
}


def authorized_role_views(request, view, view_name=None):
    """Return grants for active memberships in the selected project and action."""
    user = request.user
    capability = METHOD_CAPABILITIES.get(request.method.upper())
    if not user.is_authenticated or not user.is_active or capability is None:
        return RoleView.objects.none()
    try:
        project_id = int(request.query_params.get('p'))
    except (TypeError, ValueError):
        return RoleView.objects.none()
    if project_id <= 0:
        return RoleView.objects.none()

    roles = RoleAssignment.objects.filter(
        user=user, project_id=project_id, is_deleted=False,
        role__is_active=True, project__is_active=True,
    ).values_list('role_id', flat=True)
    method = request.method.upper()
    if method in ('HEAD', 'OPTIONS'):
        method = 'GET'
    return RoleView.objects.filter(
        role_id__in=roles,
        view_method_name__method=method,
        view_method_name__view_name=view_name or view.__class__.__name__,
        **{capability: True},
    )


class PriorityRolePermission(BasePermission):
    """
    Priority of Roles in whole core!
    """

    def has_permission(self, request, view):
        try:
            if not request.user.is_authenticated:
                return False
            if str(request.method).upper() == 'GET':
                return True
            user_roles = RoleAssignment.objects.filter(user=request.user, project=request.query_params.get('p',
                                                                                                           Role.objects.get(
                                                                                                               id=
                                                                                                               request.data[
                                                                                                                   'role'])).role)
            if not user_roles.exists():
                return False
            user_role = user_roles[0]
            if user_role.priority >= request.data['role']['priority']:
                return False
            return True
        except:
            return False


class DeleteCreateUpdateGetPermission(BasePermission):
    message = 'This User does not have permission to this view with this method'
    role_view = None
    method = None

    def has_permission(self, request, view):
        self.method = request.method.upper()
        self.role_view = authorized_role_views(request, view)
        return self.role_view.exists()
