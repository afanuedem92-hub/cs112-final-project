"""
GridCare-Lite data access layer.

All database reads/writes for the app live here, kept separate from the
Tkinter GUI code so the logic can be tested without opening any windows.

DB_PATH is built from this file's own absolute location, matching the
same fix applied in db/init_db.py, so this module and init_db.py always
agree on exactly which gridcare.db file they're using.
"""

import sqlite3
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(THIS_DIR, "..", "db", "gridcare.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------- Substations
def list_substations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT substation_id, name, region, voltage_kv, status FROM substations ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows


def substation_exists(substation_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM substations WHERE substation_id = ?", (substation_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


# ---------------------------------------------------------------- Outages
def create_outage(substation_id, reported_by, description, severity):
    if not substation_exists(substation_id):
        raise ValueError(f"Substation ID {substation_id} does not exist in the dataset.")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO outages (substation_id, reported_by, description, severity) "
        "VALUES (?, ?, ?, ?)",
        (substation_id, reported_by, description, severity),
    )
    conn.commit()
    outage_id = cur.lastrowid
    conn.close()
    return outage_id


def list_outages(status=None, region=None):
    conn = get_conn()
    cur = conn.cursor()
    query = (
        "SELECT o.outage_id, s.name, s.region, o.description, o.severity, "
        "o.status, o.reported_at, u.full_name "
        "FROM outages o "
        "JOIN substations s ON o.substation_id = s.substation_id "
        "JOIN users u ON o.reported_by = u.user_id "
        "WHERE 1=1"
    )
    params = []
    if status:
        query += " AND o.status = ?"
        params.append(status)
    if region:
        query += " AND s.region = ?"
        params.append(region)
    query += " ORDER BY o.reported_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def outages_without_work_order():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT o.outage_id, s.name, o.description, o.severity, o.reported_at "
        "FROM outages o "
        "JOIN substations s ON o.substation_id = s.substation_id "
        "LEFT JOIN work_orders w ON o.outage_id = w.outage_id "
        "WHERE w.work_order_id IS NULL AND o.status != 'Resolved' "
        "ORDER BY o.reported_at ASC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------- Work Orders
def list_technicians():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, full_name FROM users WHERE role = 'Technician'")
    rows = cur.fetchall()
    conn.close()
    return rows


def create_work_order(outage_id, created_by, technician_id, scheduled_date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work_orders (outage_id, created_by, assigned_technician_id, "
        "scheduled_date, status) VALUES (?, ?, ?, ?, 'Scheduled')",
        (outage_id, created_by, technician_id, scheduled_date),
    )
    work_order_id = cur.lastrowid
    cur.execute(
        "INSERT INTO status_history (work_order_id, old_status, new_status, changed_by) "
        "VALUES (?, NULL, 'Scheduled', ?)",
        (work_order_id, created_by),
    )
    conn.commit()
    conn.close()
    return work_order_id


def list_work_orders_for_technician(technician_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT w.work_order_id, s.name, o.description, o.severity, w.status, w.scheduled_date "
        "FROM work_orders w "
        "JOIN outages o ON w.outage_id = o.outage_id "
        "JOIN substations s ON o.substation_id = s.substation_id "
        "WHERE w.assigned_technician_id = ? "
        "ORDER BY w.scheduled_date",
        (technician_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def update_work_order_status(work_order_id, new_status, changed_by):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT status, outage_id FROM work_orders WHERE work_order_id = ?", (work_order_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise ValueError("Work order not found.")
    old_status, outage_id = row

    cur.execute("UPDATE work_orders SET status = ? WHERE work_order_id = ?", (new_status, work_order_id))
    cur.execute(
        "INSERT INTO status_history (work_order_id, old_status, new_status, changed_by) "
        "VALUES (?, ?, ?, ?)",
        (work_order_id, old_status, new_status, changed_by),
    )
    if new_status == "Completed":
        cur.execute(
            "UPDATE outages SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP WHERE outage_id = ?",
            (outage_id,),
        )
    elif new_status == "In Progress":
        cur.execute("UPDATE outages SET status = 'In Progress' WHERE outage_id = ?", (outage_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- Complaints
def create_complaint(logged_by, customer_name, description, outage_id=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO complaints (outage_id, logged_by, customer_name, description) "
        "VALUES (?, ?, ?, ?)",
        (outage_id, logged_by, customer_name, description),
    )
    complaint_id = cur.lastrowid
    conn.commit()
    conn.close()
    return complaint_id


def list_complaints():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT complaint_id, customer_name, description, outage_id, status, logged_at "
        "FROM complaints ORDER BY logged_at DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------- Reports
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM outages WHERE status != 'Resolved'")
    open_outages = cur.fetchone()[0]

    cur.execute(
        "SELECT AVG(julianday(resolved_at) - julianday(reported_at)) * 24 "
        "FROM outages WHERE status = 'Resolved' AND resolved_at IS NOT NULL"
    )
    avg_hours = cur.fetchone()[0]

    cur.execute(
        "SELECT s.region, COUNT(*) FROM outages o "
        "JOIN substations s ON o.substation_id = s.substation_id "
        "GROUP BY s.region ORDER BY COUNT(*) DESC"
    )
    by_region = cur.fetchall()

    conn.close()
    return {
        "open_outages": open_outages,
        "avg_resolution_hours": round(avg_hours, 1) if avg_hours is not None else None,
        "outages_by_region": by_region,
    }
