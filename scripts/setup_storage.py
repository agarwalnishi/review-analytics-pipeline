"""One-time setup of the data lake (a local folder or an S3 bucket, based on STORAGE in .env).

Usage:  python -m scripts.setup_storage
"""

import logging

from etl.storage import get_storage

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    get_storage().setup()