"""Create an isolated, synthetic local client with narrowly scoped permissions."""
import json
import sqlite3
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from config.models import NavMenu
from visit.models import (Building, BuildingClient, BuildingElevator, Client, Elevator,
                          Product, ProductElevator, ProductModel, UserClient, VisitType,
                          Visit, QuestionType, Question, Answer)
from visit.report_snapshot import capture_report_snapshot


class Command(BaseCommand):
    help = 'Prepare a synthetic local client; credentials must be in an ignored local file.'

    def add_arguments(self, parser):
        parser.add_argument('--credentials-file', required=True)
        parser.add_argument('--project', type=int, default=1)

    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        if (settings.SETTINGS_MODULE != 'core.local_settings' or not settings.DEBUG
                or db['ENGINE'] != 'django.db.backends.sqlite3'):
            raise CommandError('Only local DEBUG SQLite is supported.')
        credentials_path = Path(options['credentials_file']).resolve()
        data_directory = (Path(settings.BASE_DIR) / 'data').resolve()
        if data_directory not in credentials_path.parents:
            raise CommandError('Credentials must be inside the ignored backend/data directory.')
        credentials = json.loads(credentials_path.read_text(encoding='utf-8-sig'))
        username, password = credentials.get('username'), credentials.get('password')
        if not username or not password:
            raise CommandError('Username and password are required in the credentials file.')
        project = Project.objects.filter(pk=options['project'], is_active=True).first()
        if not project:
            raise CommandError('An active local project is required.')
        account = User.objects.filter(username=username).first()
        if account and not RoleAssignment.objects.filter(user=account, role__title='LocalClientPreview').exists():
            raise CommandError('Refusing to change an unrelated account.')
        backup = data_directory / ('db-before-client-preview-' + timezone.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
        with sqlite3.connect(str(db['NAME'])) as current, sqlite3.connect(str(backup)) as saved:
            current.backup(saved)
        with transaction.atomic():
            role, _ = Role.objects.get_or_create(title='LocalClientPreview', defaults={
                'title_abbreviation': 'C', 'verbose_name': 'کلاینت آزمایشی لوکال',
                'asset_scope': 'client', 'priority': 7, 'is_active': True})
            if role.asset_scope != 'client':
                raise CommandError('Unexpected scope on the local preview role.')
            if not account:
                account = User.objects.create_user(username=username, password=password,
                                                   first_name='مدیر ساختمان', last_name='آزمایشی')
            RoleAssignment.objects.get_or_create(user=account, role=role, project=project, is_deleted=False)
            allowed = [('NavMenuList', 'GET'), ('BuildingClientListCreateAPIView', 'GET'),
                       ('BuildingListCreateAPIView', 'GET'), ('BuildingEditsAPIView', 'GET'),
                       ('VisitTypeListCreateView', 'GET'), ('ClientVisitsAPIView', 'GET'),
                       ('ClientVisitFeedbackAPIView', 'GET'), ('ClientVisitFeedbackAPIView', 'POST'),
                       ('ClientSupportTicketsAPIView', 'GET'), ('ClientSupportTicketsAPIView', 'POST'),
                       ('ClientSupportTicketDetailAPIView', 'GET'), ('ClientSupportTicketDetailAPIView', 'POST'),
                       ('ServiceRequestCreate', 'POST'),
                       ('ClientListCreateAPIView', 'GET'), ('ProductListCreateAPIView', 'GET'),
                       ('WarrantyContractListCreateView', 'GET'),
                       ('WarrantyClaimListCreateView', 'GET'), ('WarrantyClaimListCreateView', 'POST'),
                       ('RepairCaseListCreateView', 'GET')]
            # This role is dedicated to the preview; remove any accidentally broadened grants.
            RoleView.objects.filter(role=role).delete()
            for name, method in allowed:
                view_method, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
                RoleView.objects.create(role=role, view_method_name=view_method,
                                        can_view=method == 'GET', can_create=method == 'POST',
                                        can_update=False, can_delete=False)
            client, _ = Client.objects.get_or_create(name='LocalClientPreview', project=project,
                defaults={'name_fa': 'مدیریت ساختمان‌های آزمایشی', 'type': Client.CUSTOMER})
            UserClient.objects.get_or_create(user=account, client=client)
            parent = None
            for code, name, count in [('LOCAL-C-01', 'مجتمع سروستان', 2),
                                       ('LOCAL-C-02', 'ساختمان نیلوفر', 1),
                                       ('LOCAL-C-03', 'برج سروستان • بلوک شرقی', 2)]:
                building, _ = Building.objects.get_or_create(code=code, defaults={
                    'project': project, 'name': code, 'verbose_name': name,
                    'address': 'آدرس آزمایشی لوکال • خیابان نمونه، پلاک ۱۲',
                    'type': Building.APARTMENT if parent else Building.COMPLEX,
                    'parent': parent if code == 'LOCAL-C-03' else None})
                if building.project_id != project.id:
                    raise CommandError('Synthetic building belongs to another project.')
                BuildingClient.objects.get_or_create(building=building, client=client)
                if code == 'LOCAL-C-01':
                    parent = building
                for index in range(1, count + 1):
                    elevator, _ = Elevator.objects.get_or_create(project=project, title=code + ' • آسانسور ' + str(index),
                        defaults={'capacity': '۸ نفر', 'number_of_floors': 10 + index, 'type': 'TRACTION'})
                    BuildingElevator.objects.get_or_create(building=building, elevator=elevator)
                    model, _ = ProductModel.objects.get_or_create(project=project, model_number='LOCAL-CTRL-1',
                        defaults={'name': 'LocalControlBoard', 'name_fa': 'برد کنترل آزمایشی', 'type': 'BOARD'})
                    product, _ = Product.objects.get_or_create(project=project, serial_number=code + '-' + str(index),
                        defaults={'model': model, 'is_used': True, 'status': 'INSTALLED'})
                    ProductElevator.objects.get_or_create(product=product, elevator=elevator)
            for title in ('سرویس دوره‌ای', 'بررسی برد آسانسور', 'درخواست تعمیر'):
                VisitType.objects.get_or_create(project=project, title='LOCAL: ' + title,
                                               defaults={'verbose_name': title, 'is_active': True})
            visit_type = VisitType.objects.get(project=project, title='LOCAL: سرویس دوره‌ای')
            preview_building = Building.objects.get(code='LOCAL-C-01', project=project)
            sample_visit, _ = Visit.objects.get_or_create(
                type=visit_type, building=preview_building, creator=account,
                visit_comment='LocalClientPreview: completed service',
                defaults={'status': Visit.COMPLETED, 'is_active': True})
            if sample_visit.status in (Visit.COMPLETED, Visit.APPROVED):
                section, _ = QuestionType.objects.get_or_create(
                    project=project, visit_type=visit_type, name='LOCAL: service report',
                    defaults={'verbose_name': 'گزارش نمونه'})
                question, _ = Question.objects.get_or_create(
                    question_type=section, text='آیا وضعیت ایمنی بررسی شد؟',
                    defaults={'type': Question.TGENERAL})
                Answer.objects.get_or_create(visit=sample_visit, question=question,
                                             defaults={'bool': True})
                capture_report_snapshot(sample_visit, account)
            for priority, (route, title) in enumerate([('home', 'ساختمان‌ها'), ('clientVisits', 'درخواست‌ها'),
                                                       ('clientWarranty', 'گارانتی'), ('setting', 'حساب من')]):
                NavMenu.objects.update_or_create(role=role, route=route, defaults={
                    'title': route, 'title_fa': title, 'priority': priority, 'is_landing': route == 'home'})
        self.stdout.write(self.style.SUCCESS('Synthetic local client prepared. Credentials remain in the ignored file.'))
        self.stdout.write('Backup: ' + str(backup))
