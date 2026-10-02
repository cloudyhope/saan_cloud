"""Skill-, quality- and workload-aware assignment of visits to field workers.

A worker is *eligible* when no hard rule blocks them (inactive for planning, time off, missing required
skill level, grade below the service's complexity, no capacity left). Eligible workers are ranked by a
weighted score of four factors, each 0-100: skill fit, quality, free capacity and familiarity with the
building. Critical and high priority visits weigh skill and quality more (`urgent_boost`) and are placed
first, so the best workers go to the most sensitive work. Nothing here assigns on its own; the planner
confirms every proposal (`apply_assignments`).
"""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Min, Q
from django.utils import timezone

from auth_app.models import RoleAssignment
from visit.models import (AssignmentSetting, ClientVisitFeedback, ExpertProfile, ExpertSkill, ExpertTimeOff,
                          ServiceRequirement, Visit)

DEFAULT_WORK_DAYS = [5, 6, 0, 1, 2]  # Saturday to Wednesday
WEEKDAY_LABELS = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']  # Python weekday order
NEUTRAL_QUALITY = 60.0
QUALITY_WINDOW_DAYS = 180
FAMILIARITY_WINDOW_DAYS = 365
OPEN_STATES = (Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND)
URGENT_SCORE = 60  # priority score from which a visit counts as urgent (the «high» level)


def person(user):
    return ' '.join(filter(None, (user.first_name, user.last_name))) or 'کارشناس'


def project_settings(project_id):
    return AssignmentSetting.objects.filter(project_id=project_id).first() or AssignmentSetting(project_id=project_id)


def worker_users(project_id):
    """Active users holding a field role (assigned or supervised scope) in the project."""
    ids = RoleAssignment.objects.filter(
        project_id=project_id, is_deleted=False, role__is_active=True, project__is_active=True,
        role__asset_scope__in=('assigned', 'supervised')).values('user_id')
    return list(User.objects.filter(pk__in=ids, is_active=True).order_by('first_name', 'last_name', 'id'))


class Context:
    """Everything the scoring needs, loaded once per request so a batch plan stays cheap."""

    def __init__(self, project_id, today=None, users=None):
        self.project_id = project_id
        self.today = today or timezone.localdate()
        self.setting = project_settings(project_id)
        self.users = users if users is not None else worker_users(project_id)
        self.user_ids = [user.pk for user in self.users]
        self.profiles = {row.user_id: row for row in ExpertProfile.objects.filter(
            project_id=project_id, user_id__in=self.user_ids)}
        self.skills = defaultdict(dict)
        for row in ExpertSkill.objects.filter(project_id=project_id, user_id__in=self.user_ids, skill__is_active=True):
            self.skills[row.user_id][row.skill_id] = row.level
        self.time_off = defaultdict(list)
        for row in ExpertTimeOff.objects.filter(project_id=project_id, user_id__in=self.user_ids,
                                                end_date__gte=self.today):
            self.time_off[row.user_id].append(row)
        self.requirements = defaultdict(list)
        for row in ServiceRequirement.objects.filter(visit_type__project_id=project_id,
                                                     skill__is_active=True).select_related('skill'):
            self.requirements[row.visit_type_id].append(row)
        self._quality = None
        self._load = None
        self._familiarity = {}

    # -------------------------------------------------------------- profile helpers
    def profile(self, user_id):
        row = self.profiles.get(user_id)
        return {
            'grade': row.grade if row else 3,
            'work_days': (row.work_days if row and row.work_days else DEFAULT_WORK_DAYS),
            'daily_capacity': row.daily_capacity if row else 4,
            'max_open': row.max_open if row else 10,
            'is_assignable': row.is_assignable if row else True,
            'note': row.note if row else '',
        }

    # -------------------------------------------------------------- quality
    def quality(self, user_id):
        if self._quality is None:
            self._quality = self._load_quality()
        return self._quality.get(user_id) or self._neutral()

    @staticmethod
    def _neutral():
        return {'score': NEUTRAL_QUALITY, 'has_history': False, 'reviewed': 0, 'rated': 0, 'avg_rating': None,
                'first_pass': None, 'on_time': None}

    def _load_quality(self):
        since = timezone.now() - timedelta(days=QUALITY_WINDOW_DAYS)
        rows = Visit.objects.filter(
            Q(expert_id__in=self.user_ids) | Q(promoter_id__in=self.user_ids), type__project_id=self.project_id,
            is_deleted=False, datetime_last_change__gte=since,
            status__in=(Visit.COMPLETED, Visit.APPROVED, Visit.REJECTED, Visit.RETRY),
        ).annotate(versions=Count('report_snapshots', distinct=True), first_report=Min('report_snapshots__created_at')
                   ).values('id', 'expert_id', 'promoter_id', 'status', 'due_date', 'versions', 'first_report')
        ratings = defaultdict(list)
        visit_ids = []
        by_user = defaultdict(list)
        for row in rows:
            visit_ids.append(row['id'])
            for user_id in {row['expert_id'], row['promoter_id']} & set(self.user_ids):
                by_user[user_id].append(row)
        for visit_id, rating in ClientVisitFeedback.objects.filter(
                visit_id__in=visit_ids, rating__isnull=False).values_list('visit_id', 'rating'):
            ratings[visit_id].append(rating)
        result = {}
        for user_id, items in by_user.items():
            outcomes = [item for item in items if item['status'] in (Visit.APPROVED, Visit.REJECTED, Visit.RETRY)]
            review = None
            if outcomes:
                points = [(1.0 if item['versions'] <= 1 else 0.6) if item['status'] == Visit.APPROVED else 0.0
                          for item in outcomes]
                review = 100.0 * sum(points) / len(points)
            values = [rating for item in items for rating in ratings.get(item['id'], [])]
            rating_score = (sum(values) / len(values) - 1) / 4 * 100 if values else None
            timed = [item for item in items if item['due_date'] and item['first_report']]
            punctual = (100.0 * sum(timezone.localtime(item['first_report']).date() <= item['due_date']
                                    for item in timed) / len(timed)) if timed else None
            parts = [(0.45, review), (0.35, rating_score), (0.20, punctual)]
            used = [(weight, value) for weight, value in parts if value is not None]
            if not used:
                continue
            raw = sum(weight * value for weight, value in used) / sum(weight for weight, _ in used)
            confidence = min(1.0, len(outcomes) / 8)  # a few reports do not make a reputation
            result[user_id] = {
                'score': round(NEUTRAL_QUALITY + (raw - NEUTRAL_QUALITY) * confidence, 1), 'has_history': True,
                'reviewed': len(outcomes), 'rated': len(values),
                'avg_rating': round(sum(values) / len(values), 2) if values else None,
                'first_pass': round(review, 1) if review is not None else None,
                'on_time': round(punctual, 1) if punctual is not None else None,
            }
        return result

    # -------------------------------------------------------------- load
    def load(self):
        if self._load is None:
            open_count = defaultdict(int)
            per_day = defaultdict(int)
            for expert_id, promoter_id, due in Visit.objects.filter(
                    Q(expert_id__in=self.user_ids) | Q(promoter_id__in=self.user_ids), type__project_id=self.project_id,
                    is_active=True, is_deleted=False, status__in=OPEN_STATES).values_list(
                    'expert_id', 'promoter_id', 'due_date'):
                for user_id in {expert_id, promoter_id} & set(self.user_ids):
                    open_count[user_id] += 1
                    if due:
                        per_day[(user_id, due)] += 1
            self._load = {'open': open_count, 'day': per_day}
        return self._load

    def reserve(self, user_id, due_date):
        """Count a proposed assignment so later proposals of the same plan see the extra work."""
        load = self.load()
        load['open'][user_id] += 1
        if due_date:
            load['day'][(user_id, due_date)] += 1

    # -------------------------------------------------------------- familiarity
    def familiarity(self, building_id):
        if building_id not in self._familiarity:
            counts = defaultdict(int)
            since = timezone.now() - timedelta(days=FAMILIARITY_WINDOW_DAYS)
            for expert_id, promoter_id in Visit.objects.filter(
                    building_id=building_id, is_deleted=False, status__in=(Visit.COMPLETED, Visit.APPROVED),
                    datetime_last_change__gte=since).values_list('expert_id', 'promoter_id'):
                for user_id in {expert_id, promoter_id} - {None}:
                    counts[user_id] += 1
            self._familiarity[building_id] = counts
        return self._familiarity[building_id]


def evaluate(ctx, user, visit):
    """Score one worker for one visit. `visit` is a dict: type_id, building_id, due_date, priority."""
    profile = ctx.profile(user.pk)
    blockers, warnings = [], []
    due = visit.get('due_date')
    check_day = due or ctx.today
    if not profile['is_assignable']:
        blockers.append('در تنظیمات برای تخصیص غیرفعال است')
    for off in ctx.time_off.get(user.pk, []):
        if off.start_date <= check_day <= off.end_date:
            blockers.append('در مرخصی است' + (f' ({off.reason})' if off.reason else ''))
            break
    open_now = ctx.load()['open'].get(user.pk, 0)
    day_load = ctx.load()['day'].get((user.pk, due), 0) if due else 0
    if open_now >= profile['max_open']:
        blockers.append('ظرفیت کل مأموریت‌های باز پر است')

    # Skill fit: each requirement of the service plus the grade against its complexity.
    levels = ctx.skills.get(user.pk, {})
    fits = []
    skill_notes = []
    for requirement in ctx.requirements.get(visit['type_id'], []):
        have = levels.get(requirement.skill_id, 0)
        need = requirement.min_level
        if have >= need:
            fits.append(80 + 10 * min(2, have - need))
            skill_notes.append(f'{requirement.skill.name}: سطح {have} از حداقل {need}')
        elif requirement.is_required:
            fits.append(0)
            blockers.append(f'مهارت «{requirement.skill.name}» حداقل سطح {need} لازم است (سطح فعلی {have or "ندارد"})')
        else:
            fits.append(40 * have / need)
            warnings.append(f'مهارت ترجیحی «{requirement.skill.name}» زیر سطح {need} است')
    complexity = visit.get('complexity') or 1
    if profile['grade'] < complexity:
        fits.append(0)
        blockers.append(f'گرید {profile["grade"]} پایین‌تر از پیچیدگی {complexity} این خدمت است')
    elif complexity > 1:
        fits.append(80 + 10 * min(2, profile['grade'] - complexity))
    skill_fit = sum(fits) / len(fits) if fits else 70.0  # a service with no requirement is open to everyone

    quality = ctx.quality(user.pk)

    capacity_left = max(0.0, 1 - open_now / profile['max_open'])
    workload = 100.0 * capacity_left
    if due:
        if due.weekday() not in profile['work_days']:
            warnings.append('روز موعد جزو روزهای کاری نیست')
            workload -= 30
        if day_load >= profile['daily_capacity']:
            warnings.append(f'در روز موعد {day_load} مأموریت دارد (ظرفیت روزانه {profile["daily_capacity"]})')
            workload -= 40
    workload = max(0.0, workload)

    known = ctx.familiarity(visit['building_id']).get(user.pk, 0) if visit.get('building_id') else 0
    familiarity = min(100.0, 100.0 * known / 3)

    setting = ctx.setting
    boost = float(setting.urgent_boost) if (visit.get('priority') or 0) >= URGENT_SCORE else 1.0
    factors = {
        'skill': (skill_fit, float(setting.skill_weight) * boost),
        'quality': (quality['score'], float(setting.quality_weight) * boost),
        'workload': (workload, float(setting.workload_weight)),
        'familiarity': (familiarity, float(setting.familiarity_weight)),
    }
    total_weight = sum(weight for _, weight in factors.values())
    score = sum(value * weight for value, weight in factors.values()) / total_weight if total_weight else 50.0
    return {
        'user': user.pk, 'name': person(user), 'score': round(score, 1), 'eligible': not blockers,
        'blockers': blockers, 'warnings': warnings, 'grade': profile['grade'],
        'factors': {key: {'value': round(value, 1), 'weight': round(weight, 2)} for key, (value, weight) in factors.items()},
        'skill_notes': skill_notes, 'open': open_now, 'max_open': profile['max_open'], 'day_load': day_load,
        'quality': quality['score'], 'has_history': quality['has_history'], 'known_visits': known,
    }


def rank(candidates):
    return sorted(candidates, key=lambda c: (not c['eligible'], -c['score'], c['open'], c['user']))


def visit_facts(visit):
    from visit.priority import visit_priority
    info = visit_priority(visit)
    return {
        'id': visit.pk, 'type_id': visit.type_id, 'building_id': visit.building_id,
        'due_date': visit.due_date if visit.has_due_date else None,
        'complexity': visit.type.complexity if visit.type_id else 1,
        'priority': info['score'] if info and info.get('score') is not None else None,
    }


def candidates_for(ctx, visit, exclude=()):
    facts = visit_facts(visit)
    return facts, rank([evaluate(ctx, user, facts) for user in ctx.users if user.pk not in exclude])


def plan_queryset(project_id):
    from visit.priority import annotate_visits
    rows = Visit.objects.filter(
        type__project_id=project_id, building__project_id=project_id, is_deleted=False, status=Visit.NOTVISITED,
        expert__isnull=True, promoter__isnull=True).filter(
        Q(is_active=True) | Q(service_submissions__isnull=False)).distinct()
    return annotate_visits(rows.select_related('type', 'building')).order_by(
        '-priority_rank', '-has_due_date', 'due_date', 'id')


def build_plan(project_id, limit=50, today=None):
    """Proposals for unassigned visits, most sensitive first; each proposal reserves capacity."""
    ctx = Context(project_id, today)
    proposals = []
    for visit in plan_queryset(project_id)[:limit]:
        facts, ranked = candidates_for(ctx, visit)
        best = next((item for item in ranked if item['eligible']), None)
        if best:
            ctx.reserve(best['user'], facts['due_date'])
        building = visit.building
        proposals.append({
            'visit': visit.pk, 'type': visit.type.verbose_name or visit.type.title or 'خدمت',
            'building': (building.verbose_name or building.name or building.code) if building else '',
            'due_date': facts['due_date'], 'priority': facts['priority'],
            'pending_request': not visit.is_active, 'complexity': facts['complexity'],
            'suggested': best, 'alternatives': [item for item in ranked if item is not best][:3],
            'why_none': sorted({reason for item in ranked[:3] for reason in item['blockers']})[:3] if not best else [],
        })
    return {'proposals': proposals, 'workers': len(ctx.users)}


class AssignmentError(Exception):
    pass


def apply_assignment(project_id, visit_id, user_id, actor, force=False, activate=False, reassign=False):
    """Assign one visit to one worker after re-checking the rules against fresh data."""
    from notification.in_app import notify_visit_assignment

    with transaction.atomic():
        visit = Visit.objects.select_for_update().select_related('type', 'building').filter(
            pk=visit_id, type__project_id=project_id, building__project_id=project_id, is_deleted=False).first()
        if visit is None:
            raise AssignmentError('مأموریت پیدا نشد.')
        if visit.status != Visit.NOTVISITED:
            raise AssignmentError('فقط مأموریت شروع‌نشده قابل تخصیص است.')
        if (visit.expert_id or visit.promoter_id) and not reassign:
            raise AssignmentError('این مأموریت پیش‌تر به کارشناس دیگری تخصیص داده شده است.')
        if not visit.is_active and not (activate and visit.service_submissions.exists()):
            raise AssignmentError('مأموریت فعال نیست.')
        ctx = Context(project_id)
        user = next((item for item in ctx.users if item.pk == user_id), None)
        if user is None:
            raise AssignmentError('کارشناس نقش اجرایی فعال در این پروژه ندارد.')
        facts = visit_facts(visit)
        result = evaluate(ctx, user, facts)
        if result['blockers'] and not force:
            raise AssignmentError('؛ '.join(result['blockers']))
        visit.expert = visit.promoter = user
        fields = ['expert', 'promoter', 'datetime_last_change']
        newly_active = activate and not visit.is_active
        if newly_active:
            visit.is_active = True
            fields.append('is_active')
        visit.save(update_fields=fields)
        stamp = timezone.now().isoformat()
        transaction.on_commit(lambda: notify_visit_assignment(visit, f'visit-assigned:{visit.pk}:{user.pk}:{stamp}')
                              if visit.is_active else None)
    return result
