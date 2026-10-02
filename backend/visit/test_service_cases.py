"""Warranty, repair, and loaner records must stay in their project and owner scope."""
from datetime import timedelta
import uuid

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import AdminMenu, Project, Role, RoleAssignment, RoleView, ViewMethod
from notification.models import InAppNotification
from visit.models import (Building, BuildingClient, BuildingElevator, Client, Elevator,
                          Product, ProductElevator, ProductModel, RepairCase, RepairEvent,
                          UserClient, WarrantyClaim, WarrantyContract)
from warehouse.models import Ware, WarehouseLocation, WarehouseTransaction, WarehouseTransactionLine


class ServiceCaseTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Service cases')
        self.other_project = Project.objects.create(name='Other service cases')
        self.manager = User.objects.create(username='service-manager')
        self.customer = User.objects.create(username='service-customer')
        self.manager_role = Role.objects.create(title='Service manager', title_abbreviation='M', asset_scope='project')
        self.customer_role = Role.objects.create(title='Service customer', title_abbreviation='C', asset_scope='client')
        RoleAssignment.objects.create(user=self.manager, project=self.project, role=self.manager_role)
        RoleAssignment.objects.create(user=self.customer, project=self.project, role=self.customer_role)
        self.client = Client.objects.create(name='Owned', project=self.project)
        self.other_client = Client.objects.create(name='Other', project=self.project)
        UserClient.objects.create(user=self.customer, client=self.client)
        self.building = Building.objects.create(code='W-OWN', project=self.project)
        BuildingClient.objects.create(building=self.building, client=self.client)
        elevator = Elevator.objects.create(project=self.project)
        BuildingElevator.objects.create(building=self.building, elevator=elevator)
        model = ProductModel.objects.create(name='Board', project=self.project)
        self.product = Product.objects.create(model=model, project=self.project, serial_number='SERIAL-1')
        self.loaner = Product.objects.create(model=model, project=self.project, serial_number='LOANER-1')
        self.other_product = Product.objects.create(model=model, project=self.project, serial_number='OTHER-1')
        ProductElevator.objects.create(product=self.product, elevator=elevator, is_active=True)
        self.api = APIClient()
        self.api.force_authenticate(self.manager)

    def grant(self, view, method, role=None):
        vm, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
        RoleView.objects.create(
            role=role or self.manager_role, view_method_name=vm,
            can_view=method == 'GET', can_create=method == 'POST',
            can_update=method in ('PATCH', 'PUT'),
        )

    def url(self, path, project=None):
        separator = '&' if '?' in path else '?'
        return f'/core/api/{path}{separator}p={project or self.project.pk}'

    def contract(self):
        return WarrantyContract.objects.create(
            project=self.project, client=self.client, product=self.product,
            reference='W-001', coverage_start=timezone.localdate(),
            coverage_end=timezone.localdate() + timedelta(days=365),
        )

    def repair(self, claim=None):
        return RepairCase.objects.create(project=self.project, client=self.client,
                                         product=self.product, claim=claim,
                                         serial_snapshot=self.product.serial_number)

    def test_repair_material_consumption_is_linked_and_replay_safe(self):
        self.grant('RepairCaseMaterialView', 'GET')
        self.grant('RepairCaseMaterialView', 'POST')
        self.grant('WareTransactionEzCreateView', 'POST')
        repair = self.repair()
        repair.status = RepairCase.REPAIRING
        repair.save(update_fields=['status'])
        ware = Ware.objects.create(name_fa='Relay', project=self.project, is_for_use=True)
        location = WarehouseLocation.objects.create(name_fa='Repair stock')
        location.projects.add(self.project)
        receipt = {'description': 'Synthetic receipt', 'request_key': str(uuid.uuid4()),
                   'lines': [{'ware': ware.pk, 'amount': -3, 'side': 'FROM', 'involved': None},
                             {'ware': ware.pk, 'amount': 3, 'side': 'TO',
                              'involved': 'LOCATION', 'location': location.pk}]}
        self.assertEqual(self.api.post(f'/api/warehouse/v1/ware_transaction/ez_create/?p={self.project.pk}',
                                       receipt, format='json').status_code, 200)
        path = self.url(f'repair/cases/{repair.pk}/materials/')
        options = self.api.get(path)
        self.assertEqual(options.status_code, 200)
        self.assertEqual(options.data[0]['available'], 3)
        payload = {'ware': ware.pk, 'quantity': 2, 'source_type': 'LOCATION',
                   'source_id': location.pk, 'request_key': str(uuid.uuid4())}
        result = self.api.post(path, payload, format='json')
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['materials'][0]['quantity'], 2)
        self.assertEqual(self.api.post(path, payload, format='json').status_code, 200)
        self.assertEqual(WarehouseTransaction.objects.filter(repair_case=repair).count(), 1)
        remaining = WarehouseTransactionLine.objects.filter(ware=ware, location=location).aggregate(
            total=Sum('amount'))['total']
        self.assertEqual(remaining, 1)
        replay_key = payload['request_key']
        payload['request_key'] = str(uuid.uuid4())
        self.assertEqual(self.api.post(path, payload, format='json').status_code, 400)
        self.assertEqual(WarehouseTransaction.objects.filter(repair_case=repair).count(), 1)
        repair.status = RepairCase.DELIVERED
        repair.save(update_fields=['status'])
        self.assertEqual(self.api.post(path, payload, format='json').status_code, 400)
        payload['request_key'] = replay_key
        self.assertEqual(self.api.post(path, payload, format='json').status_code, 200)
        self.api.force_authenticate(self.customer)
        self.grant('RepairCaseMaterialView', 'POST', self.customer_role)
        self.assertEqual(self.api.post(path, payload, format='json').status_code, 403)

    def test_contract_unique_reference_and_client_scope(self):
        self.grant('WarrantyContractListCreateView', 'POST')
        self.grant('WarrantyContractListCreateView', 'GET', self.customer_role)
        self.grant('WarrantyEligibleProductsView', 'GET')
        payload = {'client': self.client.pk, 'product': self.product.pk,
                   'reference': 'W-001', 'coverage_start': str(timezone.localdate()),
                   'coverage_end': str(timezone.localdate() + timedelta(days=30))}
        self.assertEqual(self.api.post(self.url('warranty/contracts/'), payload, format='json').status_code, 201)
        self.assertEqual(self.api.post(self.url('warranty/contracts/'),
                                       {**payload, 'client': self.other_client.pk, 'reference': 'W-002'},
                                       format='json').status_code, 400)
        self.assertEqual(self.api.post(self.url('warranty/contracts/'), payload, format='json').status_code, 400)
        self.assertEqual([row['id'] for row in self.api.get(self.url(
            f'warranty/eligible_products/?client={self.client.pk}')).data], [self.product.pk])
        self.assertEqual(self.api.get(self.url(
            f'warranty/eligible_products/?client={self.other_client.pk}')).data, [])
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.contract()
        self.api.force_authenticate(self.customer)
        response = self.api.get(self.url('warranty/contracts/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['reference'] for row in response.data], ['W-001'])
        self.assertEqual(self.api.get(self.url('warranty/contracts/', self.other_project)).status_code, 403)

    def test_client_can_claim_installed_product_but_not_another_client_part(self):
        self.grant('WarrantyClaimListCreateView', 'POST', self.customer_role)
        self.grant('WarrantyClaimListCreateView', 'GET', self.customer_role)
        contract = self.contract()
        self.api.force_authenticate(self.customer)
        payload = {'client': self.client.pk, 'product': self.product.pk, 'issue': 'Board failure'}
        response = self.api.post(self.url('warranty/claims/'), payload, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], WarrantyClaim.PENDING)
        self.assertEqual(response.data['contract'], contract.pk)
        self.assertEqual(self.api.post(self.url('warranty/claims/'),
                                       {**payload, 'product': self.other_product.pk}, format='json').status_code, 403)
        self.assertEqual(self.api.post(self.url('warranty/claims/'),
                                       {**payload, 'client': self.other_client.pk}, format='json').status_code, 403)
        self.assertEqual(len(self.api.get(self.url('warranty/claims/')).data), 1)

    def test_decision_is_final_and_manager_only(self):
        colleague = User.objects.create(username='service-colleague')
        outsider = User.objects.create(username='service-outsider')
        RoleAssignment.objects.create(user=colleague, project=self.project, role=self.customer_role)
        RoleAssignment.objects.create(user=outsider, project=self.project, role=self.customer_role)
        UserClient.objects.create(user=colleague, client=self.client)
        UserClient.objects.create(user=outsider, client=self.other_client)
        claim = WarrantyClaim.objects.create(project=self.project, client=self.client,
                                             product=self.product, issue='Board failure', opened_by=self.customer)
        self.grant('WarrantyClaimDecisionView', 'POST')
        self.grant('WarrantyClaimDecisionView', 'POST', self.customer_role)
        url = self.url(f'warranty/claims/{claim.pk}/decision/')
        self.api.force_authenticate(self.customer)
        self.assertEqual(self.api.post(url, {'status': 'COVERED', 'reason': 'Valid'}, format='json').status_code, 403)
        self.api.force_authenticate(self.manager)
        self.assertEqual(self.api.post(url, {'status': 'COVERED', 'reason': 'Valid'}, format='json').status_code, 200)
        self.assertEqual(self.api.post(url, {'status': 'DENIED', 'reason': 'Changed'}, format='json').status_code, 400)
        claim.refresh_from_db()
        self.assertEqual(claim.decision_reason, 'Valid')
        self.assertEqual(claim.decided_by, self.manager)
        item = InAppNotification.objects.get(recipient=self.customer, kind='warranty_decision')
        self.assertEqual(item.object_id, claim.pk)
        self.assertEqual(InAppNotification.objects.filter(recipient=colleague, kind='warranty_decision').count(), 1)
        self.assertEqual(InAppNotification.objects.filter(recipient=outsider).count(), 0)
        self.assertEqual(InAppNotification.objects.filter(kind='warranty_decision').count(), 2)

    def test_overlapping_contracts_require_explicit_choice(self):
        first = self.contract()
        second = WarrantyContract.objects.create(
            project=self.project, client=self.client, product=self.product,
            reference='W-002', coverage_start=timezone.localdate(),
            coverage_end=timezone.localdate() + timedelta(days=60),
        )
        self.grant('WarrantyClaimListCreateView', 'POST', self.customer_role)
        self.api.force_authenticate(self.customer)
        payload = {'client': self.client.pk, 'product': self.product.pk, 'issue': 'Another fault'}
        self.assertEqual(self.api.post(self.url('warranty/claims/'), payload,
                                       format='json').status_code, 400)
        response = self.api.post(self.url('warranty/claims/'),
                                 {**payload, 'contract': second.pk}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['contract'], second.pk)
        self.assertNotEqual(response.data['contract'], first.pk)

    def test_repair_progression_requires_evidence_and_keeps_events(self):
        repair = self.repair()
        self.grant('RepairCaseTransitionView', 'POST')
        url = self.url(f'repair/cases/{repair.pk}/transition/')
        def advance(state, **data):
            return self.api.post(url, {'to_status': state, **data}, format='json')
        self.assertEqual(advance('READY').status_code, 400)
        self.assertEqual(advance('DIAGNOSING').status_code, 200)
        self.assertEqual(advance('REPAIRING').status_code, 400)
        self.assertEqual(advance('REPAIRING', diagnosis='Failed IC').status_code, 200)
        self.assertEqual(advance('TESTING').status_code, 400)
        self.assertEqual(advance('TESTING', work_performed='Replaced IC').status_code, 200)
        self.assertEqual(advance('READY').status_code, 400)
        self.assertEqual(advance('READY', test_result='48-hour pass').status_code, 200)
        self.assertEqual(advance('DELIVERED').status_code, 200)
        self.assertEqual(advance('DIAGNOSING').status_code, 400)
        repair.refresh_from_db()
        self.assertIsNotNone(repair.delivered_at)
        self.assertEqual(repair.events.count(), 5)
        self.assertEqual(InAppNotification.objects.filter(
            recipient=self.customer, kind='repair_status', object_id=repair.pk).count(), 5)

    def test_repair_intake_notifies_client(self):
        self.grant('RepairCaseListCreateView', 'POST')
        response = self.api.post(self.url('repair/cases/'), {
            'client': self.client.pk, 'product': self.product.pk,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        item = InAppNotification.objects.get(recipient=self.customer, kind='repair_status')
        self.assertEqual(item.object_id, response.data['id'])

    def test_loaner_is_unique_and_history_keeps_product_after_reassignment(self):
        repair = self.repair()
        second = self.repair()
        self.grant('RepairCaseLoanerView', 'GET')
        self.grant('RepairCaseLoanerView', 'POST')
        self.assertEqual([row['id'] for row in self.api.get(self.url(
            f'repair/cases/{repair.pk}/loaner/')).data],
            [self.loaner.pk, self.other_product.pk])
        due = str(timezone.localdate() + timedelta(days=5))
        def loan(case, action, product=None):
            payload = {'action': action}
            if product is not None:
                payload.update(product=product.pk, due_at=due)
            return self.api.post(self.url(f'repair/cases/{case.pk}/loaner/'), payload, format='json')
        self.assertEqual(loan(repair, 'assign', self.loaner).status_code, 200)
        self.assertEqual([row['id'] for row in self.api.get(self.url(
            f'repair/cases/{second.pk}/loaner/')).data], [self.other_product.pk])
        self.assertEqual(loan(second, 'assign', self.loaner).status_code, 400)
        self.assertEqual(loan(repair, 'return').status_code, 200)
        self.assertEqual(loan(second, 'assign', self.loaner).status_code, 200)
        history = list(RepairEvent.objects.filter(case=repair).order_by('at'))
        self.assertEqual([item.loaner_product_id for item in history], [self.loaner.pk, self.loaner.pk])
        self.assertEqual(loan(repair, 'return').status_code, 400)

    def test_cross_project_product_and_case_do_not_leak(self):
        repair = self.repair()
        self.grant('RepairCaseListCreateView', 'POST')
        self.grant('RepairCaseDetailView', 'GET')
        foreign_model = ProductModel.objects.create(name='Foreign', project=self.other_project)
        foreign_product = Product.objects.create(model=foreign_model, project=self.other_project)
        response = self.api.post(self.url('repair/cases/'), {
            'client': self.client.pk, 'product': foreign_product.pk,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.api.get(self.url(f'repair/cases/{repair.pk}/', self.other_project)).status_code, 403)

    def test_provision_command_previews_and_requires_multi_project_acknowledgment(self):
        RoleAssignment.objects.create(user=self.manager, project=self.other_project, role=self.manager_role)
        command = {'project': self.project.pk, 'role': self.manager_role.pk}
        call_command('provision_service_case_access', **command)
        self.assertFalse(RoleView.objects.filter(role=self.manager_role).exists())
        with self.assertRaises(CommandError):
            call_command('provision_service_case_access', apply=True, **command)
        call_command('provision_service_case_access', apply=True, all_projects=True, **command)
        call_command('provision_service_case_access', apply=True, all_projects=True, **command)
        self.assertEqual(AdminMenu.objects.filter(project=self.project, role=self.manager_role,
                                                  frontend_route_url='/service-cases').count(), 1)
        self.assertTrue(RoleView.objects.filter(role=self.manager_role,
                                                view_method_name__view_name='RepairCaseTransitionView',
                                                can_create=True).exists())
