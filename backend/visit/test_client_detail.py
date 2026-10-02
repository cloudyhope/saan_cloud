"""Client visit detail shows only owned work and released answers."""
from django.contrib.auth.models import User
from django.test import TestCase
from io import BytesIO
from types import SimpleNamespace
from copy import deepcopy
import hashlib
import json
from pypdf import PdfReader
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Answer, Building, BuildingClient, Client, ClientVisitFeedback, Question, QuestionType, UserClient, Visit, VisitType
from visit.report_snapshot import capture_report_snapshot
from visit.report_pdf import render_report_pdf


class ClientVisitDetailTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Client detail one')
        self.other_project = Project.objects.create(name='Client detail two')
        self.user = User.objects.create(username='client-detail')
        self.worker = User.objects.create(username='detail-worker', first_name='Sara')
        role = Role.objects.create(title='Detail client', title_abbreviation='D', asset_scope='client')
        RoleAssignment.objects.create(user=self.user, role=role, project=self.project)
        method, _ = ViewMethod.objects.get_or_create(view_name='ClientVisitsAPIView', method='GET')
        self.grant = RoleView.objects.create(role=role, view_method_name=method, can_view=True)
        for method_name in ('GET', 'POST'):
            feedback_method, _ = ViewMethod.objects.get_or_create(
                view_name='ClientVisitFeedbackAPIView', method=method_name)
            RoleView.objects.create(role=role, view_method_name=feedback_method,
                                    can_view=method_name == 'GET', can_create=method_name == 'POST')
        client = Client.objects.create(project=self.project, name='Own client')
        UserClient.objects.create(client=client, user=self.user)
        building = Building.objects.create(project=self.project, code='OWN-DETAIL')
        BuildingClient.objects.create(building=building, client=client)
        kind = VisitType.objects.create(project=self.project, title='Inspection')
        self.visit = Visit.objects.create(type=kind, building=building, creator=self.worker,
                                          expert=self.worker, status=Visit.INPROGRESS, is_active=True)
        question_type = QuestionType.objects.create(project=self.project, visit_type=kind, name='Safety')
        question = Question.objects.create(question_type=question_type, text='Door secure?', type='GE')
        Answer.objects.create(visit=self.visit, question=question, bool=True)
        foreign_building = Building.objects.create(project=self.other_project, code='FOREIGN-DETAIL')
        foreign_type = VisitType.objects.create(project=self.other_project, title='Other')
        self.foreign = Visit.objects.create(type=foreign_type, building=foreign_building,
                                            creator=self.worker, status=Visit.COMPLETED)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def url(self, visit):
        return f'/core/api/client/visits/{visit.pk}/?p={self.project.pk}'

    def feedback_url(self, visit):
        return f'/core/api/client/visits/{visit.pk}/feedback/?p={self.project.pk}'

    def pdf_url(self, visit):
        return f'/core/api/client/visits/{visit.pk}/report.pdf?p={self.project.pk}'

    def test_owned_visit_and_released_report(self):
        response = self.api.get(self.url(self.visit))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['building']['code'], 'OWN-DETAIL')
        self.assertEqual(response.data['expert_name'], 'Sara')
        self.assertEqual(response.data['report'], [])
        self.visit.status = Visit.COMPLETED
        self.visit.save()
        response = self.api.get(self.url(self.visit))
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['report'][0]['question'], 'Door secure?')
        self.assertIs(response.data['report'][0]['bool'], True)
        capture_report_snapshot(self.visit, self.worker)
        answer = Answer.objects.get(visit=self.visit)
        answer.bool = False
        answer.save()
        response = self.api.get(self.url(self.visit))
        self.assertEqual(response.data['report_version'], 1)
        self.assertIs(response.data['report'][0]['bool'], True)

    def test_foreign_and_missing_grant_are_denied(self):
        self.assertEqual(self.api.get(self.url(self.foreign)).status_code, 404)
        self.grant.can_view = False
        self.grant.save()
        self.assertEqual(self.api.get(self.url(self.visit)).status_code, 403)

    def test_feedback_and_receipt_are_owned_and_one_way(self):
        self.assertEqual(self.api.get(self.feedback_url(self.foreign)).status_code, 404)
        self.assertEqual(self.api.post(self.feedback_url(self.visit),
                                       {'rating': 5}, format='json').status_code, 400)
        self.visit.status = Visit.COMPLETED
        self.visit.save()
        self.assertEqual(self.api.post(self.feedback_url(self.visit),
                                       {'note': ''}, format='json').status_code, 400)
        self.assertEqual(ClientVisitFeedback.objects.filter(visit=self.visit).count(), 0)
        self.assertEqual(self.api.post(self.feedback_url(self.foreign),
                                       {'rating': 5}, format='json').status_code, 404)
        self.assertEqual(self.api.post(self.feedback_url(self.visit),
                                       {'rating': 6}, format='json').status_code, 400)
        response = self.api.post(self.feedback_url(self.visit),
                                 {'rating': 5, 'note': 'Helpful', 'received': True}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertIsNotNone(response.data['received_at'])
        self.assertEqual(self.api.post(self.feedback_url(self.visit),
                                       {'received': False}, format='json').status_code, 400)
        self.assertEqual(self.api.post(self.feedback_url(self.visit),
                                       {'rating': 4}, format='json').status_code, 200)
        self.assertEqual(self.api.post(self.feedback_url(self.visit),
                                       {'note': ''}, format='json').status_code, 200)
        self.assertEqual(ClientVisitFeedback.objects.filter(visit=self.visit, user=self.user).count(), 1)
        self.assertEqual(self.api.get(self.feedback_url(self.visit)).data['rating'], 4)
        self.assertEqual(self.api.get(self.feedback_url(self.visit)).data['note'], '')

    def test_pdf_uses_fixed_snapshot_and_client_scope(self):
        self.assertEqual(self.api.get(self.pdf_url(self.visit)).status_code, 409)
        self.assertEqual(self.api.get(self.pdf_url(self.foreign)).status_code, 404)
        self.visit.status = Visit.COMPLETED
        self.visit.save()
        self.assertEqual(self.api.get(self.pdf_url(self.visit)).status_code, 409)
        capture_report_snapshot(self.visit, self.worker)
        response = self.api.get(self.pdf_url(self.visit))
        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content)
        self.assertTrue(content.startswith(b'%PDF-'))
        self.assertEqual(len(PdfReader(BytesIO(content)).pages), 1)
        answer = Answer.objects.get(visit=self.visit)
        answer.bool = False
        answer.save()
        self.assertEqual(b''.join(self.api.get(self.pdf_url(self.visit)).streaming_content), content)
        self.grant.can_view = False
        self.grant.save()
        self.assertEqual(self.api.get(self.pdf_url(self.visit)).status_code, 403)

    def test_pdf_paginates_long_persian_answers(self):
        self.visit.status = Visit.COMPLETED
        self.visit.save()
        snapshot = capture_report_snapshot(self.visit, self.worker)
        payload = deepcopy(snapshot.payload)
        payload['answers'] = [{'question': 'شرح بازدید طولانی',
                               'description': 'شرح وضعیت آسانسور و اقدام انجام‌شده ' * 500}]
        digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                           sort_keys=True).encode('utf-8')).hexdigest()
        fake = SimpleNamespace(payload=payload, checksum=digest, visit_id=self.visit.pk,
                               version=1, created_at=snapshot.created_at)
        content = render_report_pdf(fake).getvalue()
        self.assertGreater(len(PdfReader(BytesIO(content)).pages), 1)
