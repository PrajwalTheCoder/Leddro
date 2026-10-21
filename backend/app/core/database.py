from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    pool_pre_ping=True,
    echo=False
)

import sqlite3

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce foreign key cascade and constraint checks on SQLite connections."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate_db(db_engine):
    """
    Safe, database-agnostic schema migration for SQLite and PostgreSQL.
    Inspects existing columns in 'prospects' and 'email_drafts' tables
    and adds newly introduced columns if they do not yet exist.
    """
    try:
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()

        with db_engine.connect() as conn:
            # Check prospects table
            if "prospects" in existing_tables:
                existing_prospect_cols = {col["name"] for col in inspector.get_columns("prospects")}
                prospect_cols_to_add = [
                    ("source_provider", "VARCHAR(255)"),
                    ("source_record_id", "VARCHAR(255)"),
                    ("source_url", "VARCHAR(1024)"),
                    ("identity_status", "VARCHAR(64) DEFAULT 'not_checked'"),
                    ("identity_evidence", "TEXT DEFAULT '{}'"),
                    ("contact_provenance", "TEXT DEFAULT '{}'"),
                    ("social_profiles", "TEXT DEFAULT '{}'"),
                    ("discovered_at", "TIMESTAMP"),
                    ("last_verified_at", "TIMESTAMP")
                ]

                for col_name, col_type in prospect_cols_to_add:
                    if col_name not in existing_prospect_cols:
                        conn.execute(text(f"ALTER TABLE prospects ADD COLUMN {col_name} {col_type}"))
                        conn.commit()

            # Check email_drafts table
            if "email_drafts" in existing_tables:
                existing_draft_cols = {col["name"] for col in inspector.get_columns("email_drafts")}
                draft_cols_to_add = [
                    ("audit_id", "VARCHAR(255)"),
                    ("outreach_purpose", "VARCHAR(255)"),
                    ("writing_tone", "VARCHAR(255)"),
                    ("ai_provider", "VARCHAR(255)"),
                    ("ai_model", "VARCHAR(255)"),
                    ("generation_metadata", "TEXT"),
                    ("provider_message_id", "VARCHAR(255)"),
                    ("submitted_at", "TIMESTAMP")
                ]

                for col_name, col_type in draft_cols_to_add:
                    if col_name not in existing_draft_cols:
                        conn.execute(text(f"ALTER TABLE email_drafts ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
    except Exception:
        # Table might not exist yet; Base.metadata.create_all handles initial creation
        pass



