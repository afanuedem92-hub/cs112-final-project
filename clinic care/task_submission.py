"""
ClinicCare-Lite: TaskSubmission model
Stores submissions in data/task_submissions.json, and copies the
submitted file into submissions/{patient_id}/{task_id}.ext

Schema (per the brief): patient ID, task ID, file path, timestamp,
review status, notes.
"""

import json
import os
import shutil
from datetime import datetime

SUBMISSIONS_FILE = os.path.join("data", "task_submissions.json")
SUBMISSIONS_DIR = "submissions"

ALLOWED_EXTENSIONS = (".txt", ".csv", ".pdf")
VALID_STATUSES = ("Pending", "Reviewed - Normal", "Needs Follow-up", "Escalated")


class TaskSubmission:
    def __init__(self, patient_id, task_id, file_path, timestamp=None,
                 review_status="Pending", notes=None):
        self.patient_id = patient_id
        self.task_id = task_id
        self.file_path = file_path
        self.timestamp = timestamp or datetime.now().isoformat()
        self.review_status = review_status
        self.notes = notes

    def validate_file(self) -> bool:
        return self.file_path.lower().endswith(ALLOWED_EXTENSIONS)

    def save_file(self):
        """Copies the source file into submissions/{patient_id}/{task_id}.ext
        and updates self.file_path to point at the new location."""
        if not self.validate_file():
            raise ValueError("Only .txt, .csv, and .pdf files are allowed.")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Source file not found: {self.file_path}")

        ext = os.path.splitext(self.file_path)[1]
        dest_path = os.path.join(SUBMISSIONS_DIR, self.patient_id, f"{self.task_id}{ext}")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(self.file_path, dest_path)
        self.file_path = dest_path

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "task_id": self.task_id,
            "file_path": self.file_path,
            "timestamp": self.timestamp,
            "review_status": self.review_status,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(d):
        return TaskSubmission(
            d["patient_id"], d["task_id"], d["file_path"],
            d["timestamp"], d["review_status"], d["notes"],
        )


def _load_all() -> dict:
    os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)
    if not os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(SUBMISSIONS_FILE, "r") as f:
        return json.load(f)


def _save_all(submissions: dict) -> None:
    with open(SUBMISSIONS_FILE, "w") as f:
        json.dump(submissions, f, indent=4)


def _submission_key(patient_id, task_id) -> str:
    return f"{patient_id}_{task_id}"


def submit_task(patient_id, task_id, source_file_path) -> TaskSubmission:
    """Full submission flow: validate, copy file, record in JSON.
    Raises ValueError or FileNotFoundError on failure (nothing is
    saved if the file copy fails)."""
    submission = TaskSubmission(patient_id, task_id, source_file_path)
    submission.save_file()  # raises if invalid — happens before we touch the JSON

    submissions = _load_all()
    key = _submission_key(patient_id, task_id)
    submissions[key] = submission.to_dict()
    _save_all(submissions)
    return submission


def get_submission(patient_id: str, task_id: str) -> TaskSubmission | None:
    submissions = _load_all()
    d = submissions.get(_submission_key(patient_id, task_id))
    return TaskSubmission.from_dict(d) if d else None


def get_submissions_for_task(task_id: str) -> list[TaskSubmission]:
    submissions = _load_all()
    return [TaskSubmission.from_dict(d) for d in submissions.values() if d["task_id"] == task_id]


def get_submissions_for_patient(patient_id: str) -> list[TaskSubmission]:
    submissions = _load_all()
    return [TaskSubmission.from_dict(d) for d in submissions.values() if d["patient_id"] == patient_id]


def update_review_status(patient_id: str, task_id: str, new_status: str, notes: str = None) -> TaskSubmission:
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Status must be one of {VALID_STATUSES}, got: {new_status!r}")

    submissions = _load_all()
    key = _submission_key(patient_id, task_id)
    if key not in submissions:
        raise ValueError(f"No submission found for patient {patient_id}, task {task_id}")

    submissions[key]["review_status"] = new_status
    if notes is not None:
        submissions[key]["notes"] = notes
    _save_all(submissions)
    return TaskSubmission.from_dict(submissions[key])


def filter_submissions(patient_id=None, task_id=None, status=None) -> list[TaskSubmission]:
    """Used by the clinician dashboard's submission filter view."""
    submissions = _load_all()
    results = [TaskSubmission.from_dict(d) for d in submissions.values()]
    if patient_id:
        results = [s for s in results if s.patient_id == patient_id]
    if task_id:
        results = [s for s in results if s.task_id == task_id]
    if status:
        results = [s for s in results if s.review_status == status]
    return results


if __name__ == "__main__":
    # Self-test: create a dummy .csv file, submit it against TASK001,
    # then verify it can be looked up and its review status updated.
    os.makedirs("test_uploads", exist_ok=True)
    dummy_file = os.path.join("test_uploads", "bp_log.csv")
    with open(dummy_file, "w") as f:
        f.write("date,systolic,diastolic\n2026-08-20,120,80\n")

    try:
        submission = submit_task("12342024", "TASK001", dummy_file)
        print(f"Submitted: {submission.to_dict()}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Submission failed or already exists: {e}")

    print("\nSubmissions for TASK001:")
    for s in get_submissions_for_task("TASK001"):
        print(f"  {s.patient_id}: {s.review_status} (file: {s.file_path})")

    updated = update_review_status("12342024", "TASK001", "Reviewed - Normal", "Looks good, values within range.")
    print("\nAfter review:", updated.to_dict())