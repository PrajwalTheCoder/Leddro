"""
Leddro Database Backup and Recovery Engine (Phase 7 Data Safety)
Provides consistent, SQLite-safe backups via the native SQLite online backup API
(sqlite3_backup), pre-restore integrity validation, automatic rollback snapshotting,
and migration verification.
"""

import os
import shutil
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.database import db_url, engine

BACKUP_DIR = Path("backups")

def get_backup_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR

def is_sqlite() -> bool:
    return "sqlite" in db_url.lower()

def get_sqlite_path() -> Optional[Path]:
    if not is_sqlite():
        return None
    # sqlite:////path or sqlite:///./leddro.db
    clean_url = db_url.replace("sqlite:///", "")
    return Path(clean_url).resolve()

def backup_sqlite_database(destination_path: Optional[Path] = None) -> Path:
    """
    Creates an atomic, consistent SQLite backup using the native sqlite3.backup API.
    Does not copy raw bytes while writes might be occurring.
    """
    source_path = get_sqlite_path()
    if not source_path or not source_path.exists():
        raise FileNotFoundError(f"Source SQLite database not found at {source_path}")

    if destination_path is None:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        destination_path = get_backup_dir() / f"leddro_backup_{timestamp}.db"

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    # Perform online backup
    src_conn = sqlite3.connect(str(source_path))
    dst_conn = sqlite3.connect(str(destination_path))
    try:
        with dst_conn:
            src_conn.backup(dst_conn, pages=100, progress=None)
    finally:
        dst_conn.close()
        src_conn.close()

    return destination_path

def verify_sqlite_backup(backup_path: Path) -> Dict[str, Any]:
    """
    Validates backup file integrity using SQLite's PRAGMA integrity_check
    and queries table record counts.
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    conn = sqlite3.connect(str(backup_path))
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA integrity_check;")
        check_result = cursor.fetchone()
        is_ok = bool(check_result and check_result[0] == "ok")

        # Gather table summaries
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

        table_counts = {}
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
            table_counts[tbl] = cursor.fetchone()[0]

        return {
            "valid": is_ok,
            "status": check_result[0] if check_result else "unknown",
            "tables": tables,
            "counts": table_counts,
            "file_size_bytes": backup_path.stat().st_size
        }
    finally:
        conn.close()

def restore_sqlite_database(backup_path: Path, create_safety_snapshot: bool = True) -> Dict[str, Any]:
    """
    Safely restores a SQLite database from a backup file.
    1. Validates the integrity of the backup file first.
    2. Takes a pre-restore safety snapshot of the active database before overwriting.
    3. Replaces active DB safely using online backup or atomic file swap.
    """
    source_path = get_sqlite_path()
    if not source_path:
        raise ValueError("Restore is only supported for local SQLite databases. For PostgreSQL/Neon, use standard pg_restore.")

    # 1. Validate backup before anything else
    verification = verify_sqlite_backup(backup_path)
    if not verification["valid"]:
        raise ValueError(f"Backup verification failed: {verification.get('status')}")

    safety_snapshot_path = None
    if create_safety_snapshot and source_path.exists():
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        safety_snapshot_path = get_backup_dir() / f"pre_restore_safety_{timestamp}.db"
        backup_sqlite_database(safety_snapshot_path)

    # 2. Overwrite target database using online backup
    src_conn = sqlite3.connect(str(backup_path))
    dst_conn = sqlite3.connect(str(source_path))
    try:
        with dst_conn:
            src_conn.backup(dst_conn, pages=100, progress=None)
    finally:
        dst_conn.close()
        src_conn.close()

    return {
        "restored_from": str(backup_path),
        "target": str(source_path),
        "safety_snapshot": str(safety_snapshot_path) if safety_snapshot_path else None,
        "verification": verification
    }
