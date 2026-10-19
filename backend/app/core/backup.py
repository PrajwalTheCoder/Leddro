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

def backup_sqlite_database(destination_path: Optional[Path] = None, source_path: Optional[Path] = None) -> Path:
    """
    Creates an atomic, consistent SQLite backup using the native sqlite3.backup API.
    Does not copy raw bytes while writes might be occurring.
    """
    src_path = source_path or get_sqlite_path()
    if not src_path or not src_path.exists():
        raise FileNotFoundError(f"Source SQLite database not found at {src_path}")

    if destination_path is None:
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        destination_path = get_backup_dir() / f"leddro_backup_{timestamp}.db"

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    # Perform online backup
    src_conn = sqlite3.connect(str(src_path))
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
    and queries table record counts. Safely catches file corruption.
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    file_size = backup_path.stat().st_size
    try:
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()
        try:
            cursor.execute("PRAGMA integrity_check;")
            check_result = cursor.fetchone()
            is_ok = bool(check_result and check_result[0] == "ok")

            if not is_ok:
                return {
                    "valid": False,
                    "status": check_result[0] if check_result else "integrity_check_failed",
                    "tables": [],
                    "counts": {},
                    "file_size_bytes": file_size
                }

            # Gather table summaries
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

            table_counts = {}
            for tbl in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
                table_counts[tbl] = cursor.fetchone()[0]

            return {
                "valid": True,
                "status": "ok",
                "tables": tables,
                "counts": table_counts,
                "file_size_bytes": file_size
            }
        finally:
            conn.close()
    except sqlite3.Error as e:
        return {
            "valid": False,
            "status": f"corrupt: {str(e)}",
            "tables": [],
            "counts": {},
            "file_size_bytes": file_size
        }

def restore_sqlite_database(
    backup_path: Path,
    create_safety_snapshot: bool = True,
    target_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Safely restores a SQLite database from a backup file.
    1. Validates the integrity of the backup file first.
    2. Takes a pre-restore safety snapshot of the target database before overwriting.
    3. Replaces target DB safely using online backup.
    """
    dest_path = target_path or get_sqlite_path()
    if not dest_path:
        raise ValueError("Restore is only supported for local SQLite databases. For PostgreSQL/Neon, use standard pg_restore.")

    # 1. Validate backup before anything else
    verification = verify_sqlite_backup(backup_path)
    if not verification["valid"]:
        raise ValueError(f"Backup verification failed: {verification.get('status')}")

    safety_snapshot_path = None
    if create_safety_snapshot and dest_path.exists():
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        safety_snapshot_path = get_backup_dir() / f"pre_restore_safety_{timestamp}.db"
        backup_sqlite_database(safety_snapshot_path, source_path=dest_path)

    # 2. Overwrite target database using online backup
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    src_conn = sqlite3.connect(str(backup_path))
    dst_conn = sqlite3.connect(str(dest_path))
    try:
        with dst_conn:
            src_conn.backup(dst_conn, pages=100, progress=None)
    finally:
        dst_conn.close()
        src_conn.close()

    return {
        "restored_from": str(backup_path),
        "target": str(dest_path),
        "safety_snapshot": str(safety_snapshot_path) if safety_snapshot_path else None,
        "verification": verification
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Leddro SQLite Database Backup & Recovery Utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", action="store_true", help="Create an atomic online backup snapshot")
    group.add_argument("--verify", type=str, metavar="PATH", help="Verify integrity of an existing backup file")
    group.add_argument("--restore", type=str, metavar="PATH", help="Restore active database from verified backup")
    parser.add_argument("--target", type=str, metavar="TARGET_PATH", help="Optional target database path for restore (defaults to active database)")

    args = parser.parse_args()

    if args.backup:
        print("[backup] Creating atomic SQLite backup...")
        saved_path = backup_sqlite_database()
        info = verify_sqlite_backup(saved_path)
        print(f"[OK] Backup created successfully: {saved_path}")
        print(f"     Integrity: {info['status']} | Size: {info['file_size_bytes']} bytes")
        print(f"     Tables: {', '.join(info['tables'])}")

    elif args.verify:
        p = Path(args.verify)
        print(f"[backup] Verifying backup integrity for {p}...")
        info = verify_sqlite_backup(p)
        print(f"     Integrity: {info['status']} (Valid: {info['valid']})")
        print(f"     Table records: {info['counts']}")

    elif args.restore:
        p = Path(args.restore)
        tgt = Path(args.target).resolve() if args.target else None
        print(f"[backup] Initiating safe restore from {p}...")
        res = restore_sqlite_database(p, target_path=tgt)
        print(f"[OK] Restored successfully into {res['target']}")
        if res['safety_snapshot']:
            print(f"     Pre-restore safety snapshot saved at: {res['safety_snapshot']}")
