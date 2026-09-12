from pathlib import Path
import sqlite3

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


def load_csv(connection, filename, table_name):
    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_csv(file_path)

    print(f"Loading {filename}: {len(df):,} rows")

    df.to_sql(
        table_name,
        connection,
        if_exists="replace",
        index=False,
    )


def main():
    connection = sqlite3.connect(DB_PATH)

    tables = {
        "olist_customers_dataset.csv": "customers",
        "olist_products_dataset.csv": "products",
        "olist_sellers_dataset.csv": "sellers",
        "olist_orders_dataset.csv": "orders",
        "olist_order_items_dataset.csv": "order_items",
        "olist_order_payments_dataset.csv": "payments",
        "olist_order_reviews_dataset.csv": "reviews",
    }

    for filename, table_name in tables.items():
        load_csv(connection, filename, table_name)

    connection.commit()
    connection.close()

    print("\nOlist bootstrap completed successfully.")


if __name__ == "__main__":
    main()