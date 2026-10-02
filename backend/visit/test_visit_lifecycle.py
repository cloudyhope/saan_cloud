"""End-to-end visit lifecycle: start, finish, review, return for correction and re-finish."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import ExtendedUser, Project, Role, RoleAssignment, RoleView, ViewMethod
from notification.models import InAppNotification
from visit.models import (Answer, AnswerType, Building, BuildingClient, Client, Question, QuestionType, UserClient,
                          Visit, VisitType)


def grant(role, name, method):
    view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
    flag = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'PATCH': 'can_update'}[method]
    RoleView.objects.update_or_create(role=role, view_method_name=view_method, defaults={flag: True})


class VisitLifecycleTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Lifecycle')
        self.expert = User.objects.create(username='life-expert')
        self.other_expert = User.objects.create(username='life-other')
        self.admin = User.objects.create(username='life-admin')
        self.client_user = User.objects.create(username='life-client')
        ExtendedUser.objects.bulk_create([ExtendedUser(user=self.admin, role='M')])
        self.expert_role = Role.objects.create(title='Life expert', title_abbreviation='P', asset_scope='assigned')
        self.admin_role = Role.objects.create(title='Life admin', title_abbreviation='M', asset_scope='project')
        self.client_role = Role.objects.create(title='Life client', title_abbreviation='C', asset_scope='client')
        for user in (self.expert, self.other_expert):
            RoleAssignment.objects.create(user=user, role=self.expert_role, project=self.project)
        RoleAssignment.objects.create(user=self.admin, role=self.admin_role, project=self.project)
        RoleAssignment.objects.create(user=self.client_user, role=self.client_role, project=self.project)
        for name, method in [('FrontVisitPageSettingsView', 'GET'), ('PromoterVisitStatusChangeAPIView', 'PUT'),
                             ('PromoterAnswersQuestionsView', 'POST'), ('PromoterVisitsAPIView', 'GET'),
                             ('PromoterVisistsHistory', 'GET')]:
            grant(self.expert_role, name, method)
        grant(self.admin_role, 'FrontVisitPageSettingsView', 'GET')
        grant(self.admin_role, 'AdminUpdateVisitStatusView', 'PUT')
        building = Building.objects.create(project=self.project, code='LIFE-1', verbose_name='Life building')
        client = Client.objects.create(project=self.project, name='Life client')
        UserClient.objects.create(client=client, user=self.client_user)
        BuildingClient.objects.create(building=building, client=client)
        self.kind = VisitType.objects.create(project=self.project, title='Service')
        section = QuestionType.objects.create(project=self.project, visit_type=self.kind, name='Safety',
                                              is_mandatory=True)
        self.question = Question.objects.create(question_type=section, text='Doors safe?', type='GE')
        yes_no, _ = AnswerType.objects.get_or_create(name='YesNo', field='bool')
        self.question.answer_type.set([yes_no])
        self.visit = Visit.objects.create(type=self.kind, building=building, creator=self.admin,
                                          expert=self.expert, promoter=self.expert, is_active=True)
        self.api = APIClient()

    def as_user(self, user):
        self.api.force_authenticate(user)
        return self.api

    def url(self, path):
        return f'{path}?p={self.project.pk}'

    def set_status(self, status):
        return self.as_user(self.expert).put(
            self.url(f'/core/api/promoter/open_visit/change_status/{self.visit.pk}/'), {'status': status},
            format='json')

    def review(self, status, reason=''):
        payload = {'status': status}
        if reason:
            payload['rejection_reason'] = reason
        return self.as_user(self.admin).put(
            self.url(f'/core/api/admin/visit_status_change/{self.visit.pk}/'), payload, format='json')

    def answer(self, value):
        return self.as_user(self.expert).post(self.url('/core/api/promoter/answer_to_question/'), {
            'visit': self.visit.pk, 'question': self.question.pk, 'bool': value}, format='json')

    def settings(self, user):
        return self.as_user(user).get(self.url(f'/core/api/promoter/visit_page_settings/{self.visit.pk}/'))

    def test_page_settings_report_progress_and_editability(self):
        response = self.settings(self.expert)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['editable'])
        self.assertTrue(response.data['is_assignee'])
        self.assertEqual(response.data['questions'][0]['question_count'], 1)
        self.assertEqual(response.data['questions'][0]['required_count'], 1)
        self.assertEqual(response.data['requirements']['questions'], [self.question.pk])
        self.assertIsNone(response.data['report_version'])
        # A project reviewer may read the page without being the assignee, never edit it.
        response = self.settings(self.admin)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data['editable'])
        self.assertFalse(response.data['is_assignee'])
        # Another field worker of the same project still cannot read it.
        self.assertEqual(self.settings(self.other_expert).status_code, 404)

    def test_finish_return_for_correction_and_refinish(self):
        self.assertEqual(self.set_status(Visit.COMPLETED).status_code, 400)  # not started
        self.assertEqual(self.set_status(Visit.INPROGRESS).status_code, 200)
        self.visit.refresh_from_db()
        self.assertIsNotNone(self.visit.start_datetime)
        response = self.set_status(Visit.COMPLETED)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['requirements']['questions'], [self.question.pk])
        self.assertEqual(self.answer(True).status_code, 200)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.set_status(Visit.COMPLETED).status_code, 200)
        self.assertEqual(self.visit.report_snapshots.count(), 1)
        self.assertTrue(InAppNotification.objects.filter(recipient=self.admin, kind='visit_review').exists())
        self.assertTrue(InAppNotification.objects.filter(recipient=self.client_user, kind='visit_report').exists())
        self.assertFalse(self.settings(self.expert).data['editable'])
        self.assertEqual(self.answer(False).status_code, 404)  # closed after completion

        self.assertEqual(self.review(Visit.RETRY).status_code, 400)  # a reason is required
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.review(Visit.RETRY, 'Photo is unreadable').status_code, 200)
        self.assertTrue(InAppNotification.objects.filter(recipient=self.expert, kind='visit_returned').exists())
        tasks = self.as_user(self.expert).get(self.url('/core/api/promoter/open_visits/list/'))
        self.assertIn(self.visit.pk, [row['id'] for row in tasks.data])
        page = self.settings(self.expert).data
        self.assertTrue(page['editable'])
        self.assertEqual(page['visit']['rejection_reason'], 'Photo is unreadable')

        self.assertEqual(self.set_status(Visit.INPROGRESS).status_code, 200)
        self.assertEqual(self.answer(False).status_code, 200)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.set_status(Visit.COMPLETED).status_code, 200)
        versions = list(self.visit.report_snapshots.order_by('version').values_list('version', flat=True))
        self.assertEqual(versions, [1, 2])
        latest = self.visit.report_snapshots.order_by('-version').first()
        self.assertIs(latest.payload['answers'][0]['bool'], False)
        self.assertEqual(self.settings(self.expert).data['report_version'], 2)

        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.review(Visit.APPROVED).status_code, 200)
        self.assertTrue(InAppNotification.objects.filter(recipient=self.expert, kind='visit_reviewed').exists())
        history = self.as_user(self.expert).get(self.url('/core/api/promoter/visit/history/'))
        self.assertEqual([row['id'] for row in history.data], [self.visit.pk])

    def test_review_accepts_only_final_transitions_from_completed_work(self):
        self.assertEqual(self.review(Visit.APPROVED).status_code, 400)  # still open
        self.visit.status = Visit.COMPLETED
        self.visit.save()
        self.assertEqual(self.review(Visit.INPROGRESS).status_code, 400)
        self.assertEqual(self.review(Visit.REJECTED).status_code, 400)  # missing reason
        self.assertEqual(self.review(Visit.REJECTED, 'Wrong building').status_code, 200)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, Visit.REJECTED)
        self.assertEqual(self.visit.checked_by, self.admin)

    def test_history_lists_visits_where_user_is_only_the_expert(self):
        self.visit.promoter = None
        self.visit.status = Visit.APPROVED
        self.visit.save()
        Answer.objects.create(visit=self.visit, question=self.question, bool=True)
        history = self.as_user(self.expert).get(self.url('/core/api/promoter/visit/history/'))
        self.assertEqual(history.status_code, 200)
        self.assertEqual([row['id'] for row in history.data], [self.visit.pk])
        self.assertEqual(self.as_user(self.other_expert).get(
            self.url('/core/api/promoter/visit/history/')).data, [])

    def test_report_keeps_score_and_price_answers(self):
        from visit.report_pdf import _answer_text
        from visit.report_snapshot import capture_report_snapshot
        score = Question.objects.create(question_type=self.question.question_type, text='Rail lubrication', type='GE')
        price = Question.objects.create(question_type=self.question.question_type, text='Parts cost', type='GE')
        Answer.objects.create(visit=self.visit, question=score, score=4)
        Answer.objects.create(visit=self.visit, question=price, price=1250000)
        payload = capture_report_snapshot(self.visit, self.expert).payload
        by_question = {row['question']: row for row in payload['answers']}
        self.assertEqual(by_question['Rail lubrication']['score'], 4)
        self.assertEqual(by_question['Parts cost']['price'], 1250000)
        self.assertIn('4', _answer_text(by_question['Rail lubrication']))
        self.assertIn('1,250,000', _answer_text(by_question['Parts cost']))
