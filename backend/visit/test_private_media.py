from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile

from core.media_access import media_read_url
from core.storage import ArvanStorage


class LocalPrivateMediaTests(TestCase):
    def test_only_signed_local_upload_url_serves_bytes(self):
        with TemporaryDirectory() as directory, override_settings(
                SETTINGS_MODULE='core.local_settings', MEDIA_ROOT=directory, MEDIA_URL='/media/'):
            upload = Path(directory) / 'uploads' / 'picture.png'
            upload.parent.mkdir()
            upload.write_bytes(b'private-picture')
            request = RequestFactory().get('/')
            signed = media_read_url('http://localhost:18110/media/uploads/picture.png', request)
            self.assertIn('/core/api/media/', signed)
            response = self.client.get(signed)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'private-picture')
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertEqual(self.client.get('/media/uploads/picture.png').status_code, 404)
            self.assertEqual(self.client.get(signed + 'broken').status_code, 404)
            self.assertIsNone(media_read_url('https://foreign.example/private.png', request))
            self.assertIsNone(media_read_url('http://localhost:18110/media/uploads/../secret', request))

    @override_settings(SETTINGS_MODULE='core.settings')
    @patch.dict('os.environ', {
        'GENERAL_ARVAN_STORAGE_BUCKET_NAME': 'private-test',
        'GENERAL_ARVAN_STORAGE_ADDRESS': 'https://storage.example.test',
        'GENERAL_ARVAN_STORAGE_PUBLIC_ADDRESS': 'https://media.example.test/',
    })
    @patch.object(ArvanStorage, 'connect')
    def test_new_object_is_private_and_read_url_expires(self, connect):
        resource = Mock()
        connect.return_value = resource
        storage = ArvanStorage()
        link = storage.put_file(SimpleUploadedFile('picture.png', b'pixels'))
        self.assertTrue(link.startswith('https://media.example.test/'))
        self.assertEqual(resource.Bucket.return_value.put_object.call_args.kwargs['ACL'], 'private')
        resource.meta.client.generate_presigned_url.return_value = 'https://storage.example.test/signed'
        self.assertEqual(storage.presigned_read_url(link), 'https://storage.example.test/signed')
        self.assertEqual(resource.meta.client.generate_presigned_url.call_args.kwargs['ExpiresIn'], 300)
        self.assertIsNone(storage.presigned_read_url('https://other.example.test/picture.png'))
