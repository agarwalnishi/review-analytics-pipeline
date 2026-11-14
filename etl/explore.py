"""Profile the raw data with DuckDB and write docs/data_profile.md.

Usage:
    python -m etl.explore            # full downloaded data
    python -m etl.explore --sample   # small sample in data/sample

DuckDB reads the gzipped JSONL directly (no loading step), and the category
comes from the hive-style folder name. Everything this finds becomes a rule in
Day 2's transform + quality checks, so read the report before writing transform.py.
"""

import argparse
import time
from datetime import datetime

import duckdb

from etl import config

REVIEW_COLUMNS = """{
    'rating': 'DOUBLE', 'title': 'VARCHAR', 'text': 'VARCHAR',
    'asin': 'VARCHAR', 'parent_asin': 'VARCHAR', 'user_id': 'VARCHAR',
    'timestamp': 'BIGINT', 'helpful_vote': 'BIGINT', 'verified_purchase': 'BOOLEAN'
}"""

# price is read as text on purpose: it isn't always a clean number in the source.
PRODUCT_COLUMNS = """{
    'parent_asin': 'VARCHAR', 'main_category': 'VARCHAR', 'title': 'VARCHAR',
    'average_rating': 'DOUBLE', 'rating_number': 'BIGINT', 'price': 'VARCHAR',
    'store': 'VARCHAR', 'categories': 'VARCHAR[]', 'details': 'JSON'
}"""

CHECKS = [
    ("Volume per category", """
        SELECT category,
               count(*)                    AS reviews,
               count(DISTINCT user_id)     AS users,
               count(DISTINCT parent_asin) AS products
        FROM reviews GROUP BY category ORDER BY category
    """),
    ("Date range", """
        SELECT category,
               min(review_ts)::DATE AS first_review,
               max(review_ts)::DATE AS last_review
        FROM reviews GROUP BY category ORDER BY category
    """),
    ("Reviews per year", """
        SELECT year(review_ts)::VARCHAR AS year, category, count(*) AS reviews
        FROM reviews GROUP BY ALL ORDER BY year, category
    """),
    ("Rating distribution", """
        SELECT rating,
               count(*) AS reviews,
               round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct
        FROM reviews GROUP BY rating ORDER BY rating
    """),
    ("Data quality red flags (Day 2 rules come from here)", """
        SELECT
            count(*) FILTER (WHERE user_id IS NULL OR user_id = '')                 AS null_user_id,
            count(*) FILTER (WHERE parent_asin IS NULL OR parent_asin = '')         AS null_parent_asin,
            count(*) FILTER (WHERE rating IS NULL OR rating NOT BETWEEN 1 AND 5)    AS bad_rating,
            count(*) FILTER (WHERE "timestamp" IS NULL)                             AS null_timestamp,
            count(*) FILTER (WHERE review_ts > now())                               AS future_dates,
            count(*) FILTER (WHERE text IS NULL OR trim(text) = '')                 AS empty_text,
            count(*) FILTER (WHERE helpful_vote < 0)                                AS negative_votes
        FROM reviews
    """),
    ("Exact duplicates (same user + product + timestamp)", """
        SELECT count(*) AS duplicate_groups, coalesce(sum(n - 1), 0) AS extra_rows
        FROM (
            SELECT user_id, parent_asin, "timestamp", count(*) AS n
            FROM reviews GROUP BY ALL HAVING count(*) > 1
        )
    """),
    ("Verified purchase share", """
        SELECT category,
               round(100.0 * avg(verified_purchase::INT), 2) AS verified_pct,
               round(avg(rating) FILTER (WHERE verified_purchase), 3)     AS avg_rating_verified,
               round(avg(rating) FILTER (WHERE NOT verified_purchase), 3) AS avg_rating_unverified
        FROM reviews GROUP BY category ORDER BY category
    """),
    ("Helpful votes", """
        SELECT round(100.0 * avg((helpful_vote = 0)::INT), 2) AS pct_zero_votes,
               quantile_cont(helpful_vote, 0.5)  AS p50,
               quantile_cont(helpful_vote, 0.9)  AS p90,
               quantile_cont(helpful_vote, 0.99) AS p99,
               max(helpful_vote) AS max
        FROM reviews
    """),
    ("Review text length (characters)", """
        SELECT quantile_cont(length(text), 0.5)  AS p50,
               quantile_cont(length(text), 0.9)  AS p90,
               quantile_cont(length(text), 0.99) AS p99,
               max(length(text)) AS max
        FROM reviews
    """),
    ("Most active reviewers (possible bots)", """
        SELECT user_id, count(*) AS reviews, round(avg(rating), 2) AS avg_rating
        FROM reviews GROUP BY user_id ORDER BY reviews DESC LIMIT 5
    """),
    ("Orphan reviews (product missing from product data)", """
        SELECT r.category,
               count(*) AS orphan_reviews,
               round(100.0 * count(*) / any_value(t.total), 2) AS pct
        FROM reviews r
        ANTI JOIN products m ON r.parent_asin = m.parent_asin
        JOIN (SELECT category, count(*) AS total FROM reviews GROUP BY category) t USING (category)
        GROUP BY r.category ORDER BY r.category
    """),
    ("Products: duplicate product rows", """
        SELECT count(*) - count(DISTINCT parent_asin) AS duplicate_products FROM products
    """),
    ("Products: field coverage", """
        SELECT category,
               count(*) AS products,
               round(100.0 * avg((TRY_CAST(price AS DOUBLE) IS NOT NULL)::INT), 1) AS has_price_pct,
               round(100.0 * avg((nullif(trim(store), '') IS NOT NULL)::INT), 1) AS has_store_pct,
               round(100.0 * avg((json_extract_string(details, '$.Brand') IS NOT NULL)::INT), 1) AS has_brand_pct
        FROM products GROUP BY category ORDER BY category
    """),
    ("Products: price values that aren't numbers", """
        SELECT price, count(*) AS products
        FROM products
        WHERE price IS NOT NULL AND TRY_CAST(price AS DOUBLE) IS NULL
        GROUP BY price ORDER BY products DESC LIMIT 10
    """),
    ("Products: price distribution", """
        SELECT category,
               min(p) AS min, quantile_cont(p, 0.25) AS p25, quantile_cont(p, 0.5) AS p50,
               quantile_cont(p, 0.75) AS p75, quantile_cont(p, 0.99) AS p99, max(p) AS max
        FROM (SELECT category, TRY_CAST(price AS DOUBLE) AS p FROM products)
        WHERE p IS NOT NULL GROUP BY category ORDER BY category
    """),
]


def to_markdown(columns: list[str], rows: list[tuple]) -> str:
    def fmt(v):
        if v is None:
            return "NULL"
        if isinstance(v, float):
            return f"{v:,.2f}"
        if isinstance(v, int):
            return f"{v:,}"
        return str(v).replace("|", "\\|")

    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="profile data/sample instead of data/downloads")
    args = parser.parse_args()

    base = (config.SAMPLE_DIR if args.sample else config.DOWNLOAD_DIR) / config.SOURCE
    reviews_glob = (base / "reviews" / "*" / "*.jsonl.gz").as_posix()
    products_glob = (base / "products" / "*" / "*.jsonl.gz").as_posix()

    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW reviews AS
        SELECT *, to_timestamp("timestamp" / 1000) AS review_ts
        FROM read_json('{reviews_glob}', format = 'newline_delimited',
                       hive_partitioning = true, columns = {REVIEW_COLUMNS})
    """)
    con.execute(f"""
        CREATE VIEW products AS
        SELECT * FROM read_json('{products_glob}', format = 'newline_delimited',
                                hive_partitioning = true, columns = {PRODUCT_COLUMNS})
    """)

    report = [
        "# Raw Data Profile",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} by `etl/explore.py` "
        f"on `{base.relative_to(config.ROOT)}` ({'sample' if args.sample else 'full data'}).",
        "",
    ]
    for title, sql in CHECKS:
        start = time.perf_counter()
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        elapsed = time.perf_counter() - start
        print(f"\n== {title} ({elapsed:.1f}s)")
        print(to_markdown(cols, rows))
        report += [f"## {title}", "", to_markdown(cols, rows), ""]

    report += [
        "## Decisions for Day 2",
        "",
        "Fill this in after reading the tables above:",
        "",
        "- Duplicates: ",
        "- Orphan reviews: ",
        "- Price parsing: ",
        "- Brand source (details.Brand vs store): ",
        "- Other: ",
        "",
    ]

    config.DOCS_DIR.mkdir(exist_ok=True)
    out = config.DOCS_DIR / "data_profile.md"
    out.write_text("\n".join(report))
    print(f"\nReport written to {out.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()