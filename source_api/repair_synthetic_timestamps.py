from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


def get_ids_from_csv(filename, id_column):
    """
    Return IDs belonging to the original Olist historical dataset.
    """
    import pandas as pd

    file_path = DATA_DIR / filename

    df = pd.read_csv(file_path)

    return set(
        df[id_column]
        .dropna()
        .astype(str)
    )


def main():

    connection = sqlite3.connect(DB_PATH)

    historical_customer_ids = get_ids_from_csv(
        "olist_customers_dataset.csv",
        "customer_id",
    )

    historical_product_ids = get_ids_from_csv(
        "olist_products_dataset.csv",
        "product_id",
    )

    historical_seller_ids = get_ids_from_csv(
        "olist_sellers_dataset.csv",
        "seller_id",
    )

    # ------------------------------------------------------------
    # CUSTOMERS
    # ------------------------------------------------------------

    synthetic_customers = connection.execute(
        """
        SELECT
            customer_id,
            MIN(order_purchase_timestamp) AS first_order_timestamp,
            MAX(order_purchase_timestamp) AS last_order_timestamp
        FROM orders
        WHERE customer_id NOT IN (
            SELECT customer_id
            FROM customers
            WHERE customer_id IN (
                SELECT customer_id
                FROM customers
            )
        )
        GROUP BY customer_id
        """
    ).fetchall()

    # The query above is intentionally replaced below with a
    # Python-level historical-ID check for clarity/reliability.

    customer_rows = connection.execute(
        """
        SELECT
            customer_id
        FROM customers
        """
    ).fetchall()

    for (customer_id,) in customer_rows:

        customer_id = str(customer_id)

        if customer_id in historical_customer_ids:
            continue

        row = connection.execute(
            """
            SELECT
                MIN(order_purchase_timestamp),
                MAX(order_purchase_timestamp)
            FROM orders
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()

        first_timestamp, last_timestamp = row

        if first_timestamp:

            connection.execute(
                """
                UPDATE customers
                SET
                    created_at = ?,
                    updated_at = ?
                WHERE customer_id = ?
                """,
                (
                    first_timestamp,
                    last_timestamp or first_timestamp,
                    customer_id,
                ),
            )

    # ------------------------------------------------------------
    # PRODUCTS
    # ------------------------------------------------------------

    product_rows = connection.execute(
        """
        SELECT product_id
        FROM products
        """
    ).fetchall()

    for (product_id,) in product_rows:

        product_id = str(product_id)

        if product_id in historical_product_ids:
            continue

        row = connection.execute(
            """
            SELECT
                MIN(o.order_purchase_timestamp),
                MAX(o.order_purchase_timestamp)
            FROM order_items oi
            INNER JOIN orders o
                ON oi.order_id = o.order_id
            WHERE oi.product_id = ?
            """,
            (product_id,),
        ).fetchone()

        first_timestamp, last_timestamp = row

        if first_timestamp:

            connection.execute(
                """
                UPDATE products
                SET
                    created_at = ?,
                    updated_at = ?
                WHERE product_id = ?
                """,
                (
                    first_timestamp,
                    last_timestamp or first_timestamp,
                    product_id,
                ),
            )

    # ------------------------------------------------------------
    # SELLERS
    # ------------------------------------------------------------

    seller_rows = connection.execute(
        """
        SELECT seller_id
        FROM sellers
        """
    ).fetchall()

    for (seller_id,) in seller_rows:

        seller_id = str(seller_id)

        if seller_id in historical_seller_ids:
            continue

        row = connection.execute(
            """
            SELECT
                MIN(o.order_purchase_timestamp),
                MAX(o.order_purchase_timestamp)
            FROM order_items oi
            INNER JOIN orders o
                ON oi.order_id = o.order_id
            WHERE oi.seller_id = ?
            """,
            (seller_id,),
        ).fetchone()

        first_timestamp, last_timestamp = row

        if first_timestamp:

            connection.execute(
                """
                UPDATE sellers
                SET
                    created_at = ?,
                    updated_at = ?
                WHERE seller_id = ?
                """,
                (
                    first_timestamp,
                    last_timestamp or first_timestamp,
                    seller_id,
                ),
            )

    connection.commit()
    connection.close()

    print("Synthetic timestamp repair completed.")


if __name__ == "__main__":
    main()