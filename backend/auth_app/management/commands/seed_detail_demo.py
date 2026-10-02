"""Idempotent, local-only rich data for the admin detail screens."""
import json
import sqlite3
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from auth_app.models import Project, City, RoleAssignment, RoleView, ViewMethod
from visit.models import (VisitType, Visit, Building, Elevator, BuildingElevator,
                          Client, UserClient, BuildingClient, AnswerType,
                          AnswerChoice, ReportCategory, QuestionType, Question,
                          Answer, PhotoType, Photo, Store, StoreCategory, Ticket, TicketMessage)
from warehouse.models import Ware, WareType, Unit, WarehouseLocation, WarehouseTransaction, WarehouseTransactionLine
from survey.models import (Survey, SurveyFillOut, SurveyReportCategory,
                           SurveyQuestionType, SurveyQuestion, SurveyAnswer,
                           SurveyPhotoType, SurveyPhoto)


class Command(BaseCommand):
    help = 'Seed clearly labelled demo records in core.local_settings SQLite only.'

    def handle(self, *args, **options):
        db = settings.DATABASES['default']
        if settings.SETTINGS_MODULE != 'core.local_settings' or not settings.DEBUG or db['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('Local DEBUG SQLite only.')
        directory = Path(settings.BASE_DIR) / 'data'
        directory.mkdir(exist_ok=True)
        backup = directory / ('db-before-detail-demo-' + timezone.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3')
        with sqlite3.connect(str(db['NAME'])) as current, sqlite3.connect(str(backup)) as saved:
            current.backup(saved)
        user = User.objects.get(username='09000000001')
        project = Project.objects.get(pk=1)
        city = City.objects.filter(name__contains='تهران').first() or City.objects.first()
        now = timezone.now()

        def put(model, pk, **data):
            # Avoid custom save hooks and outbound business side effects.
            if model.objects.filter(pk=pk).exists():
                model.objects.filter(pk=pk).update(**data)
            else:
                model.objects.bulk_create([model(pk=pk, **data)])
            return model.objects.get(pk=pk)

        with transaction.atomic():
            parent = put(Building, 2000001, name='local-demo-complex', verbose_name='نمونه طراحی · مجتمع آفتاب', code='LOCAL-DEMO-01', city=city, address='تهران، خیابان نمونه، مجتمع آفتاب — داده آزمایشی لوکال', latitude=35.7, longitude=51.4, type='Complex')
            building = put(Building, 2000002, name='local-demo-building', verbose_name='نمونه طراحی · ساختمان سرو', code='LOCAL-DEMO-02', city=city, parent=parent, address='تهران، خیابان نمونه، ساختمان سرو، ورودی شرقی — داده آزمایشی لوکال', latitude=35.7001, longitude=51.4001, type='Apartment')
            elevator = put(Elevator, 2000001, title='نمونه طراحی · آسانسور شرقی', type='Passenger', capacity='8', number_of_floors=12, elevator_type='TRACTION', usage_type='RESIDENTIAL', cabin_capacity_kg=630, stops_count=12, operation_type='SIMPLEX', motor_type='GEARLESS', motor_brand='Demo Motor', motor_power_kw=7, motor_encoder_type='ERN_1387', elevator_speed_mps=1, control_panel_brand='Demo Control', control_panel_serial='LOCAL-CTRL-2026', control_panel_type='MRL', control_system_type='CLOSED_LOOP', door_brand='Demo Door', door_count=2, door1_type='AUTO', door1_voltage='24V', door2_type='AUTO', door2_voltage='24V', emergency_system_type='UPS', weight_sensor='EXISTS', firefighter_mode='INACTIVE', input_voltage='THREE_PHASE', standard_type='EN81-20', landing_call_comm_type='SERIAL')
            put(BuildingElevator, 2000001, building=building, elevator=elevator)
            client = put(Client, 2000001, name='Local Demo Customer', name_fa='نمونه طراحی · شرکت آفتاب', type='Business', description='مشتری آزمایشی برای بررسی نمایش اطلاعات، متن طولانی و ساختمان‌های مرتبط. این رکورد فقط در دیتابیس لوکال ساخته شده است.')
            put(UserClient, 2000001, user=user, client=client)
            put(BuildingClient, 2000001, building=building, client=client)
            store_category = put(StoreCategory, 2000001, project=project, name='local-demo', verbose_name='فروشگاه نمونه')
            store = put(Store, 2000001, project=project, category=store_category, city=city, name='نمونه طراحی · فروشگاه سرو', code='LOCAL-STORE-01', customer_code='LOCAL-CUSTOMER-01', phone='02100000000', mobile_phone='09000000002', owner_name='مالک نمونه لوکال', owner_national_code='0000000000', address='تهران، خیابان نمونه، فروشگاه سرو — اطلاعات آزمایشی', postal_code='0000000000', latitude=35.7, longitude=51.4, datetime_created=now)
            visit_type = put(VisitType, 2000001, title='local-detail-demo', verbose_name='بازدید نمونه طراحی', project=project, is_active=True)
            visit = put(Visit, 2000001, type=visit_type, building=building, creator=user, promoter=user, expert=user, status='2', visit_turn=1, start_datetime=now, datetime_created=now, datetime_last_change=now, is_active=True, visit_comment='بازدید نمونه تکمیل شد. روشنایی کابین مناسب است و سیستم اضطراری در بررسی اولیه عملکرد صحیح داشت. سرویس دوره‌ای در برنامه بعدی پیگیری شود.', comment_publisher=user)
            visit.elevator.set([elevator])
            survey = put(Survey, 2000001, name='local-detail-demo', verbose_name='نمونه طراحی · ارزیابی کیفیت خدمات', project=project, datetime_created=now, datetime_last_change=now)
            fillout = put(SurveyFillOut, 2000001, survey=survey, user=user, visit=visit, city=city, province=city.province if city else None, phone_number='09000000002', phone_verified=False, status='1', datetime_created=now, datetime_last_change=now)
            visit_type.surveys.set([survey])
            # Empty cases exercise records without users, city, answers or images.
            put(Visit, 2000002, type=visit_type, building=parent, creator=user, status='0', datetime_created=now, datetime_last_change=now)
            put(SurveyFillOut, 2000002, survey=survey, phone_number='09000000003', user=None, city=None, province=None, status='0', datetime_created=now, datetime_last_change=now)
            visit_categories, survey_categories, visit_qtypes, survey_qtypes = [], [], [], []
            for index, title in enumerate(['وضعیت و ایمنی', 'کیفیت خدمات و بازخورد']):
                pk = 2000001 + index
                vc = put(ReportCategory, pk, name='local-demo-' + str(index), verbose_name=title, project=project, visit_type=visit_type)
                sc = put(SurveyReportCategory, pk, name='local-demo-' + str(index), verbose_name=title)
                visit_categories.append(vc); survey_categories.append(sc)
                visit_qtypes.append(put(QuestionType, pk, name='local-demo-' + str(index), verbose_name=title, project=project, visit_type=visit_type, report_category=vc))
                survey_qtypes.append(put(SurveyQuestionType, pk, name='local-demo-' + str(index), verbose_name=title, survey_report_category=sc))
            specifications = [
                ('YesNo', 'آیا نیاز به تعمیر فوری وجود دارد؟', {'bool': False}),
                ('Triple', 'آیا سیستم اضطراری فعال است؟', {'bool': True}),
                ('Score', 'کیفیت اجرای سرویس را چگونه ارزیابی می‌کنید؟', {'score': 4}),
                ('Number', 'تعداد خطاهای ثبت‌شده در این بازدید چند مورد است؟', {'number': 0}),
                ('RadioChoice', 'وضعیت نظافت کابین چگونه است؟', {}),
                ('DropDownList', 'زمان پیشنهادی برای سرویس بعدی', {}),
                ('Multichoice', 'کدام موارد در بازدید بررسی شده است؟', {}),
                ('Input', 'نام مسئول هماهنگی ساختمان', {'text': 'مسئول نمونه ساختمان'}),
                ('Description', 'توضیحات و پیشنهادهای تکمیلی', {'description': 'روشنایی و تهویه کابین در وضعیت مناسب قرار دارد.\nدر مراجعه بعدی تنظیم آرام‌بند درب طبقه همکف بررسی شود.\nاین متن بلند برای بررسی خوانایی، فاصله خطوط و نمایش پاسخ‌های چندخطی روی موبایل ثبت شده است.'}),
                ('Price', 'برآورد هزینه سرویس (ریال)', {'price': 12500000}),
            ]
            for index, (kind, text, values) in enumerate(specifications):
                pk = 2000001 + index
                group = 0 if index < 5 else 1
                answer_type = AnswerType.objects.filter(name=kind).first() or put(AnswerType, pk, name=kind, field={'YesNo':'bool','Triple':'bool','Score':'score','Number':'number','RadioChoice':'radio','DropDownList':'dropdown','Multichoice':'multichoice','Input':'text','Description':'description','Price':'price'}[kind])
                vq = put(Question, pk, type='GE', text=text, priority=index + 1, report_category=visit_categories[group], question_type=visit_qtypes[group], description='سؤال آزمایشی برای طراحی و بررسی صفحه جزئیات', is_active=True)
                sq = put(SurveyQuestion, pk, text=text, priority=index + 1, survey=survey, survey_report_category=survey_categories[group], survey_question_type=survey_qtypes[group], description='داده نمونه لوکال', is_active=True)
                vq.answer_type.set([answer_type]); sq.answer_type.set([answer_type])
                choices = []
                if kind in ['RadioChoice', 'DropDownList', 'Multichoice']:
                    titles = ['مناسب', 'نیازمند پیگیری', 'بررسی مجدد'] if kind == 'RadioChoice' else ['هفته آینده', 'ماه آینده', 'پس از هماهنگی'] if kind == 'DropDownList' else ['درب‌های طبقات', 'تابلو فرمان', 'سیستم اضطراری']
                    for n, choice_title in enumerate(titles):
                        choices.append(put(AnswerChoice, 2000100 + index * 3 + n, answer=choice_title, question=vq))
                    relation = {'RadioChoice':'radio_choices', 'DropDownList':'dropdown_choices', 'Multichoice':'answer_choices'}[kind]
                    getattr(vq, relation).set(choices); getattr(sq, relation).set(choices)
                    if kind == 'RadioChoice': values = {'radio': choices[0]}
                    elif kind == 'DropDownList': values = {'dropdown': choices[1]}
                va = put(Answer, pk, visit=visit, question=vq, datetime_created=now, datetime_last_change=now, **values)
                sa = put(SurveyAnswer, pk, survey_fill_out=fillout, survey_question=sq, datetime_created=now, datetime_last_change=now, **values)
                if kind == 'Multichoice': va.multichoice.set(choices); sa.multichoice.set(choices)
            q = put(Question, 2000050, type='GE', text='سؤال نمونه بدون پاسخ برای افزودن پاسخ جدید', priority=50, report_category=visit_categories[1], question_type=visit_qtypes[1])
            sq = put(SurveyQuestion, 2000050, text='سؤال نمونه بدون پاسخ برای افزودن پاسخ جدید', priority=50, survey=survey, survey_report_category=survey_categories[1], survey_question_type=survey_qtypes[1])
            input_type = AnswerType.objects.filter(name='Input').first()
            q.answer_type.set([input_type]); sq.answer_type.set([input_type])
            media = Path(settings.MEDIA_ROOT) / 'ui-fixtures'
            media.mkdir(parents=True, exist_ok=True)
            for n, title in enumerate(['نمای کابین', 'تابلو فرمان', 'درب طبقات']):
                filename = 'detail-demo-' + str(n) + '.svg'
                # Generated schematic fixture, visibly labelled; no external images.
                (media / filename).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="520" viewBox="0 0 800 520"><rect width="800" height="520" fill="{["#edf1f7","#e8eef5","#f0ede7"][n]}"/><rect x="180" y="60" width="440" height="400" rx="12" fill="#a9b8cd"/><rect x="200" y="80" width="400" height="360" fill="#dae2ed"/><path d="M400 80v360M200 410h400" stroke="#8fa2bc" stroke-width="6"/><rect x="555" y="170" width="20" height="120" rx="6" fill="#657c9d"/><circle cx="565" cy="195" r="5" fill="#edf3ff"/><text x="28" y="490" font-family="sans-serif" font-size="22" fill="#65758d">LOCAL DEMO / {n + 1}</text></svg>', encoding='utf-8')
                pt = put(PhotoType, 2000001+n, name='local-demo-' + str(n), verbose_name=title, project=project, visit_type=visit_type, report_category=visit_categories[0], min=0, max=20)
                spt = put(SurveyPhotoType, 2000001+n, name='local-demo-' + str(n), verbose_name=title, survey=survey, survey_report_category=survey_categories[0], min=0, max=20)
                fields = dict(link='http://localhost:18110/media/ui-fixtures/' + filename, creator=user, datetime_created=now, datetime_last_change=now, latitude=35.7001 if n != 2 else None, longitude=51.4001 if n != 2 else None, supervision_confirm=['CONFIRMED','NOT_CHECKED','REJECTED'][n], supervision_location_confirm='NOT_CHECKED', recognition_status=None)
                put(Photo, 2000001+n, visit=visit, type=pt, **fields)
                put(SurveyPhoto, 2000001+n, survey_fill_out=fillout, survey_photo_type=spt, is_favourite=n==0, **fields)
            # Preserve the existing preview role's read-only access.
            assignment = RoleAssignment.objects.get(user=user, project=project, is_deleted=False)
            ticket = put(Ticket, 2000001, project=project, building=building, visit=visit, creator=user, role_assignee=assignment.role, title='نمونه طراحی · پیگیری سرویس', subject='هماهنگی سرویس دوره‌ای ساختمان', status='W', datetime_created=now, datetime_last_change=now)
            put(TicketMessage, 2000001, ticket=ticket, created_by=user, created_by_role_assignment=assignment, body='برای هماهنگی سرویس دوره‌ای و بررسی درب طبقه همکف درخواست پیگیری داریم.\nزمان مراجعه لطفاً با مسئول ساختمان هماهنگ شود.', datetime_created=now, datetime_last_change=now)
            put(TicketMessage, 2000002, ticket=ticket, created_by=user, created_by_role_assignment=assignment, body='اطلاعات تکمیلی نمونه: دسترسی به موتورخانه از ورودی شرقی امکان‌پذیر است.', datetime_created=now, datetime_last_change=now)
            put(Ticket, 2000002, project=project, creator=user, role_assignee=assignment.role, title='نمونه طراحی · تیکت بدون پیام', status='W', datetime_created=now, datetime_last_change=now)
            ware_type = put(WareType, 2000001, name='local-demo', verbose_name='قطعات نمونه')
            unit = put(Unit, 2000001, unit_en='piece', unit_fa='عدد', unit_abbreviation='عدد')
            ware = put(Ware, 2000001, project=project, type=ware_type, unit=unit, name_fa='نمونه طراحی · قطعه درب آسانسور', name_en='Local Demo Part', identifier='LOCAL-PART-01', datetime_created=now, datetime_last_change=now)
            location = put(WarehouseLocation, 2000001, name_fa='نمونه طراحی · انبار مرکزی', name_en='Local Demo Warehouse')
            location.projects.set([project])
            receipt = put(WarehouseTransaction, 2000001, creator=user, description='نمونه طراحی؛ موجودی آزمایشی لوکال', datetime_created=now, datetime_last_change=now)
            put(WarehouseTransactionLine, 2000001, transaction=receipt, ware=ware, location=location, user=None, amount=20)
            put(WarehouseTransactionLine, 2000002, transaction=receipt, ware=ware, location=None, user=user, amount=5)
            for name in ['AdminStoreListCreateView','AdminStoreDetailView','AdminStoreCategoryListView']:
                method, _ = ViewMethod.objects.get_or_create(view_name=name, method='GET')
                RoleView.objects.get_or_create(role=assignment.role, view_method_name=method, defaults={'can_view': True})
        links = {'ticket': '/ticket/ticketdetail/2000001', 'empty_ticket': '/ticket/ticketdetail/2000002', 'warehouse': '/warehouse/waredetail/2000001', 'visit': '/visitmanagment/answerlist/2000001', 'survey': '/surveymanagment/answerlist/2000001', 'building': '/elevatormanagement/buildingdetail/2000002', 'elevator': '/elevatormanagement/elevatordetail/2000001', 'customer': '/customermanagement/detail/2000001', 'store': '/storemng/detail/2000001', 'empty_visit': '/visitmanagment/answerlist/2000002', 'empty_survey': '/surveymanagment/answerlist/2000002'}
        (directory / 'detail-demo-links.json').write_text(json.dumps(links, indent=2), encoding='utf-8')
        self.stdout.write('Local demo: 10 answer types, 2 groups, 6 photos, 6 entity detail pages + empty records. Backup: ' + str(backup))
