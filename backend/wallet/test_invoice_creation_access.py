"""Field invoice creation must stay with the assigned visit and one client recipient."""
from unittest.mock import patch
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Building, BuildingClient, Client, UserClient, Visit, VisitType
from wallet.models import WalletInvoice


class InvoiceCreationAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Invoice issue one')
        self.other_project = Project.objects.create(name='Invoice issue two')
        self.expert = User.objects.create(username='issue-expert')
        self.other_expert = User.objects.create(username='issue-other-expert')
        self.customer = User.objects.create(username='issue-customer')
        expert_role = Role.objects.create(title='Issue expert', title_abbreviation='P', asset_scope='assigned')
        client_role = Role.objects.create(title='Issue client', title_abbreviation='C', asset_scope='client')
        RoleAssignment.objects.create(user=self.expert, role=expert_role, project=self.project)
        RoleAssignment.objects.create(user=self.customer, role=client_role, project=self.project)
        for method, capability in (('GET', 'can_view'), ('POST', 'can_create')):
            view, _ = ViewMethod.objects.get_or_create(view_name='WalletInvoiceExpertListCreateView', method=method)
            RoleView.objects.create(role=expert_role, view_method_name=view, **{capability: True})
        client = Client.objects.create(project=self.project, name='Managed client')
        UserClient.objects.create(client=client, user=self.customer)
        building = Building.objects.create(project=self.project, code='ISSUE-OWN')
        BuildingClient.objects.create(building=building, client=client)
        visit_type = VisitType.objects.create(project=self.project, title='Invoice visit')
        self.visit = Visit.objects.create(type=visit_type, building=building, creator=self.expert,
                                          expert=self.expert, is_active=True)
        other_building = Building.objects.create(project=self.project, code='ISSUE-OTHER')
        self.other_visit = Visit.objects.create(type=visit_type, building=other_building,
                                                creator=self.other_expert, expert=self.other_expert,
                                                is_active=True)
        foreign_type = VisitType.objects.create(project=self.other_project, title='Foreign invoice visit')
        foreign_building = Building.objects.create(project=self.other_project, code='ISSUE-FOREIGN')
        self.foreign_visit = Visit.objects.create(type=foreign_type, building=foreign_building,
                                                  creator=self.expert, expert=self.expert,
                                                  is_active=True)
        self.api = APIClient()
        self.api.force_authenticate(self.expert)

    def url(self, project=None):
        return f'/wallet/invoice/expert/list_create/?p={project or self.project.pk}'

    def create(self, visit=None, **kwargs):
        payload = {'visit': (visit or self.visit).pk, 'amount_rials': 500000,
                   'description': 'Local service', 'type': 'CREDIT',
                   'request_key': str(uuid.uuid4())}
        payload.update(kwargs)
        return self.api.post(self.url(), payload, format='json')

    def test_only_assigned_same_project_visit_and_unique_recipient(self):
        for visit in (self.other_visit, self.foreign_visit):
            self.assertEqual(self.create(visit).status_code, 404)
        self.assertEqual(self.create(amount_rials=-1).status_code, 400)
        self.assertEqual(self.create(amount_rials=1_000_000_000_001).status_code, 400)
        with patch('notification.modules.notification.Notification'):
            response = self.create(is_closed=True, client=self.other_expert.pk)
        self.assertEqual(response.status_code, 201, response.data)
        invoice = WalletInvoice.objects.get(pk=response.data['id'])
        self.assertEqual(invoice.expert, self.expert)
        self.assertEqual(invoice.client, self.customer)
        self.assertFalse(invoice.is_closed)
        self.assertEqual(invoice.payable_amount_rials, 500000)
        listing = self.api.get(self.url())
        self.assertEqual(len(listing.data), 1)
        self.assertNotIn('request_key', listing.data[0])
        self.assertNotIn('payload_hash', listing.data[0])
        self.assertEqual(self.api.get(self.url(self.other_project.pk)).status_code, 403)

    def test_same_request_key_replays_and_changed_payload_conflicts(self):
        key = str(uuid.uuid4())
        first = self.create(request_key=key)
        self.assertEqual(first.status_code, 201, first.data)
        replay = self.create(request_key=key)
        self.assertEqual(replay.status_code, 201, replay.data)
        self.assertEqual(replay.data['id'], first.data['id'])
        self.assertEqual(WalletInvoice.objects.count(), 1)
        conflict = self.create(request_key=key, amount_rials=600000)
        self.assertEqual(conflict.status_code, 400, conflict.data)
        self.assertEqual(WalletInvoice.objects.count(), 1)

    def test_ambiguous_recipient_and_missing_grant_do_not_create(self):
        second = User.objects.create(username='issue-second-customer')
        client_role = Role.objects.get(title='Issue client')
        RoleAssignment.objects.create(user=second, role=client_role, project=self.project)
        UserClient.objects.create(user=second, client=UserClient.objects.get(user=self.customer).client)
        self.assertEqual(self.create().status_code, 400)
        self.assertFalse(WalletInvoice.objects.exists())
        RoleView.objects.filter(role__title='Issue expert',
                                view_method_name__method='POST').update(can_create=False)
        self.assertEqual(self.create().status_code, 403)
        self.assertFalse(WalletInvoice.objects.exists())
