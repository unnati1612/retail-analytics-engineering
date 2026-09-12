from __future__ import annotations

import argparse
import sys

from google.cloud import bigquery


PROJECT_ID = "retail-analytics-engineering"

MONITORING_TABLE = (
    f"{PROJECT_ID}."
    "retail_analytics."
    "mart_ingestion_monitoring"
)

EXPECTED_ENTITIES = [
    "customers",
    "products",
    "sellers",
    "orders",
    "order_items",
    "payments",
    "reviews",
]


def validate_batch(batch_id: str) -> None:
    client = bigquery.Client(project=PROJECT_ID)

    query = f"""
        SELECT
            batch_id,
            entity,
            records_fetched,
            records_loaded,
            duration_seconds,
            status,
            ingestion_result
        FROM `{MONITORING_TABLE}`
        WHERE batch_id = @batch_id
        ORDER BY
            CASE entity
                WHEN 'customers' THEN 1
                WHEN 'products' THEN 2
                WHEN 'sellers' THEN 3
                WHEN 'orders' THEN 4
                WHEN 'order_items' THEN 5
                WHEN 'payments' THEN 6
                WHEN 'reviews' THEN 7
                ELSE 99
            END
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "batch_id",
                "STRING",
                batch_id,
            )
        ]
    )

    rows = list(
        client.query(
            query,
            job_config=job_config,
        ).result()
    )

    print("=" * 70)
    print("INGESTION VALIDATION")
    print("=" * 70)
    print(f"Batch ID: {batch_id}")
    print()

    if not rows:
        print("ERROR: No monitoring records found for this batch.")
        sys.exit(1)

    results_by_entity = {
        row.entity: row
        for row in rows
    }

    missing_entities = [
        entity
        for entity in EXPECTED_ENTITIES
        if entity not in results_by_entity
    ]

    if missing_entities:
        print(
            "ERROR: Missing entities: "
            + ", ".join(missing_entities)
        )
        sys.exit(1)

    has_failure = False

    for entity in EXPECTED_ENTITIES:
        row = results_by_entity[entity]

        print(
            f"{row.entity:<12} "
            f"{row.records_loaded:>6} loaded  "
            f"{row.records_fetched:>6} fetched  "
            f"{row.duration_seconds:>4}s  "
            f"{row.status:<8}  "
            f"{row.ingestion_result}"
        )

        if row.status != "SUCCESS":
            has_failure = True

        if row.records_loaded < 0:
            has_failure = True

        if row.records_fetched < 0:
            has_failure = True

        if row.records_loaded > row.records_fetched:
            has_failure = True

    print()
    print("=" * 70)

    if has_failure:
        print("Pipeline validation: FAILED")
        print("=" * 70)
        sys.exit(1)

    print("Pipeline validation: PASSED")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-id",
        required=True,
    )

    args = parser.parse_args()

    validate_batch(args.batch_id)


if __name__ == "__main__":
    main()