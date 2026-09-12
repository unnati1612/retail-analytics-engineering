from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


def main():
    connection = sqlite3.connect(DB_PATH)

    # Historical Olist master data existed before the synthetic API period.
    connection.execute(
        """
        UPDATE customers
        SET
            created_at = '2018-10-17 00:00:00',
            updated_at = '2018-10-17 00:00:00'
        WHERE created_at IS NULL
        """
    )

    connection.execute(
        """
        UPDATE products
        SET
            created_at = '2018-10-17 00:00:00',
            updated_at = '2018-10-17 00:00:00'
        WHERE created_at IS NULL
        """
    )

    connection.execute(
        """
        UPDATE sellers
        SET
            created_at = '2018-10-17 00:00:00',
            updated_at = '2018-10-17 00:00:00'
        WHERE created_at IS NULL
        """
    )

    connection.commit()
    connection.close()

    print("Historical timestamps backfilled.")


if __name__ == "__main__":
    main()