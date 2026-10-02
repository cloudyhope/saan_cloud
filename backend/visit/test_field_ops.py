"""Field operations: accept/hand back, client completion code, visit chat, asset context, earnings,
maintenance plans, due alerts and spare-part requests."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import ExtendedUser, Project, Role, RoleAssignment, RoleView, ViewMethod
from notification.models import InAppNotification
from visit.maintenance import generate_due_visits, send_due_alerts
from visit.models import (Building, BuildingClient, BuildingElevator, Client, Elevator, MaintenancePlan, Product,
                          ProductElevator, ProductModel, UserClient, Visit, VisitAssignmentEvent, VisitType)
from warehouse.models import (PartRequest, Ware, WarehouseLocation, WarehouseTransaction,
                              WarehouseTransactionLine)

FLAGS = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'PATCH': 'can_update', 'DELETE': 'can_delete'}


def grant(role, name, method):
    view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
    RoleView.objects.update_or_create(role=role, view_method_name=view_method, defaults={FLAGS[method]: True})


class FieldOpsTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Field ops')
        self.expert = User.objects.create(username='09120000001', first_name='Ali', last_name='Field')
        self.planner = User.objects.create(username='09120000002', first_name='Pat', last_name='Plan')
        self.keeper = User.objects.create(username='09120000003', first_name='Kim', last_name='Store')
        self.client_user = User.objects.create(username='09120000004', first_name='Cy', last_name='Manager')
        self.rep = User.objects.create(username='09120000005', first_name='Rae', last_name='Rep')
        ExtendedUser.objects.bulk_create([ExtendedUser(user=self.planner, role='M'), ExtendedUser(user=self.keeper, role='S')])
        roles = {
            'expert': Role.objects.create(title='FO expert', title_abbreviation='P', asset_scope='assigned'),
            'planner': Role.objects.create(title='FO planner', title_abbreviation='M', asset_scope='project'),
            'keeper': Role.objects.create(title='FO keeper', title_abbreviation='S', asset_scope='project'),
            'client': Role.objects.create(title='FO client', title_abbreviation='C', asset_scope='client'),
            'rep': Role.objects.create(title='FO rep', title_abbreviation='C', asset_scope='client'),
        }
        for user, key in ((self.expert, 'expert'), (self.planner, 'planner'), (self.keeper, 'keeper'),
                          (self.client_user, 'client'), (self.rep, 'rep')):
            RoleAssignment.objects.create(user=user, role=roles[key], project=self.project)
        for name, method in [('PromoterVisitStatusChangeAPIView', 'PUT'), ('FrontVisitPageSettingsView', 'GET'),
                             ('VisitAssignmentResponseView', 'POST'), ('VisitAssetContextView', 'GET'),
                             ('PromoterVisitChatView', 'GET'), ('PromoterVisitChatView', 'POST'),
                             ('PromoterPartRequestView', 'GET'), ('PromoterPartRequestView', 'POST'),
                             ('PromoterPartRequestCancelView', 'POST'), ('PromoterEarningsView', 'GET')]:
            grant(roles['expert'], name, method)
        for name, method in [('AdminUpdateVisitView', 'PUT'), ('AdminVisitFieldOpsView', 'GET'),
                             ('MaintenancePlanListCreateView', 'GET'), ('MaintenancePlanListCreateView', 'POST'),
                             ('MaintenancePlanDetailView', 'PUT'), ('MaintenancePlanDetailView', 'DELETE')]:
            grant(roles['planner'], name, method)
        for name, method in [('PartRequestListView', 'GET'), ('PartRequestDecisionView', 'POST')]:
            grant(roles['keeper'], name, method)
        for key in ('client', 'rep'):
            grant(roles[key], 'ClientVisitsAPIView', 'GET')
            grant(roles[key], 'ClientVisitChatView', 'GET')
            grant(roles[key], 'ClientVisitChatView', 'POST')
        grant(roles['client'], 'ClientVisitFeedbackAPIView', 'POST')
        self.building = Building.objects.create(project=self.project, code='FO-1', verbose_name='Clinic tower')
        client = Client.objects.create(project=self.project, name='Clinic')
        UserClient.objects.create(client=client, user=self.client_user)
        UserClient.objects.create(client=client, user=self.rep)
        BuildingClient.objects.create(building=self.building, client=client)
        self.lift = Elevator.objects.create(project=self.project, title='Lift A')
        BuildingElevator.objects.create(building=self.building, elevator=self.lift)
        self.kind = VisitType.objects.create(project=self.project, title='Service', default_wage=500000)
        self.visit = Visit.objects.create(type=self.kind, building=self.building, creator=self.planner,
                                          expert=self.expert, is_active=True)
        self.visit.elevator.set([self.lift])
        self.api = APIClient()

    def as_user(self, user):
        self.api.force_authenticate(user)
        return self.api

    def url(self, path, **query):
        extra = ''.join(f'&{key}={value}' for key, value in query.items())
        return f'{path}?p={self.project.pk}{extra}'

    def change(self, status, **extra):
        return self.as_user(self.expert).put(self.url(f'/core/api/promoter/open_visit/change_status/{self.visit.pk}/'),
                                             {'status': status, **extra}, format='json')

    # -------------------------------------------------------------- assignment
    def test_decline_needs_reason_unassigns_and_notifies_planners(self):
        url = self.url(f'/core/api/promoter/visit/{self.visit.pk}/assignment/')
        self.assertEqual(self.as_user(self.expert).post(url, {'action': 'decline'}, format='json').status_code, 400)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.api.post(url, {'action': 'decline', 'reason': 'Out of town this week'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.visit.refresh_from_db()
        self.assertIsNone(self.visit.expert_id)
        self.assertEqual(response.data['assignment']['last_decline']['reason'], 'Out of town this week')
        note = InAppNotification.objects.get(recipient=self.planner, kind='visit_declined')
        self.assertIn('Out of town', note.body)
        # No longer assigned: the worker cannot act on it again.
        self.assertEqual(self.api.post(url, {'action': 'accept'}, format='json').status_code, 404)

    def test_accept_and_start_record_acceptance(self):
        self.assertEqual(VisitSerializerState(self.visit), 'pending')
        url = self.url(f'/core/api/promoter/visit/{self.visit.pk}/assignment/')
        self.assertEqual(self.as_user(self.expert).post(url, {'action': 'accept'}, format='json').data['assignment']['state'], 'accepted')
        other = Visit.objects.create(type=self.kind, building=self.building, creator=self.planner, expert=self.expert, is_active=True)
        self.visit = other
        self.assertEqual(self.change('1').status_code, 200)
        self.assertTrue(VisitAssignmentEvent.objects.filter(visit=other, action='accepted').exists())
        response = self.as_user(self.expert).post(self.url(f'/core/api/promoter/visit/{other.pk}/assignment/'),
                                                  {'action': 'decline', 'reason': 'Too late now'}, format='json')
        self.assertEqual(response.status_code, 400)  # started work cannot be handed back

    # -------------------------------------------------------------- completion code
    def test_completion_code_is_client_only_and_rate_limited(self):
        self.kind.requires_client_code = True
        self.kind.save()
        self.assertEqual(self.change('1').status_code, 200)
        page = self.as_user(self.expert).get(self.url(f'/core/api/promoter/visit_page_settings/{self.visit.pk}/'))
        self.assertNotIn('completion_code', page.data['visit'])
        detail = self.as_user(self.client_user).get(self.url(f'/core/api/client/visits/{self.visit.pk}/'))
        code = detail.data['completion_code']
        self.assertRegex(code, r'^\d{6}$')
        self.assertTrue(detail.data['chat_open'])
        missing = self.change('2')
        self.assertEqual(missing.status_code, 400)
        self.assertIn('client_code', missing.data)
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(4):
            self.assertEqual(self.change('2', client_code=wrong).status_code, 400)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.completion_code_failures, 4)  # failures persist despite the 400
        self.assertEqual(self.change('2', client_code=wrong).status_code, 400)
        self.visit.refresh_from_db()
        self.assertNotEqual(self.visit.completion_code, code)  # rotated
        self.assertIsNotNone(self.visit.completion_code_locked_until)
        locked = self.change('2', client_code=self.visit.completion_code)
        self.assertEqual(locked.status_code, 400)
        Visit.objects.filter(pk=self.visit.pk).update(completion_code_locked_until=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.change('2', client_code=self.visit.completion_code).status_code, 200)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, Visit.COMPLETED)
        closed = self.as_user(self.client_user).get(self.url(f'/core/api/client/visits/{self.visit.pk}/'))
        self.assertEqual(closed.data['completion_code'], '')

    # -------------------------------------------------------------- chat
    def test_visit_chat_between_worker_and_current_manager(self):
        expert_url = self.url(f'/core/api/promoter/visit/{self.visit.pk}/chat/')
        client_url = self.url(f'/core/api/client/visits/{self.visit.pk}/chat/')
        with self.captureOnCommitCallbacks(execute=True):
            response = self.as_user(self.expert).post(expert_url, {'body': 'On my way, 20 minutes.'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(InAppNotification.objects.filter(recipient=self.client_user, kind='visit_chat').exists())
        with self.captureOnCommitCallbacks(execute=True):
            reply = self.as_user(self.client_user).post(client_url, {'body': 'Gate code is at the desk.'}, format='json')
        self.assertEqual(reply.status_code, 201)
        self.assertTrue(InAppNotification.objects.filter(recipient=self.expert, kind='visit_chat').exists())
        thread = self.as_user(self.rep).get(client_url).data
        self.assertEqual([m['side'] for m in thread['messages']], ['expert', 'client'])
        self.assertNotIn('0912', str(thread))  # phone-number usernames never leave the server
        self.assertEqual(self.as_user(self.rep).post(client_url, {'body': 'hi'}, format='json').status_code, 403)
        Visit.objects.filter(pk=self.visit.pk).update(status=Visit.COMPLETED)
        closed = self.as_user(self.expert).post(expert_url, {'body': 'Done'}, format='json')
        self.assertEqual(closed.status_code, 400)
        self.assertFalse(self.as_user(self.expert).get(expert_url).data['open'])

    # -------------------------------------------------------------- context and earnings
    def test_asset_context_and_earnings(self):
        model = ProductModel.objects.create(project=self.project, name='Drive', name_fa='درایو')
        product = Product.objects.create(project=self.project, model=model, serial_number='DRV-9')
        ProductElevator.objects.create(product=product, elevator=self.lift, installed_at=timezone.now())
        done = Visit.objects.create(type=self.kind, building=self.building, creator=self.planner, expert=self.expert,
                                    is_active=True, status=Visit.APPROVED)
        done.elevator.set([self.lift])
        Visit.objects.create(type=self.kind, building=self.building, creator=self.planner, expert=self.expert,
                             is_active=True, status=Visit.COMPLETED)
        context = self.as_user(self.expert).get(self.url(f'/core/api/promoter/visit/{self.visit.pk}/assets/')).data
        lift = context['elevators'][0]
        self.assertEqual(lift['installed'][0]['serial'], 'DRV-9')
        self.assertEqual([row['id'] for row in lift['history']], [done.pk])
        earnings = self.api.get(self.url('/core/api/promoter/visit/earnings/')).data
        self.assertEqual(earnings['earned'], {'count': 1, 'wage': 500000})
        self.assertEqual(earnings['pending'], {'count': 1, 'wage': 500000})

    # -------------------------------------------------------------- maintenance and alerts
    def test_maintenance_plan_opens_one_visit_per_cycle(self):
        today = timezone.localdate()
        url = self.url('/core/api/admin/maintenance_plans/')
        payload = {'elevator': self.lift.pk, 'visit_type': self.kind.pk, 'expert': self.expert.pk,
                   'interval_days': 30, 'lead_days': 7, 'next_due': (today + timedelta(days=3)).isoformat()}
        self.assertEqual(self.as_user(self.planner).post(url, {**payload, 'lead_days': 40}, format='json').status_code, 400)
        self.assertEqual(self.as_user(self.expert).post(url, payload, format='json').status_code, 403)
        created = self.as_user(self.planner).post(url, payload, format='json')
        self.assertEqual(created.status_code, 201, created.data)
        with self.captureOnCommitCallbacks(execute=True):
            opened, _ = generate_due_visits(today)
        self.assertEqual(len(opened), 1)
        visit = Visit.objects.get(pk=opened[0][1])
        self.assertEqual((visit.expert_id, visit.due_date, visit.is_active), (self.expert.pk, today + timedelta(days=3), True))
        self.assertEqual(list(visit.elevator.values_list('id', flat=True)), [self.lift.pk])
        self.assertTrue(InAppNotification.objects.filter(recipient=self.expert, kind='visit_assignment', object_id=visit.pk).exists())
        self.assertEqual(MaintenancePlan.objects.get().next_due, today + timedelta(days=33))
        self.assertEqual(generate_due_visits(today)[0], [])  # one open visit per plan
        listing = self.api.get(self.url('/core/api/admin/maintenance_plans/', elevator=self.lift.pk)).data['results']
        self.assertEqual(listing[0]['open_visit'], visit.pk)

    def test_due_alerts_are_idempotent(self):
        today = timezone.localdate()
        Visit.objects.filter(pk=self.visit.pk).update(has_due_date=True, due_date=today - timedelta(days=2))
        self.assertEqual(send_due_alerts(today), 2)  # the new delay reaches the worker and the planner once
        self.assertEqual(send_due_alerts(today), 0)
        self.assertEqual(send_due_alerts(today + timedelta(days=1)), 0)  # not repeated on later days
        Visit.objects.filter(pk=self.visit.pk).update(due_date=today - timedelta(days=10))
        self.assertEqual(send_due_alerts(today), 0)  # long-running delays stay on the dashboard instead
        Visit.objects.filter(pk=self.visit.pk).update(due_date=today + timedelta(days=1))
        self.assertEqual(send_due_alerts(today), 1)
        self.assertEqual(send_due_alerts(today + timedelta(days=1)), 1)  # and again on the due day
        self.assertTrue(InAppNotification.objects.filter(recipient=self.expert, kind='visit_due').exists())

    # -------------------------------------------------------------- part requests
    def test_part_request_fulfilment_moves_stock_to_requester(self):
        ware = Ware.objects.create(project=self.project, name_fa='کلید طبقه', is_active=True)
        store = WarehouseLocation.objects.create(name_fa='انبار مرکزی')
        store.projects.add(self.project)
        empty = WarehouseLocation.objects.create(name_fa='انبار خالی')
        empty.projects.add(self.project)
        entry = WarehouseTransaction.objects.create(project=self.project, movement_kind='OPENING')
        WarehouseTransactionLine.objects.create(transaction=entry, ware=ware, amount=10, location=store)
        url = self.url(f'/core/api/promoter/visit/{self.visit.pk}/parts/')
        with self.captureOnCommitCallbacks(execute=True):
            response = self.as_user(self.expert).post(url, {'ware': ware.pk, 'amount': 3, 'note': 'Worn contacts'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.api.post(url, {'ware': ware.pk, 'amount': 1}, format='json').status_code, 400)
        request_id = response.data['requests'][0]['id']
        self.assertTrue(InAppNotification.objects.filter(recipient=self.keeper, kind='part_request').exists())
        queue = self.as_user(self.keeper).get(self.url('/api/warehouse/v1/part_requests/', status='PENDING')).data
        self.assertEqual(queue['results'][0]['stock'], [{'location': store.pk, 'name': 'انبار مرکزی', 'amount': 10}])
        decide = self.url(f'/api/warehouse/v1/part_requests/{request_id}/decision/')
        self.assertEqual(self.api.post(decide, {'action': 'fulfill', 'location': empty.pk}, format='json').status_code, 400)
        self.assertEqual(PartRequest.objects.get().status, 'PENDING')
        with self.captureOnCommitCallbacks(execute=True):
            done = self.api.post(decide, {'action': 'fulfill', 'location': store.pk}, format='json')
        self.assertEqual(done.status_code, 200, done.data)
        self.assertEqual(sum(WarehouseTransactionLine.objects.filter(user=self.expert, ware=ware).values_list('amount', flat=True)), 3)
        self.assertEqual(self.api.post(decide, {'action': 'reject', 'note': 'duplicate'}, format='json').status_code, 400)
        self.assertTrue(InAppNotification.objects.filter(recipient=self.expert, kind='part_decision').exists())
        self.assertEqual(self.as_user(self.expert).get(self.url('/api/warehouse/v1/part_requests/')).status_code, 403)
        ops = self.as_user(self.planner).get(self.url(f'/core/api/admin/visit/{self.visit.pk}/field_ops/')).data
        self.assertEqual(ops['parts'][0]['status'], 'FULFILLED')

    # -------------------------------------------------------------- service-type settings and menus
    def test_service_type_settings_are_project_scoped_and_never_hard_deleted(self):
        planner_role = Role.objects.get(title='FO planner')
        for method in ('GET', 'PATCH', 'DELETE'):
            grant(planner_role, 'VisitTypeEditsView', method)
        other = Project.objects.create(name='Other ops')
        foreign = VisitType.objects.create(project=other, title='Foreign')
        api = self.as_user(self.planner)
        self.assertEqual(api.patch(self.url(f'/core/api/admin/visit_type/edits/{foreign.pk}/'),
                                   {'default_wage': 1}, format='json').status_code, 404)
        response = api.patch(self.url(f'/core/api/admin/visit_type/edits/{self.kind.pk}/'),
                             {'requires_client_code': True, 'default_wage': 700000, 'project': other.pk}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.kind.refresh_from_db()
        self.assertEqual((self.kind.requires_client_code, self.kind.default_wage, self.kind.project_id),
                         (True, 700000, self.project.pk))  # project is not writable
        self.assertEqual(api.delete(self.url(f'/core/api/admin/visit_type/edits/{self.kind.pk}/')).status_code, 204)
        self.assertTrue(Visit.objects.filter(pk=self.visit.pk).exists())  # visits survive; the type is retired
        self.kind.refresh_from_db()
        self.assertFalse(self.kind.is_active)

    def test_menu_provisioning_previews_then_places_pages_under_groups(self):
        from io import StringIO
        from django.core.management import call_command
        from auth_app.models import AdminMenu
        role = Role.objects.get(title='FO keeper')
        group = AdminMenu.objects.create(project=self.project, role=role, priority=1, verbose_name='انبار',
                                         frontend_route_url='/warehouse/warelist')
        call_command('provision_field_ops_menus', '--project', self.project.pk, '--role', role.pk, stdout=StringIO())
        self.assertFalse(AdminMenu.objects.filter(frontend_route_url='/warehouse/part-requests').exists())
        call_command('provision_field_ops_menus', '--project', self.project.pk, '--role', role.pk, '--apply', stdout=StringIO())
        call_command('provision_field_ops_menus', '--project', self.project.pk, '--role', role.pk, '--apply', stdout=StringIO())
        row = AdminMenu.objects.get(frontend_route_url='/warehouse/part-requests')
        self.assertEqual(row.parent_id, group.pk)
        self.assertTrue(row.active_icon.startswith('data:image/svg+xml'))
        self.assertEqual(AdminMenu.objects.filter(frontend_route_url='/visitmanagment/visit-types', parent=None).count(), 1)


def VisitSerializerState(visit):
    from visit.field_ops import assignment_state
    return assignment_state(visit)['state']
