"""
ClinicCare-Lite: Main application shell

Handles login (against user.py's mock auth) and routes to either the
clinician dashboard or patient dashboard based on role.

Run with:
    python app.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from user import authenticate, get_user
from clinic import get_clinic_for_clinician, get_clinic_for_patient, get_all_clinics
from health_task import create_task, get_tasks_for_clinic, _generate_task_id
from task_submission import filter_submissions, update_review_status, submit_task, get_submissions_for_patient, VALID_STATUSES
from message import send_message, get_conversation, post_announcement, get_announcements_for_clinic
from notifications import notify_task_submitted, notify_review_posted, notify_follow_up_needed, notify_escalation, notify_announcement
from tkinter import filedialog
from collections import Counter
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ---------------------------------------------------------------
# Color themes
# Clinicians always get dark theme (per the brief).
# Patients can choose colorful or dark at registration; we default
# new/unspecified patients to colorful here.
# ---------------------------------------------------------------
DARK_THEME = {
    "bg": "#1e1e2e", "fg": "#f5f5f5", "accent": "#4f8cff",
    "entry_bg": "#2b2b3d", "button_bg": "#4f8cff", "button_fg": "#ffffff",
}
COLORFUL_THEME = {
    "bg": "#fef6ff", "fg": "#2b2b3d", "accent": "#a259ff",
    "entry_bg": "#ffffff", "button_bg": "#a259ff", "button_fg": "#ffffff",
}


class ClinicCareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ClinicCare-Lite")
        self.geometry("900x650")
        self.current_user = None
        self.theme = DARK_THEME  # login screen defaults to dark

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def clear_container(self):
        # Cancel any active message-polling timer before wiping the
        # screen, so it doesn't try to update widgets that no longer exist.
        if getattr(self, "poll_job", None):
            self.after_cancel(self.poll_job)
            self.poll_job = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def apply_theme(self, theme):
        self.theme = theme
        self.configure(bg=theme["bg"])

    # -------------------------------------------------------
    # Login screen
    # -------------------------------------------------------
    def show_login(self):
        self.clear_container()
        self.apply_theme(DARK_THEME)
        theme = self.theme

        frame = tk.Frame(self.container, bg=theme["bg"])
        frame.pack(expand=True)

        tk.Label(
            frame, text="ClinicCare-Lite", font=("Segoe UI", 26, "bold"),
            bg=theme["bg"], fg=theme["accent"],
        ).pack(pady=(0, 30))

        tk.Label(frame, text="User ID (8 digits)", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        id_entry = tk.Entry(frame, width=30, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        id_entry.pack(pady=(0, 12))

        tk.Label(frame, text="Password", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        password_entry = tk.Entry(frame, width=30, show="*", bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        password_entry.pack(pady=(0, 20))

        error_label = tk.Label(frame, text="", fg="#ff6b6b", bg=theme["bg"])
        error_label.pack()

        def attempt_login():
            user_id = id_entry.get().strip()
            password = password_entry.get()

            user = authenticate(user_id, password)
            if user:
                self.current_user = user
                self.route_to_dashboard()
            else:
                error_label.config(text="Invalid ID or password. Try again.")

        tk.Button(
            frame, text="Log In", command=attempt_login,
            bg=theme["button_bg"], fg=theme["button_fg"], width=20, relief="flat", pady=6,
        ).pack(pady=10)

        tk.Label(
            frame,
            text="Mock accounts \u2014 Clinician: 12350000 / Passw0rd!   |   Patient: 12342024 / Passw0rd!",
            font=("Segoe UI", 8), bg=theme["bg"], fg="#888888",
        ).pack(pady=(20, 0))

        # Let Enter key submit the form
        password_entry.bind("<Return>", lambda e: attempt_login())

    # -------------------------------------------------------
    # Route to the correct dashboard after login
    # -------------------------------------------------------
    def route_to_dashboard(self):
        self.clear_container()

        if self.current_user.role == "clinician":
            self.apply_theme(DARK_THEME)
            self.show_clinician_dashboard()
        else:
            theme = DARK_THEME if self.current_user.theme == "dark" else COLORFUL_THEME
            self.apply_theme(theme)
            self.show_patient_dashboard()

    # -------------------------------------------------------
    # Placeholder dashboards \u2014 built out in the next steps
    # -------------------------------------------------------
    def show_clinician_dashboard(self):
        theme = self.theme
        self.clinic = get_clinic_for_clinician(self.current_user.user_id)

        frame = tk.Frame(self.container, bg=theme["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        header = tk.Frame(frame, bg=theme["bg"])
        header.pack(fill="x")
        clinic_label = self.clinic.name if self.clinic else "No clinic assigned"
        tk.Label(
            header, text=f"Welcome, {self.current_user.name}  \u2014  {clinic_label}",
            font=("Segoe UI", 16, "bold"), bg=theme["bg"], fg=theme["fg"],
        ).pack(side="left")
        tk.Button(header, text="Log Out", command=self.show_login, bg=theme["button_bg"], fg=theme["button_fg"], relief="flat").pack(side="right")

        if not self.clinic:
            tk.Label(
                frame, text="This clinician has no clinic assigned yet. Run clinic.py's self-test, or create a clinic for this user.",
                bg=theme["bg"], fg="#ff6b6b", font=("Segoe UI", 11),
            ).pack(pady=40)
            return

        # Style the ttk Notebook and Treeview to roughly match the dark theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=theme["entry_bg"], foreground=theme["fg"], padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", theme["accent"])])
        style.configure("Treeview", background=theme["entry_bg"], fieldbackground=theme["entry_bg"],
                         foreground=theme["fg"], rowheight=26)
        style.configure("Treeview.Heading", background=theme["accent"], foreground="#ffffff")

        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True, pady=(15, 0))

        tasks_tab = tk.Frame(notebook, bg=theme["bg"])
        review_tab = tk.Frame(notebook, bg=theme["bg"])
        messages_tab = tk.Frame(notebook, bg=theme["bg"])
        analytics_tab = tk.Frame(notebook, bg=theme["bg"])
        notebook.add(tasks_tab, text="Tasks")
        notebook.add(review_tab, text="Submissions & Review")
        notebook.add(messages_tab, text="Messages")
        notebook.add(analytics_tab, text="Analytics")

        self.build_tasks_tab(tasks_tab)
        self.build_review_tab(review_tab)
        self.build_clinician_messages_tab(messages_tab)
        self.build_analytics_tab(analytics_tab)

    # -------------------------------------------------------
    # Tasks tab: create tasks + list existing ones
    # -------------------------------------------------------
    def build_tasks_tab(self, parent):
        theme = self.theme

        form = tk.LabelFrame(parent, text="Create a new task", bg=theme["bg"], fg=theme["fg"])
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Title", bg=theme["bg"], fg=theme["fg"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        title_entry = tk.Entry(form, width=40, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Due date (YYYY-MM-DD)", bg=theme["bg"], fg=theme["fg"]).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        due_entry = tk.Entry(form, width=15, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        due_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form, text="Description", bg=theme["bg"], fg=theme["fg"]).grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        desc_text = tk.Text(form, width=60, height=3, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        desc_text.grid(row=1, column=1, columnspan=3, padx=5, pady=5)

        status_label = tk.Label(form, text="", bg=theme["bg"], fg="#ff6b6b")
        status_label.grid(row=2, column=0, columnspan=4, sticky="w", padx=5)

        task_list = ttk.Treeview(parent, columns=("id", "title", "due", "desc"), show="headings", height=12)
        for col, label, width in [("id", "Task ID", 90), ("title", "Title", 220), ("due", "Due Date", 100), ("desc", "Description", 400)]:
            task_list.heading(col, text=label)
            task_list.column(col, width=width, anchor="w")
        task_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def refresh_task_list():
            task_list.delete(*task_list.get_children())
            for t in get_tasks_for_clinic(self.clinic.clinic_id):
                task_list.insert("", "end", values=(t.task_id, t.title, t.due_date, t.description))

        def submit_new_task():
            title = title_entry.get().strip()
            due_date = due_entry.get().strip()
            description = desc_text.get("1.0", "end").strip()

            try:
                new_id = _generate_task_id()
                create_task(new_id, title, description, due_date, self.clinic.clinic_id)
                status_label.config(text=f"Created {new_id}.", fg="#4fdc7b")
                title_entry.delete(0, "end")
                due_entry.delete(0, "end")
                desc_text.delete("1.0", "end")
                refresh_task_list()
            except ValueError as e:
                status_label.config(text=str(e), fg="#ff6b6b")

        tk.Button(
            form, text="Create Task", command=submit_new_task,
            bg=theme["button_bg"], fg=theme["button_fg"], relief="flat",
        ).grid(row=3, column=0, columnspan=4, pady=10)

        refresh_task_list()

    # -------------------------------------------------------
    # Submissions & Review tab: filter + review workflow
    # -------------------------------------------------------
    def build_review_tab(self, parent):
        theme = self.theme

        filter_frame = tk.Frame(parent, bg=theme["bg"])
        filter_frame.pack(fill="x", padx=10, pady=10)

        tasks = get_tasks_for_clinic(self.clinic.clinic_id)
        task_options = ["All"] + [t.task_id for t in tasks]

        tk.Label(filter_frame, text="Task:", bg=theme["bg"], fg=theme["fg"]).pack(side="left", padx=(0, 5))
        task_filter = ttk.Combobox(filter_frame, values=task_options, state="readonly", width=15)
        task_filter.set("All")
        task_filter.pack(side="left", padx=(0, 15))

        status_options = ["All"] + list(VALID_STATUSES)
        tk.Label(filter_frame, text="Status:", bg=theme["bg"], fg=theme["fg"]).pack(side="left", padx=(0, 5))
        status_filter = ttk.Combobox(filter_frame, values=status_options, state="readonly", width=18)
        status_filter.set("All")
        status_filter.pack(side="left", padx=(0, 15))

        sub_list = ttk.Treeview(parent, columns=("patient", "task", "status", "time", "file"), show="headings", height=10)
        for col, label, width in [("patient", "Patient ID", 100), ("task", "Task ID", 90),
                                   ("status", "Status", 140), ("time", "Submitted", 160), ("file", "File", 220)]:
            sub_list.heading(col, text=label)
            sub_list.column(col, width=width, anchor="w")
        sub_list.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh_submissions():
            sub_list.delete(*sub_list.get_children())
            task_id = None if task_filter.get() == "All" else task_filter.get()
            status = None if status_filter.get() == "All" else status_filter.get()
            for s in filter_submissions(task_id=task_id, status=status):
                sub_list.insert("", "end", values=(s.patient_id, s.task_id, s.review_status, s.timestamp[:19], s.file_path))

        task_filter.bind("<<ComboboxSelected>>", lambda e: refresh_submissions())
        status_filter.bind("<<ComboboxSelected>>", lambda e: refresh_submissions())

        # --- Review panel ---
        review_frame = tk.LabelFrame(parent, text="Review selected submission", bg=theme["bg"], fg=theme["fg"])
        review_frame.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(review_frame, text="Outcome:", bg=theme["bg"], fg=theme["fg"]).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        outcome_box = ttk.Combobox(review_frame, values=list(VALID_STATUSES[1:]), state="readonly", width=20)
        outcome_box.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(review_frame, text="Notes:", bg=theme["bg"], fg=theme["fg"]).grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        notes_text = tk.Text(review_frame, width=60, height=3, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        notes_text.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        review_status_label = tk.Label(review_frame, text="Select a submission above, then choose an outcome.", bg=theme["bg"], fg="#888888")
        review_status_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=5)

        selected = {"patient_id": None, "task_id": None}

        def on_select(event):
            sel = sub_list.selection()
            if not sel:
                return
            values = sub_list.item(sel[0], "values")
            selected["patient_id"], selected["task_id"] = values[0], values[1]
            review_status_label.config(
                text=f"Reviewing patient {values[0]}'s submission for {values[1]} (current status: {values[2]})",
                fg=theme["fg"],
            )

        sub_list.bind("<<TreeviewSelect>>", on_select)

        def submit_review():
            if not selected["patient_id"]:
                review_status_label.config(text="Select a submission first.", fg="#ff6b6b")
                return
            outcome = outcome_box.get()
            if not outcome:
                review_status_label.config(text="Choose an outcome before submitting.", fg="#ff6b6b")
                return
            notes = notes_text.get("1.0", "end").strip()
            try:
                update_review_status(selected["patient_id"], selected["task_id"], outcome, notes)
                review_status_label.config(text="Review saved.", fg="#4fdc7b")
                notes_text.delete("1.0", "end")
                refresh_submissions()

                # Notify the patient by email, matching the outcome type
                patient = get_user(selected["patient_id"])
                task = next((t for t in get_tasks_for_clinic(self.clinic.clinic_id) if t.task_id == selected["task_id"]), None)
                task_title = task.title if task else selected["task_id"]
                if patient:
                    if outcome == "Needs Follow-up":
                        notify_follow_up_needed(patient.email, task_title, notes)
                    elif outcome == "Escalated":
                        notify_escalation(patient.email, task_title)
                    else:
                        notify_review_posted(patient.email, task_title, outcome)
            except ValueError as e:
                review_status_label.config(text=str(e), fg="#ff6b6b")

        tk.Button(
            review_frame, text="Submit Review", command=submit_review,
            bg=theme["button_bg"], fg=theme["button_fg"], relief="flat",
        ).grid(row=3, column=0, columnspan=3, pady=10)

        refresh_submissions()

    def show_patient_dashboard(self):
        theme = self.theme
        self.clinic = get_clinic_for_patient(self.current_user.user_id)

        frame = tk.Frame(self.container, bg=theme["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        header = tk.Frame(frame, bg=theme["bg"])
        header.pack(fill="x")
        clinic_label = self.clinic.name if self.clinic else "No clinic assigned"
        tk.Label(
            header, text=f"Welcome, {self.current_user.name}  \u2014  {clinic_label}",
            font=("Segoe UI", 16, "bold"), bg=theme["bg"], fg=theme["fg"],
        ).pack(side="left")
        tk.Button(header, text="Log Out", command=self.show_login, bg=theme["button_bg"], fg=theme["button_fg"], relief="flat").pack(side="right")

        if not self.clinic:
            tk.Label(
                frame, text="This patient is not registered with a clinic yet.",
                bg=theme["bg"], fg="#ff6b6b", font=("Segoe UI", 11),
            ).pack(pady=40)
            return

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=theme["entry_bg"], foreground=theme["fg"], padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", theme["accent"])])
        style.configure("Treeview", background=theme["entry_bg"], fieldbackground=theme["entry_bg"],
                         foreground=theme["fg"], rowheight=26)
        style.configure("Treeview.Heading", background=theme["accent"], foreground="#ffffff")

        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True, pady=(15, 0))

        tasks_tab = tk.Frame(notebook, bg=theme["bg"])
        history_tab = tk.Frame(notebook, bg=theme["bg"])
        messages_tab = tk.Frame(notebook, bg=theme["bg"])
        notebook.add(tasks_tab, text="My Tasks")
        notebook.add(history_tab, text="My Submissions")
        notebook.add(messages_tab, text="Messages")

        self.build_patient_tasks_tab(tasks_tab)
        self.build_patient_history_tab(history_tab)
        self.build_patient_messages_tab(messages_tab)

    # -------------------------------------------------------
    # Patient: My Tasks tab \u2014 view assigned tasks, submit a file
    # -------------------------------------------------------
    def build_patient_tasks_tab(self, parent):
        theme = self.theme
        patient_id = self.current_user.user_id

        task_list = ttk.Treeview(parent, columns=("id", "title", "due", "status"), show="headings", height=10)
        for col, label, width in [("id", "Task ID", 90), ("title", "Title", 260), ("due", "Due Date", 100), ("status", "My Status", 160)]:
            task_list.heading(col, text=label)
            task_list.column(col, width=width, anchor="w")
        task_list.pack(fill="both", expand=True, padx=10, pady=10)

        detail_frame = tk.LabelFrame(parent, text="Task details", bg=theme["bg"], fg=theme["fg"])
        detail_frame.pack(fill="x", padx=10, pady=(0, 10))

        desc_label = tk.Label(detail_frame, text="Select a task above to see its description and submit a file.",
                               bg=theme["bg"], fg=theme["fg"], wraplength=800, justify="left")
        desc_label.pack(anchor="w", padx=10, pady=(5, 10))

        status_label = tk.Label(detail_frame, text="", bg=theme["bg"], fg="#888888")
        status_label.pack(anchor="w", padx=10)

        selected = {"task_id": None}

        def submissions_by_task():
            return {s.task_id: s for s in get_submissions_for_patient(patient_id)}

        def refresh_task_list():
            task_list.delete(*task_list.get_children())
            existing = submissions_by_task()
            for t in get_tasks_for_clinic(self.clinic.clinic_id):
                my_status = existing[t.task_id].review_status if t.task_id in existing else "Not submitted"
                task_list.insert("", "end", values=(t.task_id, t.title, t.due_date, my_status))

        def on_select(event):
            sel = task_list.selection()
            if not sel:
                return
            values = task_list.item(sel[0], "values")
            selected["task_id"] = values[0]
            task = next((t for t in get_tasks_for_clinic(self.clinic.clinic_id) if t.task_id == values[0]), None)
            if task:
                desc_label.config(text=f"{task.title}\n\n{task.description}")
            status_label.config(text="")

        task_list.bind("<<TreeviewSelect>>", on_select)

        def submit_file():
            if not selected["task_id"]:
                status_label.config(text="Select a task first.", fg="#ff6b6b")
                return
            file_path = filedialog.askopenfilename(
                title="Select a file to submit (.txt, .csv, .pdf)",
                filetypes=[("Allowed files", "*.txt *.csv *.pdf")],
            )
            if not file_path:
                return
            try:
                submit_task(patient_id, selected["task_id"], file_path)
                status_label.config(text="File submitted successfully.", fg="#4fdc7b")
                refresh_task_list()

                # Notify the clinician by email
                clinician = get_user(self.clinic.clinician_id)
                task = next((t for t in get_tasks_for_clinic(self.clinic.clinic_id) if t.task_id == selected["task_id"]), None)
                task_title = task.title if task else selected["task_id"]
                if clinician:
                    notify_task_submitted(clinician.email, self.current_user.name, task_title)
            except (ValueError, FileNotFoundError) as e:
                status_label.config(text=str(e), fg="#ff6b6b")

        tk.Button(
            detail_frame, text="Submit File for Selected Task", command=submit_file,
            bg=theme["button_bg"], fg=theme["button_fg"], relief="flat",
        ).pack(anchor="w", padx=10, pady=(0, 10))

        refresh_task_list()

    # -------------------------------------------------------
    # Patient: My Submissions tab \u2014 review outcomes + notes
    # -------------------------------------------------------
    def build_patient_history_tab(self, parent):
        theme = self.theme
        patient_id = self.current_user.user_id

        sub_list = ttk.Treeview(parent, columns=("task", "status", "time"), show="headings", height=8)
        for col, label, width in [("task", "Task ID", 100), ("status", "Status", 160), ("time", "Submitted", 180)]:
            sub_list.heading(col, text=label)
            sub_list.column(col, width=width, anchor="w")
        sub_list.pack(fill="both", expand=False, padx=10, pady=10)

        notes_box = tk.Text(parent, height=6, bg=theme["entry_bg"], fg=theme["fg"], wrap="word")
        notes_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        notes_box.insert("1.0", "Select a submission above to see the clinician's notes.")
        notes_box.config(state="disabled")

        submissions = get_submissions_for_patient(patient_id)
        for s in submissions:
            sub_list.insert("", "end", values=(s.task_id, s.review_status, s.timestamp[:19]))

        def on_select(event):
            sel = sub_list.selection()
            if not sel:
                return
            values = sub_list.item(sel[0], "values")
            task_id = values[0]
            match = next((s for s in submissions if s.task_id == task_id), None)
            notes_box.config(state="normal")
            notes_box.delete("1.0", "end")
            notes_box.insert("1.0", match.notes if match and match.notes else "No notes from your clinician yet.")
            notes_box.config(state="disabled")

        sub_list.bind("<<TreeviewSelect>>", on_select)

    # -------------------------------------------------------
    # Clinician: Messages tab \u2014 conversation with each patient,
    # plus posting/viewing clinic announcements. Uses polling
    # (self.after) to simulate live updates, since this is Tkinter.
    # -------------------------------------------------------
    def build_clinician_messages_tab(self, parent):
        theme = self.theme
        clinician_id = self.current_user.user_id

        # --- Left side: direct messages with a chosen patient ---
        left = tk.Frame(parent, bg=theme["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        tk.Label(left, text="Message a patient:", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        patient_options = self.clinic.patient_ids
        patient_picker = ttk.Combobox(left, values=patient_options, state="readonly", width=20)
        if patient_options:
            patient_picker.set(patient_options[0])
        patient_picker.pack(anchor="w", pady=(0, 8))

        convo_box = tk.Text(left, height=16, bg=theme["entry_bg"], fg=theme["fg"], wrap="word", state="disabled")
        convo_box.pack(fill="both", expand=True, pady=(0, 8))

        entry_frame = tk.Frame(left, bg=theme["bg"])
        entry_frame.pack(fill="x")
        msg_entry = tk.Entry(entry_frame, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def refresh_conversation():
            if not patient_picker.get():
                return
            convo = get_conversation(clinician_id, patient_picker.get())
            convo_box.config(state="normal")
            convo_box.delete("1.0", "end")
            for m in convo:
                sender = "You" if m.sender_id == clinician_id else "Patient"
                convo_box.insert("end", f"[{m.timestamp[:19]}] {sender}: {m.content}\n\n")
            convo_box.config(state="disabled")
            convo_box.see("end")

        def send():
            content = msg_entry.get().strip()
            if not content or not patient_picker.get():
                return
            send_message(clinician_id, patient_picker.get(), content)
            msg_entry.delete(0, "end")
            refresh_conversation()

        tk.Button(entry_frame, text="Send", command=send, bg=theme["button_bg"], fg=theme["button_fg"], relief="flat").pack(side="right")
        msg_entry.bind("<Return>", lambda e: send())
        patient_picker.bind("<<ComboboxSelected>>", lambda e: refresh_conversation())

        # --- Right side: announcements ---
        right = tk.Frame(parent, bg=theme["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        tk.Label(right, text="Post an announcement:", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        ann_entry = tk.Text(right, height=3, bg=theme["entry_bg"], fg=theme["fg"], wrap="word")
        ann_entry.pack(fill="x", pady=(0, 5))

        urgent_var = tk.BooleanVar()
        tk.Checkbutton(right, text="Urgent", variable=urgent_var, bg=theme["bg"], fg=theme["fg"],
                        selectcolor=theme["entry_bg"], activebackground=theme["bg"]).pack(anchor="w")

        expiry_frame = tk.Frame(right, bg=theme["bg"])
        expiry_frame.pack(anchor="w", pady=(0, 5))
        tk.Label(expiry_frame, text="Expiry (YYYY-MM-DD):", bg=theme["bg"], fg=theme["fg"]).pack(side="left")
        expiry_entry = tk.Entry(expiry_frame, width=12, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        expiry_entry.pack(side="left", padx=5)

        ann_status = tk.Label(right, text="", bg=theme["bg"], fg="#ff6b6b")
        ann_status.pack(anchor="w")

        ann_list = tk.Text(right, height=10, bg=theme["entry_bg"], fg=theme["fg"], wrap="word", state="disabled")
        ann_list.pack(fill="both", expand=True, pady=(8, 0))

        def refresh_announcements():
            anns = get_announcements_for_clinic(self.clinic.clinic_id)
            ann_list.config(state="normal")
            ann_list.delete("1.0", "end")
            for a in anns:
                flag = "\U0001F534 URGENT" if a.urgent else "Routine"
                ann_list.insert("end", f"[{flag}] {a.content}\n(expires {a.expiry_date})\n\n")
            ann_list.config(state="disabled")

        def post():
            content = ann_entry.get("1.0", "end").strip()
            expiry = expiry_entry.get().strip()
            if not content:
                ann_status.config(text="Announcement text cannot be empty.")
                return
            try:
                post_announcement(clinician_id, self.clinic.clinic_id, content, urgent_var.get(), expiry or None)
                ann_entry.delete("1.0", "end")
                expiry_entry.delete(0, "end")
                urgent_var.set(False)
                ann_status.config(text="Announcement posted.", fg="#4fdc7b")
                refresh_announcements()

                # Notify every patient in the clinic by email
                for pid in self.clinic.patient_ids:
                    patient = get_user(pid)
                    if patient:
                        notify_announcement(patient.email, "New clinic announcement", content)
            except ValueError as e:
                ann_status.config(text=str(e), fg="#ff6b6b")

        tk.Button(right, text="Post Announcement", command=post, bg=theme["button_bg"], fg=theme["button_fg"], relief="flat").pack(anchor="w", pady=(0, 5))

        # --- Polling: refresh both panels every 3 seconds ---
        def poll():
            refresh_conversation()
            refresh_announcements()
            self.poll_job = self.after(3000, poll)

        refresh_conversation()
        refresh_announcements()
        self.poll_job = self.after(3000, poll)

    # -------------------------------------------------------
    # Patient: Messages tab \u2014 conversation with their clinician,
    # plus a read-only feed of active clinic announcements.
    # -------------------------------------------------------
    def build_patient_messages_tab(self, parent):
        theme = self.theme
        patient_id = self.current_user.user_id
        clinician_id = self.clinic.clinician_id

        left = tk.Frame(parent, bg=theme["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        tk.Label(left, text="Message your clinician:", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w", pady=(0, 8))

        convo_box = tk.Text(left, height=16, bg=theme["entry_bg"], fg=theme["fg"], wrap="word", state="disabled")
        convo_box.pack(fill="both", expand=True, pady=(0, 8))

        entry_frame = tk.Frame(left, bg=theme["bg"])
        entry_frame.pack(fill="x")
        msg_entry = tk.Entry(entry_frame, bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def refresh_conversation():
            convo = get_conversation(patient_id, clinician_id)
            convo_box.config(state="normal")
            convo_box.delete("1.0", "end")
            for m in convo:
                sender = "You" if m.sender_id == patient_id else "Clinician"
                convo_box.insert("end", f"[{m.timestamp[:19]}] {sender}: {m.content}\n\n")
            convo_box.config(state="disabled")
            convo_box.see("end")

        def send():
            content = msg_entry.get().strip()
            if not content:
                return
            send_message(patient_id, clinician_id, content)
            msg_entry.delete(0, "end")
            refresh_conversation()

        tk.Button(entry_frame, text="Send", command=send, bg=theme["button_bg"], fg=theme["button_fg"], relief="flat").pack(side="right")
        msg_entry.bind("<Return>", lambda e: send())

        # --- Note required by the brief ---
        tk.Label(
            left, text="\u26a0 This inbox is not monitored in real time. Do not use for emergencies.",
            bg=theme["bg"], fg="#ffb84f", font=("Segoe UI", 9, "italic"), wraplength=400, justify="left",
        ).pack(anchor="w", pady=(5, 0))

        # --- Right side: read-only announcements feed ---
        right = tk.Frame(parent, bg=theme["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        tk.Label(right, text="Clinic announcements:", bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        ann_list = tk.Text(right, height=20, bg=theme["entry_bg"], fg=theme["fg"], wrap="word", state="disabled")
        ann_list.pack(fill="both", expand=True, pady=(5, 0))

        def refresh_announcements():
            anns = get_announcements_for_clinic(self.clinic.clinic_id)
            ann_list.config(state="normal")
            ann_list.delete("1.0", "end")
            for a in anns:
                flag = "\U0001F534 URGENT" if a.urgent else "Routine"
                ann_list.insert("end", f"[{flag}] {a.content}\n(expires {a.expiry_date})\n\n")
            ann_list.config(state="disabled")

        def poll():
            refresh_conversation()
            refresh_announcements()
            self.poll_job = self.after(3000, poll)

        refresh_conversation()
        refresh_announcements()
        self.poll_job = self.after(3000, poll)

    # -------------------------------------------------------
    # Clinician: Analytics tab \u2014 submission status breakdown
    # and per-task completion rates (Week 4 operational analytics)
    # -------------------------------------------------------
    def build_analytics_tab(self, parent):
        theme = self.theme
        bg_hex = theme["bg"]

        controls = tk.Frame(parent, bg=theme["bg"])
        controls.pack(fill="x", padx=10, pady=(10, 0))

        chart_frame = tk.Frame(parent, bg=theme["bg"])
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def draw_charts():
            for widget in chart_frame.winfo_children():
                widget.destroy()

            tasks = get_tasks_for_clinic(self.clinic.clinic_id)
            all_submissions = filter_submissions()
            clinic_task_ids = {t.task_id for t in tasks}
            clinic_submissions = [s for s in all_submissions if s.task_id in clinic_task_ids]

            fig = Figure(figsize=(10, 4.2), dpi=100, facecolor=bg_hex)

            # --- Chart 1: submission status breakdown ---
            ax1 = fig.add_subplot(1, 2, 1)
            status_counts = Counter(s.review_status for s in clinic_submissions)
            statuses = list(VALID_STATUSES)
            counts = [status_counts.get(s, 0) for s in statuses]
            colors = ["#888888", "#4fdc7b", "#ffb84f", "#ff6b6b"]
            ax1.bar(statuses, counts, color=colors)
            ax1.set_title("Submission Status Breakdown", color=theme["fg"], fontsize=11)
            ax1.tick_params(axis="x", labelrotation=20, colors=theme["fg"], labelsize=8)
            ax1.tick_params(axis="y", colors=theme["fg"])
            ax1.set_facecolor(bg_hex)
            for spine in ax1.spines.values():
                spine.set_color(theme["fg"])

            # --- Chart 2: per-task completion rate ---
            ax2 = fig.add_subplot(1, 2, 2)
            total_patients = max(len(self.clinic.patient_ids), 1)
            task_labels, completion_pcts = [], []
            for t in tasks:
                submitted = len({s.patient_id for s in clinic_submissions if s.task_id == t.task_id})
                pct = round((submitted / total_patients) * 100)
                task_labels.append(t.task_id)
                completion_pcts.append(pct)

            ax2.bar(task_labels, completion_pcts, color=theme["accent"])
            ax2.set_title("Task Completion Rate (%)", color=theme["fg"], fontsize=11)
            ax2.set_ylim(0, 100)
            ax2.tick_params(axis="x", labelrotation=20, colors=theme["fg"], labelsize=8)
            ax2.tick_params(axis="y", colors=theme["fg"])
            ax2.set_facecolor(bg_hex)
            for spine in ax2.spines.values():
                spine.set_color(theme["fg"])

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            # --- Summary stats below the charts ---
            summary = tk.Frame(chart_frame, bg=theme["bg"])
            summary.pack(fill="x", pady=(10, 0))
            total_tasks = len(tasks)
            total_subs = len(clinic_submissions)
            pending = status_counts.get("Pending", 0)
            tk.Label(
                summary,
                text=f"{total_tasks} tasks  \u2022  {total_subs} submissions  \u2022  {pending} pending review  \u2022  {total_patients} registered patients",
                bg=theme["bg"], fg="#888888", font=("Segoe UI", 9),
            ).pack()

        tk.Button(
            controls, text="Refresh Analytics", command=draw_charts,
            bg=theme["button_bg"], fg=theme["button_fg"], relief="flat",
        ).pack(anchor="w")

        draw_charts()


if __name__ == "__main__":
    app = ClinicCareApp()
    app.mainloop()