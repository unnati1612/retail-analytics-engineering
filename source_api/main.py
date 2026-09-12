from datetime import datetime
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


app = FastAPI(
    title="Retail Source API",
    description="Simulated e-commerce source for the retail analytics pipeline",
    version="1.0.0",
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def rows_to_dict(rows):
    return [dict(row) for row in rows]


@app.get("/")
def root():
    return {
        "service": "Retail Source API",
        "status": "healthy",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


# -------------------------------------------------------------------
# CUSTOMERS
# -------------------------------------------------------------------
@app.get("/customers")
def get_customers(
    limit: int = 100,
    offset: int = 0,
    updated_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if updated_after:
        rows = connection.execute(
            """
            SELECT *
            FROM customers
            WHERE updated_at > ?
            ORDER BY updated_at
            LIMIT ? OFFSET ?
            """,
            (updated_after, limit, offset),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM customers
            ORDER BY updated_at
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }

@app.get("/customers/count")
def get_customer_count():

    connection = get_connection()

    row = connection.execute(
        "SELECT COUNT(*) AS count FROM customers"
    ).fetchone()

    connection.close()

    return {
        "count": row["count"],
    }


# -------------------------------------------------------------------
# PRODUCTS
# -------------------------------------------------------------------
@app.get("/products")
def get_products(
    limit: int = 100,
    offset: int = 0,
    updated_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if updated_after:
        rows = connection.execute(
            """
            SELECT *
            FROM products
            WHERE updated_at > ?
            ORDER BY updated_at
            LIMIT ? OFFSET ?
            """,
            (updated_after, limit, offset),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM products
            ORDER BY updated_at
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }
@app.get("/products/count")
def get_product_count():

    connection = get_connection()

    row = connection.execute(
        "SELECT COUNT(*) AS count FROM products"
    ).fetchone()

    connection.close()

    return {
        "count": row["count"],
    }


# -------------------------------------------------------------------
# SELLERS
# -------------------------------------------------------------------

@app.get("/sellers")
def get_sellers(
    limit: int = 100,
    offset: int = 0,
    updated_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if updated_after:
        rows = connection.execute(
            """
            SELECT *
            FROM sellers
            WHERE updated_at > ?
            ORDER BY updated_at
            LIMIT ? OFFSET ?
            """,
            (updated_after, limit, offset),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM sellers
            ORDER BY updated_at
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }

@app.get("/sellers/count")
def get_seller_count():

    connection = get_connection()

    row = connection.execute(
        "SELECT COUNT(*) AS count FROM sellers"
    ).fetchone()

    connection.close()

    return {
        "count": row["count"],
    }


# -------------------------------------------------------------------
# ORDERS
# -------------------------------------------------------------------

@app.get("/orders")
def get_orders(
    limit: int = 100,
    offset: int = 0,
    created_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if created_after:

        rows = connection.execute(
            """
            SELECT *
            FROM orders
            WHERE order_purchase_timestamp > ?
            ORDER BY order_purchase_timestamp
            LIMIT ? OFFSET ?
            """,
            (created_after, limit, offset),
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT *
            FROM orders
            ORDER BY order_purchase_timestamp
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }


@app.get("/orders/count")
def get_order_count():

    connection = get_connection()

    row = connection.execute(
        "SELECT COUNT(*) AS count FROM orders"
    ).fetchone()

    connection.close()

    return {
        "count": row["count"],
    }


# -------------------------------------------------------------------
# ORDER ITEMS
# -------------------------------------------------------------------
@app.get("/order-items")
def get_order_items(
    limit: int = 100,
    offset: int = 0,
    created_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if created_after:

        rows = connection.execute(
            """
            SELECT
                oi.*,
                o.order_purchase_timestamp
                    AS order_purchase_timestamp
            FROM order_items AS oi
            INNER JOIN orders AS o
                ON oi.order_id = o.order_id
            WHERE o.order_purchase_timestamp > ?
            ORDER BY
                o.order_purchase_timestamp,
                oi.order_id,
                oi.order_item_id
            LIMIT ? OFFSET ?
            """,
            (created_after, limit, offset),
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT
                oi.*,
                o.order_purchase_timestamp
                    AS order_purchase_timestamp
            FROM order_items AS oi
            INNER JOIN orders AS o
                ON oi.order_id = o.order_id
            ORDER BY
                o.order_purchase_timestamp,
                oi.order_id,
                oi.order_item_id
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }

# -------------------------------------------------------------------
# PAYMENTS
# -------------------------------------------------------------------
@app.get("/payments")
def get_payments(
    limit: int = 100,
    offset: int = 0,
    created_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if created_after:

        rows = connection.execute(
            """
            SELECT
                p.*,
                o.order_purchase_timestamp
                    AS order_purchase_timestamp
            FROM payments AS p
            INNER JOIN orders AS o
                ON p.order_id = o.order_id
            WHERE o.order_purchase_timestamp > ?
            ORDER BY
                o.order_purchase_timestamp,
                p.order_id,
                p.payment_sequential
            LIMIT ? OFFSET ?
            """,
            (created_after, limit, offset),
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT
                p.*,
                o.order_purchase_timestamp
                    AS order_purchase_timestamp
            FROM payments AS p
            INNER JOIN orders AS o
                ON p.order_id = o.order_id
            ORDER BY
                o.order_purchase_timestamp,
                p.order_id,
                p.payment_sequential
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }

# -------------------------------------------------------------------
# REVIEWS
# -------------------------------------------------------------------
@app.get("/reviews")
def get_reviews(
    limit: int = 100,
    offset: int = 0,
    created_after: str | None = None,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    if created_after:

        rows = connection.execute(
            """
            SELECT *
            FROM reviews
            WHERE review_creation_date > ?
            ORDER BY
                review_creation_date,
                review_id,
                order_id
            LIMIT ? OFFSET ?
            """,
            (created_after, limit, offset),
        ).fetchall()

    else:

        rows = connection.execute(
            """
            SELECT *
            FROM reviews
            ORDER BY
                review_creation_date,
                review_id,
                order_id
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }

# -------------------------------------------------------------------
# SOURCE STATUS
# -------------------------------------------------------------------

@app.get("/source/status")
def source_status():

    connection = get_connection()

    tables = [
        "customers",
        "products",
        "sellers",
        "orders",
        "order_items",
        "payments",
        "reviews",
    ]

    counts = {}

    for table in tables:

        row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {table}"
        ).fetchone()

        counts[table] = row["count"]

    latest_order = connection.execute(
        """
        SELECT MAX(order_purchase_timestamp) AS latest_order
        FROM orders
        """
    ).fetchone()

    connection.close()

    return {
        "tables": counts,
        "latest_order_timestamp": latest_order["latest_order"],
    }


# Geolocation
@app.get("/geolocation")
def get_geolocation(
    limit: int = 100,
    offset: int = 0,
):
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 1000",
        )

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM geolocation
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "data": rows_to_dict(rows),
    }