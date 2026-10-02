"""Personal, project-scoped in-app notifications."""

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import RoleAssignment
from notification.models import InAppNotification


def scoped_notifications(request):
    try:
        project_id = int(request.query_params.get('p'))
    except (TypeError, ValueError):
        raise ValidationError({'p': 'پروژه معتبر لازم است.'})
    if not request.user.is_active or not RoleAssignment.objects.filter(
        user=request.user, project_id=project_id, project__is_active=True,
        is_deleted=False, role__is_active=True,
    ).exists():
        raise PermissionDenied('دسترسی به اعلان‌های این پروژه مجاز نیست.')
    return InAppNotification.objects.filter(recipient=request.user, project_id=project_id)


def notification_output(item):
    return {
        'id': item.pk, 'kind': item.kind, 'title': item.title,
        'body': item.body, 'object_id': item.object_id,
        'created_at': item.created_at, 'read_at': item.read_at,
    }


class InAppNotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = scoped_notifications(request)
        try:
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
        except (TypeError, ValueError):
            raise ValidationError({'pagination': 'شماره صفحه یا تعداد ردیف نامعتبر است.'})
        if limit < 1 or limit > 50 or offset < 0:
            raise ValidationError({'pagination': 'تعداد ردیف باید بین ۱ تا ۵۰ باشد.'})
        count = rows.count()
        unread_count = rows.filter(read_at__isnull=True).count()
        page = rows.order_by('-created_at', '-pk')[offset:offset + limit]
        return Response({'count': count, 'unread_count': unread_count,
                         'results': [notification_output(item) for item in page],
                         'next_offset': offset + limit if offset + limit < count else None})


class InAppNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        rows = scoped_notifications(request)
        item = rows.filter(pk=id).first()
        if item is None:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        if item.read_at is None:
            now = timezone.now()
            rows.filter(pk=item.pk, read_at__isnull=True).update(read_at=now)
            item.refresh_from_db(fields=['read_at'])
        return Response(notification_output(item))


class InAppNotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        rows = scoped_notifications(request)
        updated = rows.filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({'updated': updated, 'unread_count': rows.filter(read_at__isnull=True).count()})


def create_personal_notification(*, recipient_id, project_id, source_key, kind, title,
                                 body='', object_id=None):
    if not recipient_id or not project_id:
        return
    if not RoleAssignment.objects.filter(
        user_id=recipient_id, project_id=project_id,
        project__is_active=True, user__is_active=True,
        role__is_active=True, is_deleted=False,
    ).exists():
        return
    InAppNotification.objects.get_or_create(
        recipient_id=recipient_id, project_id=project_id, source_key=source_key,
        defaults={'kind': kind, 'object_id': object_id, 'title': title, 'body': body},
    )


def notify_support_reply(ticket, message):
    """Notify the ticket creator once when another user replies."""
    if message.created_by_id != ticket.creator_id:
        create_personal_notification(
            recipient_id=ticket.creator_id, project_id=ticket.project_id,
            source_key=f'support-reply:{message.pk}', kind='support_reply',
            object_id=ticket.pk, title='پاسخ تازه از پشتیبانی',
            body=f'گفتگوی «{ticket.subject or ticket.title or "پشتیبانی"}» پاسخ تازه دارد.',
        )


def notify_support_staff(ticket, message, *, new_ticket=False):
    """Notify active members of the ticket's configured responder role."""
    staff = RoleAssignment.objects.filter(
        project_id=ticket.project_id, project__is_active=True,
        role_id=ticket.role_assignee_id, role__is_active=True,
        user__is_active=True, is_deleted=False,
    ).exclude(user_id=message.created_by_id).values_list('user_id', flat=True).distinct()
    for recipient_id in staff:
        create_personal_notification(
            recipient_id=recipient_id, project_id=ticket.project_id,
            source_key=f'support-incoming:{message.pk}', kind='support_incoming',
            object_id=ticket.pk,
            title='گفتگوی پشتیبانی تازه' if new_ticket else 'پیام تازه در پشتیبانی',
            body=f'گفتگوی «{ticket.subject or ticket.title or "پشتیبانی"}» پیام تازه دارد.',
        )


def notify_warranty_decision(claim):
    label = 'تحت پوشش' if claim.status == 'COVERED' else 'خارج از پوشش'
    for recipient_id in client_recipient_ids(claim.client_id, claim.project_id):
        create_personal_notification(
            recipient_id=recipient_id, project_id=claim.project_id,
            source_key=f'warranty-decision:{claim.pk}', kind='warranty_decision',
            object_id=claim.pk, title='نتیجه بررسی گارانتی',
            body=f'درخواست گارانتی شماره {claim.pk} {label} تشخیص داده شد.',
        )


def client_recipient_ids(client_id, project_id):
    from visit.models import UserClient

    clients = UserClient.objects.filter(client_id=client_id).values('user_id')
    return RoleAssignment.objects.filter(
        user_id__in=clients, project_id=project_id, project__is_active=True,
        user__is_active=True, role__is_active=True, role__asset_scope='client',
        is_deleted=False,
    ).values_list('user_id', flat=True).distinct()


def notify_repair_event(repair, event):
    labels = {
        'RECEIVED': 'دریافت شد', 'DIAGNOSING': 'در حال عیب‌یابی',
        'REPAIRING': 'در حال تعمیر', 'TESTING': 'در حال آزمون',
        'READY': 'آماده تحویل', 'DELIVERED': 'تحویل شد', 'CANCELED': 'متوقف شد',
    }
    for recipient_id in client_recipient_ids(repair.client_id, repair.project_id):
        create_personal_notification(
            recipient_id=recipient_id, project_id=repair.project_id,
            source_key=f'repair-event:{event.pk}', kind='repair_status',
            object_id=repair.pk, title='وضعیت تعمیر تغییر کرد',
            body=f'پرونده تعمیر شماره {repair.pk}: {labels.get(event.to_status, event.to_status)}.',
        )


def notify_visit_assignment(visit, source_key):
    """Announce an active visit to its assigned field workers once per activation."""
    project_id = visit.type.project_id
    building_label = str(visit.building.verbose_name or visit.building.name or visit.building.code or 'ساختمان')[:150]
    recipients = {visit.expert_id, visit.promoter_id} - {None}
    active_workers = RoleAssignment.objects.filter(
        user_id__in=recipients, project_id=project_id, project__is_active=True,
        user__is_active=True, role__is_active=True, is_deleted=False,
        role__asset_scope__in=('assigned', 'supervised'),
    ).values_list('user_id', flat=True).distinct()
    for recipient_id in active_workers:
        create_personal_notification(
            recipient_id=recipient_id, project_id=project_id,
            source_key=source_key, kind='visit_assignment', object_id=visit.pk,
            title='مأموریت تازه برای شما',
            body=f'مأموریت شماره {visit.pk} برای ساختمان «{building_label}» فعال شد.',
        )


def _field_workers(visit):
    project_id = visit.type.project_id
    recipients = {visit.expert_id, visit.promoter_id} - {None}
    return project_id, RoleAssignment.objects.filter(
        user_id__in=recipients, project_id=project_id, project__is_active=True,
        user__is_active=True, role__is_active=True, is_deleted=False,
        role__asset_scope__in=('assigned', 'supervised'),
    ).values_list('user_id', flat=True).distinct()


def _building_label(visit):
    building = visit.building
    return str(building.verbose_name or building.name or building.code or 'ساختمان')[:120] if building else 'ساختمان'


def notify_visit_completed(visit, version, actor_id=None):
    """Tell project reviewers that a finished report waits for review, and current managers that it is ready."""
    from auth_app.models import RoleView
    from visit.management import current_management_q
    from visit.models import BuildingClient

    project_id = visit.type.project_id
    reviewer_roles = RoleView.objects.filter(
        view_method_name__view_name='AdminUpdateVisitStatusView', view_method_name__method='PUT',
        can_update=True, role__asset_scope='project', role__is_active=True).values('role_id')
    reviewers = RoleAssignment.objects.filter(
        project_id=project_id, project__is_active=True, role_id__in=reviewer_roles,
        user__is_active=True, is_deleted=False,
    ).exclude(user_id=actor_id).values_list('user_id', flat=True).distinct()
    label = _building_label(visit)
    for recipient_id in reviewers:
        create_personal_notification(
            recipient_id=recipient_id, project_id=project_id,
            source_key=f'visit-completed:{visit.pk}:{version}', kind='visit_review', object_id=visit.pk,
            title='گزارش اصلاح‌شده برای بررسی' if version > 1 else 'گزارش تازه برای بررسی',
            body=f'گزارش مأموریت شماره {visit.pk} در «{label}» (نسخه {version}) ثبت شد و منتظر بررسی است.',
        )
    clients = BuildingClient.objects.filter(building_id=visit.building_id).filter(
        current_management_q()).values_list('client_id', flat=True)
    for client_id in set(clients):
        for recipient_id in client_recipient_ids(client_id, project_id):
            create_personal_notification(
                recipient_id=recipient_id, project_id=project_id,
                source_key=f'visit-report:{visit.pk}:{version}', kind='visit_report', object_id=visit.pk,
                title='گزارش اصلاح‌شده خدمت آماده است' if version > 1 else 'گزارش خدمت آماده است',
                body=(f'نسخه {version} گزارش خدمت «{label}» ثبت شد و جایگزین نسخه قبلی شد.' if version > 1
                      else f'گزارش خدمت «{label}» ثبت شد و قابل مشاهده است.'),
            )


def notify_visit_reviewed(visit, actor_id=None):
    """Tell the assigned field workers the review result: approved, rejected or returned."""
    project_id, workers = _field_workers(visit)
    label = _building_label(visit)
    text = {
        '3': ('visit_reviewed', 'گزارش شما تأیید شد', f'گزارش مأموریت {visit.pk} در «{label}» تأیید شد.'),
        '4': ('visit_reviewed', 'گزارش شما رد شد', f'گزارش مأموریت {visit.pk} در «{label}» رد شد.'),
        '5': ('visit_returned', 'مأموریت برای اصلاح برگشت', f'مأموریت {visit.pk} در «{label}» برای اصلاح برگشت داده شد.'),
    }.get(visit.status)
    if text is None:
        return
    kind, title, body = text
    stamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
    for recipient_id in workers:
        if recipient_id == actor_id:
            continue
        create_personal_notification(
            recipient_id=recipient_id, project_id=project_id,
            source_key=f'visit-review:{visit.pk}:{visit.status}:{stamp}', kind=kind,
            object_id=visit.pk, title=title, body=body[:240],
        )


def planner_ids(project_id, exclude=None):
    """Project-wide members who may edit and assign visits."""
    from auth_app.models import RoleView

    roles = RoleView.objects.filter(
        view_method_name__view_name='AdminUpdateVisitView', view_method_name__method__in=('PUT', 'PATCH'),
        can_update=True, role__asset_scope='project', role__is_active=True).values('role_id')
    return RoleAssignment.objects.filter(
        project_id=project_id, project__is_active=True, role_id__in=roles,
        user__is_active=True, is_deleted=False,
    ).exclude(user_id=exclude).values_list('user_id', flat=True).distinct()


def notify_assignment_declined(visit, actor_id, reason):
    project_id = visit.type.project_id
    label = _building_label(visit)
    stamp = timezone.now().strftime('%Y%m%d%H%M%S%f')
    for recipient_id in planner_ids(project_id, exclude=actor_id):
        create_personal_notification(
            recipient_id=recipient_id, project_id=project_id,
            source_key=f'visit-declined:{visit.pk}:{stamp}', kind='visit_declined', object_id=visit.pk,
            title='مأموریت به برنامه‌ریزی برگشت',
            body=f'کارشناس مأموریت {visit.pk} در «{label}» را بازگرداند: {reason}'[:240],
        )


def notify_maintenance_unassigned(visit):
    project_id = visit.type.project_id
    for recipient_id in planner_ids(project_id):
        create_personal_notification(
            recipient_id=recipient_id, project_id=project_id,
            source_key=f'maintenance-unassigned:{visit.pk}', kind='visit_declined', object_id=visit.pk,
            title='سرویس ادواری منتظر تخصیص است',
            body=f'مأموریت {visit.pk} برای «{_building_label(visit)}» از برنامه ادواری ساخته شد و کارشناس ندارد.',
        )


def notify_visit_due(visit, today):
    """Return the number of notifications created; each reminder is sent once per visit and due date."""
    project_id, workers = _field_workers(visit)
    label = _building_label(visit)
    due = visit.due_date
    created = 0

    def send(recipient_id, key, kind, title, body):
        nonlocal created
        before = InAppNotification.objects.filter(recipient_id=recipient_id, source_key=key).exists()
        create_personal_notification(recipient_id=recipient_id, project_id=project_id, source_key=key,
                                     kind=kind, object_id=visit.pk, title=title, body=body[:240])
        created += int(not before and InAppNotification.objects.filter(recipient_id=recipient_id, source_key=key).exists())

    if due >= today:
        when = 'امروز' if due == today else 'فردا'
        for recipient_id in workers:
            send(recipient_id, f'visit-due:{visit.pk}:{due.isoformat()}:{(due - today).days}', 'visit_due',
                 f'موعد مأموریت {when} است', f'مأموریت {visit.pk} در «{label}» تا {when} باید انجام شود.')
        return created
    for recipient_id in workers:
        send(recipient_id, f'visit-overdue:{visit.pk}:{due.isoformat()}', 'visit_overdue',
             'مأموریت از موعد گذشته است', f'موعد مأموریت {visit.pk} در «{label}» گذشته است؛ هرچه زودتر انجام شود.')
    for recipient_id in planner_ids(project_id):
        send(recipient_id, f'visit-overdue-planner:{visit.pk}:{due.isoformat()}', 'visit_overdue',
             'دیرکرد در انجام مأموریت', f'مأموریت {visit.pk} در «{label}» از موعد گذشته و هنوز بسته نشده است.')
    return created


def notify_visit_chat(visit, message, side):
    """Expert messages reach the building's current managers; client messages reach the field workers."""
    from visit.management import current_management_q
    from visit.models import BuildingClient

    project_id = visit.type.project_id
    label = _building_label(visit)
    if side == 'expert':
        clients = BuildingClient.objects.filter(building_id=visit.building_id).filter(
            current_management_q()).values_list('client_id', flat=True)
        recipients = {user_id for client_id in set(clients) for user_id in client_recipient_ids(client_id, project_id)}
        title = 'پیام تازه از کارشناس'
    else:
        recipients = set(_field_workers(visit)[1])
        title = 'پیام تازه از مدیر ساختمان'
    for recipient_id in recipients - {message.user_id}:
        create_personal_notification(
            recipient_id=recipient_id, project_id=project_id,
            source_key=f'visit-chat:{message.pk}', kind='visit_chat', object_id=visit.pk,
            title=title, body=f'مأموریت {visit.pk} در «{label}»: {message.body}'[:240],
        )


def warehouse_staff_ids(project_id):
    from auth_app.models import RoleView

    roles = RoleView.objects.filter(
        view_method_name__view_name='PartRequestDecisionView', view_method_name__method='POST',
        can_create=True, role__asset_scope='project', role__is_active=True).values('role_id')
    return RoleAssignment.objects.filter(
        project_id=project_id, project__is_active=True, role_id__in=roles, user__is_active=True, is_deleted=False,
    ).values_list('user_id', flat=True).distinct()


def notify_part_request(row):
    name = row.ware.name_fa or row.ware.name_en or 'قطعه'
    for recipient_id in warehouse_staff_ids(row.project_id):
        create_personal_notification(
            recipient_id=recipient_id, project_id=row.project_id,
            source_key=f'part-request:{row.pk}', kind='part_request', object_id=row.pk,
            title='درخواست قطعه تازه',
            body=f'{row.amount} عدد «{name}» برای مأموریت {row.visit_id} درخواست شد.'[:240],
        )


def notify_part_decision(row):
    name = row.ware.name_fa or row.ware.name_en or 'قطعه'
    fulfilled = row.status == 'FULFILLED'
    create_personal_notification(
        recipient_id=row.requester_id, project_id=row.project_id,
        source_key=f'part-decision:{row.pk}', kind='part_decision', object_id=row.visit_id,
        title='قطعه درخواستی تحویل شد' if fulfilled else 'درخواست قطعه رد شد',
        body=(f'{row.amount} عدد «{name}» به موجودی شما منتقل شد.' if fulfilled
              else f'درخواست «{name}» رد شد: {row.decision_note}')[:240],
    )
