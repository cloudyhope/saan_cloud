"""Server-side completion requirements for a field visit."""
from django.db.models import Count

from visit.models import Answer, Photo, PhotoType, Question, QuestionType


def _has_answer(answer, fields):
    if answer is None:
        return False
    for field in fields:
        if field == 'multichoice':
            if answer.multichoice.exists():
                return True
        elif field in ('dropdown', 'radio'):
            if getattr(answer, field + '_id') is not None:
                return True
        else:
            value = getattr(answer, field, None)
            if value is not None and (not isinstance(value, str) or value.strip()):
                return True
    return False


def completion_gaps(visit, supervision=False):
    """Return missing required question and photo IDs; False and zero count as answers."""
    question_types = list(QuestionType.objects.filter(
        visit_type=visit.type, project_id=visit.type.project_id,
        is_active=True, is_for_supervision=supervision,
    ))
    questions = list(Question.objects.filter(
        question_type__in=question_types, is_active=True,
    ).prefetch_related('answer_type'))
    questions_by_type = {}
    for question in questions:
        questions_by_type.setdefault(question.question_type_id, []).append(question)
    answers = {answer.question_id: answer for answer in Answer.objects.filter(
        visit=visit, question__in=questions,
    ).prefetch_related('multichoice').order_by('id')}
    missing_questions = []
    empty_required_types = []
    for question_type in question_types:
        rows = questions_by_type.get(question_type.pk, [])
        if question_type.is_mandatory and not rows:
            empty_required_types.append(question_type.pk)
        for question in rows:
            if not (question_type.is_mandatory or question.is_mandatory):
                continue
            fields = set(question.answer_type.values_list('field', flat=True))
            if not fields or not _has_answer(answers.get(question.pk), fields):
                missing_questions.append(question.pk)

    photo_types = list(PhotoType.objects.filter(
        visit_type=visit.type, project_id=visit.type.project_id,
        is_active=True, is_for_supervision=supervision,
    ))
    counts = dict(Photo.objects.filter(
        visit=visit, type__in=photo_types, is_deleted=False,
    ).values('type_id').annotate(total=Count('id')).values_list('type_id', 'total'))
    missing_photos = []
    for photo_type in photo_types:
        minimum = max(photo_type.min or 0, 1 if photo_type.is_mandatory else 0)
        if counts.get(photo_type.pk, 0) < minimum:
            missing_photos.append({'type': photo_type.pk, 'required': minimum, 'current': counts.get(photo_type.pk, 0)})
    return {
        'questions': missing_questions,
        'photo_types': missing_photos,
        'empty_required_question_types': empty_required_types,
    }
