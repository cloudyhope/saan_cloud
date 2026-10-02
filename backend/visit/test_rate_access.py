"""Legacy visit ratings must follow visit access and creator ownership."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from visit.models import Building, BuildingClient, Client, QuestionType, UserClient, Visit, VisitRate, VisitType


class VisitRateAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Rate own')
        self.foreign_project = Project.objects.create(name='Rate foreign')
        self.user = User.objects.create(username='rate-client')
        self.other_user = User.objects.create(username='rate-other')
        role = Role.objects.create(title='Rate client', title_abbreviation='R', asset_scope='client')
        RoleAssignment.objects.create(user=self.user, project=self.project, role=role)
        for view, method in (('VisitRateListCreateView', 'GET'), ('VisitRateListCreateView', 'POST'),
                             ('VisitRateEditsView', 'GET'), ('VisitRateEditsView', 'PATCH')):
            vm, _ = ViewMethod.objects.get_or_create(view_name=view, method=method)
            RoleView.objects.create(role=role, view_method_name=vm,
                                    can_view=method == 'GET', can_create=method == 'POST',
                                    can_update=method == 'PATCH')
        client = Client.objects.create(project=self.project, name='Own')
        UserClient.objects.create(client=client, user=self.user)
        building = Building.objects.create(project=self.project, code='RATE-OWN')
        BuildingClient.objects.create(client=client, building=building)
        kind = VisitType.objects.create(project=self.project, title='Inspect')
        self.visit = Visit.objects.create(type=kind, building=building, creator=self.user,
                                          status=Visit.COMPLETED, is_active=True)
        foreign_building = Building.objects.create(project=self.foreign_project, code='RATE-OTHER')
        foreign_type = VisitType.objects.create(project=self.foreign_project, title='Other')
        self.foreign = Visit.objects.create(type=foreign_type, building=foreign_building,
                                            creator=self.other_user, status=Visit.COMPLETED)
        self.other_rate = VisitRate.objects.create(visit=self.foreign, rate=9000,
                                                   created_by=self.other_user)
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def url(self, path):
        return f'/core/api/v1/visit_rate/{path}?p={self.project.pk}'

    def test_list_create_and_edit_are_scoped(self):
        self.assertEqual(self.api.get(self.url('list_create/')).data, [])
        self.assertEqual(self.api.get(self.url(f'edits/{self.other_rate.pk}/')).status_code, 404)
        self.assertEqual(self.api.post(self.url('list_create/'),
                                       {'visit': self.foreign.pk, 'rate': 5000}, format='json').status_code, 403)
        own = self.api.post(self.url('list_create/'),
                            {'visit': self.visit.pk, 'rate': 5000}, format='json')
        self.assertEqual(own.status_code, 201, own.data)
        self.assertEqual(self.api.patch(self.url(f'edits/{own.data["id"]}/'),
                                        {'visit': self.foreign.pk}, format='json').status_code, 400)
        self.assertEqual(self.api.patch(self.url(f'edits/{own.data["id"]}/'),
                                        {'rate': 7000}, format='json').status_code, 200)
        self.assertEqual(VisitRate.objects.get(pk=own.data['id']).rate, 7000)

    def test_rating_requires_completed_visit_and_matching_question(self):
        self.visit.status = Visit.INPROGRESS
        self.visit.save()
        self.assertEqual(self.api.post(self.url('list_create/'),
                                       {'visit': self.visit.pk, 'rate': 5000}, format='json').status_code, 400)
        self.visit.status = Visit.COMPLETED
        self.visit.save()
        foreign_question = QuestionType.objects.create(project=self.foreign_project,
                                                       visit_type=VisitType.objects.get(pk=self.foreign.type_id),
                                                       name='Foreign')
        self.assertEqual(self.api.post(self.url('list_create/'),
                                       {'visit': self.visit.pk, 'question_type': foreign_question.pk,
                                        'rate': 5000}, format='json').status_code, 400)
