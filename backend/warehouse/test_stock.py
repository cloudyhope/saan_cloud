"""Balanced stock transfers are atomic, scoped, and replay-safe."""
import hashlib
import json
import uuid

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from warehouse.models import (Ware, WarehouseLocation, WarehouseTransaction,
                              WarehouseTransactionLine, WareVisitType)
from visit.models import Building, Visit, VisitType


class StockTransferTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Stock A')
        self.foreign_project = Project.objects.create(name='Stock B')
        self.manager = User.objects.create(username='stock-manager')
        self.expert = User.objects.create(username='stock-expert')
        self.other_user = User.objects.create(username='stock-other')
        self.manager_role = Role.objects.create(title='Stock manager', title_abbreviation='M', asset_scope='project')
        self.expert_role = Role.objects.create(title='Stock expert', title_abbreviation='P', asset_scope='assigned')
        RoleAssignment.objects.create(user=self.manager, project=self.project, role=self.manager_role)
        RoleAssignment.objects.create(user=self.expert, project=self.project, role=self.expert_role)
        self.ware = Ware.objects.create(name_fa='Board part', project=self.project)
        self.foreign_ware = Ware.objects.create(name_fa='Other project', project=self.foreign_project)
        self.location = WarehouseLocation.objects.create(name_fa='Main stock')
        self.location.projects.add(self.project)
        self.foreign_location = WarehouseLocation.objects.create(name_fa='Foreign stock')
        self.foreign_location.projects.add(self.foreign_project)
        self.api = APIClient()
        self.api.force_authenticate(self.manager)
        self.grant('WareTransactionEzCreateView', 'POST', self.manager_role)

    def grant(self, name, method, role):
        vm, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
        RoleView.objects.create(role=role, view_method_name=vm,
                                can_view=method == 'GET', can_create=method == 'POST')

    def url(self, path='ware_transaction/ez_create/', project=None):
        return f'/api/warehouse/v1/{path}?p={project or self.project.pk}'

    def transfer(self, source, destination, quantity=5, ware=None, key=None):
        return {'request_key': key or str(uuid.uuid4()), 'description': 'Synthetic stock move',
                'lines': [
                    {'ware': ware or self.ware.pk, 'amount': -quantity, 'side': 'FROM', **source},
                    {'ware': ware or self.ware.pk, 'amount': quantity, 'side': 'TO', **destination},
                ]}

    def balance(self, **party):
        return WarehouseTransactionLine.objects.filter(ware=self.ware, **party).aggregate(
            total=Sum('amount'))['total'] or 0

    def test_receipt_transfer_and_duplicate_replay(self):
        receipt = self.transfer({'involved': None},
                                {'involved': 'LOCATION', 'location': self.location.pk}, quantity=10)
        response = self.api.post(self.url(), receipt, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data['replayed'])
        self.assertEqual(self.balance(location=self.location), 10)
        self.assertEqual(self.api.post(self.url(), receipt, format='json').data,
                         {**response.data, 'replayed': True})
        self.assertEqual(WarehouseTransaction.objects.count(), 1)
        move = self.transfer({'involved': 'LOCATION', 'location': self.location.pk},
                             {'involved': 'USER', 'user': self.expert.pk}, quantity=4)
        self.assertEqual(self.api.post(self.url(), move, format='json').status_code, 200)
        self.assertEqual(self.balance(location=self.location), 6)
        self.assertEqual(self.balance(user=self.expert), 4)
        self.assertEqual(WarehouseTransaction.objects.filter(project=self.project).count(), 2)
        self.assertEqual(WarehouseTransactionLine.objects.count(), 4)

    def test_return_and_scrap_have_reason_balance_and_role_rules(self):
        receipt = self.transfer({'involved': None},
                                {'involved': 'USER', 'user': self.expert.pk}, quantity=8)
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 200)
        returned = self.transfer({'involved': 'USER', 'user': self.expert.pk},
                                 {'involved': 'LOCATION', 'location': self.location.pk}, quantity=5)
        returned['kind'] = 'RETURN'
        returned['description'] = 'برگشت ابزار سالم به انبار اصلی'
        response = self.api.post(self.url(), returned, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(WarehouseTransaction.objects.get(pk=response.data['transaction_id']).movement_kind, 'RETURN')
        self.assertEqual(self.api.post(self.url(), returned, format='json').data['replayed'], True)
        self.assertEqual(self.balance(user=self.expert), 3)
        self.assertEqual(self.balance(location=self.location), 5)
        scrap = self.transfer({'involved': 'LOCATION', 'location': self.location.pk},
                              {'involved': None}, quantity=2)
        scrap['kind'] = 'SCRAP'
        scrap['description'] = 'قطعه معیوب و غیرقابل استفاده'
        self.assertEqual(self.api.post(self.url(), scrap, format='json').status_code, 200)
        self.assertEqual(self.balance(location=self.location), 3)
        self.assertEqual(WarehouseTransaction.objects.order_by('-pk').first().movement_kind, 'SCRAP')
        invalid = {**scrap, 'request_key': str(uuid.uuid4()), 'description': 'کوتاه'}
        self.assertEqual(self.api.post(self.url(), invalid, format='json').status_code, 400)
        mismatch = {**scrap, 'request_key': str(uuid.uuid4()), 'kind': 'RETURN'}
        self.assertEqual(self.api.post(self.url(), mismatch, format='json').status_code, 400)
        self.api.force_authenticate(self.expert)
        self.grant('WareTransactionEzCreateView', 'POST', self.expert_role)
        self.assertEqual(self.api.post(self.url(), {**scrap, 'request_key': str(uuid.uuid4())},
                                       format='json').status_code, 403)

    def test_legacy_hash_retry_remains_replay_safe(self):
        receipt = self.transfer({'involved': None},
                                {'involved': 'LOCATION', 'location': self.location.pk}, quantity=2)
        response = self.api.post(self.url(), receipt, format='json')
        self.assertEqual(response.status_code, 200)
        canonical = {'lines': [{key: line.get(key) for key in
                                ('ware', 'amount', 'side', 'involved', 'location', 'user')}
                               for line in receipt['lines']],
                     'description': receipt['description'], 'visit': None}
        old_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True,
                                             ensure_ascii=False).encode('utf-8')).hexdigest()
        WarehouseTransaction.objects.filter(pk=response.data['transaction_id']).update(
            movement_kind='LEGACY', payload_hash=old_hash)
        replay = self.api.post(self.url(), receipt, format='json')
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertTrue(replay.data['replayed'])
        self.assertEqual(self.balance(location=self.location), 2)
        self.assertEqual(self.api.post(self.url(), {**receipt, 'kind': 'OPENING'},
                                       format='json').status_code, 400)

    def test_invalid_batch_cannot_create_partial_or_negative_stock(self):
        move = self.transfer({'involved': 'LOCATION', 'location': self.location.pk},
                             {'involved': 'USER', 'user': self.expert.pk}, quantity=1)
        self.assertEqual(self.api.post(self.url(), move, format='json').status_code, 400)
        self.assertFalse(WarehouseTransaction.objects.exists())
        receipt = self.transfer({'involved': None},
                                {'involved': 'LOCATION', 'location': self.location.pk}, quantity=3)
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 200)
        overdraw = self.transfer({'involved': 'LOCATION', 'location': self.location.pk},
                                 {'involved': 'USER', 'user': self.expert.pk}, quantity=4)
        self.assertEqual(self.api.post(self.url(), overdraw, format='json').status_code, 400)
        self.assertEqual(self.balance(location=self.location), 3)
        broken = self.transfer({'involved': 'LOCATION', 'location': self.location.pk},
                               {'involved': 'USER', 'user': self.expert.pk}, quantity=2)
        broken['lines'][1]['amount'] = 3
        self.assertEqual(self.api.post(self.url(), broken, format='json').status_code, 400)
        self.assertEqual(WarehouseTransaction.objects.count(), 1)

    def test_project_and_party_boundaries(self):
        receipt = self.transfer({'involved': None},
                                {'involved': 'LOCATION', 'location': self.foreign_location.pk})
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 400)
        receipt['lines'][1]['location'] = self.location.pk
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 200)
        wrong_ware = self.transfer({'involved': None},
                                   {'involved': 'LOCATION', 'location': self.location.pk},
                                   ware=self.foreign_ware.pk)
        self.assertEqual(self.api.post(self.url(), wrong_ware, format='json').status_code, 400)
        wrong_user = self.transfer({'involved': 'LOCATION', 'location': self.location.pk},
                                   {'involved': 'USER', 'user': self.other_user.pk})
        self.assertEqual(self.api.post(self.url(), wrong_user, format='json').status_code, 400)

    def test_expert_can_only_consume_own_stock(self):
        visit_type = VisitType.objects.create(project=self.project, title='Maintenance')
        building = Building.objects.create(project=self.project, code='STOCK-VISIT')
        visit = Visit.objects.create(type=visit_type, building=building, creator=self.manager,
                                     expert=self.expert)
        WareVisitType.objects.create(ware=self.ware, visit_type=visit_type)
        receipt = self.transfer({'involved': None},
                                {'involved': 'USER', 'user': self.expert.pk}, quantity=3)
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 200)
        self.grant('WareTransactionEzCreateView', 'POST', self.expert_role)
        self.api.force_authenticate(self.expert)
        consume = self.transfer({'involved': 'USER', 'user': self.expert.pk},
                                {'involved': None}, quantity=2)
        consume['visit'] = visit.pk
        self.assertEqual(self.api.post(self.url(), consume, format='json').status_code, 200)
        self.assertEqual(self.balance(user=self.expert), 1)
        unrelated = self.transfer({'involved': 'USER', 'user': self.manager.pk},
                                  {'involved': None}, quantity=1)
        unrelated['visit'] = visit.pk
        self.assertEqual(self.api.post(self.url(), unrelated, format='json').status_code, 403)
        unlinked = self.transfer({'involved': 'USER', 'user': self.expert.pk},
                                 {'involved': None}, quantity=1)
        self.assertEqual(self.api.post(self.url(), unlinked, format='json').status_code, 403)

    def test_reusing_key_with_changed_payload_and_direct_mutation_are_blocked(self):
        key = str(uuid.uuid4())
        receipt = self.transfer({'involved': None},
                                {'involved': 'LOCATION', 'location': self.location.pk}, key=key)
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 200)
        receipt['description'] = 'Changed amount or meaning'
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 400)
        self.grant('WarehouseTransactionLineListCreateView', 'POST', self.manager_role)
        self.assertEqual(self.api.post(self.url('transaction_line/list_create/'), {
            'ware': self.ware.pk, 'amount': 999, 'transaction': 1,
        }, format='json').status_code, 405)
        self.assertEqual(self.balance(location=self.location), 5)

    def test_catalog_and_stock_read_do_not_cross_project(self):
        RoleAssignment.objects.create(user=self.manager, project=self.foreign_project,
                                      role=self.manager_role)
        self.grant('WareListCreateView', 'POST', self.manager_role)
        self.grant('WareDistributionView', 'GET', self.manager_role)
        self.grant('WarehouseStockAggregatedByUserListView', 'GET', self.manager_role)
        self.grant('WarehouseLocationListCreateView', 'POST', self.manager_role)
        self.assertEqual(self.api.post(self.url('ware/list_create/'), {
            'name_fa': 'Injected', 'project': self.foreign_project.pk,
        }, format='json').status_code, 400)
        self.assertEqual(self.api.get(self.url(f'aggregated/user_or_location/retrieve/{self.foreign_ware.pk}/')).status_code, 404)
        self.assertEqual(self.api.post(self.url('location/list_create/'), {
            'name_fa': 'Injected location', 'projects': [self.foreign_project.pk],
        }, format='json').status_code, 400)
        self.assertEqual(self.api.post(self.url(project=self.project.pk), self.transfer(
            {'involved': None}, {'involved': 'USER', 'user': self.manager.pk},
            quantity=2), format='json').status_code, 200)
        self.assertEqual(self.api.post(self.url(project=self.foreign_project.pk), self.transfer(
            {'involved': None}, {'involved': 'USER', 'user': self.manager.pk},
            quantity=5, ware=self.foreign_ware.pk), format='json').status_code, 200)
        response = self.api.get(self.url('aggregated/user/list/') + '&me=true')
        self.assertEqual(response.status_code, 200, response.data)
        rows = response.data if isinstance(response.data, list) else response.data['results']
        self.assertEqual([item['ware']['id'] for item in rows[0]['stock_count']], [self.ware.pk])

    def test_opening_stock_creates_catalog_balance_and_visit_link_atomically(self):
        self.grant('WareListCreateView', 'POST', self.manager_role)
        visit_type = VisitType.objects.create(project=self.project, title='Repair visit')
        path = self.url('ware/opening_stock/')
        payload = {'name_fa': 'New relay', 'identifier': 'REL-01', 'quantity': 7,
                   'location': self.location.pk, 'visit_types': [visit_type.pk],
                   'request_key': str(uuid.uuid4())}
        result = self.api.post(path, payload, format='json')
        self.assertEqual(result.status_code, 201, result.data)
        ware = Ware.objects.get(pk=result.data['id'])
        self.assertEqual(ware.project_id, self.project.pk)
        self.assertEqual(WareVisitType.objects.get(ware=ware).visit_type_id, visit_type.pk)
        self.assertEqual(WarehouseTransactionLine.objects.filter(
            ware=ware, location=self.location).aggregate(total=Sum('amount'))['total'], 7)
        replay = self.api.post(path, payload, format='json')
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(replay.data['id'], ware.pk)
        self.assertEqual(WarehouseTransactionLine.objects.filter(ware=ware).count(), 2)
        self.assertEqual(self.api.post(path, {**payload, 'name_fa': 'Changed'},
                                       format='json').status_code, 400)
        self.assertEqual(self.api.post(path, {**payload, 'request_key': str(uuid.uuid4()),
                                              'location': self.foreign_location.pk},
                                       format='json').status_code, 400)
        collision_key = uuid.uuid4()
        transfer_key = uuid.uuid5(uuid.NAMESPACE_URL, f'saan/opening-stock/{collision_key}')
        receipt = self.transfer({'involved': None},
                                {'involved': 'LOCATION', 'location': self.location.pk},
                                key=str(transfer_key))
        self.assertEqual(self.api.post(self.url(), receipt, format='json').status_code, 200)
        before = Ware.objects.count()
        self.assertEqual(self.api.post(path, {**payload, 'request_key': str(collision_key)},
                                       format='json').status_code, 400)
        self.assertEqual(Ware.objects.count(), before)
        self.grant('WareListCreateView', 'POST', self.expert_role)
        self.grant('WareTransactionEzCreateView', 'POST', self.expert_role)
        self.api.force_authenticate(self.expert)
        self.assertEqual(self.api.post(path, {**payload, 'request_key': str(uuid.uuid4())},
                                       format='json').status_code, 403)
