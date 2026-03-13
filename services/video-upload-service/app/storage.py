import boto3
from botocore.exceptions import ClientError

from app.config import settings

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    region_name="us-east-1",
)


def ensure_bucket_exists():
    try:
        s3_client.head_bucket(Bucket=settings.MINIO_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=settings.MINIO_BUCKET)


def upload_file(file_obj, filename: str, content_type: str) -> bool:
    try:
        s3_client.upload_fileobj(
            file_obj,
            settings.MINIO_BUCKET,
            filename,
            ExtraArgs={"ContentType": content_type},
        )
        return True
    except ClientError:
        return False
