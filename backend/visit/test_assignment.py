"""Skill-, quality- and priority-aware assignment: eligibility, ranking, plan, apply, API scope, report parts."""
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auth_app.models import ExtendedUser, Project, Role, RoleAssignment, RoleView, ViewMethod
from notification.models import InAppNotification
from visit.assignment import Context, apply_assignment, AssignmentError, build_plan, candidates_for, evaluate, visit_facts
from visit.models import (Building, BuildingClient, Client, ClientVisitFeedback, ExpertProfile, ExpertSkill,
                          ExpertTimeOff, PriorityAssignment, PriorityFactor, PriorityOption, ServiceRequirement,
                          ServiceRequestSubmission, Skill, UserClient, Visit, VisitType)
from visit.report_snapshot import capture_report_snapshot
from warehouse.models import PartRequest, Unit, Ware

FLAGS = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'PATCH': 'can_update', 'DELETE': 'can_delete'}
PLANNER_ENDPOINTS = [
    ('AdminUpdateVisitView', 'PUT'), ('AssignmentOverviewView', 'GET'), ('AssignmentPlanView', 'GET'),
    ('AssignmentApplyView', 'POST'), ('AssignmentExpertView', 'PUT'), ('AssignmentTimeOffView', 'POST'),
    ('AssignmentTimeOffDetailView', 'DELETE'), ('AssignmentSkillListView', 'POST'), ('AssignmentSkillDetailView', 'PUT'),
    ('AssignmentSkillDetailView', 'DELETE'), ('AssignmentRequirementView', 'PUT'), ('AssignmentSettingView', 'PUT'),
]


def grant(role, name, method):
    view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
    RoleView.objects.update_or_create(role=role, view_method_name=view_method, defaults={FLAGS[method]: True})


class AssignmentTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Assign')
        self.planner = User.objects.create(username='as-planner')
        self.senior = User.objects.create(username='as-senior', first_name='Sara', last_name='Senior')
        self.junior = User.objects.create(username='as-junior', first_name='Jim', last_name='Junior')
        self.client_user = User.objects.create(username='as-client')
        ExtendedUser.objects.create(user=self.planner, role='M')
        planner_role = Role.objects.create(title='AS planner', title_abbreviation='M', asset_scope='project')
        worker_role = Role.objects.create(title='AS worker', title_abbreviation='P', asset_scope='assigned')
        client_role = Role.objects.create(title='AS client', title_abbreviation='C', asset_scope='client')
        RoleAssignment.objects.create(user=self.planner, role=planner_role, project=self.project)
        for user in (self.senior, self.junior):
            RoleAssignment.objects.create(user=user, role=worker_role, project=self.project)
        RoleAssignment.objects.create(user=self.client_user, role=client_role, project=self.project)
        for name, method in PLANNER_ENDPOINTS:
            grant(planner_role, name, method)
        grant(worker_role, 'AssignmentOverviewView', 'GET')  # a worker role must still be refused (project scope only)
        self.building = Building.objects.create(project=self.project, code='AS-1', verbose_name='Tower')
        self.hospital = Building.objects.create(project=self.project, code='AS-H', verbose_name='Clinic')
        client = Client.objects.create(project=self.project, name='AS client')
        UserClient.objects.create(client=client, user=self.client_user)
        BuildingClient.objects.create(building=self.building, client=client)
        self.kind = VisitType.objects.create(project=self.project, title='Board repair', complexity=3)
        self.boards = Skill.objects.create(project=self.project, name='Boards')
        self.doors = Skill.objects.create(project=self.project, name='Doors')
        ServiceRequirement.objects.create(visit_type=self.kind, skill=self.boards, min_level=3, is_required=True)
        ServiceRequirement.objects.create(visit_type=self.kind, skill=self.doors, min_level=2, is_required=False)
        ExpertProfile.objects.create(project=self.project, user=self.senior, grade=5, work_days=[0, 1, 2, 5, 6])
        ExpertProfile.objects.create(project=self.project, user=self.junior, grade=2, work_days=[0, 1, 2, 5, 6])
        ExpertSkill.objects.create(project=self.project, user=self.senior, skill=self.boards, level=5)
        ExpertSkill.objects.create(project=self.project, user=self.senior, skill=self.doors, level=3)
        ExpertSkill.objects.create(project=self.project, user=self.junior, skill=self.boards, level=2)
        self.api = APIClient()

    def visit(self, building=None, **extra):
        return Visit.objects.create(type=self.kind, building=building or self.building, creator=self.planner,
                                    is_active=True, **extra)

    def url(self, path, **query):
        extra = ''.join(f'&{key}={value}' for key, value in query.items())
        return f'{path}?p={self.project.pk}{extra}'

    def ranked(self, visit):
        ctx = Context(self.project.pk)
        return candidates_for(ctx, visit)[1]

    # ------------------------------------------------------------ eligibility
    def test_skill_and_grade_block_an_unqualified_worker(self):
        visit = self.visit()
        ranked = self.ranked(visit)
        self.assertEqual([item['user'] for item in ranked], [self.senior.pk, self.junior.pk])
        self.assertTrue(ranked[0]['eligible'])
        junior = ranked[1]
        self.assertFalse(junior['eligible'])
        self.assertTrue(any('Boards' in text and 'سطح 3' in text for text in junior['blockers']))
        self.assertTrue(any('گرید 2' in text for text in junior['blockers']))
        self.assertTrue(any('Doors' in text for text in junior['warnings']))  # preferred skill only warns

    def test_time_off_and_capacity_block_and_planning_switch(self):
        due = timezone.localdate() + timedelta(days=3)
        visit = self.visit(has_due_date=True, due_date=due)
        ExpertTimeOff.objects.create(project=self.project, user=self.senior, start_date=due - timedelta(days=1),
                                     end_date=due + timedelta(days=1), reason='Pilgrimage')
        senior = next(item for item in self.ranked(visit) if item['user'] == self.senior.pk)
        self.assertFalse(senior['eligible'])
        self.assertTrue(any('مرخصی' in text for text in senior['blockers']))
        ExpertTimeOff.objects.all().delete()
        ExpertProfile.objects.filter(user=self.senior).update(max_open=1)
        self.visit(expert=self.senior, promoter=self.senior)
        senior = next(item for item in self.ranked(visit) if item['user'] == self.senior.pk)
        self.assertFalse(senior['eligible'])
        ExpertProfile.objects.filter(user=self.senior).update(max_open=10, is_assignable=False)
        senior = next(item for item in self.ranked(visit) if item['user'] == self.senior.pk)
        self.assertIn('در تنظیمات برای تخصیص غیرفعال است', senior['blockers'])

    def test_busy_day_and_rest_day_lower_the_score_but_do_not_block(self):
        today = timezone.localdate()
        thursday = today + timedelta(days=(3 - today.weekday()) % 7 or 7)  # Python weekday 3 is not a work day
        visit = self.visit(has_due_date=True, due_date=thursday)
        senior = next(item for item in self.ranked(visit) if item['user'] == self.senior.pk)
        self.assertTrue(senior['eligible'])
        self.assertTrue(any('روزهای کاری' in text for text in senior['warnings']))
        self.assertLess(senior['factors']['workload']['value'], 100 - 29)

    # ------------------------------------------------------------ quality
    def test_quality_uses_review_rating_and_punctuality_with_shrinkage(self):
        ctx = Context(self.project.pk)
        self.assertEqual(ctx.quality(self.senior.pk)['score'], 60.0)  # no history yet: neutral
        self.assertFalse(ctx.quality(self.senior.pk)['has_history'])
        for index in range(8):
            done = Visit.objects.create(type=self.kind, building=self.building, creator=self.planner, is_active=True,
                                        expert=self.senior, promoter=self.senior, has_due_date=True,
                                        due_date=timezone.localdate() + timedelta(days=1))
            capture_report_snapshot(done, self.senior)
            Visit.objects.filter(pk=done.pk).update(status=Visit.APPROVED)
            ClientVisitFeedback.objects.create(visit=done, user=self.client_user, rating=5)
        bad = Visit.objects.create(type=self.kind, building=self.building, creator=self.planner, is_active=True,
                                   expert=self.junior, promoter=self.junior)
        Visit.objects.filter(pk=bad.pk).update(status=Visit.REJECTED)
        ctx = Context(self.project.pk)
        strong, weak = ctx.quality(self.senior.pk), ctx.quality(self.junior.pk)
        self.assertEqual(strong['score'], 100.0)  # eight clean, rated, on-time reports: full confidence
        self.assertEqual((strong['reviewed'], strong['rated'], strong['avg_rating']), (8, 8, 5.0))
        self.assertLess(weak['score'], 60.0)
        self.assertGreater(weak['score'], 50.0)  # one rejection is a hint, not a verdict (confidence 1/8)

    def test_corrected_reports_count_less_than_clean_ones(self):
        done = Visit.objects.create(type=self.kind, building=self.building, creator=self.planner, is_active=True,
                                    expert=self.junior, promoter=self.junior)
        capture_report_snapshot(done, self.junior)
        capture_report_snapshot(done, self.junior, new_version=True)
        Visit.objects.filter(pk=done.pk).update(status=Visit.APPROVED)
        self.assertEqual(Context(self.project.pk).quality(self.junior.pk)['first_pass'], 60.0)

    # ------------------------------------------------------------ priority
    def sensitive(self, building):
        factor = PriorityFactor.objects.create(project=self.project, name='Use', target='building', weight=1,
                                               default_value=10)
        option = PriorityOption.objects.create(factor=factor, label='Medical', value=100)
        PriorityAssignment.objects.create(factor=factor, option=option, building=building)
        from visit.priority import recompute_project
        recompute_project(self.project.pk)
        building.refresh_from_db()

    def test_plan_places_sensitive_work_first_and_reserves_capacity(self):
        self.sensitive(self.hospital)
        ExpertSkill.objects.update_or_create(user=self.junior, skill=self.boards,
                                             defaults={'project': self.project, 'level': 4})
        ExpertProfile.objects.filter(user=self.junior).update(grade=4)
        ExpertProfile.objects.filter(user=self.senior).update(max_open=1)  # room for one more visit only
        ordinary = self.visit()
        urgent = self.visit(building=self.hospital)
        plan = build_plan(self.project.pk)
        self.assertEqual([row['visit'] for row in plan['proposals']], [urgent.pk, ordinary.pk])
        first, second = plan['proposals']
        self.assertEqual(first['priority'], 100.0)
        self.assertEqual(first['suggested']['user'], self.senior.pk)  # the best worker goes to the sensitive visit
        self.assertEqual(second['suggested']['user'], self.junior.pk)  # senior is full after the first proposal
        self.assertEqual(plan['proposals'][0]['alternatives'][0]['user'], self.junior.pk)

    def test_urgent_visits_weigh_skill_and_quality_more(self):
        ordinary = self.visit()
        self.sensitive(self.hospital)
        urgent = self.visit(building=self.hospital)
        ctx = Context(self.project.pk)
        weights = lambda visit: evaluate(ctx, self.senior, visit_facts(visit))['factors']  # noqa: E731
        self.assertEqual(weights(urgent)['skill']['weight'], round(4 * 1.5, 2))
        self.assertEqual(weights(ordinary)['skill']['weight'], 4.0)
        self.assertEqual(weights(urgent)['workload']['weight'], 2.0)

    def test_unscored_pending_requests_are_planned_too(self):
        request = Visit.objects.create(type=self.kind, building=self.building, creator=self.client_user, is_active=False)
        submission = ServiceRequestSubmission.objects.create(
            project=self.project, creator=self.client_user, request_key='11111111-1111-1111-1111-111111111111',
            payload_hash='x')
        submission.visits.add(request)
        plan = build_plan(self.project.pk)
        row = next(item for item in plan['proposals'] if item['visit'] == request.pk)
        self.assertTrue(row['pending_request'])
        self.assertIsNone(row['priority'])

    # ------------------------------------------------------------ apply
    def test_apply_rechecks_rules_notifies_and_supports_force_and_activation(self):
        visit = self.visit()
        with self.assertRaises(AssignmentError):
            apply_assignment(self.project.pk, visit.pk, self.junior.pk, self.planner)  # blocked: skill and grade
        with self.captureOnCommitCallbacks(execute=True):
            apply_assignment(self.project.pk, visit.pk, self.senior.pk, self.planner)
        visit.refresh_from_db()
        self.assertEqual((visit.expert_id, visit.promoter_id), (self.senior.pk, self.senior.pk))
        self.assertTrue(InAppNotification.objects.filter(recipient=self.senior, kind='visit_assignment',
                                                         object_id=visit.pk).exists())
        with self.assertRaises(AssignmentError):
            apply_assignment(self.project.pk, visit.pk, self.senior.pk, self.planner)  # already assigned
        apply_assignment(self.project.pk, visit.pk, self.junior.pk, self.planner, force=True, reassign=True)
        visit.refresh_from_db()
        self.assertEqual(visit.expert_id, self.junior.pk)  # an explicit reassignment replaces the worker
        other = self.visit()
        apply_assignment(self.project.pk, other.pk, self.junior.pk, self.planner, force=True)
        other.refresh_from_db()
        self.assertEqual(other.expert_id, self.junior.pk)
        stranger = User.objects.create(username='as-stranger')
        third = self.visit()
        with self.assertRaises(AssignmentError):
            apply_assignment(self.project.pk, third.pk, stranger.pk, self.planner, force=True)  # never forceable
        pending = Visit.objects.create(type=self.kind, building=self.building, creator=self.client_user, is_active=False)
        with self.assertRaises(AssignmentError):
            apply_assignment(self.project.pk, pending.pk, self.senior.pk, self.planner)
        ServiceRequestSubmission.objects.create(
            project=self.project, creator=self.client_user, request_key='22222222-2222-2222-2222-222222222222',
            payload_hash='y').visits.add(pending)
        apply_assignment(self.project.pk, pending.pk, self.senior.pk, self.planner, activate=True)
        pending.refresh_from_db()
        self.assertTrue(pending.is_active)

    # ------------------------------------------------------------ API
    def test_api_scope_and_planning_flow(self):
        visit = self.visit()
        self.assertEqual(self.api.get(self.url('/core/api/admin/assignment/overview/')).status_code, 401)
        self.api.force_authenticate(self.senior)
        self.assertEqual(self.api.get(self.url('/core/api/admin/assignment/overview/')).status_code, 403)
        self.api.force_authenticate(self.planner)
        overview = self.api.get(self.url('/core/api/admin/assignment/overview/')).data
        self.assertEqual({row['name'] for row in overview['experts']}, {'Sara Senior', 'Jim Junior'})
        self.assertEqual(overview['unassigned'], 1)
        self.assertEqual(overview['visit_types'][0]['complexity'], 3)
        ranked = self.api.get(self.url('/core/api/admin/assignment/plan/', visit=visit.pk)).data
        self.assertEqual(ranked['candidates'][0]['user'], self.senior.pk)
        # Skills catalog
        created = self.api.post(self.url('/core/api/admin/assignment/skills/'), {'name': 'Hydraulics'}, format='json')
        self.assertEqual(created.status_code, 201)
        self.assertEqual(self.api.post(self.url('/core/api/admin/assignment/skills/'), {'name': 'Hydraulics'},
                                       format='json').status_code, 400)
        skill_id = created.data['id']
        # Expert profile with skills; unknown skills are refused
        body = {'grade': 4, 'work_days': [5, 6, 0], 'daily_capacity': 3, 'max_open': 6, 'is_assignable': True,
                'skills': [{'skill': skill_id, 'level': 4}, {'skill': self.boards.pk, 'level': 3}]}
        url = self.url(f'/core/api/admin/assignment/experts/{self.junior.pk}/')
        self.assertEqual(self.api.put(url, {**body, 'skills': [{'skill': 99999, 'level': 2}]}, format='json').status_code, 400)
        self.assertEqual(self.api.put(url, {**body, 'grade': 9}, format='json').status_code, 400)
        response = self.api.put(url, body, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual({row['skill'] for row in response.data['skills']}, {skill_id, self.boards.pk})
        self.assertEqual(self.api.put(self.url('/core/api/admin/assignment/experts/%d/' % self.planner.pk), body,
                                      format='json').status_code, 400)  # not a field worker
        # Service requirements
        requirement_url = self.url(f'/core/api/admin/assignment/requirements/{self.kind.pk}/')
        response = self.api.put(requirement_url, {'complexity': 2, 'requirements': [
            {'skill': self.boards.pk, 'min_level': 3, 'is_required': True}]}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(ServiceRequirement.objects.filter(visit_type=self.kind).count(), 1)
        # The junior (grade 4, boards 3) is now eligible; apply through the API.
        ranked = self.api.get(self.url('/core/api/admin/assignment/plan/', visit=visit.pk)).data['candidates']
        self.assertTrue(all(item['eligible'] for item in ranked))
        applied = self.api.post(self.url('/core/api/admin/assignment/apply/'), {'assignments': [
            {'visit': visit.pk, 'expert': self.junior.pk}, {'visit': 999999, 'expert': self.senior.pk}]}, format='json')
        self.assertEqual([row['ok'] for row in applied.data['results']], [True, False])
        # Time off and settings
        off = self.api.post(self.url(f'/core/api/admin/assignment/experts/{self.senior.pk}/time_off/'), {
            'start_date': str(timezone.localdate()), 'end_date': str(timezone.localdate() + timedelta(days=2)),
            'reason': 'Leave'}, format='json')
        self.assertEqual(off.status_code, 201)
        self.assertEqual(self.api.post(self.url(f'/core/api/admin/assignment/experts/{self.senior.pk}/time_off/'), {
            'start_date': '2026-01-10', 'end_date': '2026-01-05'}, format='json').status_code, 400)
        self.assertEqual(self.api.delete(self.url(f'/core/api/admin/assignment/time_off/{off.data["id"]}/')).status_code, 204)
        settings_url = self.url('/core/api/admin/assignment/settings/')
        weights = {'skill_weight': 0, 'quality_weight': 0, 'workload_weight': 0, 'familiarity_weight': 0, 'urgent_boost': 1.5}
        self.assertEqual(self.api.put(settings_url, weights, format='json').status_code, 400)
        weights['quality_weight'] = 8
        self.assertEqual(self.api.put(settings_url, weights, format='json').data['quality_weight'], 8.0)
        self.assertEqual(self.api.delete(self.url(f'/core/api/admin/assignment/skills/{skill_id}/')).data['is_active'], False)

    def test_projects_stay_separate(self):
        other = Project.objects.create(name='Other assign')
        foreign = Skill.objects.create(project=other, name='Foreign')
        self.api.force_authenticate(self.planner)
        url = self.url(f'/core/api/admin/assignment/skills/{foreign.pk}/')
        self.assertEqual(self.api.put(url, {'name': 'Taken'}, format='json').status_code, 404)
        self.assertEqual(self.api.get(self.url('/core/api/admin/assignment/plan/', visit=Visit.objects.create(
            type=VisitType.objects.create(project=other, title='X'), building=Building.objects.create(project=other, code='O-1'),
            creator=self.planner).pk)).status_code, 404)

    # ------------------------------------------------------------ report parts and wage
    def test_snapshot_freezes_parts_and_wage_only_when_the_service_type_opts_in(self):
        unit = Unit.objects.create(unit_fa='عدد')
        ware = Ware.objects.create(project=self.project, name_fa='کنتاکتور', unit=unit, is_active=True)
        self.kind.default_wage = 750000
        self.kind.save()
        visit = self.visit(expert=self.senior, promoter=self.senior)
        Visit.objects.filter(pk=visit.pk).update(total_wage=750000)
        visit.refresh_from_db()
        PartRequest.objects.create(project=self.project, visit=visit, requester=self.senior, ware=ware, amount=2,
                                   status=PartRequest.FULFILLED)
        PartRequest.objects.create(project=self.project, visit=visit, requester=self.senior, ware=ware, amount=5,
                                   status=PartRequest.PENDING)
        first = capture_report_snapshot(visit, self.senior)
        self.assertEqual(first.payload['parts'], [{'name': 'کنتاکتور', 'amount': 2, 'unit': 'عدد'}])
        self.assertIsNone(first.payload['wage'])  # the fee is also the worker's pay: hidden by default
        VisitType.objects.filter(pk=self.kind.pk).update(show_wage_in_report=True)
        visit = Visit.objects.select_related('type').get(pk=visit.pk)
        second = capture_report_snapshot(visit, self.senior, new_version=True)
        self.assertEqual(second.payload['wage'], 750000)
        from visit.report_pdf import render_report_pdf
        pdf = render_report_pdf(second)
        self.assertTrue(pdf.read(5).startswith(b'%PDF'))
        # The client's detail carries the frozen parts and wage.
        grant(Role.objects.get(title='AS client'), 'ClientVisitsAPIView', 'GET')
        Visit.objects.filter(pk=visit.pk).update(status=Visit.COMPLETED)
        self.api.force_authenticate(self.client_user)
        detail = self.api.get(self.url(f'/core/api/client/visits/{visit.pk}/')).data
        self.assertEqual((detail['parts'][0]['amount'], detail['wage']), (2, 750000))
