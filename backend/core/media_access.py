"""Short-lived read URLs for uploaded media; only scoped APIs may issue them."""
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.core import signing
from django.http import FileResponse, Http404
from django.urls import reverse
from django.views.decorators.http import require_GET

from core.storage import ArvanStorage, uses_local_media


MEDIA_SALT = 'saan-upload-read-v1'
MEDIA_TTL_SECONDS = 300


def _local_key(link):
    parsed = urlparse(link or '')
    base = urlparse(settings.MEDIA_PUBLIC_BASE_URL)
    # Only links this server issued (same scheme and host as MEDIA_PUBLIC_BASE_URL) count as local files.
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
        return None
    prefix = settings.MEDIA_URL.rstrip('/') + '/'
    if not parsed.path.startswith(prefix) or parsed.query or parsed.fragment:
        return None
    key = unquote(parsed.path[len(prefix):])
    path = Path(key)
    if not key.startswith('uploads/') or path.is_absolute() or '..' in path.parts or '\\' in key:
        return None
    return key


def media_read_url(link, request=None, storage='general'):
    if not link:
        return None
    if uses_local_media():
        key = _local_key(link)
        if key is None:
            return None
        token = signing.dumps(key, salt=MEDIA_SALT)
        path = reverse('LocalUploadedMediaReadView', args=[token])
        return request.build_absolute_uri(path) if request else path
    return ArvanStorage(storage=storage).presigned_read_url(link, expires=MEDIA_TTL_SECONDS)


@require_GET
def local_uploaded_media_read(request, token):
    if not uses_local_media():
        raise Http404
    try:
        key = signing.loads(token, salt=MEDIA_SALT, max_age=MEDIA_TTL_SECONDS)
    except signing.BadSignature:
        raise Http404
    if not isinstance(key, str) or not key.startswith('uploads/') or '..' in Path(key).parts or '\\' in key:
        raise Http404
    root = Path(settings.MEDIA_ROOT).resolve()
    path = (root / key).resolve()
    if root not in path.parents or not path.is_file():
        raise Http404
    response = FileResponse(path.open('rb'))
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
