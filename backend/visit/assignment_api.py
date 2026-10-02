"""Admin API for expert planning data (skills, grades, calendar) and skill/quality-aware assignment."""
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import DeleteCreateUpdateGetPermission
from visit.asset_access import AssetAccess
from visit.assignment import (DEFAULT_WORK_DAYS, WEEKDAY_LABELS, AssignmentError, Context, apply_assignment, build_plan,
                              candidates_for, person, plan_queryset, worker_users)
from visit.models import (AssignmentSetting, ExpertProfile, ExpertSkill, ExpertTimeOff, ServiceRequirement, Skill,
                          Visit, VisitType)


class ProjectAdminMixin:
    permission_classes = [DeleteCreateUpdateGetPermission]

    def project(self, request):
        if not AssetAccess(request, self).project_wide:
            raise PermissionDenied('تخصیص هوشمند نیازمند نقش مدیریتی پروژه است.')
        return int(request.query_params['p'])

    def worker(self, project_id, user_id):
        user = next((item for item in worker_users(project_id) if item.pk == user_id), None)
        if user is None:
            raise ValidationError({'user': 'کارشناس نقش اجرایی فعال در این پروژه ندارد.'})
        return user


def setting_row(setting):
    return {key: float(getattr(setting, key)) for key in
            ('skill_weight', 'quality_weight', 'workload_weight', 'familiarity_weight', 'urgent_boost')}


class AssignmentOverviewView(ProjectAdminMixin, APIView):
    """One call for the planning page: workers with their profile, skills, quality and load."""

    def get(self, request):
        project_id = self.project(request)
        ctx = Context(project_id)
        today = ctx.today
        experts = []
        for user in ctx.users:
            profile = ctx.profile(user.pk)
            experts.append({
                'id': user.pk, 'name': person(user), **profile,
                'skills': [{'skill': skill_id, 'level': level} for skill_id, level in sorted(ctx.skills[user.pk].items())],
                'quality': ctx.quality(user.pk), 'open': ctx.load()['open'].get(user.pk, 0),
                'time_off': [{'id': row.pk, 'start_date': row.start_date, 'end_date': row.end_date, 'reason': row.reason}
                             for row in ctx.time_off.get(user.pk, [])],
            })
        skills = Skill.objects.filter(project_id=project_id).annotate(holders_count=Count('holders', distinct=True))
        types = VisitType.objects.filter(project_id=project_id, is_active=True).order_by('id')
        requirements = {}
        for row in ServiceRequirement.objects.filter(visit_type__in=types):
            requirements.setdefault(row.visit_type_id, []).append(
                {'skill': row.skill_id, 'min_level': row.min_level, 'is_required': row.is_required})
        return Response({
            'today': today, 'weekdays': [{'day': day, 'label': WEEKDAY_LABELS[day]} for day in (5, 6, 0, 1, 2, 3, 4)],
            'default_work_days': DEFAULT_WORK_DAYS,
            'experts': experts,
            'skills': [{'id': s.pk, 'name': s.name, 'description': s.description, 'is_active': s.is_active,
                        'holders': s.holders_count} for s in skills],
            'visit_types': [{'id': t.pk, 'name': t.verbose_name or t.title or 'خدمت', 'complexity': t.complexity,
                             'requirements': requirements.get(t.pk, [])} for t in types],
            'settings': setting_row(ctx.setting),
            'unassigned': plan_queryset(project_id).count(),
        })


class AssignmentPlanView(ProjectAdminMixin, APIView):
    """Ranked workers for one visit (?visit=) or proposals for every unassigned visit."""

    def get(self, request):
        project_id = self.project(request)
        visit_id = request.query_params.get('visit')
        if visit_id:
            visit = get_object_or_404(Visit.objects.select_related('type', 'building'), pk=visit_id,
                                      type__project_id=project_id, building__project_id=project_id, is_deleted=False)
            ctx = Context(project_id)
            facts, ranked = candidates_for(ctx, visit)
            return Response({'visit': visit.pk, 'priority': facts['priority'], 'complexity': facts['complexity'],
                             'assignable': visit.status == Visit.NOTVISITED, 'candidates': ranked})
        try:
            limit = min(max(int(request.query_params.get('limit', 50)), 1), 100)
        except ValueError:
            raise ValidationError({'limit': 'عدد نامعتبر است.'})
        return Response(build_plan(project_id, limit))


class ApplyItem(serializers.Serializer):
    visit = serializers.IntegerField(min_value=1)
    expert = serializers.IntegerField(min_value=1)
    force = serializers.BooleanField(default=False)
    activate = serializers.BooleanField(default=False)
    reassign = serializers.BooleanField(default=False)


class ApplyInput(serializers.Serializer):
    assignments = ApplyItem(many=True, min_length=1, max_length=100)


class AssignmentApplyView(ProjectAdminMixin, APIView):
    """Applies the planner's confirmed choices; every row is checked again and succeeds or fails alone."""

    def post(self, request):
        project_id = self.project(request)
        data = ApplyInput(data=request.data)
        data.is_valid(raise_exception=True)
        results = []
        for item in data.validated_data['assignments']:
            try:
                outcome = apply_assignment(project_id, item['visit'], item['expert'], request.user,
                                           force=item['force'], activate=item['activate'],
                                           reassign=item['reassign'])
                results.append({'visit': item['visit'], 'ok': True, 'warnings': outcome['warnings']})
            except AssignmentError as error:
                results.append({'visit': item['visit'], 'ok': False, 'error': str(error)})
        return Response({'results': results, 'assigned': sum(row['ok'] for row in results)})


class ExpertInput(serializers.Serializer):
    grade = serializers.IntegerField(min_value=1, max_value=5)
    work_days = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=6), allow_empty=False,
                                      max_length=7)
    daily_capacity = serializers.IntegerField(min_value=1, max_value=30)
    max_open = serializers.IntegerField(min_value=1, max_value=100)
    is_assignable = serializers.BooleanField()
    note = serializers.CharField(required=False, allow_blank=True, max_length=255, default='')
    skills = serializers.ListField(child=serializers.DictField(), required=False, default=list, max_length=60)


class AssignmentExpertView(ProjectAdminMixin, APIView):
    def put(self, request, user_id):
        project_id = self.project(request)
        user = self.worker(project_id, user_id)
        data = ExpertInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        wanted = {}
        for entry in values['skills']:
            try:
                skill_id, level = int(entry['skill']), int(entry['level'])
            except (KeyError, TypeError, ValueError):
                raise ValidationError({'skills': 'هر مهارت شناسه و سطح عددی لازم دارد.'})
            if not 1 <= level <= 5:
                raise ValidationError({'skills': 'سطح مهارت بین ۱ تا ۵ است.'})
            wanted[skill_id] = level
        valid = set(Skill.objects.filter(project_id=project_id, pk__in=wanted, is_active=True).values_list('pk', flat=True))
        if set(wanted) - valid:
            raise ValidationError({'skills': 'مهارت انتخابی در این پروژه فعال نیست.'})
        with transaction.atomic():
            ExpertProfile.objects.update_or_create(project_id=project_id, user=user, defaults={
                'grade': values['grade'], 'work_days': sorted(set(values['work_days'])),
                'daily_capacity': values['daily_capacity'], 'max_open': values['max_open'],
                'is_assignable': values['is_assignable'], 'note': values['note'].strip()})
            ExpertSkill.objects.filter(project_id=project_id, user=user).exclude(skill_id__in=wanted).delete()
            for skill_id, level in wanted.items():
                ExpertSkill.objects.update_or_create(user=user, skill_id=skill_id,
                                                     defaults={'project_id': project_id, 'level': level})
        ctx = Context(project_id, users=[user])
        return Response({'id': user.pk, 'name': person(user), **ctx.profile(user.pk),
                         'skills': [{'skill': s, 'level': l} for s, l in sorted(ctx.skills[user.pk].items())],
                         'quality': ctx.quality(user.pk)})


class TimeOffInput(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255, default='')


class AssignmentTimeOffView(ProjectAdminMixin, APIView):
    def post(self, request, user_id):
        project_id = self.project(request)
        user = self.worker(project_id, user_id)
        data = TimeOffInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if values['end_date'] < values['start_date']:
            raise ValidationError({'end_date': 'پایان مرخصی نمی‌تواند پیش از شروع باشد.'})
        if values['end_date'] < timezone.localdate():
            raise ValidationError({'end_date': 'مرخصی گذشته ثبت نمی‌شود.'})
        row = ExpertTimeOff.objects.create(project_id=project_id, user=user, created_by=request.user,
                                           start_date=values['start_date'], end_date=values['end_date'],
                                           reason=values['reason'].strip())
        return Response({'id': row.pk, 'start_date': row.start_date, 'end_date': row.end_date, 'reason': row.reason},
                        status=201)


class AssignmentTimeOffDetailView(ProjectAdminMixin, APIView):
    def delete(self, request, id):
        project_id = self.project(request)
        get_object_or_404(ExpertTimeOff, pk=id, project_id=project_id).delete()
        return Response(status=204)


class SkillInput(serializers.Serializer):
    name = serializers.CharField(max_length=60)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255, default='')
    is_active = serializers.BooleanField(default=True)


class AssignmentSkillListView(ProjectAdminMixin, APIView):
    def post(self, request):
        project_id = self.project(request)
        data = SkillInput(data=request.data)
        data.is_valid(raise_exception=True)
        name = data.validated_data['name'].strip()
        if not name:
            raise ValidationError({'name': 'نام مهارت لازم است.'})
        if Skill.objects.filter(project_id=project_id, name=name).exists():
            raise ValidationError({'name': 'مهارتی با این نام وجود دارد.'})
        row = Skill.objects.create(project_id=project_id, name=name,
                                   description=data.validated_data['description'].strip())
        return Response({'id': row.pk, 'name': row.name, 'description': row.description, 'is_active': True,
                         'holders': 0}, status=201)


class AssignmentSkillDetailView(ProjectAdminMixin, APIView):
    def put(self, request, id):
        project_id = self.project(request)
        row = get_object_or_404(Skill, pk=id, project_id=project_id)
        data = SkillInput(data=request.data)
        data.is_valid(raise_exception=True)
        name = data.validated_data['name'].strip()
        if Skill.objects.filter(project_id=project_id, name=name).exclude(pk=row.pk).exists():
            raise ValidationError({'name': 'مهارتی با این نام وجود دارد.'})
        row.name, row.description = name, data.validated_data['description'].strip()
        row.is_active = data.validated_data['is_active']
        row.save()
        return Response({'id': row.pk, 'name': row.name, 'description': row.description, 'is_active': row.is_active})

    def delete(self, request, id):
        project_id = self.project(request)
        row = get_object_or_404(Skill, pk=id, project_id=project_id)
        row.is_active = False  # holders and requirements stay, but stop counting
        row.save(update_fields=['is_active'])
        return Response({'id': row.pk, 'is_active': False})


class RequirementInput(serializers.Serializer):
    complexity = serializers.IntegerField(min_value=1, max_value=5)
    requirements = serializers.ListField(child=serializers.DictField(), default=list, max_length=20)


class AssignmentRequirementView(ProjectAdminMixin, APIView):
    def put(self, request, visit_type_id):
        project_id = self.project(request)
        kind = get_object_or_404(VisitType, pk=visit_type_id, project_id=project_id)
        data = RequirementInput(data=request.data)
        data.is_valid(raise_exception=True)
        wanted = {}
        for entry in data.validated_data['requirements']:
            try:
                skill_id, level = int(entry['skill']), int(entry.get('min_level', 1))
            except (KeyError, TypeError, ValueError):
                raise ValidationError({'requirements': 'هر نیازمندی شناسه مهارت و حداقل سطح عددی لازم دارد.'})
            if not 1 <= level <= 5:
                raise ValidationError({'requirements': 'حداقل سطح بین ۱ تا ۵ است.'})
            wanted[skill_id] = (level, bool(entry.get('is_required', True)))
        valid = set(Skill.objects.filter(project_id=project_id, pk__in=wanted, is_active=True).values_list('pk', flat=True))
        if set(wanted) - valid:
            raise ValidationError({'requirements': 'مهارت انتخابی در این پروژه فعال نیست.'})
        with transaction.atomic():
            kind.complexity = data.validated_data['complexity']
            kind.save(update_fields=['complexity'])
            ServiceRequirement.objects.filter(visit_type=kind).exclude(skill_id__in=wanted).delete()
            for skill_id, (level, required) in wanted.items():
                ServiceRequirement.objects.update_or_create(visit_type=kind, skill_id=skill_id,
                                                            defaults={'min_level': level, 'is_required': required})
        return Response({'id': kind.pk, 'complexity': kind.complexity,
                         'requirements': [{'skill': s, 'min_level': l, 'is_required': r} for s, (l, r) in wanted.items()]})


class SettingInput(serializers.Serializer):
    skill_weight = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=10)
    quality_weight = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=10)
    workload_weight = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=10)
    familiarity_weight = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=10)
    urgent_boost = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=1, max_value=5)


class AssignmentSettingView(ProjectAdminMixin, APIView):
    def put(self, request):
        project_id = self.project(request)
        data = SettingInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = data.validated_data
        if not (values['skill_weight'] + values['quality_weight'] + values['workload_weight'] + values['familiarity_weight']):
            raise ValidationError({'skill_weight': 'دست‌کم یک ضریب باید بزرگ‌تر از صفر باشد.'})
        row, _ = AssignmentSetting.objects.update_or_create(project_id=project_id, defaults=values)
        return Response(setting_row(row))
