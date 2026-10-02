import os

import boto3
import logging
from botocore.exceptions import ClientError
import uuid

from django.conf import settings
from django.core.files.storage import default_storage

logging.basicConfig(level=logging.INFO)


def uses_local_media():
    """Files live on a local volume: the local dev settings or LOCAL_MEDIA_STORAGE=true in production."""
    return settings.SETTINGS_MODULE == 'core.local_settings' or getattr(settings, 'LOCAL_MEDIA_STORAGE', False)


class ArvanStorage:
    def __init__(self, storage='general'):
        self.local = uses_local_media()
        if self.local:
            return

        if storage == 'general':
            self.bucket_key = os.environ.get('GENERAL_ARVAN_STORAGE_BUCKET_NAME')
            self.endpoint_address = os.environ.get('GENERAL_ARVAN_STORAGE_ADDRESS')
            self.public_address = os.environ.get('GENERAL_ARVAN_STORAGE_PUBLIC_ADDRESS')
            self.password = os.environ.get('GENERAL_ARVAN_STORAGE_PASSWORD')
            self.username = os.environ.get('GENERAL_ARVAN_STORAGE_USERNAME')
        elif storage == 'docs':
            self.bucket_key = os.environ.get('DOCS_ARVAN_STORAGE_BUCKET_NAME')
            self.endpoint_address = os.environ.get('DOCS_ARVAN_STORAGE_ADDRESS')
            self.public_address = os.environ.get('DOCS_ARVAN_STORAGE_PUBLIC_ADDRESS')
            self.password = os.environ.get('DOCS_ARVAN_STORAGE_PASSWORD')
            self.username = os.environ.get('DOCS_ARVAN_STORAGE_USERNAME')

        self.storage = self.connect()

        # self.bucket_name = os.environ.get(self.bucket_key, None)

    def connect(self):
        try:
            s3_resource = boto3.resource(
                's3',
                endpoint_url=self.endpoint_address,
                aws_access_key_id=self.username,
                aws_secret_access_key=self.password,
            )
            return s3_resource
        except Exception:
            logging.exception('Object storage connection failed')
            return None

    def put_file(self, file):
        if self.local:
            name = default_storage.save('uploads/' + str(uuid.uuid4()) + '-' + os.path.basename(file.name), file)
            return settings.MEDIA_PUBLIC_BASE_URL + default_storage.url(name)
        try:
            # if not settings.production:
            # self.endpoint_address = self.endpoint_address[:self.endpoint_address.rfind(
            #     '/')] + '/' + f"{os.environ.get('ARVAN_DOC_BUCKET_NAME_USERS_TEST')}" + self.endpoint_address[
            #                                                                             self.endpoint_address.rfind(
            #                                                                                 '/') + 1:]
            # bucket_name = os.environ.get('ARVAN_DOC_BUCKET_NAME_USERS_TSET')
            #     bucket_name = 'core-test'
            # bucket_name = os.environ.get('ARVAN_DOC_BUCKET_NAME_USERS')
            # bucket_name = 'core-bucket'
            bucket = self.storage.Bucket(self.bucket_key)
            myuuid = uuid.uuid4()
            key = str(myuuid) + "--" + os.path.basename(str(file))
            bucket.put_object(
                ACL='private',
                Body=file,
                Key=key,
            )
            return self.public_address + key
        # if not settings.production:
        #     if self.hidden:
        #         return f"{address}" + str(myuuid) + "--" + str(file)
        #     else:
        #         return "https://core-test.s3.ir-thr-at1.arvanstorage.com/" + str(myuuid) + "--" + str(file)
        # else:
        #     if self.hidden:
        #         return f"{address}" + str(myuuid) + "--" + str(file)
        #     else:
        #         return "https://core-bucket.s3.ir-thr-at1.arvanstorage.com/" + str(myuuid) + "--" + str(file)
        except ClientError as e:
            logging.error(e)
            return None

    def presigned_read_url(self, link, expires=300):
        if self.local or not self.storage or not self.public_address or not link.startswith(self.public_address):
            return None
        key = link[len(self.public_address):]
        if not key or key.startswith('/') or '..' in key.split('/'):
            return None
        return self.storage.meta.client.generate_presigned_url(
            'get_object', Params={'Bucket': self.bucket_key, 'Key': key},
            ExpiresIn=expires)
