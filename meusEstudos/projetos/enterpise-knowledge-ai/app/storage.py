import boto3

from .config import settings


class S3Storage:
    def __init__(self) -> None:
        cfg = settings()
        self.bucket = cfg.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=cfg.s3_endpoint,
            aws_access_key_id=cfg.s3_access_key,
            aws_secret_access_key=cfg.s3_secret_key,
        )

    def put(self, key: str, body: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType=content_type)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


storage = S3Storage
