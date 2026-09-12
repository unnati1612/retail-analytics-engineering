from pathlib import Path
import sqlite3
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "source_api" / "ecommerce_source.db"


def add_column_if_missing(connection, table, column, column_type):
    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing_columns = {row[1] for row in columns}

    if column not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
        )
        print(f"Added {column} to {table}")


def main():
    connection = sqlite3.connect(DB_PATH)

    for table in ["customers", "products", "sellers"]:
        add_column_if_missing(
            connection,
            table,
            "created_at",
            "TEXT",
        )

        add_column_if_missing(
            connection,
            table,
            "updated_at",
            "TEXT",
        )

    connection.commit()
    connection.close()

    print("Migration completed.")


if __name__ == "__main__":
    main()