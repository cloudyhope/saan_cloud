"""Stable client-facing report content captured at visit completion."""
import hashlib
import json

from django.utils import timezone

from visit.models import Answer, Photo, VisitReportSnapshot


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
        'score': answer.score,
        'price': answer.price,
        'text': answer.text,
        'description': answer.description,
        'dropdown': answer.dropdown.answer if answer.dropdown else None,
        'radio': answer.radio.answer if answer.radio else None,
        'multichoice': [choice.answer for choice in answer.multichoice.all()],
    } for answer in rows]


def report_photos(visit):
    rows = Photo.objects.filter(
        visit=visit,
        type__project_id=visit.type.project_id,
        is_deleted=False,
    ).select_related('type').order_by('type_id', 'id')
    return [{
        'id': photo.pk,
        'type_id': photo.type_id,
        'type_name': photo.type.verbose_name or photo.type.name,
        'link': photo.link,
        'created_at': photo.datetime_created.isoformat() if photo.datetime_created else None,
    } for photo in rows]


def report_parts(visit):
    """Spare parts the warehouse fulfilled for this visit, frozen with the report."""
    from warehouse.models import PartRequest
    rows = PartRequest.objects.filter(visit=visit, status=PartRequest.FULFILLED).select_related(
        'ware__unit').order_by('id')
    return [{'name': row.ware.name_fa or row.ware.name_en or 'قطعه', 'amount': row.amount,
             'unit': (row.ware.unit.unit_fa or '') if row.ware.unit else ''} for row in rows]


def report_wage(visit):
    """The service fee is shown to the client only for service types that opt in."""
    return visit.total_wage if visit.type.show_wage_in_report and visit.total_wage else None


def capture_report_snapshot(visit, actor, source='completion', new_version=False):
    """Freeze the report once; a corrected re-completion (new_version) appends the next version."""
    existing = visit.report_snapshots.order_by('-version').first()
    if existing and not new_version:
        return existing
    payload = {
        'format': 2,
        'visit_id': visit.pk,
        'project_id': visit.type.project_id,
        'captured_at': timezone.now().isoformat(),
        'answers': report_answers(visit),
        'photos': report_photos(visit),
        'parts': report_parts(visit),
        'wage': report_wage(visit),
    }
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
    return VisitReportSnapshot.objects.create(
        visit=visit, version=existing.version + 1 if existing else 1, payload=payload, checksum=digest,
        source=source, created_by=actor,
    )
