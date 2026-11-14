"""Storage backends for the data lake.

The pipeline only ever calls get_storage().put(...) / .exists(...), so it doesn't
care whether the lake is a folder on your laptop or an S3 bucket. Adding GCS or
Azure Blob later means writing one more small class here.
"""

import logging
import os
import shutil
from pathlib import Path

from etl import config

log = logging.getLogger("storage")


class LocalStorage:
    """A folder on disk that behaves like a bucket: data/lake/raw/..., data/lake/processed/..."""

    def __init__(self, root: Path = config.LAKE_DIR):
        self.root = root

    def setup(self) -> None:
        for zone in config.LAKE_ZONES:
            (self.root / zone).mkdir(parents=True, exist_ok=True)
        log.info("Local lake ready at %s", self.root.relative_to(config.ROOT))

    def exists(self, key: str, size: int) -> bool:
        path = self.root / key
        return path.exists() and path.stat().st_size == size

    def put(self, local_file: Path, key: str, metadata: dict) -> None:
        dest = self.root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        try:
            os.link(local_file, dest)       # hard link: no extra disk space used
        except OSError:
            shutil.copy2(local_file, dest)  # different drive: fall back to a real copy

    def uri(self, key: str) -> str:
        return str(self.root / key)


class S3Storage:
    def __init__(self):
        import boto3

        if not config.S3_BUCKET:
            raise SystemExit("STORAGE=s3 but S3_BUCKET is not set in .env")
        self.bucket = config.S3_BUCKET
        session = boto3.Session(profile_name=config.AWS_PROFILE, region_name=config.AWS_REGION)
        self.s3 = session.client("s3")

    def setup(self) -> None:
        from botocore.exceptions import ClientError

        try:
            kwargs = {"Bucket": self.bucket}
            if config.AWS_REGION != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": config.AWS_REGION}
            self.s3.create_bucket(**kwargs)
            log.info("Created bucket %s in %s", self.bucket, config.AWS_REGION)
        except ClientError as e:
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise
            log.info("Bucket %s already exists (yours), continuing", self.bucket)

        self.s3.put_public_access_block(
            Bucket=self.bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True, "IgnorePublicAcls": True,
                "BlockPublicPolicy": True, "RestrictPublicBuckets": True,
            },
        )
        self.s3.put_bucket_tagging(
            Bucket=self.bucket,
            Tagging={"TagSet": [{"Key": "project", "Value": "review-analytics-pipeline"}]},
        )
        self.s3.put_bucket_lifecycle_configuration(
            Bucket=self.bucket,
            LifecycleConfiguration={"Rules": [
                {"ID": f"expire-{z.rstrip('/')}", "Filter": {"Prefix": z},
                 "Status": "Enabled", "Expiration": {"Days": 30}}
                for z in ("rejected/", "query-results/")
            ]},
        )
        for zone in config.LAKE_ZONES:
            self.s3.put_object(Bucket=self.bucket, Key=zone)
        log.info("Bucket ready: private, tagged, zones %s", ", ".join(config.LAKE_ZONES))

    def exists(self, key: str, size: int) -> bool:
        from botocore.exceptions import ClientError

        try:
            return self.s3.head_object(Bucket=self.bucket, Key=key)["ContentLength"] == size
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    def put(self, local_file: Path, key: str, metadata: dict) -> None:
        from tqdm import tqdm

        size = local_file.stat().st_size
        with tqdm(total=size, unit="B", unit_scale=True, desc=f"upload {local_file.name}") as bar:
            self.s3.upload_file(
                str(local_file), self.bucket, key,
                ExtraArgs={"Metadata": {k: str(v) for k, v in metadata.items()}},
                Callback=bar.update,
            )

    def uri(self, key: str) -> str:
        return f"s3://{self.bucket}/{key}"


def get_storage():
    if config.STORAGE == "local":
        return LocalStorage()
    if config.STORAGE == "s3":
        return S3Storage()
    raise SystemExit(f"Unknown STORAGE '{config.STORAGE}'. Use 'local' or 's3'.")