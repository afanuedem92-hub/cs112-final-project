-- GridCare-Lite database schema
-- Run via init_db.py, which creates gridcare.db from this file.

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('Administrator', 'Engineer', 'Technician', 'CustomerService'))
);

CREATE TABLE IF NOT EXISTS substations (
    substation_id INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    region        TEXT,
    voltage_kv    REAL,
    status        TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS outages (
    outage_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    substation_id INTEGER NOT NULL,
    reported_by   INTEGER NOT NULL,
    description   TEXT,
    severity      TEXT CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    reported_at   TEXT DEFAULT CURRENT_TIMESTAMP,
    status        TEXT DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved')),
    resolved_at   TEXT,
    FOREIGN KEY (substation_id) REFERENCES substations(substation_id),
    FOREIGN KEY (reported_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id                INTEGER NOT NULL,
    created_by                INTEGER NOT NULL,
    assigned_technician_id    INTEGER,
    scheduled_date             TEXT,
    status                     TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Scheduled', 'In Progress', 'Completed')),
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (assigned_technician_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS status_history (
    history_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL,
    old_status    TEXT,
    new_status    TEXT,
    changed_by    INTEGER,
    timestamp     TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id),
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    outage_id     INTEGER,
    logged_by     INTEGER NOT NULL,
    customer_name TEXT,
    description   TEXT,
    status        TEXT DEFAULT 'Open' CHECK (status IN ('Open', 'Resolved')),
    logged_at     TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outage_id) REFERENCES outages(outage_id),
    FOREIGN KEY (logged_by) REFERENCES users(user_id)
);