from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

from api_client import APIClient
from audit import write_audit_record
from bigquery_loader import BigQueryLoader
from watermark import WatermarkStore
import argparse

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


PROJECT_ID = os.getenv("GCP_PROJECT_ID")
API_BASE_URL = os.getenv(
    "SOURCE_API_URL",
    "http://127.0.0.1:8000",
)

RAW_DATASET = os.getenv(
    "BQ_DATASET_RAW",
    "retail_raw",
)


if not PROJECT_ID:
    raise ValueError(
        "GCP_PROJECT_ID is not set in .env"
    )


api = APIClient(API_BASE_URL)

loader = BigQueryLoader(
    project_id=PROJECT_ID,
    dataset=RAW_DATASET,
)

watermarks = WatermarkStore(
    BASE_DIR / "ingestion" / "watermarks.json"
)


def process_merge_entity(
    endpoint: str,
    target_table: str,
    key_columns: list[str],
    columns: list[str],
    watermark_field: str = "updated_after",
):
    """
    Process a dimension entity (customers, products, sellers) using append-only ingestion.
    
    IMPORTANT: This function ONLY appends to retail_raw._ingest_<table>.
    It NEVER modifies retail_raw.<table> (the historical Olist data is preserved).
    Deduplication happens in dbt, not here.
    
    Flow:
    1. Fetch incremental data from API using watermark.
    2. Append to retail_raw._ingest_<table> with metadata (_batch_id, _ingested_at, _record_hash).
    3. Advance watermark only after successful append.
    4. If append fails, do not update watermark (safe to retry).
    """

    previous = watermarks.get(target_table)

    print(f"\n{target_table}: previous watermark = {previous}")

    rows = api.fetch(
        endpoint=endpoint,
        timestamp_param=watermark_field if previous else None,
        timestamp_value=previous,
    )

    if not rows:
        print(f"{target_table}: no new/updated records")

        return {
            "records_fetched": 0,
            "records_loaded": 0,
            "watermark_after": previous,
        }

    print(f"{target_table}: fetched {len(rows):,} records from API")

    # Append to _ingest_<table> (WRITE_APPEND, Sandbox-safe).
    ingest_table = f"_ingest_{target_table}"
    batch_id = loader.append_batch(
        rows=rows,
        ingest_table=ingest_table,
        key_columns=key_columns,
    )

    print(
        f"{target_table}: appended {len(rows):,} records to {ingest_table} "
        f"(batch_id={batch_id})"
    )

    # Advance watermark only after successful append.
    watermark_value = max(
        row["updated_at"]
        for row in rows
        if row.get("updated_at")
    )

    watermarks.save(target_table, watermark_value)
    print(f"{target_table}: advanced watermark to {watermark_value}")
    return {
    "records_fetched": len(rows),
    "records_loaded": len(rows),
    "watermark_after": watermark_value,
    }


def process_order_entity(
    endpoint: str,
    target_table: str,
    columns: list[str],
    key_columns: list[str],
    timestamp_field: str,
):
    """
    Process an order-related entity (orders, order_items, payments) using append-only ingestion.
    
    IMPORTANT: This function ONLY appends to retail_raw._ingest_<table>.
    It NEVER modifies retail_raw.<table> (the historical Olist data is preserved).
    Deduplication happens in dbt, not here.
    
    For order_items and payments: The API returns order_purchase_timestamp as an extraction field
    for filtering. We drop it before appending (it's not part of the target schema).
    
    Flow:
    1. Fetch incremental data from API using watermark.
    2. Clean rows (drop extraction fields not in target schema).
    3. Append to retail_raw._ingest_<table> with metadata.
    4. Advance watermark only after successful append.
    5. If append fails, do not update watermark (safe to retry).
    """
    previous = watermarks.get(target_table)

    print(f"\n{target_table}: previous watermark = {previous}")

    rows = api.fetch(
        endpoint=endpoint,
        timestamp_param="created_after" if previous else None,
        timestamp_value=previous,
    )

    if not rows:
        print(f"{target_table}: no new records")

        return {
            "records_fetched": 0,
            "records_loaded": 0,
            "watermark_after": previous,
        }

    print(f"{target_table}: fetched {len(rows):,} records from API")

    # Drop extraction fields not in target schema.
    cleaned_rows = [
        {column: row.get(column) for column in columns}
        for row in rows
    ]

    # Append to _ingest_<table> (WRITE_APPEND, Sandbox-safe).
    ingest_table = f"_ingest_{target_table}"
    batch_id = loader.append_batch(
        rows=cleaned_rows,
        ingest_table=ingest_table,
        key_columns=key_columns,
    )

    print(
        f"{target_table}: appended {len(cleaned_rows):,} records to {ingest_table} "
        f"(batch_id={batch_id})"
    )

    # Advance watermark only after successful append.
    watermark_value = max(
        row[timestamp_field]
        for row in rows
        if row.get(timestamp_field)
    )

    watermarks.save(target_table, watermark_value)
    print(f"{target_table}: advanced watermark to {watermark_value}")

    return {
        "records_fetched": len(rows),
        "records_loaded": len(cleaned_rows),
        "watermark_after": watermark_value,
    }

def process_review_entity():
    """
    Process reviews using append-only ingestion.
    
    IMPORTANT: This function ONLY appends to retail_raw._ingest_reviews.
    It NEVER modifies retail_raw.reviews (the historical Olist data is preserved).
    Deduplication happens in dbt, not here.
    
    NOTE: Reviews are currently not generated by simulate_day.py.
    This path is present but will not be triggered until reviews API is enabled.
    
    Flow:
    1. Fetch incremental reviews from API using watermark.
    2. Append to retail_raw._ingest_reviews with metadata.
    3. Advance watermark only after successful append.
    4. If append fails, do not update watermark (safe to retry).
    """
    target_table = "reviews"

    previous = watermarks.get(target_table)

    print(f"\nreviews: previous watermark = {previous}")

    rows = api.fetch(
        endpoint="reviews",
        timestamp_param="created_after" if previous else None,
        timestamp_value=previous,
    )

    if not rows:
        print("reviews: no new records")

        return {
            "records_fetched": 0,
            "records_loaded": 0,
            "watermark_after": previous,
        }

    print(f"reviews: fetched {len(rows):,} records from API")

    columns = [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ]

    cleaned_rows = [
        {column: row.get(column) for column in columns}
        for row in rows
    ]

    # Append to _ingest_reviews (WRITE_APPEND, Sandbox-safe).
    batch_id = loader.append_batch(
        rows=cleaned_rows,
        ingest_table="_ingest_reviews",
        key_columns=["review_id", "order_id"],
    )

    print(
        f"reviews: appended {len(cleaned_rows):,} records to _ingest_reviews "
        f"(batch_id={batch_id})"
    )

    # Advance watermark only after successful append.
    watermark_value = max(
        row["review_creation_date"]
        for row in rows
        if row.get("review_creation_date")
    )

    watermarks.save(target_table, watermark_value)
    print(f"reviews: advanced watermark to {watermark_value}")

    return {
    "records_fetched": len(rows),
    "records_loaded": len(cleaned_rows),
    "watermark_after": watermark_value,
    }

def run_with_audit(
    *,
    batch_id: str,
    entity: str,
    processor,
    client: bigquery.Client,
):
    """
    Execute one ingestion entity and append an immutable audit record.
    """

    started_at = datetime.now(timezone.utc)

    watermark_before = watermarks.get(entity)

    try:
        result = processor()

        completed_at = datetime.now(timezone.utc)

        write_audit_record(
            client,
            batch_id=batch_id,
            entity=entity,
            started_at=started_at,
            completed_at=completed_at,
            records_fetched=result["records_fetched"],
            records_loaded=result["records_loaded"],
            watermark_before=watermark_before,
            watermark_after=result["watermark_after"],
            status="SUCCESS",
        )

        print(
            f"AUDIT: {entity} -> SUCCESS "
            f"({result['records_loaded']:,} records loaded)"
        )

        return result

    except Exception as exc:
        completed_at = datetime.now(timezone.utc)

        try:
            write_audit_record(
                client,
                batch_id=batch_id,
                entity=entity,
                started_at=started_at,
                completed_at=completed_at,
                records_fetched=0,
                records_loaded=0,
                watermark_before=watermark_before,
                watermark_after=None,
                status="FAILED",
                error_message=str(exc)[:1000],
            )
        except Exception as audit_error:
            print(
                f"AUDIT ERROR: Could not write failure audit for "
                f"{entity}: {audit_error}"
            )

        print(f"AUDIT: {entity} -> FAILED: {exc}")

        raise

def main(batch_id: str | None = None):
    """
    Run append-only ingestion for all entities and record
    ingestion metrics in retail_raw.ingestion_audit.
    """

    if batch_id is None:
        batch_id = (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            + "_"
            + uuid.uuid4().hex[:8]
        )

    print("=" * 70)
    print(f"Starting ingestion batch: {batch_id}")
    print("=" * 70)

    client = bigquery.Client(project=PROJECT_ID)

    run_with_audit(
        batch_id=batch_id,
        entity="customers",
        client=client,
        processor=lambda: process_merge_entity(
            endpoint="customers",
            target_table="customers",
            key_columns=["customer_id"],
            columns=[
                "customer_id",
                "customer_unique_id",
                "customer_zip_code_prefix",
                "customer_city",
                "customer_state",
                "created_at",
                "updated_at",
            ],
        ),
    )

    run_with_audit(
        batch_id=batch_id,
        entity="products",
        client=client,
        processor=lambda: process_merge_entity(
            endpoint="products",
            target_table="products",
            key_columns=["product_id"],
            columns=[
                "product_id",
                "product_category_name",
                "product_name_lenght",
                "product_description_lenght",
                "product_photos_qty",
                "product_weight_g",
                "product_length_cm",
                "product_height_cm",
                "product_width_cm",
                "created_at",
                "updated_at",
            ],
        ),
    )

    run_with_audit(
        batch_id=batch_id,
        entity="sellers",
        client=client,
        processor=lambda: process_merge_entity(
            endpoint="sellers",
            target_table="sellers",
            key_columns=["seller_id"],
            columns=[
                "seller_id",
                "seller_zip_code_prefix",
                "seller_city",
                "seller_state",
                "created_at",
                "updated_at",
            ],
        ),
    )

    run_with_audit(
        batch_id=batch_id,
        entity="orders",
        client=client,
        processor=lambda: process_order_entity(
            endpoint="orders",
            target_table="orders",
            key_columns=["order_id"],
            columns=[
                "order_id",
                "customer_id",
                "order_status",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
            timestamp_field="order_purchase_timestamp",
        ),
    )

    run_with_audit(
        batch_id=batch_id,
        entity="order_items",
        client=client,
        processor=lambda: process_order_entity(
            endpoint="order-items",
            target_table="order_items",
            key_columns=["order_id", "order_item_id"],
            columns=[
                "order_id",
                "order_item_id",
                "product_id",
                "seller_id",
                "shipping_limit_date",
                "price",
                "freight_value",
            ],
            timestamp_field="order_purchase_timestamp",
        ),
    )

    run_with_audit(
        batch_id=batch_id,
        entity="payments",
        client=client,
        processor=lambda: process_order_entity(
            endpoint="payments",
            target_table="payments",
            key_columns=["order_id", "payment_sequential"],
            columns=[
                "order_id",
                "payment_sequential",
                "payment_type",
                "payment_installments",
                "payment_value",
            ],
            timestamp_field="order_purchase_timestamp",
        ),
    )

    run_with_audit(
        batch_id=batch_id,
        entity="reviews",
        client=client,
        processor=process_review_entity,
    )

    print("=" * 70)
    print(f"Ingestion batch completed: {batch_id}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run append-only API ingestion."
    )

    parser.add_argument(
        "--batch-id",
        dest="batch_id",
        default=None,
        help="Batch ID supplied by Airflow. "
             "If omitted, one is generated automatically.",
    )

    args = parser.parse_args()

    main(batch_id=args.batch_id)