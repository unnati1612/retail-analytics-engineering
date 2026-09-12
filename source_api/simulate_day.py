from datetime import datetime, timedelta
from pathlib import Path
import random
import sqlite3
import uuid


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


ORDER_STATUSES = [
    "delivered",
    "shipped",
    "invoiced",
    "processing",
    "canceled",
]

PAYMENT_TYPES = [
    "credit_card",
    "boleto",
    "voucher",
    "debit_card",
]


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def get_next_simulation_date(connection):
    """
    Generate the next simulated business date based on
    the latest order in the source.
    """

    row = connection.execute(
        """
        SELECT MAX(order_purchase_timestamp) AS max_date
        FROM orders
        """
    ).fetchone()

    if not row["max_date"]:
        return datetime(2018, 10, 18)

    latest = datetime.fromisoformat(
        row["max_date"].replace("Z", "")
    )

    return latest + timedelta(days=1)


def random_existing_customer(connection):
    row = connection.execute(
        """
        SELECT customer_id
        FROM customers
        ORDER BY RANDOM()
        LIMIT 1
        """
    ).fetchone()

    return row["customer_id"]


def random_existing_product(connection):
    row = connection.execute(
        """
        SELECT product_id
        FROM products
        ORDER BY RANDOM()
        LIMIT 1
        """
    ).fetchone()

    return row["product_id"]


def random_existing_seller(connection):
    row = connection.execute(
        """
        SELECT seller_id
        FROM sellers
        ORDER BY RANDOM()
        LIMIT 1
        """
    ).fetchone()

    return row["seller_id"]


def generate_customer(connection, simulation_time):
    customer_id = str(uuid.uuid4())
    customer_unique_id = str(uuid.uuid4())

    timestamp = simulation_time.isoformat(sep=" ")

    connection.execute(
        """
        INSERT INTO customers (
            customer_id,
            customer_unique_id,
            customer_zip_code_prefix,
            customer_city,
            customer_state,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            customer_unique_id,
            str(random.randint(1000, 99999)),
            "synthetic_city",
            random.choice(
                ["SP", "RJ", "MG", "PR", "SC", "BA"]
            ),
            timestamp,
            timestamp,
        ),
    )

    return customer_id


def generate_product(connection, simulation_time):
    product_id = str(uuid.uuid4())

    timestamp = simulation_time.isoformat(sep=" ")

    connection.execute(
        """
        INSERT INTO products (
            product_id,
            product_category_name,
            product_name_lenght,
            product_description_lenght,
            product_photos_qty,
            product_weight_g,
            product_length_cm,
            product_height_cm,
            product_width_cm,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            random.choice(
                [
                    "electronics",
                    "home",
                    "sports",
                    "fashion",
                    "beauty",
                ]
            ),
            random.randint(10, 60),
            random.randint(50, 500),
            random.randint(1, 8),
            round(random.uniform(100, 5000), 2),
            round(random.uniform(10, 100), 2),
            round(random.uniform(5, 80), 2),
            round(random.uniform(5, 80), 2),
            timestamp,
            timestamp,
        ),
    )

    return product_id


def generate_seller(connection, simulation_time):
    seller_id = str(uuid.uuid4())

    timestamp = simulation_time.isoformat(sep=" ")

    connection.execute(
        """
        INSERT INTO sellers (
            seller_id,
            seller_zip_code_prefix,
            seller_city,
            seller_state,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            seller_id,
            str(random.randint(1000, 99999)),
            "synthetic_city",
            random.choice(
                ["SP", "RJ", "MG", "PR", "SC", "BA"]
            ),
            timestamp,
            timestamp,
        ),
    )

    return seller_id


def generate_order(connection, simulation_date):
    order_id = str(uuid.uuid4())

    # Most orders use an existing customer.
    if random.random() < 0.85:
        customer_id = random_existing_customer(connection)
    else:
        customer_time = simulation_date

        customer_id = generate_customer(
            connection,
            customer_time,
        )

    purchase_time = simulation_date.replace(
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )

    status = random.choices(
        ORDER_STATUSES,
        weights=[80, 7, 4, 4, 5],
        k=1,
    )[0]

    approved_at = purchase_time + timedelta(
        minutes=random.randint(5, 120)
    )

    delivered_carrier = None
    delivered_customer = None

    estimated_delivery = purchase_time + timedelta(
        days=random.randint(3, 15)
    )

    if status == "delivered":

        delivered_carrier = purchase_time + timedelta(
            days=random.randint(1, 3)
        )

        delivered_customer = purchase_time + timedelta(
            days=random.randint(2, 18)
        )

    connection.execute(
        """
        INSERT INTO orders (
            order_id,
            customer_id,
            order_status,
            order_purchase_timestamp,
            order_approved_at,
            order_delivered_carrier_date,
            order_delivered_customer_date,
            order_estimated_delivery_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order_id,
            customer_id,
            status,
            purchase_time.isoformat(sep=" "),
            approved_at.isoformat(sep=" "),
            (
                delivered_carrier.isoformat(sep=" ")
                if delivered_carrier
                else None
            ),
            (
                delivered_customer.isoformat(sep=" ")
                if delivered_customer
                else None
            ),
            estimated_delivery.isoformat(sep=" "),
        ),
    )

    return order_id, purchase_time


def generate_order_items_and_payment(
    connection,
    order_id,
    purchase_time,
):
    item_count = random.randint(1, 4)

    total_value = 0.0

    for item_number in range(1, item_count + 1):

        # Occasionally create new master entities.
        product_id = (
            generate_product(
                connection,
                purchase_time,
            )
            if random.random() < 0.05
            else random_existing_product(connection)
        )

        seller_id = (
            generate_seller(
                connection,
                purchase_time,
            )
            if random.random() < 0.03
            else random_existing_seller(connection)
        )

        price = round(random.uniform(20, 1000), 2)
        freight = round(random.uniform(5, 100), 2)

        shipping_limit = purchase_time + timedelta(
            days=random.randint(1, 5)
        )

        connection.execute(
            """
            INSERT INTO order_items (
                order_id,
                order_item_id,
                product_id,
                seller_id,
                shipping_limit_date,
                price,
                freight_value
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item_number,
                product_id,
                seller_id,
                shipping_limit.isoformat(sep=" "),
                price,
                freight,
            ),
        )

        total_value += price + freight

    payment_type = random.choice(PAYMENT_TYPES)

    connection.execute(
        """
        INSERT INTO payments (
            order_id,
            payment_sequential,
            payment_type,
            payment_installments,
            payment_value
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            order_id,
            1,
            payment_type,
            random.randint(1, 6),
            round(total_value, 2),
        ),
    )


def simulate_day():

    connection = get_connection()

    simulation_date = get_next_simulation_date(
        connection
    )

    orders_to_generate = random.randint(50, 100)

    for _ in range(orders_to_generate):

        order_id, purchase_time = generate_order(
            connection,
            simulation_date,
        )

        generate_order_items_and_payment(
            connection,
            order_id,
            purchase_time,
        )

    connection.commit()
    connection.close()

    print(
        f"Generated {orders_to_generate} orders "
        f"for {simulation_date.date()}"
    )


if __name__ == "__main__":
    simulate_day()