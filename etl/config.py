"""Central config: which source, which storage, and where every file lives."""

import os
from pathlib import Path

from dotenv import load_dotenv

from etl.sources import SOURCES

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---- which dataset ----
SOURCE = os.getenv("SOURCE", "amazon_reviews_2023")
if SOURCE not in SOURCES:
    raise SystemExit(f"Unknown SOURCE '{SOURCE}'. Options: {', '.join(SOURCES)}")
SOURCE_CFG = SOURCES[SOURCE]
KINDS = tuple(SOURCE_CFG["files"])  # e.g. ("reviews", "products")

_env_categories = os.getenv("CATEGORIES", "")
CATEGORIES = [c.strip() for c in _env_categories.split(",") if c.strip()] or SOURCE_CFG["categories"]

# ---- where things live ----
DATA_DIR = ROOT / "data"
DOWNLOAD_DIR = DATA_DIR / "downloads"   # local cache of source files
LAKE_DIR = DATA_DIR / "lake"            # local data lake (used when STORAGE=local)
SAMPLE_DIR = DATA_DIR / "sample"        # small committed sample
DOCS_DIR = ROOT / "docs"
MANIFEST_PATH = DOWNLOAD_DIR / SOURCE / "manifest.json"
LAKE_ZONES = ("raw/", "processed/", "rejected/", "query-results/")

# ---- storage backend ----
STORAGE = os.getenv("STORAGE", "local").lower()   # "local" or "s3"
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_PROFILE = os.getenv("AWS_PROFILE") or None
S3_BUCKET = os.getenv("S3_BUCKET")


def file_name(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def source_url(kind: str, category: str) -> str:
    return SOURCE_CFG["files"][kind].format(category=category)


def relative_path(kind: str, category: str) -> str:
    """Same layout everywhere: <source>/<kind>/category=<category>/<file>"""
    return f"{SOURCE}/{kind}/category={category}/{file_name(source_url(kind, category))}"


def download_path(kind: str, category: str, base: Path = DOWNLOAD_DIR) -> Path:
    return base / relative_path(kind, category)


def raw_key(kind: str, category: str) -> str:
    return f"raw/{relative_path(kind, category)}"