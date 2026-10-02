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
