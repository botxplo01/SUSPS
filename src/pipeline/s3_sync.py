from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Optional dependency; import only when needed
try:  # pragma: no cover - optional
    import boto3  # type: ignore
    from botocore.client import Config as _BotoConfig  # type: ignore
except Exception:  # pragma: no cover - optional
    boto3 = None  # type: ignore
    _BotoConfig = None  # type: ignore

from . import config as _cfg


def _truthy(val: Optional[str]) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on"}


def _client():  # pragma: no cover - network
    if boto3 is None:
        raise RuntimeError("boto3 is required for S3 sync; please install boto3")
    # Use explicit region if provided; otherwise rely on default resolution
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    session = boto3.session.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=region,
    )
    # Keep timeouts reasonable
    cfg = _BotoConfig(connect_timeout=10, read_timeout=30, retries={"max_attempts": 3})
    return session.client("s3", config=cfg)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sync_raw_from_s3() -> int:  # pragma: no cover - network
    """Download objects from AWS_S3_DATA_PREFIX into local data/raw/.

    Returns number of objects downloaded.
    """
    if not _truthy(os.getenv("USE_S3_STORAGE")):
        return 0
    bucket = os.getenv("AWS_BUCKET_NAME")
    prefix = os.getenv("AWS_S3_DATA_PREFIX", "") or ""
    if not bucket:
        raise RuntimeError("AWS_BUCKET_NAME is required when USE_S3_STORAGE is true")

    s3 = _client()

    dest_root = _cfg.RAW_DIR
    _ensure_dir(dest_root)

    # Paginate
    token = None
    total = 0
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        contents = resp.get("Contents", [])
        for obj in contents:
            key: str = obj.get("Key", "")
            if not key or key.endswith("/"):
                continue
            rel = key[len(prefix) :] if key.startswith(prefix) else key
            dest = dest_root / rel
            _ensure_dir(dest.parent)
            s3.download_file(bucket, key, str(dest))
            total += 1
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return total
