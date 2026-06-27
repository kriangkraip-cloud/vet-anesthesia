from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_DIR lets Docker/production store the database in a persistent volume.
# Default: same folder as the app (works for local/manual installs).
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "anesthesia.db")

_raw_url = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
# Railway provides postgres:// — SQLAlchemy 2.x requires postgresql://
SQLALCHEMY_DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # check_same_thread is SQLite-only; passing it to psycopg2 raises TypeError
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
