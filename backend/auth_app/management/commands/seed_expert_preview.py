"""Prepare a separate full-access field-app account in the local SQLite only."""
import sqlite3
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.urls import get_resolver
from django.utils import timezone

from auth_app.models import (City, ExtendedUser, FieldValidation, Project,
                            QuestionAnswerTypeValidation, Role, RoleAssignment,
                            RoleView, ViewMethod)
from config.models import NavMenu
from visit.models import Answer, Photo, Question, Visit
from warehouse.models import TransactionLineType, WarehouseTransaction, WarehouseTransactionLine


class Command(BaseCommand):
    help = "Create an isolated local field-app preview with every registered API permission."

    def add_arguments(self, parser):
        parser.add_argument('--username', default='09000000004')
        parser.add_argument('--password', required=True)

    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        if (settings.SETTINGS_MODULE != 'core.local_settings' or not settings.DEBUG
                or db['ENGINE'] != 'django.db.backends.sqlite3'):
            raise CommandError('This command is only available for local DEBUG SQLite.')
        source = Visit.objects.filter(pk=2000001).first()
        if not source:
            raise CommandError('Run seed_detail_demo first; existing demo records are required.')
        account = User.objects.filter(username=options['username']).first()
        if account and not RoleAssignment.objects.filter(user=account, role__title='LocalFullAccess').exists():
            raise CommandError('Refusing to change an existing unrelated account.')
        directory = Path(settings.BASE_DIR) / 'data'
        directory.mkdir(exist_ok=True)
        backup = directory / ('db-before-expert-preview-' + timezone.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
        with sqlite3.connect(str(db['NAME'])) as current, sqlite3.connect(str(backup)) as saved:
            current.backup(saved)

        def views(patterns):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    yield from views(pattern.url_patterns)
                else:
                    cls = getattr(pattern.callback, 'cls', None)
                    if cls:
                        yield cls

        def copy_row(model, original, pk, overrides):
            values = {field.attname: getattr(original, field.attname)
                      for field in model._meta.concrete_fields if not field.primary_key}
            values.update(overrides)
            if model.objects.filter(pk=pk).exists():
                model.objects.filter(pk=pk).update(**values)
            else:
                model.objects.bulk_create([model(pk=pk, **values)])
            return model.objects.get(pk=pk)

        with transaction.atomic():
            project = Project.objects.get(pk=1)
            role, _ = Role.objects.get_or_create(title='LocalFullAccess', defaults={
                'title_abbreviation': 'M', 'verbose_name': 'بررسی کامل لوکال',
                'priority': 0, 'is_active': True, 'asset_scope': 'project'})
            if not account:
                account = User.objects.create_user(username=options['username'], password=options['password'],
                                                   first_name='بررسی کامل', last_name='لوکال')
            RoleAssignment.objects.get_or_create(user=account, role=role, project=project, is_deleted=False)
            city = City.objects.filter(name__contains='تهران').first() or City.objects.first()
            profile, _ = ExtendedUser.objects.get_or_create(user=account, defaults={
                'full_name': 'حساب بررسی کامل لوکال', 'role': 'M', 'city': city,
                'province': city.province if city else None})
            profile.roles.add(role)
            for cls in set(views(get_resolver().url_patterns)):
                for method in ('get', 'post', 'put', 'patch', 'delete', 'options'):
                    if hasattr(cls, method):
                        ViewMethod.objects.get_or_create(view_name=cls.__name__, method=method.upper())
            for method in ViewMethod.objects.all():
                RoleView.objects.update_or_create(role=role, view_method_name=method, defaults={
                    'can_view': True, 'can_create': True, 'can_update': True, 'can_delete': True})

            icons = 'http://localhost:18110/media/expert-preview/'
            for priority, (route, title, icon) in enumerate([
                    ('tasks', 'کارها', 'order-list'), ('edu', 'آکادمی', 'academy'),
                    ('wares', 'تجهیزات', 'equipment'), ('setting', 'تنظیمات', 'profile')]):
                NavMenu.objects.update_or_create(role=role, route=route, defaults={
                    'title': route, 'title_fa': title, 'priority': priority,
                    'active_icon': icons + icon + '-active.svg',
                    'deactive_icon': icons + icon + '.svg', 'is_landing': route == 'tasks'})

            now = timezone.now()
            for pk, status in [(3000001, '0'), (3000002, '2')]:
                visit = copy_row(Visit, source, pk, {
                    'creator_id': account.id, 'expert_id': account.id, 'promoter_id': account.id,
                    'status': status, 'is_active': True, 'has_due_date': False, 'due_date': None,
                    'checked_by_id': None, 'start_datetime': None if status == '0' else now,
                    'datetime_created': now, 'datetime_last_change': now,
                    'visit_comment': 'داده آزمایشی حساب اکسپرت لوکال', 'comment_publisher_id': account.id})
                visit.elevator.set(source.elevator.all())
                if status == '2':
                    for answer in Answer.objects.filter(visit=source):
                        copied = copy_row(Answer, answer, 3000000 + answer.id - 2000000, {'visit_id': visit.id})
                        copied.multichoice.set(answer.multichoice.all())
                    for photo in Photo.objects.filter(visit=source):
                        copy_row(Photo, photo, 3000000 + photo.id - 2000000,
                                 {'visit_id': visit.id, 'creator_id': account.id})

            validation, _ = FieldValidation.objects.get_or_create(name='local-expert-preview', defaults={
                'min_value': 0, 'max_value': 1000, 'min_lenght': 0, 'max_lenght': 2000,
                'min_choice_count': 0, 'max_choice_count': 3, 'is_mandatory': False})
            for question in Question.objects.filter(report_category__visit_type=source.type, id__gte=2000000).distinct():
                for answer_type in question.answer_type.all():
                    QuestionAnswerTypeValidation.objects.get_or_create(visit_question=question,
                        answer_type=answer_type, is_for='V', defaults={'validation': validation})

            stock = WarehouseTransactionLine.objects.filter(pk=2000002).first()
            if stock:
                receipt_type, _ = TransactionLineType.objects.get_or_create(
                    name='LocalExpertReceipt', defaults={'verbose_name': 'موجودی آزمایشی کارشناس',
                                                         'side': 'TO', 'involved': 'USER'})
                receipt, _ = WarehouseTransaction.objects.get_or_create(pk=3000001, defaults={
                    'creator': account, 'description': 'موجودی آزمایشی اکسپرت لوکال',
                    'datetime_created': now, 'datetime_last_change': now})
                copy_row(WarehouseTransactionLine, stock, 3000001,
                         {'transaction_id': receipt.id, 'user_id': account.id, 'type_id': receipt_type.id})
        self.stdout.write(self.style.SUCCESS('Local field preview prepared: ' + account.username))
        self.stdout.write('Permissions: ' + str(RoleView.objects.filter(role=role).count()))
        self.stdout.write('Demo visits: 3000001 (open), 3000002 (completed). Backup: ' + backup.name)
