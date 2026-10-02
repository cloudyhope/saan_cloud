from rest_framework.permissions import BasePermission
# from auth_app.models import *
# from django.conf import settings
from auth_app.models import Permission, ExtendedUser, Role

class IsSuperUser(BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff and request.user.is_superuser)

class RolePermission(BasePermission):
    """
    Check Role and Permission
    """
    def has_permission(self, request, view):
        # view_obj = Permission.objects.get(view_name=view.__class__.__name__, method=request.method)
        view_objs = Permission.objects.filter(view_name=view.__class__.__name__, method=request.method)
        if not view_objs.exists() and request.method in ["GET", "OPTIONS",]:
            return True
        view_obj = view_objs.first()
        if view_obj.is_public:
            return True
        if not request.user.is_authenticated:
            return False
        extended_users = ExtendedUser.objects.filter(user = request.user)
        if not extended_users.exists():
            return False
        extended_user = extended_users.first()
        user_roles = extended_user.roles.all()
        for role in user_roles:
            permissions = role.permissions.all()
            for permission in permissions:
                if permission == view_obj:
                    return True
        return False


class ShaqayeqSafeIPPermission(BasePermission):
    def has_permission(self, request, view):
        # from core.elk import ElasticLog
        # logger = ElasticLog()
        SAFE_IPS = [
            '87.107.147.147', #CarpieceIP
            '127.0.0.1', #LocalhostIP
            '10.1.10.15',
            '10.1.10.13',
            '10.1.10.3',
            '10.1.10.5',
        ]
        # if ip := request.META.get('HTTP_X_FORWARDED_FOR'):
            # ip = ip.split(',')[-1]
        # else:
            # ip = request.META.get('REMOTE_ADDR')
        ip = request.META.get('REMOTE_ADDR')
        return ip in SAFE_IPS

class LocalhostOnly(BasePermission):
    """
    Custom permission class to allow API requests only from localhost (127.0.0.1).
    """

    def has_permission(self, request, view):
        # Check if the request is coming from localhost
        return request.META.get('REMOTE_ADDR') == '127.0.0.1'