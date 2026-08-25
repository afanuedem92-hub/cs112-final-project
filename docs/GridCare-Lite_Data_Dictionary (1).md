# GridCare-Lite — Data Dictionary

Database: SQLite, file `gridcare.db`, created by `db/init_db.py` from `db/schema.sql`.

## users
| Column | Type | Notes |
|---|---|---|
| user_id | INTEGER, PK, autoincrement | |
| username | TEXT, unique | login identifier |
| password_hash | TEXT | PBKDF2-HMAC-SHA256, 100,000 iterations |
| salt | TEXT | random per-user salt, hex-encoded |
| full_name | TEXT | display name |
| role | TEXT | one of: Administrator, Engineer, Technician, CustomerService |

## substations
| Column | Type | Notes |
|---|---|---|
| substation_id | INTEGER, PK | matches the ID from Component 1's substations.csv |
| name | TEXT | |
| region | TEXT | |
| voltage_kv | REAL | |
| status | TEXT | Active / Inactive |

Populated automatically from `grid-network-analysis/data/substations.csv` the first time `init_db.py` runs, so outages can only be logged against substations that genuinely exist in the shared dataset.

## outages
| Column | Type | Notes |
|---|---|---|
| outage_id | INTEGER, PK, autoincrement | |
| substation_id | INTEGER, FK → substations | rejected if the substation doesn't exist |
| reported_by | INTEGER, FK → users | must be an Engineer |
| description | TEXT | |
| severity | TEXT | Low / Medium / High / Critical |
| reported_at | TEXT (timestamp) | defaults to now |
| status | TEXT | Open / In Progress / Resolved — auto-updated as its work order progresses |
| resolved_at | TEXT (timestamp) | set automatically when status becomes Resolved |

## work_orders
| Column | Type | Notes |
|---|---|---|
| work_order_id | INTEGER, PK, autoincrement | |
| outage_id | INTEGER, FK → outages | |
| created_by | INTEGER, FK → users | must be an Administrator |
| assigned_technician_id | INTEGER, FK → users | must be a Technician |
| scheduled_date | TEXT (date) | |
| status | TEXT | Pending / Scheduled / In Progress / Completed |

## status_history
| Column | Type | Notes |
|---|---|---|
| history_id | INTEGER, PK, autoincrement | |
| work_order_id | INTEGER, FK → work_orders | |
| old_status | TEXT | nullable (null on creation) |
| new_status | TEXT | |
| changed_by | INTEGER, FK → users | |
| timestamp | TEXT (timestamp) | defaults to now |

Every work order status change is appended here automatically — this is the audit trail referenced in the Week 1 requirements (NFR: "every work-order status change must be recorded").

## complaints
| Column | Type | Notes |
|---|---|---|
| complaint_id | INTEGER, PK, autoincrement | |
| outage_id | INTEGER, FK → outages | nullable — a complaint may not be linked to a known outage yet |
| logged_by | INTEGER, FK → users | must be CustomerService |
| customer_name | TEXT | |
| description | TEXT | |
| status | TEXT | Open / Resolved |
| logged_at | TEXT (timestamp) | defaults to now |

## Key relationships
- One substation → many outages
- One outage → at most one work order
- One work order → many status_history rows (one per transition)
- One outage → zero or more complaints
- One technician (user) → many work orders
