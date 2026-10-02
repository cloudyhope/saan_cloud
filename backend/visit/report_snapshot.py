"""Stable client-facing report content captured at visit completion."""
import hashlib
import json

from django.utils import timezone

from visit.models import Answer, VisitReportSnapshot


def report_answers(visit):
    rows = Answer.objects.filter(
        visit=visit,
        question__question_type__project_id=visit.type.project_id,
        question__question_type__visit_type=visit.type,
    ).select_related('question', 'dropdown', 'radio').prefetch_related('multichoice').order_by(
        'question__question_type_id', 'question_id', 'id')
    return [{
        'question': answer.question.text,
        'bool': answer.bool,
        'number': answer.number,
        'text': answer.text,
        'description': answer.description,
        'dropdown': answer.dropdown.answer if answer.dropdown else None,
        'radio': answer.radio.answer if answer.radio else None,
        'multichoice': [choice.answer for choice in answer.multichoice.all()],
    } for answer in rows]


def capture_report_snapshot(visit, actor, source='completion'):
    existing = visit.report_snapshots.order_by('-version').first()
    if existing:
        return existing
    payload = {
        'format': 1,
        'visit_id': visit.pk,
        'project_id': visit.type.project_id,
        'captured_at': timezone.now().isoformat(),
        'answers': report_answers(visit),
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
    return VisitReportSnapshot.objects.create(
        visit=visit, version=1, payload=payload, checksum=digest, source=source, created_by=actor,
    )
