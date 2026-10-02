"""Survey records and answers may not cross project or ownership boundaries."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from survey.models import Survey, SurveyAnswer, SurveyFillOut, SurveyQuestion


class SurveyRecordAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Survey record one')
        self.other_project = Project.objects.create(name='Survey record two')
        self.manager = User.objects.create(username='record-manager')
        role = Role.objects.create(title='Record manager', title_abbreviation='R',
                                   asset_scope='project')
        RoleAssignment.objects.create(user=self.manager, project=self.project, role=role)
        for name, method in (
            ('SurveyFillOutListCreateView', 'GET'), ('SurveyFillOutListCreateView', 'POST'),
            ('SurveyFillOutEditsView', 'GET'), ('SurveyFillOutEditsView', 'PATCH'),
            ('SurveyAnswerListCreateView', 'GET'), ('SurveyAnswerListCreateView', 'POST'),
            ('SurveyAnswerEditsView', 'GET'), ('SurveyAnswerEditsView', 'PATCH'),
            ('PromoterSurveyQuestionList', 'GET'), ('FrontSurveyPageSettingsView', 'GET'),
            ('PromoterAnswersSurveyQuestionsView', 'POST'),
        ):
            view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
            RoleView.objects.create(role=role, view_method_name=view_method,
                                    can_view=method == 'GET', can_create=method == 'POST',
                                    can_update=method == 'PATCH')
        self.survey = Survey.objects.create(project=self.project, name='One')
        self.other_survey = Survey.objects.create(project=self.other_project, name='Two')
        self.fillout = SurveyFillOut.objects.create(survey=self.survey, user=self.manager)
        self.other_fillout = SurveyFillOut.objects.create(survey=self.other_survey)
        self.question = SurveyQuestion.objects.create(survey=self.survey, text='One question')
        self.other_question = SurveyQuestion.objects.create(survey=self.other_survey,
                                                            text='Two question')
        self.answer = SurveyAnswer.objects.create(survey_fill_out=self.fillout,
                                                  survey_question=self.question, number=1)
        self.other_answer = SurveyAnswer.objects.create(survey_fill_out=self.other_fillout,
                                                        survey_question=self.other_question, number=2)
        self.api = APIClient()
        self.api.force_authenticate(self.manager)

    def url(self, resource, record=None):
        suffix = f'/{record.pk}/' if record else '/'
        return f'/core/api/admin/{resource}{suffix}?p={self.project.pk}'

    def test_lists_and_edits_do_not_expose_foreign_records(self):
        for resource, owned in (('survey_fill_out/list_create', self.fillout),
                                ('survey_answer/list_create', self.answer)):
            response = self.api.get(self.url(resource))
            self.assertEqual(response.status_code, 200, response.data)
            rows = response.data if isinstance(response.data, list) else response.data['results']
            self.assertEqual([row['id'] for row in rows], [owned.pk])
        for resource, foreign in (('survey_fill_out/edits', self.other_fillout),
                                  ('survey_answer/edits', self.other_answer)):
            self.assertEqual(self.api.get(self.url(resource, foreign)).status_code, 404)
            self.assertEqual(self.api.patch(self.url(resource, foreign),
                                            {'number': 9}, format='json').status_code, 404)
        public = APIClient()
        self.assertIn(public.get(self.url('survey_fill_out/list_create')).status_code, (401, 403))
        self.assertIn(public.post(self.url('survey_fill_out/list_create'),
                                  {'survey': self.survey.pk}, format='json').status_code, (401, 403))

    def test_writes_validate_project_question_and_closed_state(self):
        self.assertEqual(self.api.post(self.url('survey_fill_out/list_create'),
                                       {'survey': self.other_survey.pk}, format='json').status_code, 400)
        self.assertEqual(self.api.post(self.url('survey_answer/list_create'),
                                       {'survey_fill_out': self.fillout.pk,
                                        'survey_question': self.other_question.pk, 'number': 3},
                                       format='json').status_code, 400)
        self.assertEqual(self.api.patch(self.url('survey_answer/edits', self.answer),
                                        {'survey_fill_out': self.other_fillout.pk},
                                        format='json').status_code, 400)
        self.assertEqual(self.api.patch(self.url('survey_fill_out/edits', self.fillout),
                                        {'survey': self.other_survey.pk}, format='json').status_code, 400)
        self.fillout.is_closed = True
        self.fillout.save()
        self.assertEqual(self.api.patch(self.url('survey_answer/edits', self.answer),
                                        {'number': 9}, format='json').status_code, 400)
        self.assertEqual(self.api.post(self.url('survey_answer/list_create'),
                                       {'survey_fill_out': self.fillout.pk,
                                        'survey_question': self.question.pk, 'number': 4},
                                       format='json').status_code, 400)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.number, 1)

    def test_field_question_and_answer_paths_are_scoped_and_allowlisted(self):
        base = f'/core/api/promoter/answer_to_survey_question/?p={self.project.pk}'
        own = {'survey_fill_out': self.fillout.pk, 'survey_question': self.question.pk}
        self.assertEqual(self.api.get(
            f'/core/api/promoter/survey_question/list/{self.other_fillout.pk}/?p={self.project.pk}'
        ).status_code, 404)
        self.assertEqual(self.api.get(
            f'/core/api/promoter/survey_page_settings/{self.other_fillout.pk}/?p={self.project.pk}'
        ).status_code, 404)
        self.assertEqual(self.api.post(base, {**own, 'survey_fill_out_id': self.other_fillout.pk},
                                       format='json').status_code, 400)
        self.assertEqual(self.api.post(base, {**own, 'survey_question': self.other_question.pk},
                                       format='json').status_code, 400)
        self.assertEqual(self.api.post(base, {**own, 'number': 7}, format='json').status_code, 200)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.number, 7)
        self.fillout.is_closed = True
        self.fillout.save()
        self.assertEqual(self.api.post(base, {**own, 'number': 8}, format='json').status_code, 400)
