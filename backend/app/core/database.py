import re
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

db_url = settings.DATABASE_URL.strip()
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Clean up accidental literal brackets around password e.g. [mypassword]
db_url = re.sub(r':\[(.*?)\]@', r':\1@', db_url)

# Supabase direct hostname (db.<ref>.supabase.co) only supports IPv6.
# On Render (IPv4 only), automatically route through the IPv4 Connection Pooler.
if "db.telbaduznhrtbjmzvbwu.supabase.co" in db_url:
    db_url = db_url.replace("db.telbaduznhrtbjmzvbwu.supabase.co", "aws-0-ap-northeast-1.pooler.supabase.com")
    if "postgres:" in db_url and "postgres.telbaduznhrtbjmzvbwu:" not in db_url:
        db_url = db_url.replace("postgres:", "postgres.telbaduznhrtbjmzvbwu:", 1)

# Configure connection args
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Ensure SSL for Supabase PostgreSQL
    if "sslmode" not in db_url:
        connect_args["sslmode"] = "require"

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False
    )
except Exception as e:
    print(f"Warning: Primary database engine init failed: {e}. Falling back to SQLite.")
    engine = create_engine("sqlite:///./credvista.db", connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

