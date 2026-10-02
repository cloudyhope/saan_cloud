from rest_framework.permissions import BasePermission
# from auth_app.models import *
# from django.conf import settings
from main.models import ViewMethod, Profile, Role

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
        # view_obj = ViewMethod.objects.get(view_name=view.__class__.__name__, method=request.method)
        view_objs = ViewMethod.objects.filter(view_name=view.__class__.__name__, method=request.method)
        if not view_objs.exists() and request.method in ["GET", "OPTIONS",]:
            return True
        view_obj = view_objs.first()
        if view_obj.is_public:
            return True
        if not request.user.is_authenticated:
            return False
        profiles = Profile.objects.filter(user = request.user)
        if not profiles.exists():
            return False
        profile = profiles.first()
        user_roles = profile.roles.all()
        for role in user_roles:
            allowed_view_methods = role.allowed_view_methods.all()
            for allowed_view_method in allowed_view_methods: 
                if allowed_view_method == view_obj:
                    return True
        return False


class SafeIPPermission(BasePermission):
    def has_permission(self, request, view):
        # logger = ElasticLog()
        SAFE_IPS = [
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