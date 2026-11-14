# Roadmap: Review Analytics Pipeline

A batch data pipeline that turns raw e-commerce review data into an
analytics-ready warehouse for product quality monitoring, review behavior
analysis, and fake-review detection.

**Timeline:** 5 days
**Dataset:** Amazon Reviews 2023 (public), All_Beauty + Appliances
(2,830,133 reviews, 206,917 products)

---

## Tech Stack

| Layer | Local (default) | Cloud |
|---|---|---|
| Data lake | Local folder (`data/lake/`) | Amazon S3 |
| Transformation | DuckDB (SQL) | DuckDB / AWS Glue (stretch) |
| Storage format | Parquet, partitioned by category and year | Same |
| Warehouse | DuckDB | Amazon Redshift Serverless |
| Dashboard | Streamlit | Streamlit |
| Language | Python, SQL | Python, SQL |

Everything runs locally for free. Switching the lake to S3 is one setting
(`STORAGE=s3` in `.env`).

---

## Repo Structure

```
review-analytics-pipeline/
├── etl/
│   ├── sources.py         # dataset registry
│   ├── config.py          # settings and path layout
│   ├── storage.py         # local / S3 storage backends
│   ├── extract.py         # download + verify + land in lake
│   ├── explore.py         # data profiling
│   ├── transform.py       # clean, dedupe, write Parquet       (Day 2)
│   ├── quality.py         # data quality rules                 (Day 2)
│   └── load.py            # build star schema warehouse        (Day 3)
├── scripts/
│   ├── setup_storage.py
│   └── make_sample.py
├── sql/
│   ├── ddl/               # warehouse table definitions        (Day 3)
│   └── analytics/         # the 10 showcase queries            (Day 4)
├── dashboard/
│   └── app.py             # Streamlit app                      (Day 5)
├── data/sample/           # small committed sample
├── docs/
│   ├── data_profile.md    # raw data findings + decisions
│   └── QUERIES.md         # query docs                         (Day 4)
├── ROADMAP.md
└── README.md
```

---

## Day 1: Ingestion + Profiling ✅

**Goal:** Raw data in the lake and a clear picture of its quality.

- [x] Project structure, `.gitignore`, `requirements.txt`, `.env.example`
- [x] Source registry so new datasets plug in without code changes
- [x] Storage abstraction: local folder or S3 behind the same interface
- [x] Resumable downloads with automatic retries and exponential backoff
- [x] Gzip integrity check, line counts and SHA-256 recorded in a manifest
- [x] Raw files landed in `lake/raw/` with Hive-style partitions
- [x] DuckDB profiling across 15 checks -> `docs/data_profile.md`
- [x] Small committed sample with matching product rows

**Result:** 2,830,133 reviews and 206,917 products landed and verified.
Found 29,933 duplicate reviews, 2,785 empty reviews, 0 orphan reviews,
and low price coverage (15.7% Beauty, 49.5% Appliances).

---

## Day 2: Transform + Data Quality

**Goal:** Clean, partitioned Parquet in `lake/processed/`, bad rows in
`lake/rejected/`, and counts that reconcile exactly.

- [ ] Rename source-specific columns to generic ones
      (`parent_asin` -> `product_id`, etc.)
- [ ] Convert millisecond timestamps to proper dates
- [ ] Deduplicate reviews (same user + product + timestamp), keeping the
      row with the most helpful votes
- [ ] Add derived columns: `has_text`, `review_length`, `review_year`,
      `review_month`, `is_partial_year`
- [ ] Products: brand = `details.Brand` falling back to `store`,
      price as nullable number, `is_price_suspect` flag for prices under $1,
      `price_bucket`
- [ ] Quality rules in one place (`quality.py`), each with a name and reason
- [ ] Failed rows written to `lake/rejected/` with the rule that failed
- [ ] Write Parquet partitioned by `category` and `year`
- [ ] Reconciliation: raw rows = processed rows + rejected rows,
      checked against the manifest (2,830,133)
- [ ] Re-run profiling on Parquet and record the speedup vs raw JSON
- [ ] Test everything on the sample first

**Done when:** `processed/` holds clean Parquet, `rejected/` explains every
dropped row, and the reconciliation check passes.

---

## Day 3: Warehouse (Star Schema)

**Goal:** Analytics-ready tables built from the processed Parquet.

- [ ] DDL in `sql/ddl/`:
  - `fact_reviews`: rating, helpful_votes, verified_purchase, has_text,
    review_length, date_key, product_key, user_key
  - `dim_product`: title, brand, store, price, price_bucket, category
  - `dim_user`: first_review_date, total_reviews
  - `dim_date`: day, week, month, quarter, year, is_weekend
- [ ] `load.py` builds the warehouse from `processed/`
- [ ] Incremental loading: only new partitions are processed, tracked in a
      watermark table, so re-runs never create duplicates
- [ ] Row count checks between processed data and the fact table
- [ ] Stretch: same schema on Redshift Serverless

**Done when:** All tables are populated, counts match, and re-running the
load changes nothing.

---

## Day 4: Analytics Queries

**Goal:** 10 business queries that show advanced SQL, documented in
`docs/QUERIES.md`.

- [ ] Monthly average rating and % negative reviews per category, with
      month-over-month change (`LAG`)
- [ ] Top 5 products per category by review volume (`ROW_NUMBER`)
- [ ] Rolling 90-day average rating per product (window frames)
- [ ] Product review retention: of products first reviewed in a month,
      how many still get reviews 3, 6 and 12 months later
- [ ] Product review streaks: longest run of consecutive months with
      reviews (gaps-and-islands)
- [ ] Rating drift: products whose last-90-day rating fell 1+ star below
      their lifetime average
- [ ] Verified vs unverified rating gap per category and year
- [ ] Helpfulness percentiles (`NTILE`) vs review length
- [ ] Price bucket vs rating and % negative (Appliances-focused)
- [ ] Review spike detection: days with 3x+ a product's average volume
      (possible fake-review bursts)

Each query in `QUERIES.md`: business question, SQL, sample result,
one-line insight.

**Done when:** All 10 run on the full data and are documented.

---

## Day 5: Dashboard + Documentation

**Goal:** Demoable and understandable in 60 seconds.

- [ ] Streamlit dashboard:
  - Category rating and % negative trends
  - Rating drift alerts
  - Review spike alerts
  - Verified vs unverified comparison
- [ ] README: architecture diagram, how to run, key findings with real
      numbers, design decisions, JSON vs Parquet benchmark
- [ ] Screenshots of the dashboard
- [ ] Stretch: deploy the lake to S3 and document it

**Done when:** A stranger understands the project from the README alone.

---

## Stretch Goals

- [ ] Orchestration with Airflow or Prefect
- [ ] Same transform in PySpark for comparison
- [ ] CI with GitHub Actions running quality checks on the sample
- [ ] SCD Type 2 on `dim_product` for price changes
- [ ] Add more categories and benchmark how the pipeline scales