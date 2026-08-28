"""
ClinicCare-Lite: Clinic model
Stores clinic records in data/clinics.json

Schema (per the brief):
  clinic ID, name, assigned clinician ID, registered patient IDs
"""

import json
import os

CLINICS_FILE = os.path.join("data", "clinics.json")


class Clinic:
    def __init__(self, clinic_id, name, clinician_id, patient_ids=None):
        self.clinic_id = clinic_id
        self.name = name
        self.clinician_id = clinician_id
        self.patient_ids = patient_ids or []

    def to_dict(self):
        return {
            "clinic_id": self.clinic_id,
            "name": self.name,
            "clinician_id": self.clinician_id,
            "patient_ids": self.patient_ids,
        }

    @staticmethod
    def from_dict(d):
        return Clinic(d["clinic_id"], d["name"], d["clinician_id"], d.get("patient_ids", []))


def _load_all() -> dict:
    os.makedirs(os.path.dirname(CLINICS_FILE), exist_ok=True)
    if not os.path.exists(CLINICS_FILE):
        with open(CLINICS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(CLINICS_FILE, "r") as f:
        return json.load(f)


def _save_all(clinics: dict) -> None:
    with open(CLINICS_FILE, "w") as f:
        json.dump(clinics, f, indent=2)


def create_clinic(clinic_id, name, clinician_id, patient_ids=None) -> Clinic:
    clinics = _load_all()
    if clinic_id in clinics:
        raise ValueError(f"Clinic {clinic_id} already exists.")
    clinic = Clinic(clinic_id, name, clinician_id, patient_ids)
    clinics[clinic_id] = clinic.to_dict()
    _save_all(clinics)
    return clinic


def get_clinic(clinic_id: str) -> Clinic | None:
    clinics = _load_all()
    d = clinics.get(clinic_id)
    return Clinic.from_dict(d) if d else None


def get_all_clinics() -> list[Clinic]:
    return [Clinic.from_dict(d) for d in _load_all().values()]


def add_patient_to_clinic(clinic_id: str, patient_id: str) -> None:
    clinics = _load_all()
    if clinic_id not in clinics:
        raise ValueError(f"Clinic {clinic_id} does not exist.")
    if patient_id not in clinics[clinic_id]["patient_ids"]:
        clinics[clinic_id]["patient_ids"].append(patient_id)
        _save_all(clinics)


def get_clinic_for_clinician(clinician_id: str) -> Clinic | None:
    """Convenience lookup: find the clinic a given clinician runs."""
    for clinic in get_all_clinics():
        if clinic.clinician_id == clinician_id:
            return clinic
    return None


def get_clinic_for_patient(patient_id: str) -> Clinic | None:
    """Convenience lookup: find the clinic a given patient is registered under."""
    for clinic in get_all_clinics():
        if patient_id in clinic.patient_ids:
            return clinic
    return None


if __name__ == "__main__":
    # Self-test: create one mock clinic linking our mock clinician and
    # patient from user.py's self-test, then verify lookups work.
    try:
        create_clinic("CLINIC001", "Ashesi Community Clinic", "12350000", ["12342024"])
        print("Created CLINIC001 with clinician 12350000 and patient 12342024")
    except ValueError as e:
        print(f"Clinic already exists or error: {e}")

    clinic = get_clinic("CLINIC001")
    print("Lookup by ID:", clinic.to_dict() if clinic else "NOT FOUND")

    by_clinician = get_clinic_for_clinician("12350000")
    print("Lookup by clinician:", by_clinician.to_dict() if by_clinician else "NOT FOUND")