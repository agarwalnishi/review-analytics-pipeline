"""Build a small, committed sample (data/sample/) from the downloaded files.

Usage:  python -m scripts.make_sample --rows 5000

Takes the first N reviews per category, then keeps only the product rows those
reviews point to, so joins still work on the sample.
"""

import argparse
import gzip
import json

from etl import config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=5000)
    args = parser.parse_args()

    for category in config.CATEGORIES:
        src = config.download_path("reviews", category)
        dst = config.download_path("reviews", category, base=config.SAMPLE_DIR)
        dst.parent.mkdir(parents=True, exist_ok=True)

        product_ids, written = set(), 0
        with gzip.open(src, "rt", encoding="utf-8") as fin, gzip.open(dst, "wt", encoding="utf-8") as fout:
            for line in fin:
                if written >= args.rows:
                    break
                fout.write(line)
                written += 1
                product_ids.add(json.loads(line)["parent_asin"])

        src = config.download_path("products", category)
        dst = config.download_path("products", category, base=config.SAMPLE_DIR)
        dst.parent.mkdir(parents=True, exist_ok=True)
        kept = 0
        with gzip.open(src, "rt", encoding="utf-8") as fin, gzip.open(dst, "wt", encoding="utf-8") as fout:
            for line in fin:
                if json.loads(line).get("parent_asin") in product_ids:
                    fout.write(line)
                    kept += 1

        print(f"{category}: {written:,} reviews, {kept:,} of {len(product_ids):,} products found")


if __name__ == "__main__":
    main()