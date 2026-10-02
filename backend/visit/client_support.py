"""Small, scoped support API for client-owned tickets and conversations."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import RoleAssignment, RoleView
from auth_app.permissions import DeleteCreateUpdateGetPermission, authorized_role_views
from notification.in_app import notify_support_staff
from visit.asset_access import AssetAccess
from visit.models import Ticket, TicketMessage


class SupportTicketInput(serializers.Serializer):
    title = serializers.CharField(max_length=60, allow_blank=False, trim_whitespace=True)
    body = serializers.CharField(max_length=5000, allow_blank=False, trim_whitespace=True)
    building = serializers.IntegerField(required=False)
    visit = serializers.IntegerField(required=False)


class SupportMessageInput(serializers.Serializer):
    body = serializers.CharField(max_length=5000, allow_blank=False, trim_whitespace=True)


def support_role(project_id):
    """Route to a project staff role that can read tickets and reply to them."""
    ticket_roles = RoleView.objects.filter(
        view_method_name__view_name='TicketListCreateView',
        view_method_name__method='GET', can_view=True).values('role_id')
    message_roles = RoleView.objects.filter(
        view_method_name__view_name='TicketMessageListCreateView',
        view_method_name__method='POST', can_create=True).values('role_id')
    assignment = RoleAssignment.objects.filter(
        project_id=project_id, project__is_active=True, is_deleted=False,
        role__is_active=True, role__asset_scope='project',
        role_id__in=ticket_roles).filter(role_id__in=message_roles).select_related('role').order_by('role__priority', 'role_id').first()
    return assignment.role if assignment else None


def ticket_output(ticket):
    return {
        'id': ticket.pk, 'title': ticket.subject or ticket.title or 'گفتگو با پشتیبانی',
        'status': ticket.status, 'building_id': ticket.building_id,
        'visit_id': ticket.visit_id, 'created_at': ticket.datetime_created,
        'updated_at': ticket.datetime_last_change,
    }


def message_output(message, user):
    return {'id': message.pk, 'body': message.body,
            'is_mine': message.created_by_id == user.pk,
            'created_at': message.datetime_created}


class ClientSupportBase(APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def access(self, request):
        grants = authorized_role_views(request, self)
        if not grants.filter(role__asset_scope='client').exists():
            return None
        return AssetAccess(request, self)

    @staticmethod
    def own_tickets(request, access):
        return Ticket.objects.filter(project_id=access.project_id,
                                     creator=request.user, is_deleted=False)

    @staticmethod
    def allowed_visits(access):
        return access.visits

    @staticmethod
    def allowed_buildings(access):
        return access.buildings


class ClientSupportTicketsAPIView(ClientSupportBase):
    def get(self, request):
        access = self.access(request)
        if access is None:
            return Response({'detail': 'دسترسی به پشتیبانی مجاز نیست.'}, status=403)
        rows = self.own_tickets(request, access).order_by('-datetime_last_change', '-pk')[:100]
        return Response([ticket_output(row) for row in rows])

    def post(self, request):
        access = self.access(request)
        if access is None:
            return Response({'detail': 'دسترسی به پشتیبانی مجاز نیست.'}, status=403)
        payload = SupportTicketInput(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data
        building = None
        visit = None
        if 'visit' in values:
            visit = self.allowed_visits(access).filter(pk=values['visit']).first()
            if visit is None:
                raise serializers.ValidationError({'visit': 'خدمت انتخاب‌شده در دسترس نیست.'})
            building = visit.building
        if 'building' in values:
            selected = self.allowed_buildings(access).filter(pk=values['building']).first()
            if selected is None or (building and building.pk != selected.pk):
                raise serializers.ValidationError({'building': 'ساختمان انتخاب‌شده در دسترس نیست.'})
            building = selected
        recipient = support_role(access.project_id)
        if recipient is None:
            return Response({'detail': 'پشتیبانی این پروژه هنوز تنظیم نشده است.'}, status=503)
        with transaction.atomic():
            ticket = Ticket.objects.create(
                project_id=access.project_id, creator=request.user, role_assignee=recipient,
                visit=visit, building=building, title=values['title'][:35],
                subject=values['title'], status=Ticket.WAITING)
            message = TicketMessage.objects.create(ticket=ticket, created_by=request.user, body=values['body'])
            notify_support_staff(ticket, message, new_ticket=True)
        return Response(ticket_output(ticket), status=201)


class ClientSupportTicketDetailAPIView(ClientSupportBase):
    def scoped_ticket(self, request, id):
        access = self.access(request)
        if access is None:
            return None
        return get_object_or_404(self.own_tickets(request, access), pk=id)

    def get(self, request, id):
        ticket = self.scoped_ticket(request, id)
        if ticket is None:
            return Response({'detail': 'دسترسی به پشتیبانی مجاز نیست.'}, status=403)
        result = ticket_output(ticket)
        messages = TicketMessage.objects.filter(ticket=ticket, is_deleted=False).order_by('datetime_created', 'pk')[:500]
        result['messages'] = [message_output(message, request.user) for message in messages]
        return Response(result)

    def post(self, request, id):
        ticket = self.scoped_ticket(request, id)
        if ticket is None:
            return Response({'detail': 'دسترسی به پشتیبانی مجاز نیست.'}, status=403)
        payload = SupportMessageInput(data=request.data)
        payload.is_valid(raise_exception=True)
        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
            if ticket.status == Ticket.CLOSED or ticket.is_deleted:
                raise serializers.ValidationError('این گفتگو بسته شده است.')
            message = TicketMessage.objects.create(
                ticket=ticket, created_by=request.user,
                body=payload.validated_data['body'])
            ticket.status = Ticket.WAITING
            ticket.save(update_fields=['status', 'datetime_last_change'])
            notify_support_staff(ticket, message)
        return Response(message_output(message, request.user), status=201)


class ExpertSupportBase(ClientSupportBase):
    def access(self, request):
        grants = authorized_role_views(request, self)
        if not grants.filter(role__asset_scope__in=('assigned', 'supervised')).exists():
            return None
        return AssetAccess(request, self)

    @staticmethod
    def allowed_visits(access):
        return access.assigned_visits

    @staticmethod
    def allowed_buildings(access):
        return access.buildings.filter(pk__in=access.assigned_visits.values('building_id'))


class ExpertSupportTicketsAPIView(ExpertSupportBase, ClientSupportTicketsAPIView):
    pass


class ExpertSupportTicketDetailAPIView(ExpertSupportBase, ClientSupportTicketDetailAPIView):
    pass
