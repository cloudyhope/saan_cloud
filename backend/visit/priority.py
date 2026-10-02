"""Service priority: weighted factors on clients, buildings and elevators.

Each active factor contributes `weight × value` where value is the chosen option (0-100) or the
factor's default. A client is scored by client factors; a building also inherits the factors of
its current managing client; an elevator inherits its building's (and that client's). The score is
the weighted average, so it stays on a 0-100 scale whatever factors are added later.

Scores are stored on Client/Building/Elevator so task lists can sort by them; `recompute_project`
refreshes them after any change to factors, options, assignments, management or elevator links.
"""
from django.db.models import FloatField, Max, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce

from visit.management import current_management_q

# Level boundaries on the 0-100 score; kept in one place for the API and every UI.
LEVELS = ((80, 'critical', 'بحرانی'), (60, 'high', 'بالا'), (40, 'medium', 'متوسط'), (0, 'low', 'عادی'))


def level(score):
    if score is None:
        return None
    for floor, key, label in LEVELS:
        if score >= floor:
            return {'key': key, 'label': label}
    return {'key': 'low', 'label': 'عادی'}


def describe(score):
    return {'score': None if score is None else round(score, 1), 'level': level(score)}


class _Model:
    """Loads one project's factors and assignments once, then scores any entity of it."""

    def __init__(self, project_id):
        from visit.models import BuildingClient, BuildingElevator, PriorityAssignment, PriorityFactor
        self.factors = {target: [] for target, _ in PriorityFactor.TARGETS}
        for factor in PriorityFactor.objects.filter(project_id=project_id, is_active=True).prefetch_related('options'):
            self.factors[factor.target].append(factor)
        self.chosen = {}
        rows = PriorityAssignment.objects.filter(factor__project_id=project_id, factor__is_active=True,
                                                 option__is_active=True).select_related('option')
        for row in rows:
            target = 'client' if row.client_id else 'building' if row.building_id else 'elevator'
            entity = row.client_id or row.building_id or row.elevator_id
            self.chosen[(target, entity, row.factor_id)] = row.option
        self.manager = dict(BuildingClient.objects.filter(building__project_id=project_id).filter(
            current_management_q()).order_by('start_at').values_list('building_id', 'client_id'))
        self.home = dict(BuildingElevator.objects.filter(building__project_id=project_id)
                         .order_by('id').values_list('elevator_id', 'building_id'))

    def parts(self, target, entity):
        """(factor, option or None, value, inherited_from) for every factor reaching the entity."""
        chain = [(target, entity)]
        if target == 'elevator':
            building = self.home.get(entity)
            chain.append(('building', building))
            target, entity = 'building', building
        if target == 'building':
            chain.append(('client', self.manager.get(entity)))
        result = []
        for level_target, level_entity in chain:
            for factor in self.factors[level_target]:
                option = self.chosen.get((level_target, level_entity, factor.id)) if level_entity else None
                value = option.value if option else factor.default_value
                result.append((factor, option, value, level_target))
        return result

    def score(self, target, entity):
        parts = [part for part in self.parts(target, entity) if part[0].weight > 0]
        total = sum(float(part[0].weight) for part in parts)
        if not total:
            return None
        return sum(float(part[0].weight) * part[2] for part in parts) / total


def recompute_project(project_id):
    """Refresh stored scores of every client, building and elevator of the project."""
    from visit.models import Building, Client, Elevator
    model = _Model(project_id)
    for target, queryset in (('client', Client.objects.filter(project_id=project_id)),
                             ('building', Building.objects.filter(project_id=project_id)),
                             ('elevator', Elevator.objects.filter(project_id=project_id))):
        changed = []
        for row in queryset.only('id', 'priority_score'):
            score = model.score(target, row.id)
            score = None if score is None else round(score, 2)
            if row.priority_score != score:
                row.priority_score = score
                changed.append(row)
        queryset.model.objects.bulk_update(changed, ['priority_score'], batch_size=500)


def explain(project_id, target, entity_id):
    """Score with its breakdown, for the detail panels."""
    model = _Model(project_id)
    parts = model.parts(target, entity_id)
    total = sum(float(factor.weight) for factor, *_ in parts)
    return {
        **describe(model.score(target, entity_id)),
        'parts': [{
            'factor': factor.id, 'name': factor.name, 'target': factor.target, 'inherited': source != target,
            'weight': float(factor.weight), 'option': option.id if option else None,
            'option_label': option.label if option else None, 'value': value, 'is_default': option is None,
            'share': round(float(factor.weight) / total * 100, 1) if total else 0,
        } for factor, option, value, source in parts],
    }


def annotate_visits(queryset):
    """Adds `priority_value`: the highest elevator score of the visit, else its building score."""
    from visit.models import Visit
    elevators = Visit.elevator.through.objects.filter(visit_id=OuterRef('pk')).values('visit_id').annotate(
        top=Max('elevator__priority_score')).values('top')
    queryset = queryset.annotate(priority_value=Coalesce(
        Subquery(elevators, output_field=FloatField()), 'building__priority_score', Value(None, output_field=FloatField())))
    # NULL-safe sort key: unscored work sorts last on every database (PostgreSQL puts NULLs first on DESC).
    return queryset.annotate(priority_rank=Coalesce('priority_value', Value(-1.0, output_field=FloatField())))


def visit_priority(visit):
    if hasattr(visit, 'priority_value'):
        return describe(visit.priority_value)
    scores = [e.priority_score for e in visit.elevator.all() if e.priority_score is not None]
    if scores:
        return describe(max(scores))
    return describe(visit.building.priority_score if visit.building_id else None)


def schedule_recompute(project_id):
    """Recompute after the surrounding transaction commits (nothing runs if it rolls back)."""
    from django.db import transaction
    if project_id:
        transaction.on_commit(lambda: recompute_project(project_id))


def connect_signals():
    """Management transfers and elevator moves change inherited factors."""
    from django.db.models.signals import post_delete, post_save
    from visit.models import BuildingClient, BuildingElevator

    def changed(sender, instance, **kwargs):
        building = getattr(instance, 'building', None)
        schedule_recompute(building.project_id if building else None)

    for model in (BuildingClient, BuildingElevator):
        post_save.connect(changed, sender=model, dispatch_uid=f'priority-{model.__name__}-save')
        post_delete.connect(changed, sender=model, dispatch_uid=f'priority-{model.__name__}-delete')
