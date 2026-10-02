"""Record boundaries for warranty and repair work."""
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError

from visit.asset_access import AssetAccess
from visit.management import current_management_q
from visit.models import BuildingClient, RepairCase, WarrantyClaim, WarrantyContract


class ServiceCaseAccess:
    def __init__(self, request, view):
        self.assets = AssetAccess(request, view)
        self.request = request

    @property
    def project_id(self):
        return self.assets.project_id

    def require_manager(self):
        if not self.assets.project_wide:
            raise PermissionDenied('این عملیات نیازمند دسترسی مدیریتی پروژه است.')

    @property
    def contracts(self):
        rows = WarrantyContract.objects.filter(project_id=self.project_id)
        if self.assets.project_wide:
            return rows
        if 'client' in self.assets.scopes:
            return rows.filter(client__in=self.assets.own_clients)
        return rows.none()

    @property
    def claims(self):
        rows = WarrantyClaim.objects.filter(project_id=self.project_id)
        if self.assets.project_wide:
            return rows
        condition = Q(pk__in=[])
        if 'client' in self.assets.scopes:
            condition |= Q(client__in=self.assets.own_clients)
        if {'assigned', 'supervised'} & self.assets.scopes:
            condition |= Q(visit__in=self.assets.assigned_visits)
        return rows.filter(condition).distinct()

    @property
    def repairs(self):
        rows = RepairCase.objects.filter(project_id=self.project_id)
        if self.assets.project_wide:
            return rows
        condition = Q(pk__in=[])
        if 'client' in self.assets.scopes:
            condition |= Q(client__in=self.assets.own_clients)
        if {'assigned', 'supervised'} & self.assets.scopes:
            condition |= Q(claim__visit__in=self.assets.assigned_visits)
        return rows.filter(condition).distinct()

    def linked_products(self, client):
        managed_buildings = BuildingClient.objects.filter(client=client).filter(
            current_management_q()).values('building_id')
        return self.assets.products.filter(
            productelevator__is_active=True,
            productelevator__elevator__buildingelevator__building_id__in=managed_buildings,
        ).distinct()

    def validate_client_product(self, client, product, client_write=False, require_link=False):
        if client.project_id != self.project_id or product.project_id != self.project_id:
            raise ValidationError({'product': 'کلاینت و قطعه باید در پروژه انتخاب‌شده باشند.'})
        if client_write:
            if not self.assets.own_clients.filter(pk=client.pk).exists():
                raise PermissionDenied('این کلاینت در دسترس نیست.')
        if client_write or require_link:
            if not self.linked_products(client).filter(pk=product.pk).exists():
                if not client_write:
                    raise ValidationError({'product': 'این قطعه روی دارایی جاری مشتری نصب نیست.'})
                raise PermissionDenied('این قطعه در دارایی‌های جاری شما نیست.')
