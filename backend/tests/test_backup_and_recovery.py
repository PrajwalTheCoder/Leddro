import pytest
import sqlite3
import tempfile
from pathlib import Path
from backend.app.core.backup import backup_sqlite_database, verify_sqlite_backup, restore_sqlite_database
from backend.app.models.prospect import ProspectModel

def test_backup_and_recovery_flow(tmp_path):
    # Setup temporary database
    test_db_path = tmp_path / "test_leddro.db"
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE prospects (id INTEGER PRIMARY KEY, name TEXT, domain TEXT);")
    cursor.execute("INSERT INTO prospects (id, name, domain) VALUES (1, 'Acme Corp', 'acme.com');")
    cursor.execute("INSERT INTO prospects (id, name, domain) VALUES (2, 'Globex Inc', 'globex.org');")
    conn.commit()
    conn.close()

    # Create backup
    backup_file = tmp_path / "backup_test.db"
    src_conn = sqlite3.connect(str(test_db_path))
    dst_conn = sqlite3.connect(str(backup_file))
    src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    # Verify backup
    verification = verify_sqlite_backup(backup_file)
    assert verification["valid"] is True
    assert "prospects" in verification["tables"]
    assert verification["counts"]["prospects"] == 2

    # Simulate database modification / corruption / loss
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prospects;")
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM prospects;")
    assert cursor.fetchone()[0] == 0
    conn.close()

    # Restore from backup into test_db_path
    src_conn = sqlite3.connect(str(backup_file))
    dst_conn = sqlite3.connect(str(test_db_path))
    src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    # Verify restored records
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name, domain FROM prospects ORDER BY id;")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0] == ("Acme Corp", "acme.com")
    assert rows[1] == ("Globex Inc", "globex.org")
