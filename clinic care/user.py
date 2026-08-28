"""
ClinicCare-Lite: User model
Handles clinician/patient accounts stored in data/users.json

ID rules (from the brief):
  - Exactly 8 digits
  - Clinician ID ends in "0000"        e.g. 12350000
  - Patient ID ends in a year 2022-2028 e.g. 12342024

Password rules:
  - Minimum 8 characters
  - At least one uppercase, one lowercase, one digit, one special char
  - Hashed with bcrypt before storage — never stored in plain text
"""

import json
import os
import re
import bcrypt

USERS_FILE = os.path.join("data", "users.json")

CLINICIAN_ID_PATTERN = re.compile(r"^\d{4}0000$")
PATIENT_ID_PATTERN = re.compile(r"^\d{4}(202[2-8])$")
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=\[\]{};:'\",.<>/?\\|]).{8,}$"
)


class ValidationError(Exception):
    """Raised when an ID or password fails the brief's validation rules."""
    pass


def validate_id(user_id: str, role: str) -> None:
    if not re.match(r"^\d{8}$", user_id):
        raise ValidationError("ID must be exactly 8 digits.")

    if role == "clinician" and not CLINICIAN_ID_PATTERN.match(user_id):
        raise ValidationError("Clinician IDs must end in '0000' (e.g. 12350000).")

    if role == "patient" and not PATIENT_ID_PATTERN.match(user_id):
        raise ValidationError(
            "Patient IDs must end in a registration year between 2022 and 2028 "
            "(e.g. 12342024)."
        )


def validate_password(password: str) -> None:
    if not PASSWORD_PATTERN.match(password):
        raise ValidationError(
            "Password must be at least 8 characters and include an uppercase "
            "letter, a lowercase letter, a digit, and a special character."
        )


class User:
    def __init__(self, user_id, name, email, role, password_hash, theme="colorful"):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role  # "clinician" or "patient"
        self.password_hash = password_hash
        # Clinicians always use dark theme per the brief; patients can choose.
        self.theme = "dark" if role == "clinician" else theme

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "password_hash": self.password_hash,
            "theme": self.theme,
        }

    @staticmethod
    def from_dict(d):
        return User(d["user_id"], d["name"], d["email"], d["role"], d["password_hash"], d.get("theme", "colorful"))

    def check_password(self, plain_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), self.password_hash.encode("utf-8"))


def _load_all() -> dict:
    """Returns {user_id: user_dict}. Creates the file if missing."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_all(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def register_user(user_id, name, email, role, plain_password, theme="colorful") -> User:
    """Validates, hashes the password, and persists a new user.
    Raises ValidationError on any rule violation."""
    validate_id(user_id, role)
    validate_password(plain_password)

    users = _load_all()
    if user_id in users:
        raise ValidationError(f"A user with ID {user_id} already exists.")
    if any(u["email"].lower() == email.lower() for u in users.values()):
        raise ValidationError(f"A user with email {email} already exists.")

    password_hash = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(user_id, name, email, role, password_hash, theme)

    users[user_id] = user.to_dict()
    _save_all(users)
    return user


def get_user(user_id: str) -> User | None:
    users = _load_all()
    d = users.get(user_id)
    return User.from_dict(d) if d else None


def get_all_users(role: str | None = None) -> list[User]:
    users = _load_all()
    result = [User.from_dict(d) for d in users.values()]
    if role:
        result = [u for u in result if u.role == role]
    return result


def authenticate(user_id: str, plain_password: str) -> User | None:
    """Returns the User if credentials are correct, else None."""
    user = get_user(user_id)
    if user and user.check_password(plain_password):
        return user
    return None


if __name__ == "__main__":
    # Quick self-test: register a mock clinician and patient, then confirm
    # login works. Safe to re-run — skips users that already exist.
    try:
        register_user("12350000", "Dr. Ama Boateng", "ama.boateng@clinic.test",
                       "clinician", "Passw0rd!")
        print("Created mock clinician 12350000 / Passw0rd!")
    except ValidationError as e:
        print(f"Clinician already exists or error: {e}")

    try:
        register_user("12342024", "Kwame Mensah", "kwame.mensah@patient.test",
                       "patient", "Passw0rd!", theme="colorful")
        print("Created mock patient 12342024 / Passw0rd!")
    except ValidationError as e:
        print(f"Patient already exists or error: {e}")

    test = authenticate("12350000", "Passw0rd!")
    print("Login test:", "SUCCESS" if test else "FAILED")