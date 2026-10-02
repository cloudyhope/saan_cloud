import os

import boto3
import logging
from botocore.exceptions import ClientError
import uuid

logging.basicConfig(level=logging.INFO)


class ArvanStorage:
    def __init__(self):

        self.bucket_key = os.environ.get('GENERAL_ARVAN_STORAGE_BUCKET_NAME')
        self.endpoint_address = os.environ.get('GENERAL_ARVAN_STORAGE_ADDRESS')
        self.public_address = os.environ.get('GENERAL_ARVAN_STORAGE_PUBLIC_ADDRESS')
        self.password = os.environ.get('GENERAL_ARVAN_STORAGE_PASSWORD')
        self.username = os.environ.get('GENERAL_ARVAN_STORAGE_USERNAME')

        self.storage = self.connect()

        print("storage", self.storage, type(self.storage))

    def connect(self):
        try:
            s3_resource = boto3.resource(
                's3',
                endpoint_url=self.endpoint_address,
                aws_access_key_id=self.username,
                aws_secret_access_key=self.password,
            )
            return s3_resource
        except Exception as exc:
            logging.info(exc)

    def put_file(self, file):
        try:
            bucket = self.storage.Bucket(self.bucket_key)
            myuuid = uuid.uuid4()
            bucket.put_object(
                ACL='private',
                Body=file,
                Key=str(myuuid) + "--" + str(file)
            )
            return self.public_address + str(myuuid) + "--" + str(file)
        except ClientError as e:
            logging.error(e)
            return None
