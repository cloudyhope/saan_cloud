"""Detail read/write regressions, with an isolated test database."""
import tempfile
from io import BytesIO
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod, ExtendedUser
from visit.models import Visit, VisitType, Building, AnswerType, QuestionType, Question, Answer, AnswerChoice, PhotoType, Photo, Store, StoreCategory, Ticket, TicketMessage
from survey.models import Survey, SurveyFillOut, SurveyQuestion, SurveyAnswer, SurveyQuestionType


class AdminDetailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='local-detail-test')
        ExtendedUser.objects.bulk_create([ExtendedUser(user=self.user, role='M')])
        self.project = Project.objects.create(name='Test')
        self.role = Role.objects.create(title='Test', title_abbreviation='M', asset_scope='project')
        RoleAssignment.objects.create(user=self.user, role=self.role, project=self.project)
        self.api = APIClient()
        self.api.force_authenticate(self.user)
        self.building = Building.objects.create(code='TEST-1', verbose_name='Test building')
        self.visit_type = VisitType.objects.create(title='Test', project=self.project)
        self.visit = Visit.objects.create(type=self.visit_type, creator=self.user, building=self.building, status='2')
        self.qtype = QuestionType.objects.create(name='Test', project=self.project, visit_type=self.visit_type)
        self.question = Question.objects.create(type='GE', question_type=self.qtype, text='Test question')
        self.answer = Answer.objects.create(visit=self.visit, question=self.question, bool=False, number=0)
        self.survey = Survey.objects.create(name='Test survey', project=self.project)
        self.fillout = SurveyFillOut.objects.create(survey=self.survey, phone_number='09000000000', user=None, city=None, province=None)

    def allow(self, name, method):
        vm, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
        RoleView.objects.update_or_create(role=self.role, view_method_name=vm, defaults={'can_view': method == 'GET', 'can_create': method == 'POST', 'can_update': method in ['PUT', 'PATCH'], 'can_delete': method == 'DELETE'})

    def url(self, path):
        return path + '?p=' + str(self.project.pk)

    def test_visit_settings_without_photo_types(self):
        self.allow('FrontVisitPageSettingsView', 'GET')
        self.building.project = self.project
        self.building.save()
        self.visit.expert = self.user
        self.visit.is_active = True
        self.visit.save()
        response = self.api.get(self.url(f'/core/api/promoter/visit_page_settings/{self.visit.pk}/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['photos'], [])
        self.assertIsNone(response.data['start_time'])

    def test_answer_list_preserves_false_and_zero(self):
        self.allow('AdminAnswerListView', 'GET')
        response = self.api.get(self.url('/core/api/admin/answer_list/') + '&visit=' + str(self.visit.pk))
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.data[0]['bool'], False)
        self.assertEqual(response.data[0]['number'], 0)

    def test_answer_edit_multi_choice_and_nullable_values(self):
        self.allow('AdminAnswerEdistsView', 'PATCH')
        choices = [AnswerChoice.objects.create(answer='A'), AnswerChoice.objects.create(answer='B')]
        response = self.api.patch(self.url(f'/core/api/admin/answer_edit/{self.answer.pk}/'), {'bool': False, 'number': 0, 'multichoice': [c.pk for c in choices], 'dropdown': None}, format='json')
        self.assertEqual(response.status_code, 200)
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.bool)
        self.assertEqual(self.answer.number, 0)
        self.assertEqual(self.answer.multichoice.count(), 2)

    def test_answer_create(self):
        self.allow('AdminAnswerCreateAPIView', 'POST')
        q = Question.objects.create(type='GE', text='New question')
        response = self.api.post(self.url('/core/api/admin/visit_answer/create/'), {'visit': self.visit.pk, 'question': q.pk, 'description': 'line one\nline two'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Answer.objects.filter(question=q, description='line one\nline two').exists())

    def test_approve_visit_with_project_query(self):
        self.allow('AdminUpdateVisitStatusView', 'PUT')
        self.building.project = self.project
        self.building.save(update_fields=['project'])
        response = self.api.put(self.url(f'/core/api/admin/visit_status_change/{self.visit.pk}/'), {'status': '3'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, '3')
        foreign_project = Project.objects.create(name='Other visit project')
        foreign_building = Building.objects.create(project=foreign_project, code='FOREIGN-VISIT')
        foreign_type = VisitType.objects.create(project=foreign_project, title='Other')
        foreign_visit = Visit.objects.create(type=foreign_type, building=foreign_building,
                                             creator=self.user, status=Visit.COMPLETED)
        self.assertEqual(self.api.put(self.url(
            f'/core/api/admin/visit_status_change/{foreign_visit.pk}/'),
            {'status': Visit.APPROVED}, format='json').status_code, 404)

    def test_empty_survey_detail_is_independent_of_answers(self):
        self.allow('SurveyFillOutEditsView', 'GET')
        response = self.api.get(self.url(f'/core/api/admin/survey_fill_out/edits/{self.fillout.pk}/'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['user'])
        self.assertIsNone(response.data['city'])

    def test_survey_answer_create_edit(self):
        self.allow('SurveyAnswerListCreateView', 'POST')
        self.allow('SurveyAnswerEditsView', 'PATCH')
        q = SurveyQuestion.objects.create(survey=self.survey, text='Survey question')
        response = self.api.post(self.url('/core/api/admin/survey_answer/list_create/'), {'survey_fill_out': self.fillout.pk, 'survey_question': q.pk, 'bool': False, 'number': 0}, format='json')
        self.assertEqual(response.status_code, 201)
        answer = SurveyAnswer.objects.get(survey_question=q)
        response = self.api.patch(self.url(f'/core/api/admin/survey_answer/edits/{answer.pk}/'), {'number': 12}, format='json')
        self.assertEqual(response.status_code, 200)
        answer.refresh_from_db()
        self.assertEqual(answer.number, 12)

    def test_store_read_write_and_project_isolation(self):
        self.allow('AdminStoreDetailView', 'GET')
        self.allow('AdminStoreDetailView', 'PATCH')
        category = StoreCategory.objects.create(project=self.project, name='demo', verbose_name='Demo')
        store = Store.objects.create(project=self.project, category=category, name='Store', code='STORE1', mobile_phone='09000000000')
        url = self.url(f'/core/api/admin/outlet_with_more_info/edits/{store.pk}/')
        response = self.api.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['category']['verbose_name'], 'Demo')
        response = self.api.patch(url, {'owner_name': 'Updated', 'mobile_phone': '09000000002'}, format='json')
        self.assertEqual(response.status_code, 200)
        store.refresh_from_db()
        self.assertEqual(store.mobile_phone, '09000000002')
        other = Project.objects.create(name='Other')
        RoleAssignment.objects.create(user=self.user, role=self.role, project=other)
        response = self.api.get(f'/core/api/admin/outlet_with_more_info/edits/{store.pk}/?p={other.pk}')
        self.assertEqual(response.status_code, 404)
        other_category = StoreCategory.objects.create(project=other, name='other', verbose_name='Other')
        response = self.api.patch(url, {'category': other_category.pk}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_store_write_requires_permission(self):
        self.allow('AdminStoreDetailView', 'GET')
        store = Store.objects.create(project=self.project, name='Store', code='STORE1')
        response = self.api.patch(self.url(f'/core/api/admin/outlet_with_more_info/edits/{store.pk}/'), {'name': 'Blocked'}, format='json')
        self.assertEqual(response.status_code, 403)
        store.refresh_from_db()
        self.assertEqual(store.name, 'Store')

    def test_local_photo_upload_and_soft_delete(self):
        self.allow('PromoterUploadImageAPIView', 'POST')
        self.allow('AdminPhotoEditsView', 'DELETE')
        self.building.project = self.project
        self.building.save()
        self.visit.expert = self.user
        self.visit.status = Visit.INPROGRESS
        self.visit.is_active = True
        self.visit.save()
        photo_type = PhotoType.objects.create(name='Test', project=self.project, visit_type=self.visit_type)
        with tempfile.TemporaryDirectory() as directory, override_settings(SETTINGS_MODULE='core.local_settings', MEDIA_ROOT=directory, MEDIA_URL='/media/', DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage'):
            from PIL import Image
            buffer = BytesIO()
            Image.new('RGB', (2, 2), 'blue').save(buffer, format='PNG')
            image = SimpleUploadedFile('test.png', buffer.getvalue(), content_type='image/png')
            response = self.api.post(self.url('/core/api/promoter/open_visit/upload_image/'), {'link': image, 'visit': self.visit.pk, 'type': photo_type.pk, 'latitude': 'null', 'longitude': 'null'}, format='multipart')
            self.assertEqual(response.status_code, 200)
            photo = Photo.objects.get(visit=self.visit)
            self.assertTrue(photo.link.startswith('http://localhost:18110/media/uploads/'))
            response = self.api.delete(self.url(f'/core/api/admin/photo_edit/{photo.pk}/'))
            self.assertEqual(response.status_code, 204)
            photo.refresh_from_db()
            self.assertTrue(photo.is_deleted)

    def test_visit_feedback_and_rejection(self):
        self.allow('PlaceVisitCommentView', 'PUT')
        self.allow('AdminUpdateVisitStatusView', 'PUT')
        self.building.project = self.project
        self.building.save(update_fields=['project'])
        response = self.api.put(self.url(f'/core/api/admin/vist/place_comment/{self.visit.pk}/'), {'visit_comment': 'Local test feedback'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.visit_comment, 'Local test feedback')
        response = self.api.put(self.url(f'/core/api/admin/visit_status_change/{self.visit.pk}/'), {'status': '4', 'rejection_reason': 'Local test reason'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, '4')

    def test_survey_settings_with_optional_type_and_mandatory_score(self):
        self.allow('FrontSurveyPageSettingsView', 'GET')
        qt = SurveyQuestionType.objects.create(name='Score', has_score=True)
        q = SurveyQuestion.objects.create(survey=self.survey, text='Scored', survey_question_type=qt, is_mandatory=True)
        kind = AnswerType.objects.create(name='RadioChoice', field='radio')
        q.answer_type.add(kind)
        choice = AnswerChoice.objects.create(answer='Good', score=7)
        SurveyAnswer.objects.create(survey_fill_out=self.fillout, survey_question=q, radio=choice)
        SurveyQuestion.objects.create(survey=self.survey, text='No question type')
        response = self.api.get(self.url(f'/core/api/promoter/survey_page_settings/{self.fillout.pk}/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['questions'][0]['total_score'], 7)

    def test_unanswered_survey_questions(self):
        self.allow('PromoterSurveyQuestionList', 'GET')
        q = SurveyQuestion.objects.create(survey=self.survey, text='Unanswered')
        response = self.api.get(self.url(f'/core/api/promoter/survey_question/list/{self.fillout.pk}/'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['question']['id'], q.pk)
        self.assertIsNone(response.data[0]['submitted_answer']['id'])

    def test_store_create_and_duplicate_code_validation(self):
        self.allow('AdminStoreListCreateView', 'POST')
        url = self.url('/core/api/admin/outlet_with_more_info/create/')
        response = self.api.post(url, {'name': 'Test store', 'code': 'CODE-ONE'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['project'], self.project.pk)
        response = self.api.post(url, {'name': 'Second', 'code': 'CODE-ONE'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_supervision_status_uses_separate_field(self):
        self.allow('AdminUpdateSupervisionVisitStatusView', 'PUT')
        response = self.api.put(self.url(f'/core/api/admin/supervision_visit_status_change/{self.visit.pk}/'), {'supervision_status': '3'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.supervision_status, '3')
        self.assertEqual(self.visit.status, '2')

    def test_ticket_without_messages_and_reply(self):
        self.allow('TicketRetriveUpdateDestroyView', 'GET')
        self.allow('TicketRetriveUpdateDestroyView', 'PATCH')
        self.allow('TicketMessageListCreateView', 'GET')
        self.allow('TicketMessageListCreateView', 'POST')
        ticket = Ticket.objects.create(project=self.project, creator=self.user, role_assignee=self.role, title='Local ticket')
        detail_url = self.url(f'/core/api/admin/ticket/edits/{ticket.pk}/')
        response = self.api.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], 'Local ticket')
        messages_url = self.url('/core/api/admin/ticket_message/list_create/')
        response = self.api.get(messages_url + '&ticket=' + str(ticket.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        response = self.api.post(messages_url, {'ticket': ticket.pk, 'body': 'Test reply'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(TicketMessage.objects.filter(ticket=ticket, body='Test reply').exists())
        response = self.api.patch(detail_url, {'status': 'C'}, format='json')
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'C')

    def test_warehouse_distribution_modes_and_nullable_type(self):
        from warehouse.models import Ware, WarehouseLocation, WarehouseTransaction, WarehouseTransactionLine
        self.allow('WareDistributionView', 'GET')
        ware = Ware.objects.create(name_fa='Local item', project=self.project)
        location = WarehouseLocation.objects.create(name_fa='Local warehouse')
        location.projects.add(self.project)
        transaction = WarehouseTransaction.objects.create(creator=self.user)
        WarehouseTransactionLine.objects.create(ware=ware, transaction=transaction, location=location, amount=20)
        WarehouseTransactionLine.objects.create(ware=ware, transaction=transaction, user=self.user, amount=5)
        url = self.url(f'/api/warehouse/v1/aggregated/user_or_location/retrieve/{ware.pk}/')
        response = self.api.get(url + '&based_on=location')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['type'])
        self.assertEqual(response.data['locations'][0]['stock_count'], 20)
        self.assertEqual(response.data['users_stock_count'], 5)
        response = self.api.get(url + '&based_on=user')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users'][0]['stock_count'], 5)
        self.assertEqual(response.data['locations_stock_count'], 20)
