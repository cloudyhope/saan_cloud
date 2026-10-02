"""Validate whole batches before changing project-owned visit records."""
from rest_framework.exceptions import PermissionDenied, ValidationError

from auth_app.models import Supervisor
from visit.asset_access import AssetAccess
from visit.models import Photo, Visit


def locked_project_batch(request, view, model, ids, allow_supervised_creator=False):
    access = AssetAccess(request, view)
    supervised_creator = (model is Visit and allow_supervised_creator
                          and 'supervised' in access.scopes)
    if not access.project_wide and not supervised_creator:
        raise PermissionDenied('این عملیات به دسترسی مدیریتی پروژه نیاز دارد.')
    if not ids or len(set(ids)) != len(ids):
        raise ValidationError({'ids': 'شناسه‌ها باید غیرخالی و یکتا باشند.'})
    if model is Visit:
        rows = Visit.objects.filter(is_deleted=False, type__project_id=access.project_id,
                                    building__project_id=access.project_id)
        if not access.project_wide:
            subordinate_ids = Supervisor.objects.filter(
                supervisor=request.user, project_id=access.project_id, is_active=True,
            ).values('promoter_id')
            rows = rows.filter(creator=request.user, promoter_id__in=subordinate_ids)
    elif model is Photo:
        rows = Photo.objects.filter(is_deleted=False, type__project_id=access.project_id,
                                    visit__type__project_id=access.project_id,
                                    visit__building__project_id=access.project_id,
                                    visit__is_deleted=False)
    else:
        raise ValueError('Unsupported batch model')
    locked = rows.select_for_update().filter(pk__in=ids)
    if locked.count() != len(ids):
        raise ValidationError({'ids': 'بخشی از رکوردها در پروژه مجاز وجود ندارند.'})
    return locked
