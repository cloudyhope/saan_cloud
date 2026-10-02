"""Local-only QA matrix: role personas, scoped grants and scenario data for manual testing.

Creates one account per role/negative case, grants that mirror each role's real
screens, and synthetic buildings, visits, tickets, warranty/repair, stock and
notifications covering every state. Everything is labelled «QA», lives in ID
range 5,000,000+ or QA-prefixed codes, and is re-created on every run.
Passwords are generated once into an ignored JSON file and never printed.
"""
import json
import random
import re
import secrets
import sqlite3
import uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from io import StringIO

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import get_resolver
from django.utils import timezone
from PIL import Image, ImageDraw

from auth_app.models import (AdminMenu, City, ExtendedUser, FieldValidation, Project, QuestionAnswerTypeValidation,
                            Role, RoleAssignment, RoleView, Supervisor, UploadedFile, ViewMethod)
from auth_app.menu_icons import icons_for
from auth_app.permissions import METHOD_CAPABILITIES
from config.models import NavMenu
from notification.models import InAppNotification
from survey.models import (Survey, SurveyAnswer, SurveyFillOut, SurveyPhoto, SurveyPhotoType, SurveyQuestion,
                           SurveyQuestionType, SurveyReportCategory)
from visit.models import (Answer, AnswerChoice, AnswerType, Building, BuildingClient, BuildingElevator, Client,
                          ClientVisitFeedback, Elevator, Photo, PhotoType, Product, ProductElevator, ProductModel,
                          Question, QuestionType, RepairCase, RepairEvent, ReportCategory, ServiceRequestSubmission,
                          Ticket, TicketMessage, UserClient, Visit, VisitReportSnapshot, VisitType, WarrantyClaim,
                          WarrantyContract)
from visit.report_snapshot import capture_report_snapshot
from wallet.models import WalletInvoice
from warehouse.models import (Unit, Ware, WareType, WareVisitType, WarehouseLocation, WarehouseTransaction,
                              WarehouseTransactionLine)

BASE = 5000000
P1, P2, P3 = 1, BASE + 1, BASE + 2  # P1 is the existing local project; P2 second active; P3 inactive
CREDENTIALS_NAME = 'qa-accounts.json'
REPORT_NAME = 'QA_TEST_ACCOUNTS.md'
ALPHABET = 'abcdefghjkmnpqrstuvwxyz23456789'

# ---------------------------------------------------------------- personas
ROLES = {
    'admin': dict(title='QA_Admin', abbr='M', verbose='QA ادمین کامل پروژه', scope='project', priority=3),
    'planner': dict(title='QA_Planner', abbr='M', verbose='QA برنامه‌ریز و مدیر خدمات', scope='project', priority=4),
    'support': dict(title='QA_Support', abbr='S', verbose='QA پشتیبان', scope='project', priority=-10),
    'warehouse': dict(title='QA_Warehouse', abbr='S', verbose='QA انباردار', scope='project', priority=5),
    'supervisor': dict(title='QA_Supervisor', abbr='P', verbose='QA سرپرست', scope='supervised', priority=6),
    'expert': dict(title='QA_Expert', abbr='P', verbose='QA کارشناس میدانی', scope='assigned', priority=7),
    'client': dict(title='QA_Client', abbr='C', verbose='QA مدیر ساختمان (کلاینت)', scope='client', priority=8),
    'client_rep': dict(title='QA_ClientRep', abbr='C', verbose='QA نماینده کلاینت (فقط مشاهده)', scope='client',
                       priority=9),
}

PERSONAS = [
    # key, username, first, last, [(role, project)], extra
    ('admin', '09200000001', 'ادمین', 'کامل', [('admin', P1)], {}),
    ('planner', '09200000002', 'برنامه‌ریز', 'نمونه', [('planner', P1)], {}),
    ('support', '09200000003', 'پشتیبان', 'نمونه', [('support', P1)], {}),
    ('warehouse', '09200000004', 'انباردار', 'نمونه', [('warehouse', P1)], {}),
    ('supervisor', '09200000005', 'سرپرست', 'نمونه', [('supervisor', P1)], {}),
    ('expert', '09200000006', 'کارشناس', 'الف', [('expert', P1)], {}),
    ('expert2', '09200000007', 'کارشناس', 'ب', [('expert', P1)], {}),
    ('client', '09200000008', 'مدیر ساختمان', 'آلفا', [('client', P1)], {}),
    ('client_rep', '09200000009', 'نماینده', 'آلفا', [('client_rep', P1)], {}),
    ('client_b', '09200000010', 'مدیر شرکت', 'بتا', [('client', P1)], {}),
    ('dual', '09200000011', 'کارشناس و کلاینت', 'گاما', [('expert', P1), ('client', P1)], {}),
    ('multi', '09200000012', 'چندپروژه‌ای', 'نمونه', [('expert', P1), ('client', P2), ('admin', P3)], {}),
    ('norole', '09200000013', 'بدون', 'نقش', [], {}),
    ('inactive', '09200000014', 'غیرفعال', 'نمونه', [('expert', P1)], {'is_active': False}),
    ('deleted_role', '09200000015', 'نقش‌حذف‌شده', 'نمونه', [('expert', P1)], {'deleted': True}),
]
DJANGO_ADMIN = ('qa-django-admin', 'Django', 'Admin')
# Legacy admin views also require ExtendedUser.role in (M, S, C).
LEGACY_ROLE = {'admin': 'M', 'planner': 'M', 'support': 'S', 'warehouse': 'S'}

# Field-app and admin menus come from the backend, per role.
FIELD_MENUS = {
    'expert': [('tasks', 'مأموریت‌ها'), ('wares', 'تجهیزات'), ('edu', 'آکادمی'), ('wallet', 'کیف پول'),
               ('setting', 'حساب من')],
    'supervisor': [('tasks', 'مأموریت‌ها'), ('wares', 'تجهیزات'), ('edu', 'آکادمی'), ('setting', 'حساب من')],
    'client': [('home', 'ساختمان‌ها'), ('clientVisits', 'درخواست‌ها'), ('clientWarranty', 'گارانتی'),
               ('setting', 'حساب من')],
    'client_rep': [('home', 'ساختمان‌ها'), ('clientVisits', 'درخواست‌ها'), ('clientWarranty', 'گارانتی'),
                   ('setting', 'حساب من')],
}
SERVICE_ENDPOINTS = (
    ('WarrantyContractListCreateView', 'GET'), ('WarrantyContractListCreateView', 'POST'),
    ('WarrantyEligibleProductsView', 'GET'), ('WarrantyClaimListCreateView', 'GET'),
    ('WarrantyClaimDecisionView', 'POST'), ('RepairCaseListCreateView', 'GET'), ('RepairCaseListCreateView', 'POST'),
    ('RepairCaseDetailView', 'GET'), ('RepairCaseTransitionView', 'POST'), ('RepairCaseMaterialView', 'GET'),
    ('RepairCaseMaterialView', 'POST'), ('RepairCaseLoanerView', 'GET'), ('RepairCaseLoanerView', 'POST'),
)
CLIENT_GRANTS = (
    ('NavMenuList', 'GET'), ('BuildingClientListCreateAPIView', 'GET'), ('BuildingListCreateAPIView', 'GET'),
    ('BuildingEditsAPIView', 'GET'), ('VisitTypeListCreateView', 'GET'), ('ClientVisitsAPIView', 'GET'),
    ('ClientVisitFeedbackAPIView', 'GET'), ('ClientVisitFeedbackAPIView', 'POST'),
    ('ClientSupportTicketsAPIView', 'GET'), ('ClientSupportTicketsAPIView', 'POST'),
    ('ClientSupportTicketDetailAPIView', 'GET'), ('ClientSupportTicketDetailAPIView', 'POST'),
    ('ServiceRequestCreate', 'POST'), ('ClientListCreateAPIView', 'GET'), ('ProductListCreateAPIView', 'GET'),
    ('WarrantyContractListCreateView', 'GET'), ('WarrantyClaimListCreateView', 'GET'),
    ('WarrantyClaimListCreateView', 'POST'), ('RepairCaseListCreateView', 'GET'),
    ('WalletGetSignatureView', 'GET'), ('WalletInvoiceClientRetrieveView', 'GET'),
    ('WalletInvoiceCodeRequestView', 'POST'), ('WalletInvoiceCodeValidateView', 'POST'),
    ('WalletReceiptRetrieve', 'GET'), ('ClientVisitChatView', 'GET'), ('ClientVisitChatView', 'POST'),
)
CLIENT_REP_GRANTS = tuple(item for item in CLIENT_GRANTS if item[1] == 'GET' and not item[0].startswith('Wallet')) + (
    ('ClientSupportTicketsAPIView', 'GET'),)

# (route regex, allowed methods or None for all) — matched against the API route table.
COMMON_ADMIN = [
    (r'^core/api/admin/(menu/list|project_list)', {'GET'}), (r'^core/api/auth/(me|user_detail)/', None),
    (r'^core/api/active_project/', {'GET'}), (r'^config/navbar/List', {'GET'}),
    (r'^core/api/(province|city|active_city)/', {'GET'}),
]
EXPERT_FIELD = [
    (r'^core/api/promoter/', None), (r'^core/api/visit/retrieve/', {'GET'}),
    (r'^core/api/auth/(me|user_detail)/', None), (r'^core/api/auth/(document|document_photo)', None),
    (r'^core/api/(active_project|province|city|active_city)/', {'GET'}), (r'^config/(province|city)/', {'GET'}),
    (r'^core/api/admin/(retrive_photo_type|photo_edit|visit_edit|survey_photo/edits|visit_type/list_create)', None),
    (r'^core/api/admin/action_plan/(create|bulk_update)', None), (r'^core/api/expert/support/', None),
    (r'^api/warehouse/v1/(aggregated/(user/list|visit_page_settings)|ware_transaction/ez_create)', None),
    (r'^wallet/(invoice/(expert/list_create|get_qr_code)|get_signature|api/user_wallet_transaction_line|'
     r'transaction/user_balance|api/v1/wallet_receipt)', None),
    (r'^config/(navbar/List|Media/List|MediaType/List|files/list_create|terms_and_conditions)', {'GET'}),
    (r'^api/micro/personalinfo/', None), (r'^api/visit/(BuildingListCreate|BuildingEdits)', {'GET'}),
]
SUPERVISOR_EXTRA = [
    (r'^core/api/supervisor/', None), (r'^core/api/admin/supervision_visit_status_change/', None),
    (r'^core/api/auth/(supervisor|active_supervisors)', None),
]
PLANNER_RULES = COMMON_ADMIN + [
    (r'^(core|api|config)/', {'GET'}),
    (r'^core/api/admin/(create_visits|visit_edit|visit_status_change|answer_edit|visit_answer/create|photo_edit|'
     r'vist/place_comment|action_plan|ticket|ticket_message|ticket_message_attachment|survey_fill_out|'
     r'survey_answer|survey_photo)', {'POST', 'PUT', 'PATCH'}),
    (r'^core/api/v1/(visit_activation_edit|custom_bulk_edit)', {'POST', 'PUT', 'PATCH'}),
    (r'^core/api/auth/supervisor/', {'POST', 'PUT', 'PATCH'}),
    (r'^api/visit/', {'POST', 'PUT', 'PATCH'}), (r'^core/api/admin/building_management/transfer/', {'POST'}),
    (r'^core/api/admin/priority/entity/', {'PUT'}),
    (r'^core/api/admin/maintenance_plans/', {'POST', 'PUT', 'DELETE'}),
    (r'^core/api/admin/assignment/', None),
]
SUPPORT_RULES = COMMON_ADMIN + [
    (r'^core/api/admin/ticket', {'GET', 'POST', 'PUT', 'PATCH'}),
    (r'^core/api/admin/(visit_list|promoter_list)', {'GET'}), (r'^api/visit/(Building|Client)ListCreate', {'GET'}),
    (r'^core/api/visit/retrieve/', {'GET'}),
]
WAREHOUSE_RULES = COMMON_ADMIN + [
    (r'^api/warehouse/', None), (r'^core/api/admin/(visit_list|promoter_list)', {'GET'}),
    (r'^api/visit/(Building|Client)ListCreate', {'GET'}),
]

ADMIN_MENU = [
    ('داشبورد', '/dashboard', []),
    ('مدیریت کاربران', '/usermanagement/list', [('لیست کاربران', '/usermanagement/list'),
                                                ('ایجاد و ویرایش', '/usermanagement/add'),
                                                ('تخصیص نیرو به سرپرست', '/usermanagement/assignpromoter')]),
    ('مدیریت مشتریان', '/customermanagement/list', [('لیست مشتریان', '/customermanagement/list'),
                                                    ('ایجاد مشتری', '/customermanagement/create')]),
    ('مدیریت آسانسورها', '/elevatormanagement/buildinglist', [
        ('لیست ساختمان‌ها', '/elevatormanagement/buildinglist'), ('ایجاد گروه ساختمان', '/elevatormanagement/crearebuilding'),
        ('گروه ساختمان‌ها', '/elevatormanagement/groupbuildinglist'), ('لیست آسانسور', '/elevatormanagement/elevatorlist')]),
    ('مدیریت ویزیت‌ها', '/visitmanagment/lists', [
        ('تکمیل نشده', '/visitmanagment/notcompeletevisits'), ('تکمیل شده', '/visitmanagment/completeVisited'),
        ('تایید شده', '/visitmanagment/acceptedvisits'), ('لیست ویزیت‌ها', '/visitmanagment/lists'),
        ('انواع خدمت', '/visitmanagment/visit-types'), ('تخصیص هوشمند', '/assignment')]),
    ('مدیریت پرسشنامه‌ها', '/suveymanagment/lists', [
        ('تکمیل نشده', '/surveymanagment/notcompeletesurvey'), ('تکمیل شده', '/suveymanagment/completesurvey'),
        ('تایید شده', '/surveymanagment/acceptedsurvey'), ('تمام نتایج', '/suveymanagment/lists')]),
    ('نظارت', '/supervisionmanagment/lists', [
        ('لیست نظارت‌ها', '/supervisionmanagment/lists'), ('تکمیل شده', '/supervisionmanagment/completesupervision'),
        ('تایید شده', '/supervisionmanagment/acceptedsupervision'),
        ('تکمیل نشده', '/supervisionmanagment/notcompeletesupervision')]),
    ('برنامه روزانه', '/actionplan/listactionplan', [('ثبت برنامه جدید', '/actionplan/newaction'),
                                                     ('برنامه‌های فعال', '/actionplan/listactionplan')]),
    ('پشتیبانی', '/ticket/ticketlist', [('تیکت جدید', '/ticket/newticket'), ('لیست تیکت‌ها', '/ticket/ticketlist')]),
    ('مدیریت انبار', '/warehouse/warelist', [('تعریف کالا', '/warehouse/create'),
                                              ('مدیریت موجودی', '/warehouse/warelist'),
                                              ('درخواست‌های قطعه', '/warehouse/part-requests')]),
    ('گارانتی و تعمیرات', '/service-cases', []),
    ('اولویت‌بندی خدمات', '/priority', []),
    ('اعلان‌ها', '/notifications', []),
    ('فروشگاه‌ها', '/storemng/listall', []),
    ('مدیریت رسانه', '/medialist/list', [('لیست رسانه‌ها', '/medialist/list'), ('ایجاد رسانه', '/medialist/create')]),
    ('مدیریت فایل', '/filemanagement/filelist', [('آپلود فایل', '/filemanagement/uploadfile'),
                                                  ('لیست فایل‌ها', '/filemanagement/filelist')]),
    ('مدیریت حساب‌ها', '/walletmanagment/manageaccount', [('حساب‌ها', '/walletmanagment/manageaccount'),
                                                          ('شارژ کیف پول', '/walletmanagment/rechargewallet')]),
]
MENU_FILTERS = {
    'admin': None,
    'planner': {'داشبورد', 'مدیریت مشتریان', 'مدیریت آسانسورها', 'مدیریت ویزیت‌ها', 'مدیریت پرسشنامه‌ها', 'نظارت',
                'برنامه روزانه', 'پشتیبانی', 'گارانتی و تعمیرات', 'اولویت‌بندی خدمات', 'اعلان‌ها'},
    'support': {'داشبورد', 'پشتیبانی', 'اعلان‌ها'},
    'warehouse': {'داشبورد', 'مدیریت انبار', 'اعلان‌ها'},
}


def endpoint_table():
    """Map view class name -> [(route, methods)] for every registered DRF view."""
    table = {}

    def walk(patterns, prefix=''):
        for pattern in patterns:
            route = prefix + str(pattern.pattern).lstrip('^').rstrip('$')
            if hasattr(pattern, 'url_patterns'):
                walk(pattern.url_patterns, route)
                continue
            cls = getattr(pattern.callback, 'cls', None) or getattr(pattern.callback, 'view_class', None)
            if cls is None:
                continue
            methods = {m.upper() for m in ('get', 'post', 'put', 'patch', 'delete') if hasattr(cls, m)}
            table.setdefault(cls.__name__, []).append((route, methods))

    walk(get_resolver().url_patterns)
    return table


def pick(table, rules):
    chosen = set()
    for pattern, allowed in rules:
        regex = re.compile(pattern)
        for name, routes in table.items():
            for route, methods in routes:
                if regex.search(route):
                    chosen.update((name, m) for m in methods if allowed is None or m in allowed)
    return chosen


class Command(BaseCommand):
    help = 'Create QA accounts and scenario data in local SQLite; credentials go to an ignored file.'

    def add_arguments(self, parser):
        parser.add_argument('--credentials-file', default='data/' + CREDENTIALS_NAME)

    # ------------------------------------------------------------------ main
    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        if (settings.SETTINGS_MODULE != 'core.local_settings' or not settings.DEBUG
                or db['ENGINE'] != 'django.db.backends.sqlite3'):
            raise CommandError('Only local DEBUG SQLite is supported.')
        self.data_dir = (Path(settings.BASE_DIR) / 'data').resolve()
        self.data_dir.mkdir(exist_ok=True)
        credentials_path = (Path(settings.BASE_DIR) / options['credentials_file']).resolve()
        if self.data_dir not in credentials_path.parents:
            raise CommandError('The credentials file must be inside the ignored backend/data directory.')
        backup = self.data_dir / ('db-before-qa-matrix-' + timezone.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
        with sqlite3.connect(str(db['NAME'])) as current, sqlite3.connect(str(backup)) as saved:
            current.backup(saved)

        self.now = timezone.now()
        self.today = timezone.localdate()
        self.scenarios = []  # (area, who, where, expectation)
        self.passwords = self.load_passwords(credentials_path)
        self.table = endpoint_table()
        with transaction.atomic():
            self.projects()
            self.roles()
            self.users()
            self.menus()
            self.catalog()
            self.assets()
            self.priorities()
            self.visits()
            self.history()
            self.surveys()
            self.support()
            self.service_cases()
            self.stock_and_invoices()
            self.field_ops()
            self.assignment_data()
            self.notifications()
            self.academy()
        self.write_credentials(credentials_path)
        self.write_report()
        self.stdout.write(self.style.SUCCESS('QA matrix ready. Backup: ' + backup.name))
        self.stdout.write('Credentials file: ' + str(credentials_path))
        self.stdout.write('Guide: ' + str(self.data_dir / REPORT_NAME))

    # ------------------------------------------------------------- helpers
    def load_passwords(self, path):
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8')).get('passwords', {})
        return {}

    def password(self, username):
        if username not in self.passwords:
            body = ''.join(secrets.choice(ALPHABET) for _ in range(8))
            self.passwords[username] = f'Saan-{body}-QA'
        return self.passwords[username]

    def write_credentials(self, path):
        payload = {'note': 'Local test accounts only. Ignored by Git. Do not reuse these passwords.',
                   'passwords': self.passwords}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    def put(self, klass, pk, **data):
        # Avoid custom save hooks and outbound side effects; keeps IDs stable between runs.
        if klass.objects.filter(pk=pk).exists():
            klass.objects.filter(pk=pk).update(**data)
        else:
            klass.objects.bulk_create([klass(pk=pk, **data)])
        return klass.objects.get(pk=pk)

    def note(self, area, who, where, expectation):
        self.scenarios.append((area, who, where, expectation))

    def day(self, offset):
        return self.today + timedelta(days=offset)

    def ago(self, **kwargs):
        return self.now - timedelta(**kwargs)

    # -------------------------------------------------------------- phases
    def projects(self):
        self.put(Project, P2, name='qa-second-project', name_fa='QA پروژه دوم', is_active=True,
                 datetime_created=self.now, datetime_last_change=self.now)
        self.put(Project, P3, name='qa-inactive-project', name_fa='QA پروژه غیرفعال', is_active=False,
                 datetime_created=self.now, datetime_last_change=self.now)
        self.project = {P1: Project.objects.get(pk=P1), P2: Project.objects.get(pk=P2),
                        P3: Project.objects.get(pk=P3)}
        self.city = City.objects.filter(name='تهران').first() or City.objects.first()

    def roles(self):
        self.role = {}
        for key, spec in ROLES.items():
            role = Role.objects.filter(title=spec['title']).first() or Role(title=spec['title'])
            role.title_abbreviation, role.verbose_name = spec['abbr'], spec['verbose']
            role.asset_scope, role.priority, role.is_active = spec['scope'], spec['priority'], True
            role.save()
            self.role[key] = role
        grants = {
            'admin': {(name, method) for name, routes in self.table.items() for _, methods in routes
                      for method in methods},
            'planner': pick(self.table, PLANNER_RULES) | set(SERVICE_ENDPOINTS) | {
                ('ClientListCreateAPIView', 'GET'), ('ProductListCreateAPIView', 'GET')},
            'support': pick(self.table, SUPPORT_RULES),
            'warehouse': pick(self.table, WAREHOUSE_RULES),
            'supervisor': pick(self.table, EXPERT_FIELD + SUPERVISOR_EXTRA),
            'expert': pick(self.table, EXPERT_FIELD),
            'client': set(CLIENT_GRANTS), 'client_rep': set(CLIENT_REP_GRANTS),
        }
        self.grant_counts = {}
        for key, entries in grants.items():
            entries = {(n, m) for n, m in entries if m in METHOD_CAPABILITIES}
            RoleView.objects.filter(role=self.role[key]).delete()
            methods = {}
            for name, method in entries:
                methods[(name, method)] = ViewMethod.objects.get_or_create(view_name=name, method=method)[0]
            RoleView.objects.bulk_create([
                RoleView(role=self.role[key], view_method_name=obj, **{METHOD_CAPABILITIES[method]: True})
                for (name, method), obj in methods.items()])
            self.grant_counts[key] = len(methods)

    def users(self):
        self.user = {}
        city = self.city
        for key, username, first, last, assignments, extra in PERSONAS:
            account = User.objects.filter(username=username).first() or User(username=username)
            account.first_name, account.last_name = first, last
            account.is_active = extra.get('is_active', True)
            account.set_password(self.password(username))
            account.save()
            ExtendedUser.objects.update_or_create(user=account, defaults={
                'full_name': f'{first} {last}', 'role': LEGACY_ROLE.get(key, 'C' if key.startswith('client') else 'P'),
                'city': city, 'province': city.province if city else None})
            keep = []
            for role_key, project_id in assignments:
                row, _ = RoleAssignment.objects.get_or_create(
                    user=account, role=self.role[role_key], project_id=project_id)
                row.is_deleted = bool(extra.get('deleted'))
                row.save()
                keep.append(row.pk)
            RoleAssignment.objects.filter(user=account, role__title__startswith='QA_').exclude(pk__in=keep).delete()
            self.user[key] = account
        sup = User.objects.filter(username=DJANGO_ADMIN[0]).first() or User(username=DJANGO_ADMIN[0])
        sup.first_name, sup.last_name = DJANGO_ADMIN[1], DJANGO_ADMIN[2]
        sup.is_staff = sup.is_superuser = sup.is_active = True
        sup.set_password(self.password(DJANGO_ADMIN[0]))
        sup.save()
        # Supervisor oversees expert A only; expert B stays outside the supervised scope.
        Supervisor.objects.get_or_create(supervisor=self.user['supervisor'], promoter=self.user['expert'],
                                         project_id=P1, defaults={'is_active': True})
        Supervisor.objects.filter(supervisor=self.user['supervisor'], promoter=self.user['expert'],
                                  project_id=P1).update(is_active=True)

    def menus(self):
        icons = 'http://localhost:18110/media/expert-preview/'
        icon_names = {'tasks': 'order-list', 'edu': 'academy', 'wares': 'equipment', 'setting': 'profile'}
        for key, items in FIELD_MENUS.items():
            NavMenu.objects.filter(role=self.role[key]).delete()
            for priority, (route, title) in enumerate(items):
                icon = icon_names.get(route)
                NavMenu.objects.create(
                    role=self.role[key], route=route, title=route, title_fa=title, priority=priority,
                    is_landing=priority == 0,
                    active_icon=icons + icon + '-active.svg' if icon else None,
                    deactive_icon=icons + icon + '.svg' if icon else None)
        for key, wanted in MENU_FILTERS.items():
            for project_id in (P1,):
                AdminMenu.objects.filter(role=self.role[key], project_id=project_id).delete()
                priority = 0
                for title, url, children in ADMIN_MENU:
                    if wanted is not None and title not in wanted:
                        continue
                    priority += 1
                    active, inactive = icons_for(url, bool(children))
                    parent = AdminMenu.objects.create(
                        project_id=project_id, role=self.role[key], priority=priority, name='qa-' + str(priority),
                        verbose_name=title, frontend_route_url=url, has_submenu=bool(children), is_active=True,
                        active_icon=active, deactive_icon=inactive)
                    for order, (child_title, child_url) in enumerate(children, 1):
                        active, inactive = icons_for(child_url)
                        AdminMenu.objects.create(
                            project_id=project_id, role=self.role[key], parent=parent, priority=order,
                            name=f'qa-{priority}-{order}', verbose_name=child_title, frontend_route_url=child_url,
                            is_active=True, active_icon=active, deactive_icon=inactive)
                # The seeded rows have the legacy shape; the same command a real project would run shortens them
                # (status tabs, merged groups, hidden supervision and notifications).
                call_command('restructure_admin_menu', '--project', str(project_id), '--role', str(self.role[key].pk),
                             '--apply', stdout=StringIO())

    def catalog(self):
        """Visit types, questionnaire, photo types and supervision template for the main project."""
        now = self.now
        self.vt = {}
        specs = [(5000001, 'QA: سرویس دوره‌ای', 'سرویس دوره‌ای آسانسور', 350000),
                 (5000002, 'QA: تعمیر برد', 'تعمیر و بررسی برد', 900000),
                 (5000003, 'QA: بازدید اضطراری', 'بازدید اضطراری', 1200000)]
        for pk, title, verbose, wage in specs:
            self.vt[pk] = self.put(VisitType, pk, title=title, verbose_name=verbose, project=self.project[P1],
                                   is_active=True, default_wage=wage, has_supervision=pk == 5000001,
                                   description='نوع خدمت آزمایشی QA')
        self.put(VisitType, 5000009, title='QA: نوع غیرفعال', verbose_name='نوع غیرفعال', project=self.project[P1],
                 is_active=False, default_wage=0, description='باید در درخواست کلاینت دیده نشود')
        self.put(VisitType, 5000010, title='QA2: سرویس', verbose_name='سرویس پروژه دوم', project=self.project[P2],
                 is_active=True, default_wage=100000)
        vt = self.vt[5000001]
        answer_type = {}
        for name, field in [('YesNo', 'bool'), ('Score', 'score'), ('Number', 'number'), ('Input', 'text'),
                            ('Description', 'description'), ('RadioChoice', 'radio'), ('DropDownList', 'dropdown'),
                            ('Multichoice', 'multichoice'), ('Price', 'price')]:
            row = AnswerType.objects.filter(name=name, field=field).first() or AnswerType.objects.filter(name=name).first()
            answer_type[name] = row or AnswerType.objects.create(name=name, field=field)
        self.answer_type = answer_type
        categories = []
        for index, title in enumerate(['QA ایمنی', 'QA عملکرد']):
            pk = 5000001 + index
            category = self.put(ReportCategory, pk, name=f'qa-cat-{index}', verbose_name=title,
                                project=self.project[P1], visit_type=vt)
            qtype = self.put(QuestionType, pk, name=f'qa-qt-{index}', verbose_name=title, project=self.project[P1],
                             visit_type=vt, report_category=category, is_mandatory=index == 0,
                             description=['بررسی‌های ایمنی اجباری پیش از پایان کار', 'ارزیابی عملکرد و یادداشت‌های فنی'][index],
                             is_active=True)
            categories.append((category, qtype))
        self.put(QuestionType, 5000010, name='qa-supervision', verbose_name='QA نظارت', project=self.project[P1],
                 visit_type=vt, is_mandatory=True, description='بررسی سرپرست پس از پایان کار کارشناس',
                 is_active=True, is_for_supervision=True)
        spec = [  # name, text, group, mandatory
            ('YesNo', 'آیا مدار ایمنی درب‌ها بررسی شد؟', 0, True),
            ('Number', 'تعداد توقف‌های بررسی‌شده', 0, True),
            ('Score', 'کیفیت روغن‌کاری ریل (۱ تا ۵)', 1, False),
            ('Input', 'نام مسئول ساختمان در محل', 1, False),
            ('Description', 'توضیحات و پیشنهادهای فنی', 1, False),
            ('RadioChoice', 'وضعیت کابین', 1, False),
            ('DropDownList', 'زمان پیشنهادی سرویس بعدی', 1, False),
            ('Multichoice', 'موارد بررسی‌شده', 1, False),
            ('Price', 'هزینه قطعات مصرفی (ریال)', 1, False),
        ]
        hints = ['قفل و کنتاکت درب همه طبقات را با باز و بسته‌کردن بررسی کنید.',
                 'تعداد طبقاتی که توقف و تراز کابین در آن‌ها آزموده شد.',
                 'روغن‌کاری ریل‌های کابین و وزنه تعادل را ارزیابی کنید.', '',
                 'نکات فنی، ایرادهای دیده‌شده و پیشنهاد برای سرویس بعد را بنویسید.', '', '',
                 'هر بخشی را که در این مراجعه بررسی کردید انتخاب کنید.',
                 'جمع مبلغ قطعات و مواد مصرفی این مراجعه، بدون دستمزد.']
        self.questions = []
        for index, (kind, text, group, mandatory) in enumerate(spec):
            pk = 5000001 + index
            question = self.put(Question, pk, type='GE', text=text, priority=index + 1, is_mandatory=mandatory,
                                is_active=True, report_category=categories[group][0],
                                question_type=categories[group][1], description=hints[index])
            question.answer_type.set([answer_type[kind]])
            if kind in ('RadioChoice', 'DropDownList', 'Multichoice'):
                titles = {'RadioChoice': ['مناسب', 'نیازمند پیگیری', 'نامناسب'],
                          'DropDownList': ['هفته آینده', 'ماه آینده', 'پس از هماهنگی'],
                          'Multichoice': ['درب طبقات', 'تابلو فرمان', 'سیستم اضطراری', 'ریل راهنما']}[kind]
                choices = [self.put(AnswerChoice, 5000100 + index * 10 + n, answer=title, question=question,
                                    score=3 - n if n < 3 else 0) for n, title in enumerate(titles)]
                relation = {'RadioChoice': 'radio_choices', 'DropDownList': 'dropdown_choices',
                            'Multichoice': 'answer_choices'}[kind]
                getattr(question, relation).set(choices)
            else:
                choices = []
            self.questions.append((question, kind, choices))
        supervision_q = self.put(Question, 5000050, type='GE', text='آیا گزارش کارشناس با وضعیت محل مطابقت داشت؟',
                                 priority=1, is_mandatory=True, is_active=True,
                                 question_type=QuestionType.objects.get(pk=5000010),
                                 description='گزارش کارشناس را با وضعیت واقعی محل مقایسه کنید.')
        supervision_q.answer_type.set([answer_type['YesNo']])
        self.supervision_question = supervision_q
        self.photo_type = {}
        photo_hints = {
            5000001: 'درب تابلو فرمان را باز کنید و از برد، رله‌ها و سیم‌کشی عکس روشن بگیرید.',
            5000002: 'از داخل کابین، پنل احضار و نمایشگر طبقه عکس بگیرید.',
            5000003: 'در صورت دسترسی، از موتور، گیربکس و فلکه عکس بگیرید.',
            5000004: 'عکسی که درستی گزارش کارشناس را نشان دهد.'}
        for pk, name, verbose, minimum, mandatory, supervision in [
                (5000001, 'qa-panel', 'QA عکس تابلو فرمان', 1, True, False),
                (5000002, 'qa-cabin', 'QA عکس کابین', 1, True, False),
                (5000003, 'qa-machine-room', 'QA عکس موتورخانه', 0, False, False),
                (5000004, 'qa-supervision', 'QA عکس نظارت', 1, True, True)]:
            self.photo_type[pk] = self.put(PhotoType, pk, name=name, verbose_name=verbose, project=self.project[P1],
                                           visit_type=vt, min=minimum, max=5, is_mandatory=mandatory,
                                           report_category=categories[0][0], description=photo_hints[pk],
                                           is_for_supervision=supervision, is_active=True)
        validation, _ = FieldValidation.objects.get_or_create(name='qa-matrix', defaults={
            'min_value': 0, 'max_value': 100000000, 'min_lenght': 0, 'max_lenght': 2000,
            'min_choice_count': 0, 'max_choice_count': 4, 'is_mandatory': False})
        for question, kind, _ in self.questions:
            for kind_row in question.answer_type.all():
                QuestionAnswerTypeValidation.objects.get_or_create(
                    visit_question=question, answer_type=kind_row, is_for='V', defaults={'validation': validation})
        for pk, minimum in [(5000020, 1), (5000021, 0)]:
            self.put(PhotoType, pk, name='qa-repair-%d' % minimum, verbose_name='QA عکس تعمیر',
                     project=self.project[P1], visit_type=self.vt[5000002], min=minimum, max=3,
                     is_mandatory=bool(minimum), description='از برد قبل و بعد از تعمیر عکس بگیرید.', is_active=True)
        qtype = self.put(QuestionType, 5000020, name='qa-repair', verbose_name='QA تعمیر برد', project=self.project[P1],
                         visit_type=self.vt[5000002], description='نتیجه آزمون برد', is_active=True)
        repair_q = self.put(Question, 5000060, type='GE', text='نتیجه آزمون برد پس از تعمیر', priority=1,
                            is_mandatory=True, is_active=True, question_type=qtype,
                            description='نتیجه آزمون ۲۴ ساعته و خطاهای مشاهده‌شده را بنویسید.')
        repair_q.answer_type.set([answer_type['Description']])
        # Placeholder PNGs live under uploads/ so the signed-media endpoint can serve them.
        self.media = Path(settings.MEDIA_ROOT) / 'uploads' / 'qa'
        self.media.mkdir(parents=True, exist_ok=True)
        for slug, color in [('panel', (211, 224, 240)), ('cabin', (226, 232, 218)), ('machine', (240, 230, 214)),
                            ('supervision', (232, 220, 238)), ('repair', (238, 224, 224)), ('survey', (220, 236, 236))]:
            for n in range(1, 4):
                target = self.media / f'qa-{slug}-{n}.png'
                if target.exists():
                    continue
                image = Image.new('RGB', (900, 600), color)
                draw = ImageDraw.Draw(image)
                draw.rectangle((40, 40, 860, 560), outline=(90, 110, 140), width=6)
                draw.text((70, 70), f'QA TEST IMAGE  /  {slug.upper()}  /  {n}', fill=(60, 80, 110))
                draw.line((40, 40, 860, 560), fill=(150, 165, 190), width=3)
                image.save(target)

    def photo_link(self, slug, n):
        return f'http://localhost:18110/media/uploads/qa/qa-{slug}-{(n % 3) + 1}.png'

    def assets(self):
        """Clients, buildings, elevators, boards and management history (Project 1 and 2)."""
        now = self.now
        cl = self.cl = {}
        specs = [(5000001, 'QA Client Alpha', 'QA مدیریت ساختمان‌های آلفا', Client.CUSTOMER),
                 (5000002, 'QA Client Beta', 'QA شرکت پیمانکاری بتا', Client.BUSINESS),
                 (5000003, 'QA Client Gamma', 'QA مدیریت ساختمان گاما', Client.CUSTOMER)]
        for pk, name, name_fa, kind in specs:
            cl[pk] = self.put(Client, pk, name=name, name_fa=name_fa, type=kind, project=self.project[P1],
                              description='کلاینت آزمایشی QA')
            cl[pk].visit_types.set(VisitType.objects.filter(pk__in=[5000001, 5000002, 5000003]))
        cl[5000004] = self.put(Client, 5000004, name='QA Client P2', name_fa='QA کلاینت پروژه دوم',
                               type=Client.CUSTOMER, project=self.project[P2])
        cl[5000004].visit_types.set([5000010])
        for client, key in [(5000001, 'client'), (5000001, 'client_rep'), (5000002, 'client_b'),
                            (5000003, 'dual'), (5000004, 'multi')]:
            UserClient.objects.get_or_create(client=cl[client], user=self.user[key])
        models = {}
        for pk, number, name_fa, kind in [(5000001, 'QA-CTRL-A1', 'برد کنترل QA-A1', 'BOARD'),
                                          (5000002, 'QA-DRV-X2', 'برد درایو QA-X2', 'BOARD'),
                                          (5000003, 'QA-DOOR-D3', 'کنترلر درب QA-D3', 'BOARD')]:
            models[pk] = self.put(ProductModel, pk, project=self.project[P1], name=number, name_fa=name_fa,
                                  model_number=number, type=kind)
        self.pm = models
        long_address = ('تهران، منطقه ۲، بلوار نمونه‌ی آزمایشی، کوچه‌ی شانزدهم، مجتمع مسکونی و تجاری QA، '
                        'ورودی شرقی، طبقه همکف، دفتر مدیریت ساختمان — این آدرس عمداً طولانی است تا شکستن خط و '
                        'سرریز در موبایل آزمایش شود.')

        def building(pk, code, name, parent=None, kind='Apartment', address='تهران، خیابان نمونه QA، پلاک ۱۲',
                     project=P1):
            return self.put(Building, pk, project=self.project[project], code=code, name=code, verbose_name=name,
                            type=kind, parent=parent, address=address, city=self.city, latitude=35.7 + pk % 10 / 1000,
                            longitude=51.4 + pk % 10 / 1000)

        b = self.b = {}
        b[1] = building(5000001, 'QA-P1-01', 'QA مجتمع آفتاب', kind='Complex')
        b[2] = building(5000002, 'QA-P1-02', 'QA برج شرقی', parent=b[1])
        b[3] = building(5000003, 'QA-P1-03', 'QA برج غربی', parent=b[1])
        b[4] = building(5000004, 'QA-P1-04', 'QA ساختمان نیلوفر')
        b[5] = building(5000005, 'QA-P1-05', 'QA ساختمان بدون آسانسور')
        b[6] = building(5000006, 'QA-P1-06', 'QA برج بتا ' + 'با نام بسیار طولانی ' * 3, address=long_address)
        b[7] = building(5000007, 'QA-P1-07', 'QA ساختمان انتقال‌یافته')
        b[8] = building(5000008, 'QA-P1-08', 'QA ساختمان گاما')
        b[9] = building(5000009, 'QA-P1-09', 'QA ساختمان بدون مدیر')
        b[21] = building(5000021, 'QA-P2-01', 'QA ساختمان پروژه دوم', project=P2)

        def elevator(pk, title, building_key, project=P1, kind='TRACTION', floors=10):
            row = self.put(Elevator, pk, project=self.project[project], title=title, type='Passenger', capacity='8',
                           number_of_floors=floors, elevator_type=kind, usage_type='RESIDENTIAL',
                           cabin_capacity_kg=630, stops_count=floors, operation_type='SIMPLEX',
                           motor_type='GEARLESS', motor_brand='QA Motor', motor_power_kw=7,
                           control_panel_brand='QA Control', control_panel_serial='QA-%d' % pk,
                           control_panel_type='MRL', door_brand='QA Door', door_count=2, door1_type='AUTO',
                           standard_type='EN81-20', input_voltage='THREE_PHASE')
            self.put(BuildingElevator, pk, building=b[building_key], elevator=row)
            return row

        e = self.e = {}
        e[1] = elevator(5000001, 'QA برج شرقی • آسانسور ۱', 2)
        e[2] = elevator(5000002, 'QA برج شرقی • آسانسور ۲', 2, floors=14)
        e[3] = elevator(5000003, 'QA برج غربی • آسانسور ۱', 3)
        e[4] = elevator(5000004, 'QA نیلوفر • آسانسور هیدرولیک', 4, kind='HYDRAULIC', floors=4)
        e[5] = elevator(5000005, 'QA مجتمع • آسانسور باری', 1, floors=3)
        e[6] = elevator(5000006, 'QA بتا • آسانسور ۱', 6)
        e[7] = elevator(5000007, 'QA انتقالی • آسانسور ۱', 7)
        e[8] = elevator(5000008, 'QA گاما • آسانسور ۱', 8)
        e[21] = elevator(5000021, 'QA پروژه دوم • آسانسور ۱', 21, project=P2)

        def manage(pk, building_key, client, start_days, end_days=None, start_reason='', end_reason=''):
            self.put(BuildingClient, pk, building=b[building_key], client=cl[client],
                     start_at=self.ago(days=start_days), end_at=self.ago(days=end_days) if end_days else None,
                     start_reason=start_reason, end_reason=end_reason, started_by=self.user['admin'])

        for pk, key in enumerate([1, 2, 3, 4, 5], 5000001):
            manage(pk, key, 5000001, 400, start_reason='شروع قرارداد QA')
        manage(5000006, 6, 5000002, 300, start_reason='شروع قرارداد QA')
        # Transfer history: Alpha managed building 7 until 60 days ago, Beta manages it now.
        manage(5000007, 7, 5000001, 500, 60, 'قرارداد اولیه', 'پایان قرارداد؛ انتقال به بتا')
        manage(5000008, 7, 5000002, 60, None, 'انتقال از آلفا')
        manage(5000009, 8, 5000003, 200, start_reason='شروع قرارداد QA')
        manage(5000010, 21, 5000004, 100, start_reason='شروع قرارداد QA')

        self.product = {}
        for pk, serial, model_pk, status, used in [
                (5000001, 'QA-SN-0001', 5000001, 'INSTALLED', True), (5000002, 'QA-SN-0002', 5000002, 'INSTALLED', True),
                (5000003, 'QA-SN-0003', 5000001, 'INSTALLED', True), (5000004, 'QA-SN-0004', 5000003, 'INSTALLED', True),
                (5000005, 'QA-SN-0005', 5000001, 'REMOVED', True), (5000006, 'QA-SN-SPARE', 5000001, 'SPARE', False),
                (5000007, 'QA-SN-LOANER', 5000002, 'SPARE', False), (5000008, 'QA-SN-0008', 5000002, 'IN_REPAIR', True),
                (5000009, 'QA-SN-0009', 5000001, 'INSTALLED', True)]:
            self.product[pk] = self.put(Product, pk, project=self.project[P1], model=self.pm[model_pk],
                                        serial_number=serial, status=status, is_used=used,
                                        datetime_created=now, datetime_last_change=now)
        for pk, product, elevator_key, active, extra in [
                (5000001, 5000001, 1, True, {}), (5000002, 5000002, 1, True, {}), (5000003, 5000003, 3, True, {}),
                (5000004, 5000004, 4, True, {}), (5000009, 5000009, 6, True, {}),
                (5000005, 5000005, 1, False, {'removed_at': self.ago(days=30), 'removed_by': self.user['planner'],
                                              'removal_reason': 'تعویض به‌دلیل خرابی تکراری'}),
                (5000008, 5000008, 2, False, {'removed_at': self.ago(days=10), 'removed_by': self.user['planner'],
                                              'removal_reason': 'ارسال برای تعمیر کارگاه'})]:
            self.put(ProductElevator, pk, product=self.product[product], elevator=e[elevator_key], is_active=active,
                     installed_at=self.ago(days=200), installed_by=self.user['planner'], **extra)
        self.note('دارایی', 'کلاینت آلفا', 'خانه ← ساختمان‌ها',
                  'ساختمان‌های QA-P1-01..05 ؛ مجتمع با دو ساختمان فرزند؛ QA-P1-05 بدون آسانسور (حالت خالی)')
        self.note('دارایی', 'کلاینت آلفا / بتا', 'ساختمان QA-P1-07',
                  'سابقه انتقال مدیریت: آلفا تا ۶۰ روز پیش، بتا از آن زمان؛ هرکدام فقط سهم دورهٔ خود را ببینند')
        self.note('دارایی', 'ادمین', '/elevatormanagement/buildinglist',
                  'QA-P1-06 نام و آدرس بسیار طولانی؛ QA-P1-09 بدون مدیر؛ تاریخچه نصب برد روی آسانسور ۱ (۱ فعال + ۱ خارج‌شده)')

    def priorities(self):
        """Service-priority factors from the owner's brief plus two extra parameters, with QA choices."""
        from visit.models import PriorityAssignment, PriorityFactor, PriorityOption
        from visit.priority import recompute_project
        specs = [
            (5000001, 'سطح مشتری', 'client', 3, 50, [('پریمیوم', 100), ('ویژه', 80), ('نرمال', 50), ('اقتصادی', 25)]),
            (5000002, 'حساسیت کاربری ساختمان', 'building', 4, 40, [('مرکز درمانی', 100), ('دولتی', 85), ('خصوصی', 40)]),
            (5000003, 'ساکن کم‌توان یا بیمار', 'building', 2, 0, [('دارد', 100), ('ندارد', 0)]),
            (5000004, 'نقش آسانسور', 'elevator', 2, 60, [('تخت‌بر / اضطراری', 100), ('تنها آسانسور ساختمان', 85),
                                                         ('مسافربری اصلی', 60), ('باری / فرعی', 30)]),
        ]
        options = {}
        for pk, name, target, weight, default, choices in specs:
            factor = self.put(PriorityFactor, pk, project=self.project[P1], name=name, target=target, weight=weight,
                              default_value=default, is_active=True, order=pk, description='')
            for index, (label, value) in enumerate(choices):
                options[(pk, label)] = self.put(PriorityOption, pk * 10 + index, factor=factor, label=label,
                                                value=value, order=index, is_active=True)
        PriorityAssignment.objects.filter(factor_id__in=[spec[0] for spec in specs]).delete()
        picks = [(5000001, 'client', self.cl[5000001], 'پریمیوم'), (5000001, 'client', self.cl[5000002], 'اقتصادی'),
                 (5000001, 'client', self.cl[5000003], 'نرمال'),
                 (5000002, 'building', self.b[2], 'مرکز درمانی'), (5000002, 'building', self.b[3], 'خصوصی'),
                 (5000002, 'building', self.b[4], 'دولتی'), (5000002, 'building', self.b[6], 'خصوصی'),
                 (5000003, 'building', self.b[4], 'دارد'),
                 (5000004, 'elevator', self.e[1], 'تخت‌بر / اضطراری'), (5000004, 'elevator', self.e[4], 'تنها آسانسور ساختمان'),
                 (5000004, 'elevator', self.e[5], 'باری / فرعی')]
        for factor, target, entity, label in picks:
            PriorityAssignment.objects.create(factor_id=factor, option=options[(factor, label)],
                                              updated_by=self.user['admin'], **{target: entity})
        recompute_project(P1)
        self.note('اولویت', 'ادمین / برنامه‌ریز', '/priority',
                  'چهار عامل با وزن قابل تغییر: سطح مشتری، حساسیت ساختمان (درمانی/دولتی/خصوصی)، ساکن کم‌توان و نقش '
                  'آسانسور. فهرست مأموریت کارشناس و ویزیت‌های ادمین به ترتیب اولویت مرتب می‌شوند.')

    def answer_values(self, kind, choices, variant=0):
        return {'YesNo': {'bool': variant % 2 == 0}, 'Number': {'number': 6 + variant},
                'Score': {'score': 4}, 'Input': {'text': 'آقای رضایی (مسئول ساختمان)'},
                'Description': {'description': 'روشنایی و تهویه کابین مناسب است.\nدر مراجعه بعدی آرام‌بند درب همکف '
                                               'بررسی شود. متن چندخطی برای آزمون خوانایی موبایل.'},
                'RadioChoice': {'radio': choices[0] if choices else None},
                'DropDownList': {'dropdown': choices[1] if choices else None},
                'Multichoice': {}, 'Price': {'price': 2500000}}[kind]

    def fill(self, visit, mandatory_only=False, skip=()):
        for index, (question, kind, choices) in enumerate(self.questions):
            if mandatory_only and not question.is_mandatory:
                continue
            if question.pk in skip:
                continue
            row = self.put(Answer, 5000000 + visit.pk * 20 + index, visit=visit, question=question,
                           datetime_created=self.now, datetime_last_change=self.now,
                           **self.answer_values(kind, choices, visit.pk))
            if kind == 'Multichoice':
                row.multichoice.set(choices[:2])

    def photos(self, visit, types=(5000001, 5000002), creator=None, confirm='NOT_CHECKED'):
        slugs = {5000001: 'panel', 5000002: 'cabin', 5000003: 'machine', 5000004: 'supervision'}
        for index, type_pk in enumerate(types):
            self.put(Photo, 5000000 + visit.pk * 10 + index, visit=visit, type=self.photo_type[type_pk],
                     creator=creator or visit.expert, link=self.photo_link(slugs[type_pk], visit.pk + index),
                     datetime_created=self.now, datetime_last_change=self.now, latitude=35.7, longitude=51.4,
                     supervision_confirm=confirm, supervision_location_confirm='NOT_CHECKED')

    def make_visit(self, pk, vt_pk, building_key, status, expert=None, elevators=(), active=True, due=None,
                   creator=None, comment='', rejection=None, checker=None, supervision='0', created_days=2,
                   promoter=None):
        expert_user = self.user[expert] if expert else None
        visit = self.put(Visit, pk, type=self.vt[vt_pk], building=self.b[building_key], status=status,
                         creator=self.user[creator] if creator else self.user['planner'], expert=expert_user,
                         promoter=self.user[promoter] if promoter else expert_user, is_active=active, has_due_date=due is not None, due_date=due,
                         visit_comment=comment or None, rejection_reason=rejection,
                         checked_by=self.user[checker] if checker else None, supervision_status=supervision,
                         datetime_created=self.ago(days=created_days), datetime_last_change=self.now,
                         start_datetime=self.ago(days=created_days) if status != '0' else None,
                         total_wage=self.vt[vt_pk].default_wage, is_deleted=False)
        visit.elevator.set([self.e[k] for k in elevators])
        return visit

    def visits(self):
        v = self.v = {}
        A, B = 'expert', 'expert2'
        n = 5000000
        # Every run restores the QA visits exactly: answers, photos, reports and feedback added while
        # testing are removed, so each scenario starts from its documented state again.
        qa_visits = Visit.objects.filter(pk__gt=n, pk__lt=n + 300)
        VisitReportSnapshot.objects.filter(visit__in=qa_visits).delete()
        ClientVisitFeedback.objects.filter(visit__in=qa_visits).delete()
        Answer.objects.filter(visit__in=qa_visits).delete()
        Photo.objects.filter(visit__in=qa_visits).delete()
        # --- expert A: every state of the field workflow
        v['new'] = self.make_visit(n + 1, 5000001, 2, '0', A, (1,), due=self.day(3), comment='QA: مأموریت جدید با موعد آینده')
        v['today'] = self.make_visit(n + 2, 5000001, 3, '0', A, (3,), due=self.day(0), comment='QA: موعد امروز')
        v['overdue'] = self.make_visit(n + 3, 5000003, 4, '0', A, (4,), due=self.day(-5), comment='QA: دیرکرد ۵ روز')
        v['multi'] = self.make_visit(n + 4, 5000001, 2, '0', A, (1, 2), due=self.day(7),
                                     comment='QA: دو آسانسور در یک مأموریت')
        v['nodue'] = self.make_visit(n + 5, 5000001, 1, '0', A, (5,), comment='QA: بدون موعد')
        v['partial'] = self.make_visit(n + 6, 5000001, 2, '1', A, (1,), due=self.day(1),
                                       comment='QA: در حال انجام؛ پاسخ اجباری ناقص — پایان باید رد شود')
        self.fill(v['partial'], skip=(5000002,))
        v['ready'] = self.make_visit(n + 7, 5000001, 3, '1', A, (3,), due=self.day(0),
                                     comment='QA: در حال انجام؛ آمادهٔ پایان (همه الزامی‌ها کامل)')
        self.fill(v['ready'], mandatory_only=True)
        self.photos(v['ready'])
        v['retry'] = self.make_visit(n + 8, 5000001, 2, '5', A, (2,), due=self.day(2), comment='QA: وضعیت تلاش مجدد')
        v['suspend'] = self.make_visit(n + 9, 5000001, 3, '6', A, (3,), comment='QA: تعلیق‌شده')
        # --- awaiting review / approved / rejected (planner reviews, client reads reports)
        v['review1'] = self.make_visit(n + 10, 5000001, 2, '2', A, (1,), comment='QA: تکمیل‌شده؛ در انتظار تأیید ۱', supervision='0')
        v['review2'] = self.make_visit(n + 11, 5000001, 3, '2', A, (3,), comment='QA: تکمیل‌شده؛ در انتظار تأیید ۲', supervision='1')
        v['review3'] = self.make_visit(n + 12, 5000001, 4, '2', A, (4,), comment='QA: تکمیل‌شده؛ در انتظار تأیید ۳', supervision='0')
        v['approved1'] = self.make_visit(n + 13, 5000001, 2, '3', A, (1, 2), comment='QA: تأییدشده؛ بدون بازخورد کلاینت',
                                         checker='planner', created_days=20)
        v['approved2'] = self.make_visit(n + 14, 5000001, 3, '3', A, (3,), comment='QA: تأییدشده؛ بازخورد ثبت‌شده',
                                         checker='planner', created_days=40, supervision='2')
        v['approved3'] = self.make_visit(n + 15, 5000001, 1, '3', A, (5,), comment='QA: تأییدشده؛ مجتمع',
                                         checker='planner', created_days=75)
        v['rejected'] = self.make_visit(n + 16, 5000001, 4, '4', A, (4,), comment='QA: ردشده',
                                        rejection='عکس تابلو فرمان ناخوانا است؛ لطفاً دوباره ثبت شود.',
                                        checker='planner')
        for key in ('review1', 'review2', 'review3', 'approved1', 'approved2', 'approved3', 'rejected'):
            self.fill(v[key])
            self.photos(v[key], types=(5000001, 5000002, 5000003))
        for key in ('review1', 'review2', 'review3', 'approved1', 'approved2', 'approved3'):
            capture_report_snapshot(v[key], self.user['expert'])
        # supervision answers/photos for the supervised visit in progress
        self.put(Answer, 5000000 + v['review2'].pk * 20 + 15, visit=v['review2'], question=self.supervision_question,
                 bool=True, datetime_created=self.now, datetime_last_change=self.now)
        # --- pending client requests and other assignments
        v['request1'] = self.make_visit(n + 17, 5000001, 2, '0', None, (1,), active=False, creator='client',
                                        comment='QA: درخواست کلاینت در انتظار برنامه‌ریزی')
        v['request2'] = self.make_visit(n + 18, 5000002, 3, '0', None, (3,), active=False, creator='client',
                                        comment='QA: درخواست تعمیر در انتظار برنامه‌ریزی')
        for key, request_key in (('request1', 1), ('request2', 1)):
            sub, _ = ServiceRequestSubmission.objects.get_or_create(
                project=self.project[P1], creator=self.user['client'],
                request_key=uuid.uuid5(uuid.NAMESPACE_URL, 'qa-request-1'),
                defaults={'payload_hash': 'qa-seeded'})
            sub.visits.add(v[key])
        v['unassigned'] = self.make_visit(n + 19, 5000001, 4, '0', None, (4,), active=True,
                                          comment='QA: فعال و بدون کارشناس — برای تخصیص توسط برنامه‌ریز')
        v['inactive'] = self.make_visit(n + 20, 5000001, 3, '0', A, (3,), active=False,
                                        comment='QA: تخصیص‌یافته ولی غیرفعال؛ نباید در لیست کارشناس بیاید')
        v['b_new'] = self.make_visit(n + 21, 5000001, 6, '0', B, (6,), due=self.day(2), comment='QA: مأموریت کارشناس ب')
        v['b_done'] = self.make_visit(n + 22, 5000001, 6, '3', B, (6,), checker='planner', comment='QA: تأییدشدهٔ کارشناس ب',
                                      created_days=15)
        self.fill(v['b_done']); self.photos(v['b_done'], creator=self.user['expert2'])
        capture_report_snapshot(v['b_done'], self.user['expert2'])
        # --- client Beta + transferred building tenure
        v['beta_open'] = self.make_visit(n + 23, 5000001, 6, '0', B, (6,), due=self.day(10), comment='QA: کار باز بتا')
        v['t_old'] = self.make_visit(n + 24, 5000001, 7, '3', A, (7,), checker='planner', created_days=120,
                                     comment='QA: ویزیت بسته در دوران مدیریت آلفا (۱۲۰ روز پیش)')
        self.fill(v['t_old']); self.photos(v['t_old'])
        capture_report_snapshot(v['t_old'], self.user['expert'])
        v['t_new'] = self.make_visit(n + 25, 5000001, 7, '0', A, (7,), due=self.day(5), created_days=10,
                                     comment='QA: کار باز پس از انتقال؛ فقط بتا می‌بیند')
        # --- dual-role user: expert visit + client building
        v['dual_task'] = self.make_visit(n + 26, 5000001, 8, '0', 'dual', (8,), due=self.day(1),
                                         comment='QA: مأموریت حساب دو نقشه')
        v['dual_done'] = self.make_visit(n + 27, 5000001, 8, '3', A, (8,), checker='planner', created_days=30,
                                         comment='QA: گزارش تأییدشده برای کلاینت گاما')
        self.fill(v['dual_done']); self.photos(v['dual_done'])
        capture_report_snapshot(v['dual_done'], self.user['expert'])
        # --- project 2 (multi-project account)
        v['p2_new'] = self.put(Visit, n + 28, type=VisitType.objects.get(pk=5000010), building=self.b[21],
                               creator=self.user['multi'], expert=self.user['multi'], promoter=self.user['multi'],
                               status='0', is_active=True, has_due_date=False, visit_comment='QA2: پروژه دوم',
                               datetime_created=self.now, datetime_last_change=self.now, total_wage=100000)
        v['p2_new'].elevator.set([self.e[21]])
        v['p1_multi'] = self.make_visit(n + 29, 5000001, 6, '0', 'multi', (6,), due=self.day(4),
                                        comment='QA: مأموریت حساب چندپروژه‌ای در پروژه اول')
        # --- visits performed by the admin/planner themselves (field pages open editable for them).
        v['adm_review'] = self.make_visit(n + 30, 5000001, 2, '2', 'admin', (1,), promoter='planner',
                                          comment='QA: تکمیل‌شده؛ ادمین/برنامه‌ریز مجری‌اند (برای دیدن جزئیات در پنل ادمین)')
        v['adm_approved'] = self.make_visit(n + 31, 5000001, 3, '3', 'admin', (3,), promoter='planner',
                                            checker='planner', created_days=12,
                                            comment='QA: تأییدشده؛ ادمین/برنامه‌ریز مجری‌اند (برای دیدن جزئیات در پنل ادمین)')
        v['adm_new'] = self.make_visit(n + 32, 5000001, 4, '0', 'admin', (4,), promoter='planner', due=self.day(2),
                                       comment='QA: جدید؛ ادمین/برنامه‌ریز مجری‌اند')
        for key in ('adm_review', 'adm_approved'):
            self.fill(v[key])
            self.photos(v[key], types=(5000001, 5000002, 5000003), creator=self.user['admin'])
            capture_report_snapshot(v[key], self.user['admin'])
        # Reports are frozen when the work ends: shortly after the field start, never in the future.
        for visit in v.values():
            if visit.start_datetime and visit.status in ('2', '3', '4'):
                finished = min(visit.start_datetime + timedelta(hours=5), self.now - timedelta(hours=1))
                VisitReportSnapshot.objects.filter(visit=visit).update(created_at=finished)
        # --- feedback
        ClientVisitFeedback.objects.update_or_create(visit=v['approved2'], user=self.user['client'], defaults={
            'rating': 4, 'note': 'سرویس خوب بود، فقط کمی دیر رسیدند.', 'received_at': self.ago(days=35)})
        ClientVisitFeedback.objects.update_or_create(visit=v['approved3'], user=self.user['client'], defaults={
            'rating': None, 'note': '', 'received_at': self.ago(days=70)})
        self.note('ویزیت — کارشناس الف', 'کارشناس QA', 'تب «مأموریت‌ها»',
                  'جدید(+3 روز)، امروز، دیرکرد، چندآسانسوره، بدون موعد، در حال انجام ناقص، آمادهٔ پایان، تلاش‌مجدد، تعلیق؛ '
                  'غیرفعال و کارشناس ب نباید دیده شوند')
        self.note('ویزیت', 'کارشناس QA', f'/visitDetail/{v["partial"].pk}',
                  'پایان‌دادن باید به‌خاطر پاسخ/عکس اجباری ناقص رد شود؛ بعد از تکمیل پاسخ سؤال دوم باید اجازه دهد')
        self.note('ویزیت', 'کارشناس QA', f'/visitDetail/{v["ready"].pk}', 'همهٔ الزامی‌ها کامل ← پایان‌دادن باید موفق باشد')
        self.note('بازبینی', 'برنامه‌ریز / ادمین', 'ویزیت‌ها ← تکمیل‌شده',
                  f'سه ویزیت در انتظار تأیید ({v["review1"].pk}، {v["review2"].pk}، {v["review3"].pk}) برای آزمون تأیید و رد')
        self.note('بازبینی', 'ادمین', f'/visitmanagment/answerlist/{v["rejected"].pk}', 'ویزیت ردشده با دلیل رد')
        self.note('بازبینی', 'ادمین / برنامه‌ریز', 'جزئیات ویزیت در پنل ادمین',
                  'برای همه ویزیت‌های پروژه باز می‌شود (فقط‌خواندنی)؛ «بازگشت برای اصلاح» ویزیت را با دلیل به کارشناس '
                  f'برمی‌گرداند و پس از ثبت دوباره، نسخه بعدی گزارش ساخته می‌شود. ویزیت‌های {v["adm_review"].pk} و '
                  f'{v["adm_approved"].pk} مجری آن‌ها خود ادمین است.')
        self.note('درخواست', 'برنامه‌ریز', 'ویزیت‌های فعال‌نشده',
                  f'دو درخواست کلاینت بدون کارشناس ({v["request1"].pk}، {v["request2"].pk}) و ویزیت فعال بی‌کارشناس '
                  f'{v["unassigned"].pk} برای آزمون تخصیص')

    def history(self):
        """Ninety days of finished and open work, so dashboard trends, delays and schedules carry signal."""
        rnd = random.Random(5000)
        n = BASE + 100
        managers = {1: 'client', 2: 'client', 3: 'client', 4: 'client', 5: 'client', 6: 'client_b', 7: 'client_b', 8: 'dual'}
        experts = ['expert', 'expert', 'expert2', 'expert2', 'dual', 'multi']
        buildings = [(2, 1), (2, 2), (3, 3), (4, 4), (1, 5), (6, 6), (7, 7), (8, 8)]  # (building, elevator)
        outcomes = ['3'] * 11 + ['4'] + ['2'] * 2 + ['5'] + ['0'] * 3 + ['1'] * 2 + ['6']
        for index in range(1, 91):
            pk = n + index
            status = rnd.choice(outcomes)
            building, elevator = rnd.choice(buildings)
            expert = rnd.choice(experts)
            created_days = rnd.randint(2, 88) if status not in ('0', '1') else rnd.randint(4, 30)
            created = self.ago(days=created_days, hours=rnd.randint(0, 9))
            due = (created + timedelta(days=rnd.randint(3, 12))).date() if rnd.random() < .85 else None
            started = created + timedelta(days=rnd.randint(0, 3), hours=rnd.randint(1, 6)) if status != '0' else None
            if started and started > self.now:
                started = self.now - timedelta(hours=2)
            visit = self.put(Visit, pk, type=self.vt[rnd.choice([5000001, 5000001, 5000002, 5000003])],
                             building=self.b[building], status=status, creator=self.user['planner'],
                             expert=self.user[expert], promoter=self.user[expert], is_active=True,
                             has_due_date=due is not None, due_date=due, visit_comment='QA: سابقه برای داشبورد',
                             rejection_reason='عکس‌ها کافی نبود.' if status in ('4', '5') else None,
                             checked_by=self.user['planner'] if status in ('3', '4', '5') else None,
                             datetime_created=created, datetime_last_change=self.now, start_datetime=started,
                             total_wage=350000, is_deleted=False, supervision_status='0')
            visit.elevator.set([self.e[elevator]])
            if status in ('2', '3', '4', '5'):
                self.fill(visit, mandatory_only=True)
                finished = started + timedelta(days=rnd.choice([0, 0, 1, 1, 2, 3, 5, 9]), hours=rnd.randint(1, 5))
                finished = min(finished, self.now - timedelta(hours=1))
                snapshot = capture_report_snapshot(visit, self.user[expert])
                VisitReportSnapshot.objects.filter(pk=snapshot.pk).update(created_at=finished)
                if status == '3' and rnd.random() < .6:
                    ClientVisitFeedback.objects.update_or_create(visit=visit, user=self.user[managers[building]], defaults={
                        'rating': rnd.choice([3, 4, 4, 5, 5]), 'note': '', 'received_at': finished + timedelta(days=1)})
        self.note('داشبورد', 'ادمین / برنامه‌ریز', '/dashboard',
                  '۹۰ مأموریت سابقه در ۹۰ روز گذشته (تأییدشده، ردشده، منتظر بررسی، برگشتی، باز و دارای دیرکرد) با '
                  'امتیاز رضایت، برای آزمون کارت‌ها، روند، برنامه زمانی و فیلترهای ضربدری')

    def surveys(self):
        now = self.now
        # Restore QA fill-outs to their documented state on every run.
        SurveyAnswer.objects.filter(survey_fill_out_id__gt=5000000, survey_fill_out_id__lt=5000100).delete()
        SurveyPhoto.objects.filter(survey_fill_out_id__gt=5000000, survey_fill_out_id__lt=5000100).delete()
        category = self.put(SurveyReportCategory, 5000001, name='qa-survey-cat', verbose_name='QA رضایت')
        qtype = self.put(SurveyQuestionType, 5000001, name='qa-survey-qt', verbose_name='QA رضایت از خدمات',
                         survey_report_category=category, description='نظر مدیر ساختمان درباره کیفیت خدمت', is_active=True)
        survey = self.put(Survey, 5000001, name='qa-survey', verbose_name='QA ارزیابی رضایت', project=self.project[P1],
                          is_active=True, has_phone_verification=False, datetime_created=now, datetime_last_change=now,
                          sms_text='پس از پایان کار، این چند پرسش را از مدیر ساختمان بپرسید و پاسخ‌ها را ثبت کنید.')
        self.vt[5000001].surveys.set([survey])
        questions = []
        for index, (kind, text) in enumerate([('YesNo', 'آیا سرویس به‌موقع انجام شد؟'),
                                               ('Score', 'رضایت کلی از خدمات (۱ تا ۵)'),
                                               ('Description', 'پیشنهاد شما برای بهبود')]):
            question = self.put(SurveyQuestion, 5000001 + index, text=text, priority=index + 1, survey=survey,
                                survey_question_type=qtype, survey_report_category=category, is_active=True,
                                is_mandatory=index < 2,
                                description=['اگر کارشناس در بازه هماهنگ‌شده رسید «بله» را انتخاب کنید.',
                                             'از ۱ (ضعیف) تا ۵ (عالی).', ''][index])
            question.answer_type.set([self.answer_type[kind]])
            questions.append((question, kind))
        photo_type = self.put(SurveyPhotoType, 5000001, name='qa-survey-photo', verbose_name='QA عکس رضایت', min=0,
                              max=3, survey=survey, survey_report_category=category,
                              description='در صورت تمایل، از امضای فرم رضایت یا محل کار عکس بگیرید.', is_active=True)
        for pk, status, phone, verified, visit_key, user_key in [
                (5000001, '0', '09120000001', False, 'new', 'expert'), (5000002, '1', '09120000002', True, 'review1', 'expert'),
                (5000003, '2', '09120000003', True, 'approved2', 'expert')]:
            fill = self.put(SurveyFillOut, pk, survey=survey, visit=self.v[visit_key], user=self.user[user_key],
                            city=self.city, province=self.city.province if self.city else None, phone_number=phone,
                            phone_verified=verified, status=status, is_closed=status != '0', is_deleted=False,
                            datetime_created=now, datetime_last_change=now)
            if status != '0':
                for index, (question, kind) in enumerate(questions):
                    values = {'YesNo': {'bool': True}, 'Score': {'score': 5},
                              'Description': {'description': 'پیشنهاد آزمایشی QA.'}}[kind]
                    self.put(SurveyAnswer, 5000000 + pk * 10 + index, survey_fill_out=fill, survey_question=question,
                             datetime_created=now, datetime_last_change=now, **values)
                self.put(SurveyPhoto, 5000000 + pk, survey_photo_type=photo_type, survey_fill_out=fill,
                         creator=self.user[user_key], link=self.photo_link('survey', pk),
                         datetime_created=now, datetime_last_change=now)
        self.note('پرسشنامه', 'کارشناس QA', 'تب «مأموریت‌ها» ← پرسشنامه',
                  'سه فرم: شروع‌نشده، تکمیل‌شده، تأییدشده. ارسال کد تلفن به SMS نیاز دارد و روی لوکال قابل آزمون نیست')

    def support(self):
        n = 5000000

        def ticket(pk, creator, title, status, visit_key=None, building_key=None, project=P1, messages=()):
            visit = self.v.get(visit_key) if visit_key else None
            row = self.put(Ticket, pk, project=self.project[project], creator=self.user[creator],
                           role_assignee=self.role['support'], title=title[:35], subject=title[:60], status=status,
                           visit=visit, building=visit.building if visit else (self.b[building_key] if building_key else None),
                           datetime_created=self.ago(days=len(messages) + 1), datetime_last_change=self.now,
                           is_deleted=False)
            for order, (who, body) in enumerate(messages, 1):
                staff = who in ('support', 'admin')
                assignment = RoleAssignment.objects.filter(user=self.user[who], is_deleted=False,
                                                           project_id=project).first()
                self.put(TicketMessage, pk * 10 + order, ticket=row, created_by=self.user[who],
                         created_by_role_assignment=assignment, body=body,
                         datetime_created=self.ago(hours=(len(messages) - order) * 5 + (1 if staff else 2)),
                         datetime_last_change=self.now, is_deleted=False)
            return row

        ticket(n + 1, 'client', 'QA: درخواست هماهنگی سرویس', 'W', visit_key='new',
               messages=[('client', 'سلام، لطفاً زمان سرویس آسانسور برج شرقی را هماهنگ کنید.')])
        ticket(n + 2, 'client', 'QA: صدای غیرعادی کابین', 'A', building_key=2,
               messages=[('client', 'از دیروز کابین هنگام حرکت صدای ساییدگی دارد.'),
                         ('support', 'سلام. کارشناس ظرف ۴۸ ساعت آینده مراجعه می‌کند؛ لطفاً هماهنگ باشید.'),
                         ('client', 'ممنون، منتظر می‌مانیم.')])
        ticket(n + 3, 'client', 'QA: تیکت بسته‌شده', 'C', building_key=1,
               messages=[('client', 'درخواست رسید سرویس دوره‌ای.'), ('support', 'رسید برای شما ایمیل شد؛ تیکت بسته می‌شود.')])
        ticket(n + 4, 'expert', 'QA: کمبود قطعه در مأموریت', 'W', visit_key='partial',
               messages=[('expert', 'کنتاکتور آسانسور ۱ موجود نیست؛ لطفاً قطعه ارسال شود.')])
        ticket(n + 5, 'expert', 'QA: راهنمایی برای برد درایو', 'A', visit_key='ready',
               messages=[('expert', 'خطای E21 روی درایو دیده می‌شود.'),
                         ('support', 'پارامتر P-12 را بررسی کنید و نتیجه را اینجا بنویسید.')])
        ticket(n + 6, 'client_b', 'QA: تیکت کلاینت بتا (ایزوله)', 'W', building_key=6,
               messages=[('client_b', 'این تیکت نباید برای کلاینت آلفا دیده شود.')])
        self.note('پشتیبانی', 'کلاینت آلفا', 'حساب من / پشتیبانی',
                  'سه گفتگو: در انتظار، پاسخ‌داده‌شده، بسته؛ گفتگوی بتا نباید دیده شود. تیکت جدید به حساب «پشتیبان QA» می‌رسد')
        self.note('پشتیبانی', 'کارشناس QA', 'تجهیزات / حساب من ← پشتیبانی', 'دو گفتگو (یک در انتظار، یک پاسخ‌داده‌شده)')
        self.note('پشتیبانی', 'پشتیبان QA', '/ticket/ticketlist', 'پاسخ به تیکت‌ها؛ پاسخ به تیکت بسته باید رد شود')

    def service_cases(self):
        n = 5000000
        p = self.product
        client_a, client_b = self.cl[5000001], self.cl[5000002]
        today = self.today
        contracts = {}
        for pk, ref, client, product, start, end, active, terms in [
                (n + 1, 'QA-W-001', client_a, 5000001, -100, 265, True, 'پوشش کامل قطعات برد'),
                (n + 2, 'QA-W-002', client_a, 5000002, -400, -35, True, 'قرارداد منقضی‌شده'),
                (n + 3, 'QA-W-003', client_a, 5000003, -10, 355, False, 'قرارداد غیرفعال‌شده'),
                (n + 4, 'QA-W-004', client_b, 5000009, -50, 315, True, 'قرارداد کلاینت بتا')]:
            contracts[pk] = self.put(WarrantyContract, pk, project=self.project[P1], client=client, product=p[product],
                                     reference=ref, coverage_start=self.day(start), coverage_end=self.day(end),
                                     terms=terms, exclusions='آسیب ناشی از برق‌گرفتگی و دستکاری', is_active=active,
                                     created_by=self.user['planner'])
        claims = {}
        for pk, client, product, contract, status, issue, reason, decided in [
                (n + 1, client_a, 5000001, n + 1, 'PENDING', 'برد کنترل ارور E12 می‌دهد و آسانسور متوقف می‌شود.', '', None),
                (n + 2, client_a, 5000001, n + 1, 'COVERED', 'رله خروجی برد سوخته است.', 'تحت پوشش قرارداد QA-W-001', 3),
                (n + 3, client_a, 5000002, n + 2, 'DENIED', 'خرابی پس از پایان قرارداد.', 'قرارداد منقضی شده است.', 8),
                (n + 4, client_b, 5000009, n + 4, 'PENDING', 'قطعی متناوب برد؛ ادعای بتا (ایزوله).', '', None)]:
            claims[pk] = self.put(WarrantyClaim, pk, project=self.project[P1], client=client, product=p[product],
                                  contract=contracts[contract], status=status, issue=issue, decision_reason=reason,
                                  opened_by=self.user['client'] if client is client_a else self.user['client_b'],
                                  decided_by=self.user['planner'] if decided else None,
                                  decided_at=self.ago(days=decided) if decided else None,
                                  opened_at=self.ago(days=(decided or 1) + 2))
            WarrantyClaim.objects.filter(pk=pk).update(opened_at=self.ago(days=(decided or 1) + 2))
        states = ['RECEIVED', 'DIAGNOSING', 'REPAIRING', 'TESTING', 'READY', 'DELIVERED', 'CANCELED']
        cases = {}
        for index, state in enumerate(states, 1):
            product = {5: 5000005, 6: 5000002}.get(index, 5000001 if index == 3 else 5000004)
            cases[state] = self.put(
                RepairCase, n + index, rma_key=uuid.uuid5(uuid.NAMESPACE_URL, f'qa-repair-{index}'),
                project=self.project[P1], client=client_a, product=p[product], claim=claims[n + 2] if index == 3 else None,
                serial_snapshot=p[product].serial_number, status=state, received_at=self.ago(days=20 - index),
                diagnosis='' if state == 'RECEIVED' else 'خرابی رله خروجی و آسیب در مسیر مس',
                work_performed='' if state in ('RECEIVED', 'DIAGNOSING') else 'تعویض رله و لحیم‌کاری مجدد',
                test_result='' if state in ('RECEIVED', 'DIAGNOSING', 'REPAIRING') else 'آزمون ۲۴ ساعته موفق بود',
                delivered_at=self.ago(days=1) if state == 'DELIVERED' else None, created_by=self.user['planner'])
            RepairCase.objects.filter(pk=n + index).update(received_at=self.ago(days=20 - index))
            history = states[:states.index(state) + 1] if state != 'CANCELED' else ['RECEIVED', 'DIAGNOSING', 'CANCELED']
            RepairEvent.objects.filter(case=cases[state]).delete()
            previous = ''
            for step, to_state in enumerate(history):
                event = RepairEvent.objects.create(case=cases[state], from_status=previous, to_status=to_state,
                                                   actor=self.user['planner'], note=f'QA: انتقال به {to_state}')
                RepairEvent.objects.filter(pk=event.pk).update(at=self.ago(days=20 - index, hours=-step))
                previous = to_state
        # Loaner board is out on the REPAIRING case; another case has a returned loaner.
        RepairCase.objects.filter(pk=cases['REPAIRING'].pk).update(loaner_product=p[5000007], loaner_due_at=self.day(7))
        RepairCase.objects.filter(pk=cases['TESTING'].pk).update(
            loaner_product=p[5000006], loaner_due_at=self.day(-3), loaner_returned_at=self.ago(days=2))
        self.note('گارانتی', 'کلاینت آلفا', 'گارانتی',
                  'قرارداد فعال، منقضی و غیرفعال؛ ادعاها: در انتظار، تحت پوشش، رد؛ ادعای بتا نباید دیده شود')
        self.note('گارانتی', 'برنامه‌ریز / ادمین', '/service-cases',
                  'تصمیم برای ادعای در انتظار، ساخت پروندهٔ تعمیر، تغییر وضعیت‌ها، برد امانی، مصرف قطعه')
        self.note('تعمیر', 'کلاینت آلفا', 'گارانتی ← تعمیرات',
                  'هفت پرونده: دریافت‌شده، عیب‌یابی، تعمیر، آزمون، آماده، تحویل، لغو؛ دو مورد با برد امانی')

    def stock_and_invoices(self):
        n = 5000000
        proj = self.project[P1]
        unit = self.put(Unit, n + 1, unit_en='piece', unit_fa='عدد', unit_abbreviation='عدد')
        types = {k: self.put(WareType, n + i, name=f'qa-{k}', verbose_name=v) for i, (k, v) in
                 enumerate([('board', 'QA قطعات برد'), ('door', 'QA قطعات درب'), ('consumable', 'QA مصرفی')], 1)}
        wares = {}
        for pk, key, name, ident, use in [(n + 1, 'board', 'QA کنتاکتور ۲۴ ولت', 'QA-W-CONT', True),
                                          (n + 2, 'door', 'QA آرام‌بند درب', 'QA-W-DOOR', True),
                                          (n + 3, 'consumable', 'QA روغن ریل (لیتر)', 'QA-W-OIL', True),
                                          (n + 4, 'board', 'QA برد بدون موجودی', 'QA-W-EMPTY', False)]:
            wares[pk] = self.put(Ware, pk, name_fa=name, name_en=ident, type=types[key], unit=unit, is_for_use=use,
                                 identifier=ident, project=proj, is_active=True, priority=0,
                                 datetime_created=self.now, datetime_last_change=self.now)
            WareVisitType.objects.get_or_create(ware=wares[pk], visit_type=self.vt[5000001])
        location = self.put(WarehouseLocation, n + 1, name_fa='QA انبار مرکزی', name_en='QA Central')
        location.projects.set([proj])
        location2 = self.put(WarehouseLocation, n + 2, name_fa='QA انبار شعبه غرب', name_en='QA West')
        location2.projects.set([proj])
        user_ids = {k: self.user[k].pk for k in ('expert', 'expert2')}

        def txn(pk, kind, description, lines, creator='warehouse'):
            row = self.put(WarehouseTransaction, pk, creator=self.user[creator], project=proj, movement_kind=kind,
                           description=description, datetime_created=self.ago(days=3), datetime_last_change=self.now)
            WarehouseTransactionLine.objects.filter(transaction=row).delete()
            for ware_pk, amount, place in lines:
                WarehouseTransactionLine.objects.create(
                    transaction=row, ware=wares[ware_pk], amount=amount,
                    location=place if isinstance(place, WarehouseLocation) else None,
                    user_id=place if isinstance(place, int) else None)

        txn(n + 1, 'OPENING', 'QA موجودی افتتاحیه انبار مرکزی',
            [(n + 1, 50, location), (n + 2, 30, location), (n + 3, 100, location), (n + 4, 0, location)])
        txn(n + 2, 'RECEIPT', 'QA دریافت از تأمین‌کننده', [(n + 1, 20, location2)])
        txn(n + 3, 'TRANSFER', 'QA انتقال به کارشناس الف',
            [(n + 1, -10, location), (n + 1, 10, user_ids['expert']), (n + 3, -20, location), (n + 3, 20, user_ids['expert']),
             (n + 2, -5, location), (n + 2, 5, user_ids['expert'])])
        txn(n + 4, 'TRANSFER', 'QA انتقال به کارشناس ب', [(n + 1, -3, location), (n + 1, 3, user_ids['expert2'])])
        txn(n + 5, 'CONSUME', 'QA مصرف در مأموریت', [(n + 3, -2, user_ids['expert'])], creator='expert')
        txn(n + 6, 'RETURN', 'QA برگشت قطعهٔ سالم به انبار', [(n + 2, -1, user_ids['expert']), (n + 2, 1, location)])
        txn(n + 7, 'SCRAP', 'QA ضایعات: قطعه سوخته', [(n + 1, -1, user_ids['expert'])], creator='expert')
        # Invoices cover the client-facing payment states (paying needs SMS and wallet keys, absent locally).
        for key, status, closed, amount, visit_key, note in [
                ('open', WalletInvoice.STATUS.INITIAL, False, 1250000, 'approved1', 'فاکتور باز QA؛ پرداخت نیازمند SMS است'),
                ('paid', WalletInvoice.STATUS.PAID, True, 800000, 'approved2', 'فاکتور پرداخت‌شده QA'),
                ('zero', WalletInvoice.STATUS.INITIAL, False, 0, 'approved3', 'فاکتور صفر QA؛ پرداخت نباید مجاز باشد')]:
            invoice_id = uuid.uuid5(uuid.NAMESPACE_URL, f'qa-invoice-{key}')
            self.put(WalletInvoice, invoice_id, type=WalletInvoice.TYPES.CREDIT, expert=self.user['expert'],
                     visit=self.v[visit_key], client=self.user['client'], amount_rials=amount,
                     payable_amount_rials=amount, description=note, is_closed=closed, status=status,
                     datetime_created=self.ago(days=2), datetime_last_change=self.now)
        self.note('انبار', 'انباردار QA / ادمین', '/warehouse/warelist',
                  'چهار کالا (یکی بدون موجودی)، دو انبار؛ گردش‌های افتتاحی، دریافت، انتقال، مصرف، برگشت و ضایعات')
        self.note('انبار', 'کارشناس QA', 'تجهیزات', 'موجودی شخصی: کنتاکتور ۱۰ (۹ + یک درخواست تحویل‌شده)، روغن ۱۸ ، آرام‌بند ۴ (پس از برگشت/مصرف/ضایعات)؛ کارشناس ب فقط ۳ کنتاکتور')
        self.note('مالی', 'کلاینت آلفا', 'خانه ← فاکتور',
                  'سه فاکتور: باز، پرداخت‌شده، صفر. دریافت کد پرداخت به پیامک نیاز دارد و روی لوکال تکمیل نمی‌شود')

    def field_ops(self):
        """Accept / hand back, client completion codes, visit chat, part requests and maintenance plans."""
        from utils.models import Conversation, ConversationMessage
        from visit.models import MaintenancePlan, VisitAssignmentEvent
        from warehouse.models import PartRequest
        v, n = self.v, BASE
        qa = Visit.objects.filter(pk__gt=n, pk__lt=n + 300)
        # Plans on QA elevators (seeded or added while testing) and the visits run_field_schedules opened from them.
        qa_plans = MaintenancePlan.objects.filter(elevator_id__in=[row.pk for row in self.e.values()])
        Visit.objects.filter(maintenance_plan__in=qa_plans).exclude(pk__in=[row.pk for row in v.values()]).delete()
        VisitAssignmentEvent.objects.filter(visit__in=qa).delete()
        PartRequest.objects.filter(visit__in=qa).delete()
        conversations = Conversation.objects.filter(visit__in=qa)
        ConversationMessage.objects.filter(conversation__in=conversations).delete()
        conversations.delete()
        qa.update(completion_code='', completion_code_failures=0, completion_code_locked_until=None, maintenance_plan=None)
        # Emergency visits need the building manager's code to be finished.
        VisitType.objects.filter(pk__in=[5000001, 5000002]).update(requires_client_code=False)
        VisitType.objects.filter(pk=5000003).update(requires_client_code=True)
        accepted = ('today', 'multi', 'nodue', 'dual_task', 'b_new', 'beta_open', 't_new', 'p1_multi', 'adm_new')
        for key in accepted:
            event = VisitAssignmentEvent.objects.create(visit=v[key], user=v[key].expert, action='accepted')
            VisitAssignmentEvent.objects.filter(pk=event.pk).update(created_at=self.ago(days=1))
        event = VisitAssignmentEvent.objects.create(
            visit=v['unassigned'], user=self.user['expert2'], action='declined',
            reason='در تاریخ موعد در مرخصی هستم؛ لطفاً به کارشناس دیگری بسپارید.')
        VisitAssignmentEvent.objects.filter(pk=event.pk).update(created_at=self.ago(hours=6))
        # Chat on the visit in progress at the East tower (client Alpha manages it).
        chat = Conversation.objects.create(visit=v['partial'], type=1, title=f'گفتگوی مأموریت {v["partial"].pk}',
                                           subject='visit_chat', status=2)
        for hours, user, body in [
                (3, 'expert', 'سلام، حدود ساعت ۱۰ در محل هستم. لطفاً کلید موتورخانه هماهنگ شود.'),
                (2, 'client', 'سلام، کلید نزد نگهبانی است. ورود از درب شرقی ساختمان.'),
                (1, 'expert', 'ممنون، رسیدم و کار را شروع کردم.')]:
            row = ConversationMessage.objects.create(conversation=chat, user=self.user[user], body=body, is_seen=hours > 1)
            ConversationMessage.objects.filter(pk=row.pk).update(datetime_created=self.ago(hours=hours))
        # Part requests: pending, fulfilled (with its stock transfer) and rejected.
        central = WarehouseLocation.objects.get(pk=n + 1)
        transfer = self.put(WarehouseTransaction, n + 8, creator=self.user['warehouse'], project=self.project[P1],
                            movement_kind='TRANSFER', description=f'تحویل درخواست قطعه برای مأموریت {v["partial"].pk}',
                            datetime_created=self.ago(hours=20), datetime_last_change=self.now)
        WarehouseTransactionLine.objects.filter(transaction=transfer).delete()
        WarehouseTransactionLine.objects.create(transaction=transfer, ware_id=n + 1, amount=-1, location=central)
        WarehouseTransactionLine.objects.create(transaction=transfer, ware_id=n + 1, amount=1, user=self.user['expert'])
        for pk, ware, amount, status, note, extra in [
                (n + 1, n + 2, 2, 'PENDING', 'آرام‌بند درب طبقه سوم روغن پس می‌دهد.', {}),
                (n + 2, n + 1, 1, 'FULFILLED', 'کنتاکتور اصلی صدای غیرعادی دارد.',
                 {'location': central, 'stock_transaction': transfer, 'decided_by': self.user['warehouse'],
                  'decided_at': self.ago(hours=20)}),
                (n + 3, n + 4, 1, 'REJECTED', 'برد یدک برای تعویض فوری.',
                 {'decision_note': 'این برد فعلاً تأمین نمی‌شود؛ برای تعمیر برد با پشتیبانی هماهنگ کنید.',
                  'decided_by': self.user['warehouse'], 'decided_at': self.ago(hours=18)})]:
            PartRequest.objects.create(pk=pk, project=self.project[P1], visit=v['partial'], requester=self.user['expert'],
                                       ware_id=ware, amount=amount, status=status, note=note, **extra)
        # Maintenance plans: one ahead, one with its open visit, one due without an expert.
        qa_plans.delete()
        common = dict(project=self.project[P1], visit_type=self.vt[5000001], created_by=self.user['planner'],
                      is_active=True)
        MaintenancePlan.objects.create(pk=n + 1, elevator=self.e[1], expert=self.user['expert'], interval_days=30,
                                       lead_days=7, next_due=self.day(20), note='روغن‌کاری ریل و بازدید ترمز', **common)
        plan = MaintenancePlan.objects.create(pk=n + 2, elevator=self.e[3], expert=self.user['expert'], interval_days=60,
                                              lead_days=7, next_due=self.day(60), **common)
        Visit.objects.filter(pk=v['today'].pk).update(maintenance_plan=plan)
        MaintenancePlan.objects.create(pk=n + 3, elevator=self.e[4], expert=None, interval_days=30, lead_days=7,
                                       next_due=self.day(3), note='سرویس ماهانه آسانسور هیدرولیک', **common)
        self.note('پذیرش مأموریت', 'کارشناس QA', 'تب «مأموریت‌ها»',
                  f'مأموریت‌های {v["new"].pk} و {v["overdue"].pk} «منتظر پذیرش» هستند؛ «بازگرداندن» با دلیل، '
                  f'مأموریت را از فهرست خارج و برنامه‌ریز را مطلع می‌کند. {v["unassigned"].pk} را کارشناس ب برگردانده است.')
        self.note('کد تأیید', 'کلاینت آلفا + کارشناس QA', f'/client/visits/{v["overdue"].pk} و /visitDetail/{v["overdue"].pk}',
                  'نوع «بازدید اضطراری» کد مدیر ساختمان می‌خواهد؛ کد در جزئیات خدمت کلاینت است و پنج کد اشتباه آن را '
                  'عوض و ۱۵ دقیقه قفل می‌کند. تنظیم در پنل: ویزیت‌ها ← انواع خدمت')
        self.note('گفتگو', 'کارشناس QA / کلاینت آلفا', f'مأموریت {v["partial"].pk}',
                  'گفتگوی سه‌پیامی بدون نمایش شماره؛ نماینده آلفا فقط می‌خواند؛ پس از پایان مأموریت بسته می‌شود')
        self.note('درخواست قطعه', 'کارشناس QA / انباردار', f'مأموریت {v["partial"].pk} و /warehouse/part-requests',
                  'یک درخواست در انتظار (آرام‌بند)، یک تحویل‌شده از انبار مرکزی و یک ردشده با دلیل')
        self.note('سرویس ادواری', 'برنامه‌ریز', '/elevatormanagement/elevatordetail/5000003 و 5000004',
                  f'سه برنامه؛ مأموریت {v["today"].pk} از برنامه ساخته شده؛ برنامه آسانسور نیلوفر کارشناس ندارد و '
                  'دستور run_field_schedules برای آن مأموریت غیرفعال می‌سازد و به برنامه‌ریز اعلام می‌کند')

    def assignment_data(self):
        """Specialties, grades, calendar and service requirements, with unassigned visits to plan."""
        from visit.models import (AssignmentSetting, ExpertProfile, ExpertSkill, ExpertTimeOff, ServiceRequirement,
                                  Skill)
        v, n = self.v, BASE
        project = self.project[P1]
        AssignmentSetting.objects.filter(project=project).delete()
        qa_users = [self.user[key] for key in ('expert', 'expert2', 'dual', 'multi', 'supervisor')]
        ExpertTimeOff.objects.filter(project=project, user__in=qa_users).delete()
        ExpertSkill.objects.filter(project=project, user__in=qa_users).delete()
        ExpertProfile.objects.filter(project=project, user__in=qa_users).delete()
        ServiceRequirement.objects.filter(visit_type__in=self.vt.values()).delete()
        skills = {}
        for index, (name, text) in enumerate([
                ('بردهای کنترل و درایو', 'عیب‌یابی و تعمیر بردهای تابلو فرمان'),
                ('درب‌های اتوماتیک', 'تنظیم و تعمیر درب کابین و طبقات'),
                ('آسانسور هیدرولیک', 'پمپ، شیر و جک هیدرولیک'),
                ('امداد و بازدید اضطراری', 'رها‌سازی افراد گرفتار و ایمن‌سازی')], 1):
            skills[index] = self.put(Skill, n + index, project=project, name=name, description=text, is_active=True)
        grades = {'expert': (4, 30, {1: 5, 2: 4, 4: 3}), 'expert2': (2, 12, {1: 2, 2: 3}),
                  'dual': (3, 12, {1: 3, 3: 3}), 'multi': (3, 12, {})}
        for key, (grade, max_open, levels) in grades.items():
            ExpertProfile.objects.create(project=project, user=self.user[key], grade=grade, max_open=max_open,
                                         daily_capacity=4, work_days=[5, 6, 0, 1, 2], is_assignable=True)
            for skill_index, level in levels.items():
                ExpertSkill.objects.create(project=project, user=self.user[key], skill=skills[skill_index], level=level)
        ExpertTimeOff.objects.create(project=project, user=self.user['expert2'], start_date=self.day(2),
                                     end_date=self.day(6), reason='سفر', created_by=self.user['planner'])
        for pk, complexity, rules in [
                (5000001, 2, [(1, 2, False)]),
                (5000002, 3, [(1, 4, True), (2, 2, False)]),
                (5000003, 4, [(4, 3, True)])]:
            VisitType.objects.filter(pk=pk).update(complexity=complexity)
            for skill_index, level, required in rules:
                ServiceRequirement.objects.create(visit_type=self.vt[pk], skill=skills[skill_index], min_level=level,
                                                  is_required=required)
        # Two more unassigned visits next to the existing unassigned one and the two client requests.
        v['plan_emergency'] = self.make_visit(n + 33, 5000003, 2, '0', None, (1,), active=True, due=self.day(1),
                                              comment='QA: بازدید اضطراری؛ فقط کارشناس با مهارت امداد و گرید ۴')
        v['plan_repair'] = self.make_visit(n + 34, 5000002, 4, '0', None, (4,), active=True, due=self.day(4),
                                           comment='QA: تعمیر برد؛ مهارت بردها حداقل سطح ۴')
        self.note('تخصیص هوشمند', 'برنامه‌ریز / ادمین', '/assignment',
                  f'پنج مأموریت بدون کارشناس ({v["unassigned"].pk}، {v["plan_emergency"].pk}، {v["plan_repair"].pk} و دو '
                  'درخواست کلاینت). اضطراری و تعمیر برد فقط کارشناس الف را واجد شرایط می‌دانند؛ کارشناس ب تا چند روز '
                  'دیگر در مرخصی است و کارشناس‌های گرید پایین با دلیل محدود می‌شوند. سه تب: پیشنهاد، کارشناسان، مهارت‌ها و ضرایب.')

    def notifications(self):
        def note(user_key, project, key, kind, title, body, obj, days=0, read=False):
            row, _ = InAppNotification.objects.update_or_create(
                recipient=self.user[user_key], project=self.project[project], source_key='qa:' + key,
                defaults={'kind': kind, 'title': title, 'body': body, 'object_id': obj,
                          'read_at': self.ago(days=days) if read else None})
            InAppNotification.objects.filter(pk=row.pk).update(created_at=self.ago(days=days, hours=1))

        v = self.v
        note('expert', P1, 'assign-new', 'visit_assignment', 'مأموریت تازه برای شما',
             f'مأموریت شماره {v["new"].pk} فعال شد.', v['new'].pk, 0)
        note('expert', P1, 'assign-today', 'visit_assignment', 'مأموریت تازه برای شما',
             f'مأموریت شماره {v["today"].pk} فعال شد.', v['today'].pk, 1, read=True)
        note('expert', P1, 'ticket-reply', 'support_reply', 'پاسخ تازه از پشتیبانی', 'گفتگوی «راهنمایی برای برد درایو» پاسخ دارد.', 5000005, 0)
        note('supervisor', P1, 'assign', 'visit_assignment', 'مأموریت تازه برای شما', 'مأموریت تازه در محدودهٔ نظارت.', v['review2'].pk, 0)
        note('client', P1, 'ticket-reply', 'support_reply', 'پاسخ تازه از پشتیبانی', 'گفتگوی «صدای غیرعادی کابین» پاسخ دارد.', 5000002, 0)
        note('client', P1, 'warranty', 'warranty_decision', 'نتیجه بررسی گارانتی', 'ادعای گارانتی شماره ۵۰۰۰۰۰۲ تحت پوشش تشخیص داده شد.', 5000002, 3, read=True)
        note('client', P1, 'repair', 'repair_status', 'وضعیت تعمیر تغییر کرد', 'پرونده تعمیر ۵۰۰۰۰۰۵: آماده تحویل.', 5000005, 1)
        note('client_rep', P1, 'repair', 'repair_status', 'وضعیت تعمیر تغییر کرد', 'پرونده تعمیر ۵۰۰۰۰۰۵: آماده تحویل.', 5000005, 1)
        note('client_b', P1, 'private', 'support_reply', 'اعلان کلاینت بتا', 'این اعلان فقط برای بتا نمایش داده می‌شود.', 5000006, 0)
        for key in ('support', 'admin'):
            note(key, P1, 'incoming', 'support_incoming', 'گفتگوی پشتیبانی تازه', 'گفتگوی «درخواست هماهنگی سرویس» پیام تازه دارد.', 5000001, 0)
            note(key, P1, 'incoming-old', 'support_incoming', 'پیام تازه در پشتیبانی', 'گفتگوی قدیمی پیام تازه داشت.', 5000002, 5, read=True)
        self.note('اعلان', 'همهٔ نقش‌ها', 'زنگ اعلان',
                  'اعلان خوانده/نخوانده برای کارشناس، سرپرست، کلاینت‌ها، پشتیبان و ادمین؛ اعلان بتا فقط برای بتا')

    def academy(self):
        guide = self.media / 'qa-guide.pdf'
        if not guide.exists():
            guide.write_bytes(b'%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n'
                              b'2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
                              b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]>>endobj\n'
                              b'trailer<</Root 1 0 R>>\n%%EOF\n')
        base = 'http://localhost:18110/media/uploads/qa/'
        for pk, kind, name, link, desc in [
                (5000001, 'EDU', 'QA آموزش ایمنی کار در ارتفاع', base + 'qa-guide.pdf', 'فایل آموزشی PDF'),
                (5000002, 'EDU', 'QA راهنمای تصویر برد کنترل', base + 'qa-panel-1.png', 'تصویر آموزشی'),
                (5000003, 'ETC', 'QA راهنمای کار با اپلیکیشن', base + 'qa-guide.pdf', 'راهنمای عمومی')]:
            self.put(UploadedFile, pk, file=link, name=name, type=kind, description=desc,
                     uploaded_by=self.user['admin'], project=self.project[P1], is_deleted=False, priority=pk)
        self.note('آکادمی', 'کارشناس QA', 'آکادمی', 'دو محتوای آموزشی (PDF و تصویر)؛ راهنما در بخش «حساب من / راهنما»')

    # -------------------------------------------------------------- report
    def write_report(self):
        base = {'admin': 'http://localhost:18120', 'field': 'http://localhost:18122'}
        who = {  # key -> (where to sign in, what they are)
            'admin': ('admin', 'ادمین کامل: همهٔ APIها و منوی کامل پنل؛ دریافت‌کنندهٔ اعلان پشتیبانی'),
            'planner': ('admin', 'برنامه‌ریز و مدیر خدمات: مشاهدهٔ بیشتر صفحه‌ها، نوشتن ویزیت/تیکت/دارایی، مرکز گارانتی؛ بدون حذف و انبار/کیف پول'),
            'support': ('admin', 'پشتیبان: فقط تیکت‌ها و داشبورد؛ گیرندهٔ تیکت‌های تازهٔ کلاینت/کارشناس'),
            'warehouse': ('admin', 'انباردار: فقط مدیریت انبار'),
            'supervisor': ('field', 'سرپرست: کارهای کارشناس الف را نظارت می‌کند (کارشناس ب خارج از دامنه)'),
            'expert': ('field', 'کارشناس الف: مأموریت‌ها در همهٔ وضعیت‌ها، تجهیزات، آکادمی، کیف پول'),
            'expert2': ('field', 'کارشناس ب: فقط مأموریت‌های خودش؛ برای آزمون ایزولاسیون'),
            'client': ('field', 'کلاینت آلفا: مدیر ساختمان‌ها؛ درخواست، گارانتی، پشتیبانی، فاکتور'),
            'client_rep': ('field', 'نمایندهٔ آلفا: فقط مشاهده؛ هر نوشتن باید 403 شود'),
            'client_b': ('field', 'کلاینت بتا: ساختمان جدا؛ ایزولاسیون و سابقهٔ انتقال'),
            'dual': ('field', 'حساب دونقشه: کارشناس + کلاینت گاما در یک ورود'),
            'multi': ('field', 'چندپروژه‌ای: کارشناس در پروژه ۱، کلاینت در پروژه ۲؛ نمایش انتخاب پروژه'),
            'norole': ('field', 'بدون نقش: صفحهٔ «دسترسی ندارید»'),
            'inactive': ('field', 'حساب غیرفعال: ورود باید رد شود'),
            'deleted_role': ('field', 'نقش حذف‌شده: مثل بدون دسترسی'),
        }
        lines = ['# حساب‌ها و داده‌های آزمایشی QA', '',
                 f'ساخته‌شده: {timezone.localtime(self.now):%Y-%m-%d %H:%M} — فقط روی لوکال؛ این فایل و `qa-accounts.json` در Git ignore هستند.',
                 '', '## آدرس‌ها', '', '| سرویس | آدرس |', '| --- | --- |',
                 f'| پنل ادمین | {base["admin"]} |', f'| اپ میدانی (کارشناس و کلاینت) | {base["field"]} |',
                 '| API سلامت | http://localhost:18110/health/ |',
                 '| Django admin | http://localhost:18110/coreadminurl/ |', '',
                 'ورود: در هر دو برنامه روی «ورود با رمزعبور» بزنید (ورود با کد پیامکی به SMS نیاز دارد و روی لوکال کار نمی‌کند).',
                 '', '## حساب‌ها', '',
                 '| نقش | نام کاربری | رمز | ورود از | توضیح | تعداد grant |', '| --- | --- | --- | --- | --- | --- |']
        grant_key = {'expert2': 'expert', 'client_b': 'client', 'dual': 'expert', 'multi': 'expert',
                     'norole': None, 'inactive': 'expert', 'deleted_role': 'expert'}
        for key, username, first, last, assignments, extra in PERSONAS:
            site, text = who[key]
            role_key = grant_key.get(key, key)
            count = self.grant_counts.get(role_key, '—') if role_key else '—'
            lines.append(f'| {first} {last} | `{username}` | `{self.passwords[username]}` | {base[site]} | {text} | {count} |')
        lines.append(f'| Django superuser | `{DJANGO_ADMIN[0]}` | `{self.passwords[DJANGO_ADMIN[0]]}` | http://localhost:18110/coreadminurl/ | پنل Django | — |')
        lines += ['', 'حساب‌های قدیمی لوکال (`09000000001` فقط‌مشاهده ، `09000000004` دسترسی کامل اکسپرت ، `09000000005` کلاینت پیش‌نمایش) '
                  'دست‌نخورده‌اند؛ رمزشان در فایل‌های ignored همان `backend/data` است.', '',
                 '## شناسهٔ پروژه‌ها', '',
                 f'- پروژه ۱ (اصلی): `{P1}`\n- پروژه ۲ (فعال): `{P2}`\n- پروژه ۳ (غیرفعال، نباید قابل انتخاب باشد): `{P3}`', '',
                 '## سناریوها و انتظارها', '', '| حوزه | حساب | مسیر | انتظار |', '| --- | --- | --- | --- |']
        for area, who_, where, expectation in self.scenarios:
            lines.append(f'| {area} | {who_} | {where} | {expectation} |')
        v = self.v
        lines += ['', '## لینک‌های مستقیم', '', '| چه چیزی | آدرس |', '| --- | --- |']
        for key, label in [('new', 'مأموریت جدید'), ('partial', 'در حال انجام (ناقص)'), ('ready', 'آمادهٔ پایان'),
                           ('adm_review', 'تکمیل‌شده با ادمین مجری (جزئیات ادمین کار می‌کند)'),
                           ('adm_approved', 'تأییدشده با ادمین مجری'), ('review1', 'در انتظار تأیید'), ('approved2', 'تأییدشده با بازخورد'), ('rejected', 'ردشده'),
                           ('request1', 'درخواست کلاینت (برنامه‌ریزی نشده)'), ('b_new', 'مأموریت کارشناس ب'),
                           ('t_old', 'ویزیت بستهٔ دورهٔ قبلی مدیریت'), ('p2_new', 'ویزیت پروژه ۲')]:
            lines.append(f'| {label} — ادمین | {base["admin"]}/visitmanagment/answerlist/{v[key].pk} |')
            lines.append(f'| {label} — کلاینت | {base["field"]}/client/visits/{v[key].pk} |')
        lines += ['', '## آزمون ایزولاسیون (IDOR)', '',
                  f'- با کلاینت آلفا آدرس `/client/visits/{v["beta_open"].pk}` (مال بتا) و `/client/visits/{v["p2_new"].pk}` (پروژه ۲) را باز کنید ← باید «در دسترس نیست» بدهد.',
                  f'- با کارشناس الف `/visitDetail/{v["b_new"].pk}` (مال کارشناس ب) ← باید رد شود.',
                  f'- با نمایندهٔ آلفا ثبت درخواست/بازخورد/تیکت ← باید 403 بدهد.',
                  '- با حساب غیرفعال یا حذف‌شده ورود/دسترسی ← رد؛ با حساب چندپروژه‌ای پروژهٔ غیرفعال را نباید ببینید.', '',
                  '## محدودیت‌های لوکال', '',
                  '- ورود با کد پیامکی، تأیید تلفن پرسشنامه، کد پرداخت فاکتور و اعلان پیامکی به SMS نیاز دارند و اینجا آزموده نمی‌شوند.',
                  '- امضای کیف پول به کلید RSA در محیط نیاز دارد؛ فاکتورها فقط برای نمایش حالت‌ها ساخته شده‌اند.',
                  '- داده ساختگی است و برای تأیید پایگاه‌داده یا اتصالات واقعی تولید معتبر نیست.']
        (self.data_dir / REPORT_NAME).write_text('\n'.join(lines) + '\n', encoding='utf-8')
