"""
ClinicCare-Lite: Message model
Stores messages in data/messages.json

Schema (per the brief): sender ID, recipient ID, timestamp, message content.

Covers both:
  - Direct patient<->clinician messages (recipient_id = a specific user_id)
  - Clinic-wide announcements (recipient_id = "ALL:<clinic_id>", with
    optional urgent flag, publish/expiry dates)

Since this is a Tkinter app (not Flask), "real-time" messaging is done
via polling: the UI re-reads messages.json on a timer rather than
holding a live socket connection. See message_poller in the UI layer.
"""

import json
import os
from datetime import datetime

MESSAGES_FILE = os.path.join("data", "messages.json")

ANNOUNCEMENT_PREFIX = "ALL:"  # recipient_id convention for clinic-wide announcements


class Message:
    def __init__(self, message_id, sender_id, recipient_id, content,
                 timestamp=None, read=False, urgent=False, expiry_date=None):
        self.message_id = message_id
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.read = read
        self.urgent = urgent          # only meaningful for announcements
        self.expiry_date = expiry_date  # only meaningful for announcements, "YYYY-MM-DD"

    def is_announcement(self) -> bool:
        return self.recipient_id.startswith(ANNOUNCEMENT_PREFIX)

    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return datetime.now().date() > datetime.strptime(self.expiry_date, "%Y-%m-%d").date()

    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "content": self.content,
            "timestamp": self.timestamp,
            "read": self.read,
            "urgent": self.urgent,
            "expiry_date": self.expiry_date,
        }

    @staticmethod
    def from_dict(message_id, d):
        return Message(
            message_id, d["sender_id"], d["recipient_id"], d["content"],
            d["timestamp"], d.get("read", False), d.get("urgent", False),
            d.get("expiry_date"),
        )


def _load_all() -> dict:
    os.makedirs(os.path.dirname(MESSAGES_FILE), exist_ok=True)
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, "w") as f:
            json.dump({}, f)
        return {}
    with open(MESSAGES_FILE, "r") as f:
        return json.load(f)


def _save_all(messages: dict) -> None:
    with open(MESSAGES_FILE, "w") as f:
        json.dump(messages, f, indent=4)


def _generate_message_id(messages: dict) -> str:
    existing_numbers = [
        int(mid.replace("MSG", "")) for mid in messages if mid.startswith("MSG") and mid.replace("MSG", "").isdigit()
    ]
    next_number = max(existing_numbers, default=0) + 1
    return f"MSG{next_number:05d}"


def send_message(sender_id, recipient_id, content) -> Message:
    """Direct message between a patient and a clinician."""
    if not content.strip():
        raise ValueError("Message content cannot be empty.")

    messages = _load_all()
    message_id = _generate_message_id(messages)
    message = Message(message_id, sender_id, recipient_id, content)
    messages[message_id] = message.to_dict()
    _save_all(messages)
    return message


def post_announcement(sender_id, clinic_id, content, urgent=False, expiry_date=None) -> Message:
    """Clinic-wide announcement, visible to every patient in that clinic."""
    if not content.strip():
        raise ValueError("Announcement content cannot be empty.")

    recipient_id = f"{ANNOUNCEMENT_PREFIX}{clinic_id}"
    messages = _load_all()
    message_id = _generate_message_id(messages)
    message = Message(message_id, sender_id, recipient_id, content,
                       urgent=urgent, expiry_date=expiry_date)
    messages[message_id] = message.to_dict()
    _save_all(messages)
    return message


def get_conversation(user_a_id: str, user_b_id: str) -> list[Message]:
    """All direct messages between two specific users, oldest first."""
    messages = _load_all()
    convo = [
        Message.from_dict(mid, d) for mid, d in messages.items()
        if {d["sender_id"], d["recipient_id"]} == {user_a_id, user_b_id}
    ]
    convo.sort(key=lambda m: m.timestamp)
    return convo


def get_announcements_for_clinic(clinic_id: str, include_expired=False) -> list[Message]:
    messages = _load_all()
    recipient = f"{ANNOUNCEMENT_PREFIX}{clinic_id}"
    results = [
        Message.from_dict(mid, d) for mid, d in messages.items()
        if d["recipient_id"] == recipient
    ]
    if not include_expired:
        results = [m for m in results if not m.is_expired()]
    results.sort(key=lambda m: m.timestamp, reverse=True)
    return results


def get_inbox(user_id: str, clinic_id: str = None) -> list[Message]:
    """Everything a user should see: direct messages addressed to them,
    plus (if clinic_id given) that clinic's active announcements."""
    messages = _load_all()
    direct = [
        Message.from_dict(mid, d) for mid, d in messages.items()
        if d["recipient_id"] == user_id or d["sender_id"] == user_id
    ]
    announcements = get_announcements_for_clinic(clinic_id) if clinic_id else []
    combined = direct + announcements
    combined.sort(key=lambda m: m.timestamp, reverse=True)
    return combined


def mark_as_read(message_id: str) -> None:
    messages = _load_all()
    if message_id in messages:
        messages[message_id]["read"] = True
        _save_all(messages)


def search_messages(user_id: str, keyword: str) -> list[Message]:
    messages = _load_all()
    keyword_lower = keyword.lower()
    return [
        Message.from_dict(mid, d) for mid, d in messages.items()
        if (d["sender_id"] == user_id or d["recipient_id"] == user_id)
        and keyword_lower in d["content"].lower()
    ]


if __name__ == "__main__":
    # Self-test: send a direct message, post an announcement, then
    # verify conversation lookup, inbox, and search all work.
    send_message("12342024", "12350000", "Hi Dr. Boateng, I submitted my BP log for this week.")
    send_message("12350000", "12342024", "Thanks Kwame, I'll review it shortly.")
    post_announcement("12350000", "CLINIC001", "Clinic closed this Friday for maintenance.", urgent=True,
                       expiry_date="2026-08-30")

    print("Conversation between 12342024 and 12350000:")
    for m in get_conversation("12342024", "12350000"):
        print(f"  [{m.timestamp}] {m.sender_id} -> {m.recipient_id}: {m.content}")

    print("\nAnnouncements for CLINIC001:")
    for a in get_announcements_for_clinic("CLINIC001"):
        flag = "URGENT" if a.urgent else "routine"
        print(f"  ({flag}) {a.content} [expires {a.expiry_date}]")

    print("\nPatient inbox (12342024):")
    for m in get_inbox("12342024", clinic_id="CLINIC001"):
        print(f"  {m.content}")

    print("\nSearch 'BP log' for 12342024:")
    for m in search_messages("12342024", "BP log"):
        print(f"  {m.content}")