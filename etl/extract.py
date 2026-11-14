"""Extract: download source files, verify them, and land them untouched in the lake's raw zone.

Usage (from repo root):
    python -m etl.extract                    # download + land in the lake
    python -m etl.extract --download-only    # just download and verify
    python -m etl.extract --categories All_Beauty
"""

import argparse
import gzip
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from tqdm import tqdm

from etl import config
from etl.storage import get_storage

log = logging.getLogger("extract")
CHUNK = 1 << 20  # 1 MB


# ---------- PART A: download with resume ----------
def download(url: str, dest: Path, force: bool = False) -> Path:
    if dest.exists() and not force:
        log.info("Already downloaded: %s", dest.name)
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    if force and tmp.exists():
        tmp.unlink()

    resume_from = tmp.stat().st_size if tmp.exists() else 0
    headers = {"Range": f"bytes={resume_from}-"} if resume_from else {}

    with requests.get(url, stream=True, headers=headers, timeout=60) as r:
        if r.status_code == 416:
            log.info("Partial file already complete: %s", tmp.name)
        else:
            r.raise_for_status()
            if resume_from and r.status_code != 206:
                log.warning("Server ignored resume request, restarting %s", dest.name)
                resume_from = 0
            total = int(r.headers.get("Content-Length", 0)) + resume_from
            mode = "ab" if resume_from else "wb"
            with open(tmp, mode) as f, tqdm(
                total=total or None, initial=resume_from, unit="B",
                unit_scale=True, desc=dest.name,
            ) as bar:
                for chunk in r.iter_content(chunk_size=CHUNK):
                    f.write(chunk)
                    bar.update(len(chunk))

    tmp.rename(dest)
    return dest


# ---------- PART B: verify the file ----------
def inspect_file(path: Path) -> dict:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            sha.update(block)

    lines = 0
    try:
        with gzip.open(path, "rb") as g:
            for _ in g:
                lines += 1
    except (EOFError, OSError) as e:
        raise RuntimeError(f"{path.name} is corrupt or truncated ({e}). Delete it and re-run.") from e

    return {"bytes": path.stat().st_size, "lines": lines, "sha256": sha.hexdigest()}


# ---------- PART C: manifest (a receipt of every file) ----------
def load_manifest() -> dict:
    if config.MANIFEST_PATH.exists():
        return json.loads(config.MANIFEST_PATH.read_text())
    return {"source": config.SOURCE, "files": {}}


def save_manifest(manifest: dict) -> None:
    config.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    config.MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


# ---------- PART D: tie it together ----------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", nargs="+", default=config.CATEGORIES)
    parser.add_argument("--download-only", action="store_true", help="don't write to the lake")
    parser.add_argument("--force", action="store_true", help="re-download even if the file exists")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("Source: %s | Storage: %s", config.SOURCE, config.STORAGE)

    manifest = load_manifest()
    storage = None if args.download_only else get_storage()

    for category in args.categories:
        for kind in config.KINDS:
            url = config.source_url(kind, category)
            path = download(url, config.download_path(kind, category), force=args.force)

            entry = f"{kind}/{category}"
            info = manifest["files"].get(entry)
            if not info or info.get("bytes") != path.stat().st_size:
                log.info("Verifying %s", path.name)
                info = inspect_file(path)
                info.update(category=category, kind=kind, source_url=url,
                            raw_key=config.raw_key(kind, category))
                manifest["files"][entry] = info
                save_manifest(manifest)
            log.info("%s: %s lines, %.1f MB", entry, f"{info['lines']:,}", info["bytes"] / 1e6)

            if storage:
                key = config.raw_key(kind, category)
                if storage.exists(key, info["bytes"]):
                    log.info("Already in lake, skipping: %s", storage.uri(key))
                else:
                    storage.put(path, key, {"line-count": info["lines"], "sha256": info["sha256"]})
                    log.info("Landed: %s", storage.uri(key))

    if storage:
        storage.put(config.MANIFEST_PATH, f"raw/{config.SOURCE}/manifest.json", {})
    log.info("Done.")


if __name__ == "__main__":
    main()