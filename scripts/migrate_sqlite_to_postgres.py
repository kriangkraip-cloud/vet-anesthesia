"""One-time migration: copy all data from the local SQLite database to a
Supabase (or any) PostgreSQL database, preserving primary keys.

Usage:
    SOURCE_SQLITE_PATH=/app/data/anesthesia.db \\
    TARGET_DATABASE_URL="postgresql://postgres:PASSWORD@HOST:5432/postgres" \\
    python3 scripts/migrate_sqlite_to_postgres.py

Run this once, after setting TARGET_DATABASE_URL on Railway but before
switching DATABASE_URL over to Postgres for the live app (or run it against
a downloaded copy of anesthesia.db from Railway's volume).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import Base
from app import models  # noqa: F401  (registers all tables on Base.metadata)

SOURCE_SQLITE_PATH = os.environ.get(
    "SOURCE_SQLITE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "anesthesia.db"),
)
TARGET_DATABASE_URL = os.environ["TARGET_DATABASE_URL"].replace("postgres://", "postgresql://", 1)


def main():
    if not os.path.exists(SOURCE_SQLITE_PATH):
        print(f"Source SQLite file not found: {SOURCE_SQLITE_PATH}")
        sys.exit(1)

    src_engine = create_engine(f"sqlite:///{SOURCE_SQLITE_PATH}")
    dst_engine = create_engine(TARGET_DATABASE_URL)

    print("Creating tables on target (if not already present)...")
    Base.metadata.create_all(bind=dst_engine)

    tables = Base.metadata.sorted_tables  # FK-safe order

    with src_engine.connect() as src_conn, dst_engine.connect() as dst_conn:
        for table in tables:
            rows = src_conn.execute(table.select()).mappings().all()
            if not rows:
                print(f"  {table.name}: 0 rows, skipping")
                continue
            dst_conn.execute(table.delete())
            dst_conn.execute(table.insert(), [dict(r) for r in rows])
            dst_conn.commit()
            print(f"  {table.name}: migrated {len(rows)} rows")

            if "id" in table.c:
                seq_name = f"{table.name}_id_seq"
                try:
                    dst_conn.execute(text(
                        f"SELECT setval('{seq_name}', COALESCE((SELECT MAX(id) FROM {table.name}), 1))"
                    ))
                    dst_conn.commit()
                except Exception as e:
                    print(f"    (sequence reset skipped for {table.name}: {e})")

    print("Migration complete.")


if __name__ == "__main__":
    main()
