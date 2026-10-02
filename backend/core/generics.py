from django.db.models import Q
from auth_app.permissions import authorized_role_views, DeleteCreateUpdateGetPermission
from auth_app.models import RoleViewLimiter, RoleViewModelField
from rest_framework.decorators import permission_classes
import ast
import logging
from django.core.exceptions import FieldError, ValidationError as DjangoValidationError
from rest_framework.exceptions import PermissionDenied


logger = logging.getLogger(__name__)


class BaseView:
    def get_projectified_queryset(self, queryset):
        try:
            project_id = int(self.request.query_params.get('p'))
        except (TypeError, ValueError):
            return queryset.none()
        if project_id <= 0:
            return queryset.none()
        return queryset.filter(**{self.project_path + '__id': project_id})

    # BaseView
    # project_path
    # def get_queryset(self):
    #     return self.get_projectified_queryset()


@permission_classes([DeleteCreateUpdateGetPermission])
class BaseLimiter:
    is_view = True

    def limit_queryset(self, query_set):
        method = self.request.method.upper()
        if method in ('HEAD', 'OPTIONS'):
            method = 'GET'
        configured = RoleViewLimiter.objects.filter(
            role_view__view_method_name__view_name=self.__class__.__name__,
            role_view__view_method_name__method=method, is_active=True,
        )
        # Some callers (e.g. /auth/me) enforce their own self-only queryset.
        if not configured.exists():
            return query_set

        grants = list(authorized_role_views(self.request, self))
        if not grants:
            return query_set.none()
        by_grant = {}
        for row in configured.filter(role_view__in=grants).select_related('limiter'):
            by_grant.setdefault(row.role_view_id, []).append(row)

        # An explicitly authorized unrestricted role grants the original scope.
        if any(grant.pk not in by_grant for grant in grants):
            return query_set

        combined = None
        try:
            for grant in grants:
                conditions = Q()
                for row in by_grant[grant.pk]:
                    value = row.limiter.value
                    if value == '>M<':
                        value = self.request.user
                    elif value == '>P<':
                        value = int(self.request.query_params['p'])
                    elif isinstance(value, str) and value.startswith('['):
                        value = ast.literal_eval(value)
                    elif isinstance(value, str) and value.lstrip('-').isdigit():
                        value = int(value)
                    elif value in ('True', 'False'):
                        value = value == 'True'
                    conditions &= Q(**{row.limiter.key: value})
                # Validate this grant's field paths before combining scopes.
                query_set.filter(conditions)
                combined = conditions if combined is None else combined | conditions
            return query_set.filter(combined).distinct()
        except (TypeError, ValueError, SyntaxError, FieldError, DjangoValidationError):
            logger.error('Invalid record limiter configuration for view %s', self.__class__.__name__)
            return query_set.none()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ('PUT', 'PATCH'):
            return
        serializer = self.get_serializer_class()
        model = getattr(getattr(serializer, 'Meta', None), 'model', None)
        if model is None:
            return
        grants = list(authorized_role_views(request, self))
        if not grants:
            return
        fields = list(RoleViewModelField.objects.filter(
            role_view__in=grants, model_field__model_name=model.__name__,
        ).select_related('model_field'))
        by_grant = {}
        for field in fields:
            by_grant.setdefault(field.role_view_id, {})[field.model_field.field_name] = field.can_update
        denied = [name for name in request.data.keys()
                  if all(by_grant.get(grant.pk, {}).get(name, True) is False for grant in grants)]
        if denied:
            raise PermissionDenied('ویرایش این فیلد مجاز نیست: ' + ', '.join(sorted(denied)))
