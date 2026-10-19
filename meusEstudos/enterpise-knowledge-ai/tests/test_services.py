import os
from uuid import uuid4

import boto3
import pytest
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError
from redis import Redis
from sqlalchemy import text

from app.config import settings
from app.db import engine
from app.storage import storage

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SERVICE_TESTS") != "1", reason="requires PostgreSQL, Redis and MinIO"
)


def test_postgresql_schema_and_vector():
    with engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM users")).scalar_one() >= 0
        distance = connection.execute(
            text("SELECT '[1,2,3]'::vector <=> '[1,2,3]'::vector")
        ).scalar_one()
        assert distance == pytest.approx(0, abs=1e-6)


def test_redis_connection():
    with Redis.from_url(settings().redis_url, socket_connect_timeout=3, socket_timeout=3) as client:
        assert client.ping()


def test_minio_roundtrip_and_private_access():
    target = storage()
    key = f"service-test/{uuid4()}"
    anonymous = boto3.client(
        "s3",
        endpoint_url=settings().s3_endpoint,
        config=Config(signature_version=UNSIGNED, connect_timeout=3, read_timeout=3),
    )
    try:
        target.put(key, b"synthetic connection test", "text/plain")
        result = target.client.get_object(Bucket=target.bucket, Key=key)
        with result["Body"] as body:
            assert body.read() == b"synthetic connection test"
        with pytest.raises(ClientError) as denied:
            anonymous.get_object(Bucket=target.bucket, Key=key)
        assert denied.value.response["Error"]["Code"] == "AccessDenied"
    finally:
        target.delete(key)
        anonymous.close()
