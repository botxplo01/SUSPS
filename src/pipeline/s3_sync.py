from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple, Dict, List

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


def _bucket_and_prefix() -> Tuple[str, str]:
    bucket = os.getenv("AWS_BUCKET_NAME") or ""
    prefix = os.getenv("AWS_S3_DATA_PREFIX", "") or ""
    if not bucket:
        raise RuntimeError("AWS_BUCKET_NAME is required")
    return bucket, prefix


def sync_raw_from_s3() -> int:  # pragma: no cover - network
    """Download objects from AWS_S3_DATA_PREFIX into local data/raw/.

    Returns number of objects downloaded.
    """
    if not _truthy(os.getenv("USE_S3_STORAGE")):
        return 0
    bucket, prefix = _bucket_and_prefix()
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


def _list_s3_keys() -> Dict[str, int]:  # pragma: no cover - network
    bucket, prefix = _bucket_and_prefix()
    s3 = _client()
    keys: Dict[str, int] = {}
    token = None
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
            rel = key[len(prefix) :] if prefix and key.startswith(prefix) else key
            size = int(obj.get("Size", 0))
            keys[rel] = size
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys


def diff_raw_vs_s3() -> Tuple[List[str], List[str]]:  # pragma: no cover - network
    """Return (missing_on_s3, size_mismatch) relative to data/raw/.

    Size mismatch is a heuristic for changed files; for true parity you can force re-upload.
    """
    root = _cfg.RAW_DIR
    local: Dict[str, int] = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(root)).replace("\\", "/")
            local[rel] = p.stat().st_size
    remote = _list_s3_keys()
    missing = [k for k in local.keys() if k not in remote]
    mismatch = [k for k, sz in local.items() if k in remote and remote[k] != sz]
    return missing, mismatch


def sync_raw_to_s3(dry_run: bool = False) -> Tuple[int, int]:  # pragma: no cover - network
    """Upload missing/changed files in data/raw/ to S3 prefix.

    Returns (uploaded_files, skipped_files).
    """
    bucket, prefix = _bucket_and_prefix()
    s3 = _client()
    missing, mismatch = diff_raw_vs_s3()
    to_upload = sorted(set(missing + mismatch))
    uploaded = 0
    for rel in to_upload:
        src = _cfg.RAW_DIR / rel
        key = f"{prefix}{rel}" if prefix else rel
        if dry_run:
            print(f"DRY-RUN upload: {src} -> s3://{bucket}/{key}")
            continue
        _ensure_dir(src.parent)
        s3.upload_file(str(src), bucket, key)
        uploaded += 1
    return uploaded, 0


if __name__ == "__main__":  # pragma: no cover - utility CLI
    import argparse

    ap = argparse.ArgumentParser(description="S3 sync tools for data/raw")
    ap.add_argument("--check", action="store_true", help="List missing/changed files on S3")
    ap.add_argument("--push", action="store_true", help="Upload missing/changed files to S3")
    ap.add_argument("--pull", action="store_true", help="Download from S3 to data/raw")
    ap.add_argument("--dry-run", action="store_true", help="Do not perform writes (for push)")
    args = ap.parse_args()

    if args.check:
        miss, mis = diff_raw_vs_s3()
        if not miss and not mis:
            print("S3 is in sync with data/raw")
        else:
            if miss:
                print("Missing on S3:")
                for m in miss:
                    print(f"  {m}")
            if mis:
                print("Changed size (re-upload recommended):")
                for m in mis:
                    print(f"  {m}")
    if args.push:
        up, _ = sync_raw_to_s3(dry_run=args.dry_run)
        print(f"Uploaded {up} files")
    if args.pull:
        n = sync_raw_from_s3()
        print(f"Downloaded {n} objects")
