"""Local-volume media in production: links are issued under MEDIA_PUBLIC_BASE_URL and only those are signable."""
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from core.media_access import _local_key, local_uploaded_media_read, media_read_url
from core.storage import ArvanStorage


@override_settings(MEDIA_PUBLIC_BASE_URL='https://webapi.saanapp.ir', MEDIA_URL='/media/', LOCAL_MEDIA_STORAGE=True)
class LocalMediaBaseUrlTests(SimpleTestCase):
    def test_only_links_of_this_server_are_local_keys(self):
        self.assertEqual(_local_key('https://webapi.saanapp.ir/media/uploads/a-b.png'), 'uploads/a-b.png')
        for link in ('http://webapi.saanapp.ir/media/uploads/a.png', 'https://evil.example/media/uploads/a.png',
                     'https://webapi.saanapp.ir/media/other/a.png', 'https://webapi.saanapp.ir/media/uploads/../x.png',
                     'https://webapi.saanapp.ir/media/uploads/a.png?x=1', 'http://localhost:18110/media/uploads/a.png', '', None):
            self.assertIsNone(_local_key(link), link)

    def test_upload_returns_an_absolute_link_that_is_signed_for_reading(self):
        with tempfile.TemporaryDirectory() as root, override_settings(MEDIA_ROOT=root):
            link = ArvanStorage().put_file(SimpleUploadedFile('photo.png', b'\x89PNG data'))
            self.assertTrue(link.startswith('https://webapi.saanapp.ir/media/uploads/'), link)
            request = APIRequestFactory().get('/')
            url = media_read_url(link, request)
            self.assertIn('/core/api/media/', url)
            token = url.rstrip('/').rsplit('/', 1)[-1]
            response = local_uploaded_media_read(request, token)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertEqual(b''.join(response.streaming_content), b'\x89PNG data')
            self.assertTrue(any(Path(root, 'uploads').iterdir()))
