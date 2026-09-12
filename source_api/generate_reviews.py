from datetime import datetime, timedelta
from pathlib import Path
import random
import sqlite3
import uuid


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def generate_reviews():
    connection = get_connection()

    # Determine the latest simulated order date.
    latest_order_row = connection.execute(
        """
        SELECT MAX(order_purchase_timestamp) AS latest_order
        FROM orders
        """
    ).fetchone()

    latest_order = datetime.fromisoformat(
        latest_order_row["latest_order"]
    )

    # Reviews are generated as if the simulated date has
    # advanced beyond the order delivery date.
    simulated_today = latest_order + timedelta(days=7)

    eligible_orders = connection.execute(
        """
        SELECT
            o.order_id,
            o.order_delivered_customer_date
        FROM orders AS o
        LEFT JOIN reviews AS r
            ON o.order_id = r.order_id
        WHERE
            o.order_status = 'delivered'
            AND o.order_delivered_customer_date IS NOT NULL
            AND r.order_id IS NULL
        ORDER BY o.order_delivered_customer_date
        """
    ).fetchall()

    created = 0

    for order in eligible_orders:

        delivered_at = datetime.fromisoformat(
            order["order_delivered_customer_date"]
        )

        # Only generate a review once enough simulated time has passed.
        if delivered_at + timedelta(days=1) > simulated_today:
            continue

        # Not every customer reviews the order.
        if random.random() > 0.65:
            continue

        review_created_at = delivered_at + timedelta(
            days=random.randint(1, 7)
        )

        # Don't allow a review to appear in the future
        # relative to our simulated date.
        if review_created_at > simulated_today:
            continue

        review_id = str(uuid.uuid4())

        review_score = random.choices(
            [1, 2, 3, 4, 5],
            weights=[4, 5, 10, 25, 56],
            k=1,
        )[0]

        titles = {
            1: "Not satisfied",
            2: "Could be better",
            3: "Average experience",
            4: "Good experience",
            5: "Excellent experience",
        }

        messages = {
            1: "The product did not meet my expectations.",
            2: "The product was okay but had some issues.",
            3: "The product was acceptable.",
            4: "Good product and delivery experience.",
            5: "Great product and excellent experience.",
        }

        answer_at = review_created_at + timedelta(
            days=random.randint(0, 3)
        )

        connection.execute(
            """
            INSERT INTO reviews (
                review_id,
                order_id,
                review_score,
                review_comment_title,
                review_comment_message,
                review_creation_date,
                review_answer_timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_id,
                order["order_id"],
                review_score,
                titles[review_score],
                messages[review_score],
                review_created_at.isoformat(sep=" "),
                answer_at.isoformat(sep=" "),
            ),
        )

        created += 1

    connection.commit()
    connection.close()

    print(f"Generated {created} new reviews.")


if __name__ == "__main__":
    generate_reviews()