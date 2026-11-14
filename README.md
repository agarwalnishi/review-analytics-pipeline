# Review Analytics Pipeline

A batch data pipeline that turns raw e-commerce review data into an
analytics-ready warehouse for product quality monitoring, customer
retention analysis, and fake-review detection.

- **Source-agnostic:** datasets plug in through a registry (`etl/sources.py`)
- **Storage-agnostic:** runs fully locally, or on AWS S3 by changing one setting
- **Reproducible:** every raw file is verified and recorded in a manifest
  (line count + SHA-256) so loads can be reconciled end to end

Currently loaded: Amazon Reviews 2023 public dataset (All_Beauty and
Appliances, ~2.8M reviews).

> Status: in progress. See [ROADMAP.md](ROADMAP.md).

## Architecture

```
source ──> extract.py ──> lake/raw ──> transform ──> lake/processed (Parquet) ──> warehouse ──> dashboard
                                            │
                                            └──> lake/rejected (failed quality checks)
```

## Project Structure

```
etl/
  sources.py        dataset registry
  config.py         settings and path layout
  storage.py        local / S3 storage backends
  extract.py        resumable download, verification, landing in the lake
  explore.py        DuckDB profiling -> docs/data_profile.md
scripts/
  setup_storage.py  one-time lake setup
  make_sample.py    small committed sample
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env

python -m scripts.setup_storage
python -m etl.extract
python -m etl.explore
```

No cloud account? Run `python -m etl.explore --sample` on the committed sample.

## Data Profile

[docs/data_profile.md](docs/data_profile.md) lists what the raw data
looks like (duplicates, orphan reviews, price quality, field coverage)
and the cleaning decisions that came from it.