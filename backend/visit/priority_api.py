"""Admin API for service-priority factors, per-entity choices and the ranking list."""
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import DeleteCreateUpdateGetPermission
from visit.asset_access import AssetAccess
from visit.management import current_management_q
from visit.models import (Building, BuildingClient, BuildingElevator, Client, Elevator, PriorityAssignment,
                          PriorityFactor, PriorityOption)
from visit.priority import describe, explain, recompute_project

MODELS = {'client': Client, 'building': Building, 'elevator': Elevator}


class OptionInput(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    label = serializers.CharField(max_length=80, trim_whitespace=True)
    value = serializers.IntegerField(min_value=0, max_value=100)


class FactorInput(serializers.Serializer):
    name = serializers.CharField(max_length=80, trim_whitespace=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    target = serializers.ChoiceField(choices=[key for key, _ in PriorityFactor.TARGETS])
    weight = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0, max_value=100)
    default_value = serializers.IntegerField(min_value=0, max_value=100, default=50)
    is_active = serializers.BooleanField(default=True)
    order = serializers.IntegerField(default=0)
    options = OptionInput(many=True)

    def validate_options(self, options):
        if not options:
            raise ValidationError('حداقل یک گزینه لازم است.')
        labels = [option['label'] for option in options]
        if len(set(labels)) != len(labels):
            raise ValidationError('عنوان گزینه‌ها نباید تکراری باشد.')
        return options


def factor_output(factor):
    return {
        'id': factor.id, 'name': factor.name, 'description': factor.description, 'target': factor.target,
        'weight': float(factor.weight), 'default_value': factor.default_value, 'is_active': factor.is_active,
        'order': factor.order, 'assigned': factor.assignments.count(),
        'options': [{'id': o.id, 'label': o.label, 'value': o.value} for o in factor.options.all() if o.is_active],
    }


class ProjectPriorityView(APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def project(self, request):
        access = AssetAccess(request, self)
        if not access.project_wide:
            raise PermissionDenied('اولویت‌بندی نیازمند دسترسی کل پروژه است.')
        return access.project_id


def save_options(factor, options):
    keep = []
    for order, data in enumerate(options):
        option = factor.options.filter(pk=data.get('id')).first() if data.get('id') else None
        option = option or PriorityOption(factor=factor)
        option.label, option.value, option.order, option.is_active = data['label'], data['value'], order, True
        option.save()
        keep.append(option.pk)
    # Removed options are retired, not deleted, so past choices stay explainable; they stop counting.
    factor.options.exclude(pk__in=keep).update(is_active=False)
    PriorityAssignment.objects.filter(factor=factor).exclude(option_id__in=keep).delete()


class PriorityFactorListCreateView(ProjectPriorityView):
    def get(self, request):
        project_id = self.project(request)
        factors = PriorityFactor.objects.filter(project_id=project_id).prefetch_related('options')
        return Response([factor_output(factor) for factor in factors])

    def post(self, request):
        project_id = self.project(request)
        data = FactorInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        options = values.pop('options')
        with transaction.atomic():
            factor = PriorityFactor.objects.create(project_id=project_id, **values)
            save_options(factor, options)
        recompute_project(project_id)
        return Response(factor_output(factor), status=201)


class PriorityFactorDetailView(ProjectPriorityView):
    def put(self, request, id):
        project_id = self.project(request)
        factor = get_object_or_404(PriorityFactor, pk=id, project_id=project_id)
        data = FactorInput(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        options = values.pop('options')
        if values['target'] != factor.target and factor.assignments.exists():
            raise ValidationError({'target': 'برای عاملی که مقدار ثبت‌شده دارد، نوع هدف قابل تغییر نیست.'})
        with transaction.atomic():
            for key, value in values.items():
                setattr(factor, key, value)
            factor.save()
            save_options(factor, options)
        recompute_project(project_id)
        return Response(factor_output(factor))

    def delete(self, request, id):
        project_id = self.project(request)
        factor = get_object_or_404(PriorityFactor, pk=id, project_id=project_id)
        factor.is_active = False
        factor.save(update_fields=['is_active', 'updated_at'])
        recompute_project(project_id)
        return Response(status=204)


class PriorityEntityView(ProjectPriorityView):
    """Score, breakdown and own-level choices of one client, building or elevator."""

    def entity(self, project_id, target, id):
        if target not in MODELS:
            raise ValidationError({'target': 'نوع نامعتبر است.'})
        return get_object_or_404(MODELS[target], pk=id, project_id=project_id)

    def output(self, project_id, target, entity):
        factors = PriorityFactor.objects.filter(project_id=project_id, target=target, is_active=True).prefetch_related('options')
        return {**explain(project_id, target, entity.pk), 'factors': [factor_output(f) for f in factors]}

    def get(self, request, target, id):
        project_id = self.project(request)
        return Response(self.output(project_id, target, self.entity(project_id, target, id)))

    def put(self, request, target, id):
        project_id = self.project(request)
        entity = self.entity(project_id, target, id)
        choices = request.data.get('choices')
        if not isinstance(choices, dict):
            raise ValidationError({'choices': 'انتخاب‌ها باید به شکل {عامل: گزینه} باشند.'})
        with transaction.atomic():
            for factor_id, option_id in choices.items():
                factor = PriorityFactor.objects.filter(pk=factor_id, project_id=project_id, target=target, is_active=True).first()
                if factor is None:
                    raise ValidationError({'choices': f'عامل {factor_id} برای این مورد معتبر نیست.'})
                lookup = {'factor': factor, target: entity}
                if option_id in (None, ''):
                    PriorityAssignment.objects.filter(**lookup).delete()
                    continue
                option = factor.options.filter(pk=option_id, is_active=True).first()
                if option is None:
                    raise ValidationError({'choices': f'گزینه {option_id} به عامل «{factor.name}» تعلق ندارد.'})
                PriorityAssignment.objects.update_or_create(**lookup, defaults={'option': option, 'updated_by': request.user})
        recompute_project(project_id)
        entity.refresh_from_db()
        return Response(self.output(project_id, target, entity))


class PriorityRankingView(ProjectPriorityView):
    def get(self, request):
        project_id = self.project(request)
        target = request.query_params.get('target', 'building')
        if target not in MODELS:
            raise ValidationError({'target': 'نوع نامعتبر است.'})
        rows = MODELS[target].objects.filter(project_id=project_id)
        search = (request.query_params.get('search') or '').strip()
        if search:
            fields = {'client': ('name', 'name_fa'), 'building': ('verbose_name', 'name', 'code'),
                      'elevator': ('title',)}[target]
            condition = Q()
            for field in fields:
                condition |= Q(**{field + '__icontains': search})
            rows = rows.filter(condition)
        level = request.query_params.get('level')
        bounds = {'critical': (80, 101), 'high': (60, 80), 'medium': (40, 60), 'low': (-1, 40)}
        if level in bounds:
            rows = rows.filter(priority_score__gte=bounds[level][0], priority_score__lt=bounds[level][1])
        total = rows.count()
        try:
            offset = max(0, int(request.query_params.get('offset', 0)))
            limit = min(100, max(1, int(request.query_params.get('limit', 25))))
        except ValueError:
            raise ValidationError({'limit': 'عدد نامعتبر است.'})
        page = list(rows.order_by(F('priority_score').desc(nulls_last=True), 'id')[offset:offset + limit])
        ids = [row.pk for row in page]
        context = {}
        if target == 'building':
            context = {b: name_fa or name for b, name_fa, name in BuildingClient.objects.filter(building_id__in=ids)
                       .filter(current_management_q()).values_list('building_id', 'client__name_fa', 'client__name')}
        elif target == 'elevator':
            context = {e: verbose or name or code for e, verbose, name, code in BuildingElevator.objects.filter(
                elevator_id__in=ids).values_list('elevator_id', 'building__verbose_name', 'building__name', 'building__code')}
        results = []
        for row in page:
            label = {'client': lambda r: r.name_fa or r.name, 'building': lambda r: r.verbose_name or r.name or r.code,
                     'elevator': lambda r: r.title}[target](row)
            results.append({'id': row.pk, 'label': label or f'#{row.pk}', 'context': context.get(row.pk, ''),
                            **describe(row.priority_score)})
        return Response({'count': total, 'results': results})
