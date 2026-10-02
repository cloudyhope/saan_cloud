"""Local-only settings for running the Saan API without a MinIO server."""

from .settings import *  # noqa: F403

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
MEDIA_ROOT = BASE_DIR / "local_media"  # noqa: F405
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / "local_static"  # noqa: F405

# The field app sends this header from a separate localhost origin.
CORS_ALLOW_HEADERS = [*CORS_ALLOW_HEADERS, "saanapp-client"]  # noqa: F405
