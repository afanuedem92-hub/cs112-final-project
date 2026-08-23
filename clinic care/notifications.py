"""
ClinicCare-Lite: Email notifications

Sends emails for: task submitted, review posted, follow-up needed,
escalation, appointment reminders, task due-date reminders, and
clinic announcements.

Credentials are read from environment variables — NEVER hardcode
them in this file:

    CLINICCARE_EMAIL       the Gmail address sending the emails
    CLINICCARE_EMAIL_PASS  the 16-character Gmail App Password

On Windows (PowerShell), set these for your current terminal session
with:
    $env:CLINICCARE_EMAIL = "youraddress@gmail.com"
    $env:CLINICCARE_EMAIL_PASS = "abcdefghijklmnop"

(Those only last for that terminal session. To set them permanently,
search Windows for "Edit environment variables for your account" and
add them there instead.)

If the environment variables aren't set, every function here fails
safely and prints a clear message instead of crashing the app.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


class EmailNotConfigured(Exception):
    """Raised when the required environment variables aren't set."""
    pass


def _get_credentials():
    email = os.environ.get("CLINICCARE_EMAIL")
    password = os.environ.get("CLINICCARE_EMAIL_PASS")
    if not email or not password:
        raise EmailNotConfigured(
            "Email is not configured. Set CLINICCARE_EMAIL and "
            "CLINICCARE_EMAIL_PASS as environment variables before "
            "sending notifications."
        )
    return email, password


def send_email(to_address: str, subject: str, body: str) -> bool:
    """Sends a plain-text email. Returns True on success, False on
    failure (and prints why) — designed so a failed email never
    crashes the calling screen in the Tkinter app."""
    try:
        sender_email, sender_password = _get_credentials()
    except EmailNotConfigured as e:
        print(f"[Email skipped] {e}")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"[Email sent] to {to_address}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[Email failed] Login rejected — check CLINICCARE_EMAIL_PASS "
              "is a valid Gmail App Password, not your normal password.")
        return False
    except Exception as e:
        print(f"[Email failed] {e}")
        return False


# ---------------------------------------------------------------
# Specific notification types required by the brief.
# Each one just builds the right subject/body and calls send_email().
# ---------------------------------------------------------------

def notify_task_submitted(clinician_email, patient_name, task_title):
    subject = f"New submission: {task_title}"
    body = f"{patient_name} has submitted a response for the task '{task_title}'. Please log in to ClinicCare-Lite to review it."
    return send_email(clinician_email, subject, body)


def notify_review_posted(patient_email, task_title, outcome):
    subject = f"Your submission has been reviewed: {task_title}"
    body = f"Your clinician has reviewed your submission for '{task_title}'.\n\nOutcome: {outcome}\n\nLog in to ClinicCare-Lite for full details."
    return send_email(patient_email, subject, body)


def notify_follow_up_needed(patient_email, task_title, notes):
    subject = f"Follow-up needed: {task_title}"
    body = f"Your clinician has requested a follow-up regarding '{task_title}'.\n\nNotes: {notes}\n\nPlease log in to ClinicCare-Lite or contact your clinic."
    return send_email(patient_email, subject, body)


def notify_escalation(patient_email, task_title):
    subject = f"Important: Please contact your clinic regarding {task_title}"
    body = f"Your submission for '{task_title}' has been escalated by your clinician. Please contact your clinic as soon as possible."
    return send_email(patient_email, subject, body)


def notify_task_due_reminder(patient_email, task_title, due_date):
    subject = f"Reminder: {task_title} is due soon"
    body = f"This is a reminder that '{task_title}' is due on {due_date}. Please submit your response via ClinicCare-Lite."
    return send_email(patient_email, subject, body)


def notify_appointment_reminder(patient_email, appointment_details):
    subject = "Upcoming appointment reminder"
    body = f"This is a reminder of your upcoming appointment:\n\n{appointment_details}"
    return send_email(patient_email, subject, body)


def notify_announcement(patient_email, announcement_title, announcement_body):
    subject = f"Clinic announcement: {announcement_title}"
    body = announcement_body
    return send_email(patient_email, subject, body)


if __name__ == "__main__":
    # Self-test: attempts to send one real email to whatever address
    # you set CLINICCARE_EMAIL to (sending to yourself is the easiest
    # way to confirm it works). If credentials aren't set, this will
    # print a clear "skipped" message instead of crashing.
    test_email = os.environ.get("CLINICCARE_EMAIL", "not-configured@example.com")
    result = notify_task_submitted(test_email, "Kwame Mensah", "Weekly Blood Pressure Log")
    print("Test result:", "SUCCESS" if result else "FAILED / SKIPPED (see message above)")