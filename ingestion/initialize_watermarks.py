from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
RAW_DATASET = os.getenv("BQ_DATASET_RAW", "retail_raw")

if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID is not set in .env")


client = bigquery.Client(project=PROJECT_ID)

WATERMARK_FILE = BASE_DIR / "ingestion" / "watermarks.json"


def get_max_value(table: str, column: str) -> str | None:

    query = f"""
        SELECT MAX({column}) AS max_value
        FROM `{PROJECT_ID}.{RAW_DATASET}.{table}`
    """

    result = client.query(query).result()

    row = next(iter(result))

    return row["max_value"].strftime("%Y-%m-%d %H:%M:%S") if row["max_value"] else None


def main():

    existing = {}

    if WATERMARK_FILE.exists():
        with open(WATERMARK_FILE, "r", encoding="utf-8") as file:
            existing = json.load(file)

    historical_cutoff = "2018-10-17 23:59:59"

    # Master entities: historical Olist records are already in BigQuery.
    existing.setdefault("customers", historical_cutoff)
    existing.setdefault("products", historical_cutoff)
    existing.setdefault("sellers", historical_cutoff)

    # Transactions: preserve an existing watermark if one already exists.
    # Otherwise initialize from the current BigQuery state.
    for entity, table, column in [
        (
            "orders",
            "orders",
            "order_purchase_timestamp",
        ),
        (
            "order_items",
            "orders",
            "order_purchase_timestamp",
        ),
        (
            "payments",
            "orders",
            "order_purchase_timestamp",
        ),
    ]:
        if entity not in existing:
            value = get_max_value(table, column)

            if value:
                existing[entity] = value

    # Reviews use their own event timestamp.
    if "reviews" not in existing:
        value = get_max_value(
            "reviews",
            "review_creation_date",
        )

        if value:
            existing["reviews"] = value

    with open(
        WATERMARK_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            existing,
            file,
            indent=2,
        )

    print("Watermarks initialized:")
    print(json.dumps(existing, indent=2))


if __name__ == "__main__":
    main()