"""File storage abstraction: Cloudflare R2 (S3-compatible) when configured,
falls back to local disk under DATA_DIR for local development.
"""
from __future__ import annotations
import os
import mimetypes

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME")

USE_R2 = bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME)

_client = None


def _get_client():
    global _client
    if _client is None:
        import boto3
        from botocore.client import Config
        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


def save_file(key: str, content: bytes) -> None:
    if USE_R2:
        content_type = mimetypes.guess_type(key)[0] or "application/octet-stream"
        _get_client().put_object(Bucket=R2_BUCKET_NAME, Key=key, Body=content, ContentType=content_type)
    else:
        from .database import DATA_DIR
        path = os.path.join(DATA_DIR, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)


def read_file(key: str) -> bytes | None:
    if USE_R2:
        try:
            obj = _get_client().get_object(Bucket=R2_BUCKET_NAME, Key=key)
            return obj["Body"].read()
        except Exception:
            return None
    else:
        from .database import DATA_DIR
        path = os.path.join(DATA_DIR, key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()


def delete_file(key: str) -> None:
    if USE_R2:
        try:
            _get_client().delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        except Exception:
            pass
    else:
        from .database import DATA_DIR
        path = os.path.join(DATA_DIR, key)
        if os.path.exists(path):
            os.remove(path)


def image_key(record_id: int, filename: str) -> str:
    return f"procedure_images/{record_id}/{filename}"
