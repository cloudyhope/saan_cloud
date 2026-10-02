"""Project boundaries and explicit role policies for building/asset APIs."""
from functools import cached_property
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError
from auth_app.models import RoleAssignment, Supervisor
from auth_app.permissions import authorized_role_views
from visit.management import current_management_q, client_visible_visits
from visit.models import (
    Building, BuildingClient, BuildingElevator, Client, Elevator, Product,
    ProductElevator, ProductModel, UserClient, Visit,
)


class AssetAccess:
    def __init__(self, request, view):
        self.request = request
        self.view = view
        try:
            self.project_id = int(request.query_params.get('p'))
        except (TypeError, ValueError):
            self.project_id = None

    @cached_property
    def scopes(self):
        return set(authorized_role_views(self.request, self.view).values_list('role__asset_scope', flat=True))

    @property
    def project_wide(self):
        return 'project' in self.scopes

    @cached_property
    def own_clients(self):
        return Client.objects.filter(project_id=self.project_id, userclient__user=self.request.user)

    @cached_property
    def assigned_visits(self):
        visits = Visit.objects.filter(type__project_id=self.project_id, is_deleted=False,
                                      building__project_id=self.project_id)
        condition = Q(pk__in=[])
        if 'assigned' in self.scopes or 'supervised' in self.scopes:
            condition |= Q(expert=self.request.user) | Q(promoter=self.request.user)
        if 'supervised' in self.scopes:
            experts = Supervisor.objects.filter(supervisor=self.request.user, project_id=self.project_id,
                                                 is_active=True).values_list('promoter_id', flat=True)
            condition |= Q(expert_id__in=experts) | Q(promoter_id__in=experts)
        return visits.filter(condition)

    @cached_property
    def visits(self):
        rows = Visit.objects.filter(type__project_id=self.project_id,
                                    building__project_id=self.project_id, is_deleted=False)
        if self.project_wide:
            return rows
        condition = Q(pk__in=[])
        if {'assigned', 'supervised'} & self.scopes:
            condition |= Q(pk__in=self.assigned_visits.values('pk'))
        if 'client' in self.scopes:
            condition |= Q(pk__in=client_visible_visits(rows, self.own_clients).values('pk'))
        return rows.filter(condition).distinct()

    @cached_property
    def buildings(self):
        rows = Building.objects.filter(project_id=self.project_id)
        if self.project_wide:
            return rows
        condition = Q(pk__in=[])
        if 'client' in self.scopes:
            owned = BuildingClient.objects.filter(client__in=self.own_clients).filter(current_management_q())
            condition |= Q(pk__in=owned.values('building_id'))
        if {'assigned', 'supervised'} & self.scopes:
            condition |= Q(pk__in=self.assigned_visits.values('building_id'))
        return rows.filter(condition).distinct()

    @cached_property
    def elevators(self):
        rows = Elevator.objects.filter(project_id=self.project_id)
        if self.project_wide:
            return rows
        condition = Q(pk__in=[])
        if 'client' in self.scopes:
            own_buildings = BuildingClient.objects.filter(
                client__in=self.own_clients,
            ).filter(current_management_q()).values('building_id')
            condition |= Q(buildingelevator__building_id__in=own_buildings,
                           buildingelevator__building__project_id=self.project_id)
        if {'assigned', 'supervised'} & self.scopes:
            # Explicit visit assets win. Legacy visits without a selection use their building's assets.
            condition |= Q(visit_elevator__in=self.assigned_visits)
            legacy_buildings = self.assigned_visits.filter(elevator__isnull=True).values('building_id')
            condition |= Q(buildingelevator__building_id__in=legacy_buildings)
        return rows.filter(condition).distinct()

    @cached_property
    def clients(self):
        rows = Client.objects.filter(project_id=self.project_id)
        if self.project_wide:
            return rows
        condition = Q(pk__in=[])
        if 'client' in self.scopes:
            condition |= Q(pk__in=self.own_clients.values('pk'))
        if {'assigned', 'supervised'} & self.scopes:
            current = BuildingClient.objects.filter(
                building__in=self.buildings,
            ).filter(current_management_q()).values('client_id')
            condition |= Q(pk__in=current)
        return rows.filter(condition).distinct()

    @cached_property
    def products(self):
        rows = Product.objects.filter(project_id=self.project_id)
        if self.project_wide:
            return rows
        return rows.filter(productelevator__elevator__in=self.elevators,
                           productelevator__is_active=True).distinct()

    @cached_property
    def product_models(self):
        rows = ProductModel.objects.filter(project_id=self.project_id)
        return rows if self.project_wide else rows.filter(product__in=self.products).distinct()

    def filter(self, queryset):
        model = queryset.model
        primary = {Building: self.buildings, Client: self.clients, Elevator: self.elevators,
                   Product: self.products, ProductModel: self.product_models}
        if model in primary:
            return queryset.filter(pk__in=primary[model].values('pk'))
        if model is BuildingClient:
            rows = queryset.filter(building__in=self.buildings, client__in=self.clients)
            return rows if self.project_wide else rows.filter(current_management_q())
        if model is BuildingElevator:
            return queryset.filter(building__in=self.buildings, elevator__in=self.elevators)
        if model is ProductElevator:
            return queryset.filter(product__in=self.products, elevator__in=self.elevators)
        if model is UserClient:
            rows = queryset.filter(client__in=self.clients)
            return rows if self.project_wide else rows.filter(user=self.request.user)
        return queryset.none()

    def validate_write(self, serializer, creating=False):
        model = serializer.Meta.model
        values = serializer.validated_data
        if creating and not self.project_wide:
            raise PermissionDenied('ایجاد دارایی و ارتباط مدیریتی نیازمند دسترسی کل پروژه است.')
        if model is BuildingClient and not self.project_wide:
            raise PermissionDenied('تغییر مدیریت ساختمان نیازمند دسترسی کل پروژه است.')
        if model is ProductElevator and not self.project_wide:
            raise PermissionDenied('تغییر نصب قطعه نیازمند دسترسی کل پروژه است.')
        project = values.get('project')
        if 'project' in values and (project is None or project.pk != self.project_id):
            raise ValidationError({'project': 'پروژه داده باید با پروژه انتخاب‌شده یکسان باشد.'})
        related = {'parent': Building, 'building': Building, 'client': Client,
                   'elevator': Elevator, 'product': Product, 'model': ProductModel}
        for field, related_model in related.items():
            obj = values.get(field)
            if obj is not None and not self.filter(related_model.objects.filter(pk=obj.pk)).exists():
                raise ValidationError({field: 'رکورد انتخاب‌شده در محدوده دسترسی این پروژه نیست.'})
        if model is BuildingClient:
            if serializer.instance and any(field in values for field in ('building', 'client')):
                raise ValidationError({'building': 'برای انتقال مدیریت، رابطه تازه ثبت کنید.'})
            if creating and BuildingClient.objects.filter(
                building=values.get('building'), client=values.get('client'), end_at__isnull=True,
            ).exists():
                raise ValidationError({'client': 'این مدیریت فعال قبلاً ثبت شده است.'})
        if model is Building and values.get('parent') is not None:
            parent = values['parent']
            visited = {serializer.instance.pk} if serializer.instance else set()
            while parent is not None:
                if parent.pk in visited:
                    raise ValidationError({'parent': 'ساختمان نمی‌تواند زیرمجموعه خودش باشد.'})
                visited.add(parent.pk)
                parent = parent.parent
        if model is UserClient and values.get('user') is not None:
            if not self.project_wide or not RoleAssignment.objects.filter(
                user=values['user'], project_id=self.project_id, is_deleted=False,
                role__is_active=True, user__is_active=True,
            ).exists():
                raise ValidationError({'user': 'کاربر باید عضویت فعال در همین پروژه داشته باشد.'})
        if model is Client and 'visit_types' in values:
            if any(visit_type.project_id != self.project_id for visit_type in values['visit_types']):
                raise ValidationError({'visit_types': 'نوع خدمت خارج از پروژه انتخاب‌شده است.'})
