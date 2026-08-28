"""
ClinicCare-Lite: HealthTask model
Stores health tasks in data/health_tasks.json

Schema (per the brief): task ID, title, description, due date, clinic ID.

Note: tasks are assigned at the CLINIC level, not per-individual-patient —
every patient registered under a clinic (see clinic.py's patient_ids) can
see and respond to that clinic's tasks. This matches the brief's own
sample HealthTask implementation, which has no per-patient field.
"""

import json
import os
from datetime import datetime

TASKS_FILE = os.path.join("data", "health_tasks.json")


class HealthTask:
    def __init__(self, task_id, title, description, due_date, clinic_id):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.due_date = due_date  # expected format: "YYYY-MM-DD"
        self.clinic_id = clinic_id

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "clinic_id": self.clinic_id,
        }

    @staticmethod
    def from_dict(task_id, d):
        return HealthTask(task_id, d["title"], d["description"], d["due_date"], d["clinic_id"])


def _load_all() -> dict:
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def _save_all(tasks: dict) -> None:
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


def _validate_due_date(due_date: str) -> None:
    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"due_date must be in YYYY-MM-DD format, got: {due_date!r}")


def create_task(task_id, title, description, due_date, clinic_id) -> HealthTask:
    if not title.strip():
        raise ValueError("Task title cannot be empty.")
    _validate_due_date(due_date)

    tasks = _load_all()
    if task_id in tasks:
        raise ValueError(f"Task {task_id} already exists.")

    task = HealthTask(task_id, title, description, due_date, clinic_id)
    tasks[task_id] = task.to_dict()
    _save_all(tasks)
    return task


def get_task(task_id: str) -> HealthTask | None:
    tasks = _load_all()
    d = tasks.get(task_id)
    return HealthTask.from_dict(task_id, d) if d else None


def get_tasks_for_clinic(clinic_id: str) -> list[HealthTask]:
    tasks = _load_all()
    return [
        HealthTask.from_dict(tid, d)
        for tid, d in tasks.items()
        if d["clinic_id"] == clinic_id
    ]


def get_all_tasks() -> list[HealthTask]:
    tasks = _load_all()
    return [HealthTask.from_dict(tid, d) for tid, d in tasks.items()]


def delete_task(task_id: str) -> None:
    tasks = _load_all()
    if task_id in tasks:
        del tasks[task_id]
        _save_all(tasks)


def _generate_task_id() -> str:
    """Simple incrementing ID: TASK001, TASK002, ..."""
    tasks = _load_all()
    existing_numbers = [
        int(tid.replace("TASK", "")) for tid in tasks if tid.startswith("TASK") and tid.replace("TASK", "").isdigit()
    ]
    next_number = max(existing_numbers, default=0) + 1
    return f"TASK{next_number:03d}"


if __name__ == "__main__":
    # Self-test: create one task for our mock clinic (CLINIC001) and
    # confirm it can be looked up both by ID and by clinic.
    new_id = _generate_task_id()
    try:
        create_task(
            new_id,
            "Weekly Blood Pressure Log",
            "Please log your blood pressure daily and submit as a .csv by the due date.",
            "2026-08-25",
            "CLINIC001",
        )
        print(f"Created task {new_id} for CLINIC001")
    except ValueError as e:
        print(f"Error: {e}")

    print("\nTasks for CLINIC001:")
    for t in get_tasks_for_clinic("CLINIC001"):
        print(f"  {t.task_id}: {t.title} (due {t.due_date})")

    print("\nLookup by ID:", get_task(new_id).to_dict())