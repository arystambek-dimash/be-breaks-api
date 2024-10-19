from datetime import datetime
from random import randint

import boto3

from src.config import settings


def generate_key(author_role, _type, name):
    return author_role + "_" + _type + f'_{randint(0, 10000000)}_' + f'{datetime.timestamp(datetime.now())}_' + name


def upload_bytes(bytes_, key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    bucket_name = settings.AWS_BUCKET_NAME
    s3.upload_fileobj(
        bytes_,
        bucket_name,
        key
    )

    file_url = f'https://{bucket_name}.s3.amazonaws.com/{key}'
    return file_url


def upload_file(file_name, key):
    bucket = settings.AWS_BUCKET_NAME
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        print("Uploading file to S3")
        response = s3_client.upload_file(
            file_name,
            bucket,
            key
        )
        print("File in s3: ", response)
    except Exception as e:
        print(e)
        return

    file_url = f'https://{bucket}.s3.amazonaws.com/{key}'
    return file_url
