"""Field operations around an assigned visit: accept or hand back, asset context, visit chat,
earnings and the client's completion code."""
import secrets
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import DeleteCreateUpdateGetPermission
from visit.asset_access import AssetAccess
from visit.management import current_management_q
from visit.models import (BuildingClient, BuildingElevator, Elevator, ProductElevator, UserClient, Visit,
                          VisitAssignmentEvent)

OPEN_STATES = (Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND)
CHAT_KIND = 1  # utils.Conversation type Expert_Client


def person(user):
    """Display name only; usernames are phone numbers and never leave the server here."""
    if user is None:
        return ''
    return ' '.join(filter(None, (user.first_name, user.last_name))) or 'کاربر'


def ensure_completion_code(visit):
    if visit.type_id and visit.type.requires_client_code and not visit.completion_code:
        code = f'{secrets.randbelow(900000) + 100000}'
        Visit.objects.filter(pk=visit.pk, completion_code='').update(completion_code=code)
        visit.refresh_from_db(fields=['completion_code'])
    return visit.completion_code


CODE_ATTEMPTS = 5
CODE_LOCK = timedelta(minutes=15)
CODE_FIELDS = ('completion_code', 'completion_code_failures', 'completion_code_locked_until')


class CodeRejected(Exception):
    """Raised after the failure counter is persisted, so the caller can reply 400 outside its transaction."""


def check_completion_code(visit, given):
    """Constant-time compare on a locked row; five wrong codes rotate the code and lock it for 15 minutes."""
    import hmac
    now = timezone.now()
    if visit.completion_code_locked_until and visit.completion_code_locked_until > now:
        raise CodeRejected('تلاش‌های ناموفق زیاد بود؛ ۱۵ دقیقه دیگر با کد تازه مدیر ساختمان امتحان کنید.')
    if not given:
        raise CodeRejected('کد تأیید مدیر ساختمان لازم است.')
    if hmac.compare_digest(ensure_completion_code(visit), given):
        visit.completion_code_failures = 0
        visit.save(update_fields=['completion_code_failures'])
        return
    visit.completion_code_failures += 1
    if visit.completion_code_failures >= CODE_ATTEMPTS:
        visit.completion_code, visit.completion_code_failures = '', 0
        visit.completion_code_locked_until = now + CODE_LOCK
    visit.save(update_fields=list(CODE_FIELDS))
    ensure_completion_code(visit)
    raise CodeRejected('کد تأیید مدیر ساختمان درست نیست.')


def assignment_state(visit):
    """accepted / pending for the current field worker, plus the latest hand-back for planners."""
    workers = {visit.expert_id, visit.promoter_id} - {None}
    events = list(visit.assignment_events.select_related('user')[:20])
    mine = next((event for event in events if event.user_id in workers), None)
    decline = next((event for event in events if event.action == VisitAssignmentEvent.DECLINED), None)
    accepted = mine is not None and mine.action == VisitAssignmentEvent.ACCEPTED
    return {
        'state': 'unassigned' if not workers else 'accepted' if accepted or visit.status != Visit.NOTVISITED else 'pending',
        'accepted_at': mine.created_at if accepted else None,
        'last_decline': {'by': person(decline.user), 'reason': decline.reason, 'at': decline.created_at} if decline else None,
    }


def record_acceptance(visit, user):
    if not visit.assignment_events.filter(user=user, action=VisitAssignmentEvent.ACCEPTED).exists():
        VisitAssignmentEvent.objects.create(visit=visit, user=user, action=VisitAssignmentEvent.ACCEPTED)


class AssignmentInput(serializers.Serializer):
    action = serializers.ChoiceField(choices=('accept', 'decline'))
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500, default='')


class VisitAssignmentResponseView(APIView):
    """The assigned worker accepts the visit, or hands it back to planning with a reason."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def post(self, request, id):
        from visit.views import assigned_field_visit
        data = AssignmentInput(data=request.data)
        data.is_valid(raise_exception=True)
        action, reason = data.validated_data['action'], data.validated_data['reason'].strip()
        visit = assigned_field_visit(request, id, editable=True, view=self)
        if action == 'decline' and len(reason) < 5:
            raise ValidationError({'reason': 'دلیل بازگرداندن مأموریت را بنویسید (حداقل ۵ نویسه).'})
        with transaction.atomic():
            visit = Visit.objects.select_for_update().get(pk=visit.pk)
            if visit.status != Visit.NOTVISITED:
                raise ValidationError({'status': 'فقط مأموریت شروع‌نشده را می‌توان پذیرفت یا بازگرداند.'})
            if action == 'accept':
                record_acceptance(visit, request.user)
            else:
                VisitAssignmentEvent.objects.create(visit=visit, user=request.user,
                                                    action=VisitAssignmentEvent.DECLINED, reason=reason)
                fields = ['datetime_last_change']
                for field in ('expert', 'promoter'):
                    if getattr(visit, field + '_id') == request.user.id:
                        setattr(visit, field, None)
                        fields.append(field)
                visit.save(update_fields=fields)
                from notification.in_app import notify_assignment_declined
                actor_id = request.user.id
                transaction.on_commit(lambda: notify_assignment_declined(visit, actor_id, reason))
        return Response({'assignment': assignment_state(visit), 'still_assigned': action == 'accept'})


def visit_elevators(visit):
    rows = list(visit.elevator.all())
    if rows:
        return rows
    ids = BuildingElevator.objects.filter(building_id=visit.building_id).values('elevator_id')
    return list(Elevator.objects.filter(pk__in=ids).order_by('id'))


def visit_row(row):
    return {'id': row.pk, 'status': row.status, 'type': row.type.verbose_name or row.type.title if row.type else '',
            'date': row.start_datetime or row.datetime_last_change, 'expert': person(row.expert or row.promoter),
            'note': (row.rejection_reason or '')[:160] if row.status in (Visit.REJECTED, Visit.RETRY) else ''}


class VisitAssetContextView(APIView):
    """What the worker should know on site: installed parts and the recent service history."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request, id):
        from visit.views import assigned_field_visit
        visit = assigned_field_visit(request, id, view=self, allow_project_read=True)
        elevators = []
        for elevator in visit_elevators(visit):
            installed = (ProductElevator.objects.filter(elevator=elevator, is_active=True)
                         .select_related('product__model').order_by('-installed_at', '-id')[:12])
            history = (Visit.objects.filter(elevator=elevator, is_deleted=False,
                                            status__in=(Visit.COMPLETED, Visit.APPROVED, Visit.REJECTED, Visit.RETRY))
                       .exclude(pk=visit.pk).select_related('type', 'expert', 'promoter')
                       .order_by('-datetime_last_change')[:5])
            elevators.append({
                'id': elevator.pk, 'title': elevator.title or 'آسانسور',
                'priority_score': elevator.priority_score,
                'installed': [{'id': link.pk, 'model': (link.product.model.name_fa or link.product.model.name)
                               if link.product.model else 'قطعه', 'serial': link.product.serial_number or '',
                               'installed_at': link.installed_at} for link in installed],
                'history': [visit_row(row) for row in history],
            })
        building_history = (Visit.objects.filter(building_id=visit.building_id, is_deleted=False,
                                                 status__in=(Visit.COMPLETED, Visit.APPROVED, Visit.REJECTED, Visit.RETRY))
                            .exclude(pk=visit.pk).select_related('type', 'expert', 'promoter')
                            .order_by('-datetime_last_change')[:5])
        return Response({'elevators': elevators, 'building_history': [visit_row(row) for row in building_history]})


# ------------------------------------------------------------------ visit chat
def chat_open(visit):
    return visit.is_active and not visit.is_deleted and visit.status in OPEN_STATES and bool(
        visit.expert_id or visit.promoter_id)


def conversation_for(visit, create=False):
    from utils.models import Conversation
    row = Conversation.objects.filter(visit=visit, type=CHAT_KIND, is_deleted=False).order_by('id').first()
    if row is None and create:
        row = Conversation.objects.create(visit=visit, type=CHAT_KIND, title=f'گفتگوی مأموریت {visit.pk}',
                                          subject='visit_chat', status=2)
    return row


def chat_payload(visit, user, side):
    from utils.models import ConversationMessage
    conversation = conversation_for(visit)
    messages = []
    if conversation is not None:
        rows = list(ConversationMessage.objects.filter(conversation=conversation, is_deleted=False)
                    .select_related('user').order_by('datetime_created', 'id')[:300])
        workers = {visit.expert_id, visit.promoter_id}
        for row in rows:
            messages.append({'id': row.pk, 'body': row.body, 'at': row.datetime_created,
                             'mine': row.user_id == getattr(user, 'id', None),
                             'side': 'expert' if row.user_id in workers else 'client', 'name': person(row.user)})
        if side != 'admin':
            ConversationMessage.objects.filter(conversation=conversation, is_seen=False, is_deleted=False).exclude(
                user=user).update(is_seen=True)
    return {'open': chat_open(visit), 'messages': messages,
            'counterpart': 'کارشناس اعزامی' if side == 'client' else 'مدیر ساختمان'}


class ChatInput(serializers.Serializer):
    body = serializers.CharField(max_length=1000, trim_whitespace=True)


def post_chat(visit, user, side, body):
    from utils.models import ConversationMessage
    if not chat_open(visit):
        raise ValidationError({'body': 'گفتگو فقط تا پایان مأموریت باز است.'})
    with transaction.atomic():
        message = ConversationMessage.objects.create(conversation=conversation_for(visit, create=True),
                                                     user=user, body=body)
        from notification.in_app import notify_visit_chat
        transaction.on_commit(lambda: notify_visit_chat(visit, message, side))
    return message


class PromoterVisitChatView(APIView):
    """Chat between the assigned worker and the building's current managers, only while the visit is open."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def visit(self, request, id):
        from visit.views import assigned_field_visit
        visit = assigned_field_visit(request, id, view=self)
        if request.user.id not in (visit.expert_id, visit.promoter_id):
            raise NotFound()
        return visit

    def get(self, request, id):
        return Response(chat_payload(self.visit(request, id), request.user, 'expert'))

    def post(self, request, id):
        visit = self.visit(request, id)
        data = ChatInput(data=request.data)
        data.is_valid(raise_exception=True)
        post_chat(visit, request.user, 'expert', data.validated_data['body'])
        return Response(chat_payload(visit, request.user, 'expert'), status=201)


def has_grant(request, view_name, method, scope=None):
    """A grant check independent of the current request method (unlike authorized_role_views)."""
    from auth_app.models import RoleAssignment, RoleView
    from auth_app.permissions import METHOD_CAPABILITIES
    try:
        project_id = int(request.query_params.get('p'))
    except (TypeError, ValueError):
        return False
    roles = RoleAssignment.objects.filter(user=request.user, project_id=project_id, is_deleted=False,
                                          role__is_active=True, project__is_active=True).values('role_id')
    rows = RoleView.objects.filter(role_id__in=roles, view_method_name__view_name=view_name,
                                   view_method_name__method=method, **{METHOD_CAPABILITIES[method]: True})
    if scope:
        rows = rows.filter(role__asset_scope=scope)
    return request.user.is_active and rows.exists()


def current_client_visit(request, id):
    """The visit as its building's current manager sees it (same scope as the client visit detail)."""
    from visit.management import client_visible_visits
    from visit.models import Client
    if not has_grant(request, 'ClientVisitsAPIView', 'GET', scope='client'):
        raise PermissionDenied('دسترسی به این خدمت مجاز نیست.')
    project_id = int(request.query_params['p'])
    clients = Client.objects.filter(project_id=project_id, userclient__user=request.user)
    visits = Visit.objects.filter(type__project_id=project_id, building__project_id=project_id, is_deleted=False)
    visit = get_object_or_404(client_visible_visits(visits, clients).select_related('type'), pk=id)
    managing = BuildingClient.objects.filter(building_id=visit.building_id).filter(current_management_q())
    if not UserClient.objects.filter(user=request.user, client_id__in=managing.values('client_id')).exists():
        raise PermissionDenied('فقط مدیر فعلی ساختمان می‌تواند گفتگو کند.')
    return visit


class ClientVisitChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        visit = current_client_visit(request, id)
        return Response(chat_payload(visit, request.user, 'client'))

    def post(self, request, id):
        visit = current_client_visit(request, id)
        # Read-only client representatives have no write grant on their own visit endpoints.
        if not has_grant(request, 'ClientVisitFeedbackAPIView', 'POST', scope='client'):
            raise PermissionDenied('برای ارسال پیام دسترسی ندارید.')
        data = ChatInput(data=request.data)
        data.is_valid(raise_exception=True)
        post_chat(visit, request.user, 'client', data.validated_data['body'])
        return Response(chat_payload(visit, request.user, 'client'), status=201)


# ------------------------------------------------------------------ earnings
def parse_day(value, fallback):
    if not value:
        return fallback
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({'date': 'تاریخ باید به شکل YYYY-MM-DD باشد.'})


class PromoterEarningsView(APIView):
    """Wage summary of the worker's finished visits; only approved work counts as earned."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request):
        today = timezone.localdate()
        start = parse_day(request.query_params.get('from'), today.replace(day=1))
        end = parse_day(request.query_params.get('to'), today)
        if end < start or (end - start).days > 366:
            raise ValidationError({'date': 'بازه باید حداکثر یک سال و از ابتدا به انتها باشد.'})
        rows = Visit.objects.filter(Q(expert=request.user) | Q(promoter=request.user), is_deleted=False,
                                    type__project_id=request.query_params.get('p'),
                                    status__in=(Visit.COMPLETED, Visit.APPROVED, Visit.REJECTED, Visit.RETRY),
                                    datetime_last_change__date__gte=start,
                                    datetime_last_change__date__lte=end)
        totals = {row['status']: row for row in rows.values('status').annotate(count=Count('id'), wage=Sum('total_wage'))}

        def part(*states):
            return {'count': sum(totals.get(s, {}).get('count', 0) for s in states),
                    'wage': sum(totals.get(s, {}).get('wage') or 0 for s in states)}
        return Response({'from': start, 'to': end, 'earned': part(Visit.APPROVED),
                         'pending': part(Visit.COMPLETED, Visit.RETRY), 'rejected': part(Visit.REJECTED)})


# ------------------------------------------------------------------ admin readout
class AdminVisitFieldOpsView(APIView):
    """Planner view of a visit's field operations: hand-backs, part requests, chat and completion code."""
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request, id):
        access = AssetAccess(request, self)
        if not access.project_wide:
            raise PermissionDenied('این بخش نیازمند نقش مدیریتی پروژه است.')
        visit = get_object_or_404(access.visits.select_related('type'), pk=id)
        from warehouse.part_requests import part_request_row
        events = [{'action': row.action, 'by': person(row.user), 'reason': row.reason, 'at': row.created_at}
                  for row in visit.assignment_events.select_related('user')[:20]]
        parts = [part_request_row(row) for row in visit.part_requests.select_related(
            'ware__unit', 'requester', 'location', 'decided_by')]
        code = ensure_completion_code(visit) if visit.status in OPEN_STATES else visit.completion_code
        return Response({'assignment': assignment_state(visit), 'events': events, 'parts': parts,
                         'chat': chat_payload(visit, request.user, 'admin'),
                         'requires_client_code': bool(visit.type and visit.type.requires_client_code),
                         'completion_code': code if visit.type and visit.type.requires_client_code else '',
                         'maintenance_plan': visit.maintenance_plan_id})
