import os
from pathlib import Path

from google.cloud import bigquery
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET_ID = os.getenv("BQ_DATASET_RAW")

if not PROJECT_ID or not DATASET_ID:
    raise RuntimeError(
        "Missing GCP_PROJECT_ID or BQ_DATASET_RAW in "
        f"{PROJECT_ROOT / '.env'}"
    )

print(f"Using project: {PROJECT_ID}")


DATA_DIR = PROJECT_ROOT / "data"

FILES = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_products_dataset.csv": "products",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
}


def load_table(client, file_name, table_name):

    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Missing file: {file_path}"
        )

    table_id = (
        f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    )

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        allow_quoted_newlines=True,
        autodetect=True,
        write_disposition=(
            bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )

    print(f"Loading {file_name} → {table_id}")

    with open(file_path, "rb") as source_file:

        job = client.load_table_from_file(
            source_file,
            table_id,
            job_config=job_config
        )

    job.result()

    table = client.get_table(table_id)

    print(
        f"✓ {table_name}: "
        f"{table.num_rows:,} rows loaded"
    )


def main():

    client = bigquery.Client(
        project=PROJECT_ID
    )

    for file_name, table_name in FILES.items():

        load_table(
            client,
            file_name,
            table_name
        )

    print("\nRaw ingestion complete.")


if __name__ == "__main__":
    main()