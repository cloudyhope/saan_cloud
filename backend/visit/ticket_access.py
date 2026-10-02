"""Project and participant boundaries for support conversations."""
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError

from auth_app.models import RoleAssignment
from visit.asset_access import AssetAccess
from visit.models import Ticket, TicketMessage, TicketMessageAttachment


class TicketAccess:
    def __init__(self, request, view):
        self.request = request
        self.assets = AssetAccess(request, view)

    @property
    def tickets(self):
        rows = Ticket.objects.filter(project_id=self.assets.project_id, is_deleted=False)
        if self.assets.project_wide:
            return rows
        assigned_roles = RoleAssignment.objects.filter(
            user=self.request.user, project_id=self.assets.project_id,
            is_deleted=False, role__is_active=True,
        ).values('role_id')
        return rows.filter(Q(creator=self.request.user)
                           | Q(visit__in=self.assets.visits,
                               role_assignee_id__in=assigned_roles)).distinct()

    @property
    def messages(self):
        return TicketMessage.objects.filter(is_deleted=False, ticket__in=self.tickets)

    @property
    def attachments(self):
        return TicketMessageAttachment.objects.filter(
            is_deleted=False, ticket_message__in=self.messages,
        )

    @property
    def writable_tickets(self):
        return self.tickets if self.assets.project_wide else self.tickets.filter(creator=self.request.user)

    @property
    def writable_messages(self):
        return self.messages if self.assets.project_wide else self.messages.filter(created_by=self.request.user)

    @property
    def writable_attachments(self):
        return self.attachments if self.assets.project_wide else self.attachments.filter(
            ticket_message__created_by=self.request.user,
        )

    def validate_ticket(self, values):
        project_id = self.assets.project_id
        if values.get('project') is not None and values['project'].pk != project_id:
            raise ValidationError({'project': 'پروژه تیکت با پروژه انتخاب‌شده یکسان نیست.'})
        visit = values.get('visit')
        if visit is not None and not self.assets.visits.filter(pk=visit.pk).exists():
            raise ValidationError({'visit': 'بازدید انتخاب‌شده در محدوده دسترسی نیست.'})
        building = values.get('building')
        if building is not None and not self.assets.buildings.filter(pk=building.pk).exists():
            raise ValidationError({'building': 'ساختمان انتخاب‌شده در محدوده دسترسی نیست.'})
        role = values.get('role_assignee')
        if role is None or not RoleAssignment.objects.filter(
                project_id=project_id, role=role, is_deleted=False,
                role__is_active=True, project__is_active=True).exists():
            raise ValidationError({'role_assignee': 'نقش مقصد در این پروژه فعال نیست.'})

    def validate_message(self, values):
        ticket = values['ticket']
        if not self.tickets.filter(pk=ticket.pk).exists():
            raise PermissionDenied('این گفتگو در دسترس نیست.')
        if ticket.status == Ticket.CLOSED:
            raise ValidationError({'ticket': 'گفتگو بسته شده است.'})
        parent = values.get('parent')
        if parent is not None and parent.ticket_id != ticket.pk:
            raise ValidationError({'parent': 'پاسخ مرجع به این گفتگو تعلق ندارد.'})
