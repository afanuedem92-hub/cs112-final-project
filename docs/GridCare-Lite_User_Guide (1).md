# GridCare-Lite — User Guide

## Setup (one-time)
```
cd gridcare-lite
python db/init_db.py
```
This creates `gridcare.db`, seeds 4 starter accounts (one per role), and imports substations from `grid-network-analysis/data/substations.csv` if that file exists.

## Running the app
```
python gui/app.py
```

## Starter accounts
| Role | Username | Password |
|---|---|---|
| Administrator | admin | admin123 |
| Engineer | engineer1 | engineer123 |
| Technician | tech1 | tech123 |
| Customer Service | csrep1 | csrep123 |

---

## Administrator
After logging in you land on a three-tab dashboard:
- **All Outages** — every outage in the system, with status and severity. Click Refresh to see new entries.
- **Assign Work Order** — shows outages that don't yet have a work order. Enter the Outage ID, pick a technician, enter a scheduled date (YYYY-MM-DD), and click Create Work Order.
- **Reports** — open outage count, average resolution time in hours, and a breakdown of outages by region.

## Engineer
One screen: **Log a New Outage**. Pick the substation from the dropdown (only real substations from the imported dataset appear), write a description, choose a severity, and click Log Outage. The system will not accept an outage against a substation that doesn't exist in the dataset.

## Technician
Your screen lists only the work orders assigned to you. Select a row, then:
- **Mark In Progress** — once you've started the job
- **Mark Completed** — when finished; this automatically marks the linked outage as Resolved and records the resolution time

## Customer Service
Log a complaint with the customer's name and a description. If the complaint relates to a known outage, enter its Outage ID to link them — otherwise leave that field blank. Recent complaints are listed below the form.

---

## How the workflow connects, end to end
1. Engineer logs an outage against a real substation
2. Administrator sees it in "Assign Work Order," creates a work order, assigns a technician
3. Technician sees the work order in their list, updates status as they work
4. Marking a work order Completed automatically resolves the linked outage
5. If a customer calls in about it, Customer Service can log and link a complaint
6. Administrator's Reports tab reflects all of this in real time

## Troubleshooting
- **"No substations available"** on the Engineer screen — the dataset hasn't been imported yet. Run `python db/init_db.py` again after generating `grid-network-analysis/data/substations.csv`.
- **Login fails for a seeded account** — confirm you're typing the exact username/password from the table above; passwords are case-sensitive.
- **Nothing happens after clicking a button** — check the terminal window behind the app for an error message.
