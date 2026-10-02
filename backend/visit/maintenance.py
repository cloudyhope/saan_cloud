"""Periodic maintenance plans and due-date alerts, run daily by `manage.py run_field_schedules`."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import RoleAssignment
from auth_app.permissions import DeleteCreateUpdateGetPermission
from visit.asset_access import AssetAccess
from visit.models import BuildingElevator, Elevator, MaintenancePlan, Visit, VisitType

OPEN_STATES = (Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND)
OVERDUE_WINDOW = 3  # days a new delay is still announced, covering missed daily runs


def plan_building_id(plan):
    return BuildingElevator.objects.filter(elevator_id=plan.elevator_id).order_by('id').values_list(
        'building_id', flat=True).first()


def open_plan_visit(plan):
    return plan.visits.filter(is_deleted=False, status__in=OPEN_STATES).order_by('-id').first()


def generate_due_visits(today=None, project_id=None, dry_run=False):
    """Open one visit per plan whose window (due − lead days) has started and has no open visit yet."""
    from notification.in_app import notify_maintenance_unassigned, notify_visit_assignment
    today = today or timezone.localdate()
    plans = MaintenancePlan.objects.filter(is_active=True, project__is_active=True).select_related(
        'visit_type', 'elevator', 'expert', 'created_by')
    if project_id:
        plans = plans.filter(project_id=project_id)
    created, skipped = [], []
    for plan in plans:
        if plan.next_due - timedelta(days=plan.lead_days) > today:
            continue
        if open_plan_visit(plan) is not None:
            skipped.append((plan.pk, 'open visit exists'))
            continue
        building_id = plan_building_id(plan)
        if building_id is None or plan.created_by_id is None or not plan.visit_type.is_active:
            skipped.append((plan.pk, 'no building, creator or active service type'))
            continue
        if dry_run:
            created.append((plan.pk, None))
            continue
        with transaction.atomic():
            locked = MaintenancePlan.objects.select_for_update().get(pk=plan.pk)
            if open_plan_visit(locked) is not None:
                continue
            due = locked.next_due
            visit = Visit.objects.create(
                type=locked.visit_type, building_id=building_id, creator_id=locked.created_by_id,
                expert=locked.expert, has_due_date=True, due_date=due, is_active=locked.expert_id is not None,
                maintenance_plan=locked, visit_comment=locked.note or None,
                comment_publisher_id=locked.created_by_id if locked.note else None)
            visit.elevator.set([locked.elevator_id])
            locked.next_due = due + timedelta(days=locked.interval_days)
            locked.save(update_fields=['next_due', 'updated_at'])
            if visit.is_active:
                transaction.on_commit(lambda v=visit, d=due, p=locked.pk: notify_visit_assignment(
                    v, f'maintenance:{p}:{d.isoformat()}'))
            else:
                transaction.on_commit(lambda v=visit: notify_maintenance_unassigned(v))
        created.append((plan.pk, visit.pk))
    return created, skipped


def send_due_alerts(today=None, project_id=None):
    """Remind workers a day ahead and on the due day, and flag a new delay once to workers and planners.

    Long-running delays are not repeated; they stay visible on the dashboard and the overdue filter.
    The window reaches back a few days so a missed daily run still sends each reminder once.
    """
    from notification.in_app import notify_visit_due
    today = today or timezone.localdate()
    rows = Visit.objects.filter(is_active=True, is_deleted=False, has_due_date=True, due_date__isnull=False,
                                status__in=OPEN_STATES, due_date__gte=today - timedelta(days=OVERDUE_WINDOW),
                                due_date__lte=today + timedelta(days=1),
                                type__project__is_active=True).select_related('type', 'building')
    if project_id:
        rows = rows.filter(type__project_id=project_id)
    sent = 0
    for visit in rows:
        sent += notify_visit_due(visit, today)
    return sent


# ------------------------------------------------------------------ admin API
class PlanInput(serializers.Serializer):
    elevator = serializers.IntegerField(min_value=1)
    visit_type = serializers.IntegerField(min_value=1)
    expert = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    interval_days = serializers.IntegerField(min_value=7, max_value=730)
    lead_days = serializers.IntegerField(min_value=0, max_value=60, default=7)
    next_due = serializers.DateField()
    note = serializers.CharField(required=False, allow_blank=True, max_length=500, default='')
    is_active = serializers.BooleanField(default=True)


def plan_row(plan):
    expert = plan.expert
    open_visit = open_plan_visit(plan)
    return {
        'id': plan.pk, 'elevator': plan.elevator_id, 'elevator_title': plan.elevator.title or 'آسانسور',
        'visit_type': plan.visit_type_id,
        'visit_type_name': plan.visit_type.verbose_name or plan.visit_type.title or 'خدمت',
        'expert': plan.expert_id,
        'expert_name': ' '.join(filter(None, (expert.first_name, expert.last_name))) if expert else '',
        'interval_days': plan.interval_days, 'lead_days': plan.lead_days, 'next_due': plan.next_due,
        'opens_on': plan.next_due - timedelta(days=plan.lead_days), 'note': plan.note, 'is_active': plan.is_active,
        'open_visit': open_visit.pk if open_visit else None,
        'last_visit': plan.visits.filter(is_deleted=False).order_by('-id').values_list('id', flat=True).first(),
    }


class PlanAccessMixin:
    def project(self, request):
        access = AssetAccess(request, self)
        if not access.project_wide:
            raise PermissionDenied('برنامه سرویس ادواری نیازمند نقش مدیریتی پروژه است.')
        return int(request.query_params['p'])

    def validated(self, request, project_id):
        data = PlanInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        elevator = Elevator.objects.filter(pk=values['elevator'], project_id=project_id).first()
        if elevator is None or not BuildingElevator.objects.filter(elevator=elevator).exists():
            raise ValidationError({'elevator': 'آسانسور باید در این پروژه و متصل به ساختمان باشد.'})
        kind = VisitType.objects.filter(pk=values['visit_type'], project_id=project_id, is_active=True).first()
        if kind is None:
            raise ValidationError({'visit_type': 'نوع خدمت در این پروژه فعال نیست.'})
        expert = None
        if values.get('expert'):
            expert = User.objects.filter(pk=values['expert'], is_active=True).first()
            if expert is None or not RoleAssignment.objects.filter(
                    user=expert, project_id=project_id, is_deleted=False, role__is_active=True,
                    role__asset_scope__in=('assigned', 'supervised')).exists():
                raise ValidationError({'expert': 'کارشناس باید نقش اجرایی فعال در پروژه داشته باشد.'})
        if values['lead_days'] >= values['interval_days']:
            raise ValidationError({'lead_days': 'فاصله ایجاد پیش از موعد باید کمتر از دوره تکرار باشد.'})
        values.update(elevator=elevator, visit_type=kind, expert=expert)
        return values


class MaintenancePlanListCreateView(PlanAccessMixin, APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def get(self, request):
        project_id = self.project(request)
        rows = MaintenancePlan.objects.filter(project_id=project_id).select_related('elevator', 'visit_type', 'expert')
        elevator, building = request.query_params.get('elevator'), request.query_params.get('building')
        if elevator:
            rows = rows.filter(elevator_id=int(elevator))
        if building:
            rows = rows.filter(elevator__buildingelevator__building_id=int(building))
        workers = RoleAssignment.objects.filter(project_id=project_id, is_deleted=False, role__is_active=True,
                                                role__asset_scope__in=('assigned', 'supervised')).values('user_id')
        experts = User.objects.filter(is_active=True, pk__in=workers).order_by('first_name', 'last_name')
        kinds = VisitType.objects.filter(project_id=project_id, is_active=True).order_by('id')
        return Response({
            'results': [plan_row(plan) for plan in rows.distinct()[:200]],
            # Choices for the plan form, scoped to the project.
            'experts': [{'id': user.pk, 'name': ' '.join(filter(None, (user.first_name, user.last_name))) or 'کارشناس'}
                        for user in experts],
            'visit_types': [{'id': kind.pk, 'name': kind.verbose_name or kind.title or 'خدمت'} for kind in kinds],
        })

    def post(self, request):
        project_id = self.project(request)
        values = self.validated(request, project_id)
        if values['next_due'] < timezone.localdate():
            raise ValidationError({'next_due': 'موعد اولین سرویس نمی‌تواند گذشته باشد.'})
        plan = MaintenancePlan.objects.create(project_id=project_id, created_by=request.user, **values)
        return Response(plan_row(plan), status=201)


class MaintenancePlanDetailView(PlanAccessMixin, APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def put(self, request, id):
        project_id = self.project(request)
        plan = get_object_or_404(MaintenancePlan, pk=id, project_id=project_id)
        values = self.validated(request, project_id)
        if values['elevator'].pk != plan.elevator_id:
            raise ValidationError({'elevator': 'آسانسور برنامه قابل تغییر نیست؛ برنامه تازه بسازید.'})
        for key, value in values.items():
            setattr(plan, key, value)
        plan.save()
        return Response(plan_row(plan))

    def delete(self, request, id):
        project_id = self.project(request)
        plan = get_object_or_404(MaintenancePlan, pk=id, project_id=project_id)
        plan.is_active = False  # visits already opened from the plan stay as they are
        plan.save(update_fields=['is_active', 'updated_at'])
        return Response(plan_row(plan))
