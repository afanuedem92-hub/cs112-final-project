"""
Initializes gridcare.db from schema.sql, seeds starter accounts, and can
import real substations from the Component 1 dataset so outages can be
logged against actual substation IDs.

IMPORTANT: all paths here are built from the script's own absolute
location (os.path.dirname(os.path.abspath(__file__))), NOT a relative
path. This guarantees the app always finds the same gridcare.db file no
matter where you run the script from (terminal cd'd into gridcare-lite,
VS Code's Run button, another teammate's machine, etc). Using a relative
path here was a real bug found on 2026-08-22 — it caused init_db.py and
app.py to silently talk to two different database files.

Run once:
    python init_db.py
"""

import sqlite3
import hashlib
import secrets
import csv
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(THIS_DIR, "gridcare.db")
SCHEMA_PATH = os.path.join(THIS_DIR, "schema.sql")

# gridcare-lite/db/ -> ../../grid-network-analysis/data/substations.csv
SUBSTATIONS_CSV = os.path.join(
    THIS_DIR, "..", "..", "grid-network-analysis", "data", "substations.csv"
)


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return pwd_hash, salt


def verify_password(password, stored_hash, salt):
    check_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(check_hash, stored_hash)


def import_substations(conn):
    if not os.path.exists(SUBSTATIONS_CSV):
        print(f"(No substations.csv found at {SUBSTATIONS_CSV} — skipping import.)")
        return 0

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM substations")
    if cur.fetchone()[0] > 0:
        return 0

    count = 0
    with open(SUBSTATIONS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                "INSERT OR IGNORE INTO substations (substation_id, name, region, voltage_kv, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    int(row["Substation ID"]),
                    row["Name"],
                    row.get("Region"),
                    float(row["Voltage (kV)"]) if row.get("Voltage (kV)") else None,
                    row.get("Status", "Active"),
                ),
            )
            count += 1
    conn.commit()
    return count


def init_db():
    print(f"Using database file: {DB_PATH}")  # helps catch path mismatches early
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(schema)

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        seed_users = [
            ("admin", "admin123", "Ama Owusu", "Administrator"),
            ("engineer1", "engineer123", "Kwame Boateng", "Engineer"),
            ("tech1", "tech123", "Yaw Mensah", "Technician"),
            ("csrep1", "csrep123", "Efua Asante", "CustomerService"),
        ]
        for username, password, full_name, role in seed_users:
            pwd_hash, salt = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password_hash, salt, full_name, role) "
                "VALUES (?, ?, ?, ?, ?)",
                (username, pwd_hash, salt, full_name, role),
            )
        conn.commit()
        print("Seeded 4 starter accounts (admin/admin123, engineer1/engineer123, "
              "tech1/tech123, csrep1/csrep123).")

    imported = import_substations(conn)
    if imported:
        print(f"Imported {imported} substations from grid-network-analysis/data/substations.csv")

    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    init_db()
