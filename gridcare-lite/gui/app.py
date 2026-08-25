"""
GridCare-Lite — full application.

Run from gridcare-lite/gui:
    python app.py

Screens implemented (per project brief):
  - Login (routes by role)
  - Outage Dashboard (Administrator) — view all outages, filter by status/region
  - New Outage Form (Engineer) — log a new outage against a real substation
  - Work Order Assignment (Administrator) — assign a technician to an open outage
  - Technician View — see assigned work orders, update status
  - Customer Complaint Log (Customer Service) — log a complaint, optionally linked to an outage
  - Reports (Administrator) — open outages, avg resolution time, outages by region
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "db"))
from init_db import verify_password, DB_PATH, init_db  # noqa: E402
import data_access as da  # noqa: E402
import sqlite3

BG = "#f2f4f7"
NAVY = "#1a2b4c"
ACCENT = "#2f6fb0"


class GridCareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GridCare-Lite")
        self.geometry("760x520")
        self.configure(bg=BG)
        self.current_user = None  # (user_id, full_name, role)

        # Always run init_db() on startup — schema.sql uses "CREATE TABLE IF
        # NOT EXISTS", so this is safe even if the database already has data.
        # This also protects against a stray empty gridcare.db file (e.g. one
        # accidentally created by an earlier failed connection) silently
        # skipping initialization just because the file happens to exist.
        init_db()

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)
        self.show_login()

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear()
        self.current_user = None
        LoginScreen(self.container, on_success=self.handle_login)

    def handle_login(self, user_id, full_name, role):
        self.current_user = (user_id, full_name, role)
        self.route_by_role()

    def route_by_role(self):
        self.clear()
        role = self.current_user[2]
        if role == "Administrator":
            AdminHome(self.container, self)
        elif role == "Engineer":
            EngineerHome(self.container, self)
        elif role == "Technician":
            TechnicianHome(self.container, self)
        elif role == "CustomerService":
            CustomerServiceHome(self.container, self)

    def logout(self):
        self.show_login()


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_success):
        super().__init__(parent, bg=BG)
        self.on_success = on_success
        self.pack(fill="both", expand=True)

        tk.Label(self, text="GridCare-Lite", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=NAVY).pack(pady=(60, 4))
        tk.Label(self, text="Outage & Maintenance Management", font=("Segoe UI", 10),
                 bg=BG, fg="#5a6472").pack(pady=(0, 24))

        form = tk.Frame(self, bg=BG)
        form.pack()
        tk.Label(form, text="Username", bg=BG).grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.username_entry = ttk.Entry(form, width=26)
        self.username_entry.grid(row=0, column=1, pady=6)
        tk.Label(form, text="Password", bg=BG).grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.password_entry = ttk.Entry(form, width=26, show="*")
        self.password_entry.grid(row=1, column=1, pady=6)
        self.password_entry.bind("<Return>", lambda e: self.attempt_login())

        tk.Button(self, text="Log In", command=self.attempt_login, bg=ACCENT, fg="white",
                  relief="flat", font=("Segoe UI", 10, "bold"), width=18, pady=6).pack(pady=20)
        tk.Label(self, text="Try: admin/admin123, engineer1/engineer123, tech1/tech123, csrep1/csrep123",
                 font=("Segoe UI", 8), bg=BG, fg="#9aa1ab").pack()

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Missing info", "Enter both a username and password.")
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, password_hash, salt, full_name, role FROM users WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            messagebox.showerror("Login failed", "No account with that username.")
            return
        user_id, stored_hash, salt, full_name, role = row
        if not verify_password(password, stored_hash, salt):
            messagebox.showerror("Login failed", "Incorrect password.")
            return
        self.on_success(user_id, full_name, role)


class BaseHome(tk.Frame):
    """Common header + logout button shared by every role's home screen."""
    def __init__(self, parent, app, title):
        super().__init__(parent, bg=BG)
        self.app = app
        self.pack(fill="both", expand=True)

        header = tk.Frame(self, bg=NAVY, height=50)
        header.pack(fill="x")
        tk.Label(header, text=f"{title} \u2014 {app.current_user[1]}", bg=NAVY, fg="white",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=14, pady=12)
        tk.Button(header, text="Log Out", command=app.logout, bg="#e5e7eb",
                  relief="flat").pack(side="right", padx=14, pady=8)

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=14, pady=14)


class AdminHome(BaseHome):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Administrator Dashboard")

        notebook = ttk.Notebook(self.body)
        notebook.pack(fill="both", expand=True)

        outages_tab = tk.Frame(notebook, bg=BG)
        assign_tab = tk.Frame(notebook, bg=BG)
        reports_tab = tk.Frame(notebook, bg=BG)
        notebook.add(outages_tab, text="All Outages")
        notebook.add(assign_tab, text="Assign Work Order")
        notebook.add(reports_tab, text="Reports")

        self._build_outages_tab(outages_tab)
        self._build_assign_tab(assign_tab)
        self._build_reports_tab(reports_tab)

    def _build_outages_tab(self, tab):
        columns = ("ID", "Substation", "Region", "Description", "Severity", "Status", "Reported")
        tree = ttk.Treeview(tab, columns=columns, show="headings", height=14)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=90)
        tree.pack(fill="both", expand=True, pady=8)

        def refresh():
            for row in tree.get_children():
                tree.delete(row)
            for o in da.list_outages():
                tree.insert("", "end", values=(o[0], o[1], o[2], o[3], o[4], o[5], o[6]))
        tk.Button(tab, text="Refresh", command=refresh, bg=ACCENT, fg="white", relief="flat").pack()
        refresh()

    def _build_assign_tab(self, tab):
        tk.Label(tab, text="Outages awaiting a work order:", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 2))

        columns = ("Outage ID", "Substation", "Description", "Severity", "Reported")
        tree = ttk.Treeview(tab, columns=columns, show="headings", height=8)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110)
        tree.pack(fill="x", pady=6)

        def refresh_pending():
            for row in tree.get_children():
                tree.delete(row)
            for o in da.outages_without_work_order():
                tree.insert("", "end", values=o)
        refresh_pending()

        form = tk.Frame(tab, bg=BG)
        form.pack(pady=10, anchor="w")
        tk.Label(form, text="Outage ID:", bg=BG).grid(row=0, column=0, sticky="e", padx=4, pady=4)
        outage_id_entry = ttk.Entry(form, width=10)
        outage_id_entry.grid(row=0, column=1, padx=4, pady=4)

        tk.Label(form, text="Technician:", bg=BG).grid(row=1, column=0, sticky="e", padx=4, pady=4)
        technicians = da.list_technicians()
        tech_names = [f"{t[0]} - {t[1]}" for t in technicians]
        tech_var = tk.StringVar(value=tech_names[0] if tech_names else "")
        tech_menu = ttk.Combobox(form, textvariable=tech_var, values=tech_names, width=22, state="readonly")
        tech_menu.grid(row=1, column=1, padx=4, pady=4)

        tk.Label(form, text="Scheduled Date (YYYY-MM-DD):", bg=BG).grid(row=2, column=0, sticky="e", padx=4, pady=4)
        date_entry = ttk.Entry(form, width=18)
        date_entry.grid(row=2, column=1, padx=4, pady=4)

        def submit():
            try:
                outage_id = int(outage_id_entry.get())
                tech_id = int(tech_var.get().split(" - ")[0])
                scheduled_date = date_entry.get().strip()
                if not scheduled_date:
                    raise ValueError("Scheduled date is required.")
                da.create_work_order(outage_id, self.app.current_user[0], tech_id, scheduled_date)
                messagebox.showinfo("Success", f"Work order created for outage {outage_id}.")
                refresh_pending()
                outage_id_entry.delete(0, "end")
                date_entry.delete(0, "end")
            except (ValueError, sqlite3.Error) as e:
                messagebox.showerror("Could not create work order", str(e))

        tk.Button(tab, text="Create Work Order", command=submit, bg=ACCENT, fg="white",
                  relief="flat").pack(pady=6)

    def _build_reports_tab(self, tab):
        summary = da.dashboard_summary()
        tk.Label(tab, text="Open Outages:", bg=BG, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 0))
        tk.Label(tab, text=str(summary["open_outages"]), bg=BG, font=("Segoe UI", 14)).pack(anchor="w")

        tk.Label(tab, text="Average Resolution Time (hours):", bg=BG,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(14, 0))
        avg = summary["avg_resolution_hours"]
        tk.Label(tab, text=str(avg) if avg is not None else "No resolved outages yet",
                 bg=BG, font=("Segoe UI", 14)).pack(anchor="w")

        tk.Label(tab, text="Outages by Region:", bg=BG, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(14, 0))
        for region, count in summary["outages_by_region"]:
            tk.Label(tab, text=f"  {region}: {count}", bg=BG).pack(anchor="w")


class EngineerHome(BaseHome):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Engineer")

        tk.Label(self.body, text="Log a New Outage", bg=BG, font=("Segoe UI", 12, "bold")).pack(anchor="w")

        form = tk.Frame(self.body, bg=BG)
        form.pack(anchor="w", pady=10)

        tk.Label(form, text="Substation:", bg=BG).grid(row=0, column=0, sticky="e", padx=4, pady=4)
        substations = da.list_substations()
        sub_names = [f"{s[0]} - {s[1]} ({s[2]})" for s in substations]
        sub_var = tk.StringVar(value=sub_names[0] if sub_names else "")
        ttk.Combobox(form, textvariable=sub_var, values=sub_names, width=32,
                     state="readonly").grid(row=0, column=1, padx=4, pady=4)

        tk.Label(form, text="Description:", bg=BG).grid(row=1, column=0, sticky="e", padx=4, pady=4)
        desc_entry = ttk.Entry(form, width=34)
        desc_entry.grid(row=1, column=1, padx=4, pady=4)

        tk.Label(form, text="Severity:", bg=BG).grid(row=2, column=0, sticky="e", padx=4, pady=4)
        severity_var = tk.StringVar(value="Medium")
        ttk.Combobox(form, textvariable=severity_var, values=["Low", "Medium", "High", "Critical"],
                     width=15, state="readonly").grid(row=2, column=1, sticky="w", padx=4, pady=4)

        def submit():
            if not sub_var.get():
                messagebox.showerror("Missing substation", "No substations available \u2014 has the dataset been imported?")
                return
            if not desc_entry.get().strip():
                messagebox.showerror("Missing description", "Please describe the outage.")
                return
            substation_id = int(sub_var.get().split(" - ")[0])
            try:
                outage_id = da.create_outage(
                    substation_id, self.app.current_user[0], desc_entry.get().strip(), severity_var.get()
                )
                messagebox.showinfo("Logged", f"Outage #{outage_id} logged successfully.")
                desc_entry.delete(0, "end")
            except ValueError as e:
                messagebox.showerror("Could not log outage", str(e))

        tk.Button(self.body, text="Log Outage", command=submit, bg=ACCENT, fg="white",
                  relief="flat").pack(anchor="w", pady=6)


class TechnicianHome(BaseHome):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Technician")

        tk.Label(self.body, text="My Assigned Work Orders", bg=BG,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")

        columns = ("WO ID", "Substation", "Description", "Severity", "Status", "Scheduled")
        self.tree = ttk.Treeview(self.body, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill="x", pady=8)
        self.refresh()

        controls = tk.Frame(self.body, bg=BG)
        controls.pack(pady=6)
        tk.Button(controls, text="Mark In Progress", command=lambda: self.update_status("In Progress"),
                  bg="#f0ad4e", relief="flat").pack(side="left", padx=4)
        tk.Button(controls, text="Mark Completed", command=lambda: self.update_status("Completed"),
                  bg="#5cb85c", fg="white", relief="flat").pack(side="left", padx=4)
        tk.Button(controls, text="Refresh", command=self.refresh, bg=ACCENT, fg="white",
                  relief="flat").pack(side="left", padx=4)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for wo in da.list_work_orders_for_technician(self.app.current_user[0]):
            self.tree.insert("", "end", values=wo)

    def update_status(self, new_status):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a work order first.")
            return
        work_order_id = self.tree.item(selected[0])["values"][0]
        try:
            da.update_work_order_status(work_order_id, new_status, self.app.current_user[0])
            messagebox.showinfo("Updated", f"Work order {work_order_id} marked {new_status}.")
            self.refresh()
        except ValueError as e:
            messagebox.showerror("Update failed", str(e))


class CustomerServiceHome(BaseHome):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Customer Service")

        tk.Label(self.body, text="Log a Customer Complaint", bg=BG,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")

        form = tk.Frame(self.body, bg=BG)
        form.pack(anchor="w", pady=10)

        tk.Label(form, text="Customer Name:", bg=BG).grid(row=0, column=0, sticky="e", padx=4, pady=4)
        name_entry = ttk.Entry(form, width=30)
        name_entry.grid(row=0, column=1, padx=4, pady=4)

        tk.Label(form, text="Description:", bg=BG).grid(row=1, column=0, sticky="e", padx=4, pady=4)
        desc_entry = ttk.Entry(form, width=30)
        desc_entry.grid(row=1, column=1, padx=4, pady=4)

        tk.Label(form, text="Related Outage ID (optional):", bg=BG).grid(row=2, column=0, sticky="e", padx=4, pady=4)
        outage_entry = ttk.Entry(form, width=10)
        outage_entry.grid(row=2, column=1, sticky="w", padx=4, pady=4)

        def submit():
            if not name_entry.get().strip() or not desc_entry.get().strip():
                messagebox.showerror("Missing info", "Customer name and description are required.")
                return
            outage_id = None
            if outage_entry.get().strip():
                try:
                    outage_id = int(outage_entry.get().strip())
                except ValueError:
                    messagebox.showerror("Invalid outage ID", "Outage ID must be a number.")
                    return
            da.create_complaint(self.app.current_user[0], name_entry.get().strip(),
                                 desc_entry.get().strip(), outage_id)
            messagebox.showinfo("Logged", "Complaint logged successfully.")
            name_entry.delete(0, "end")
            desc_entry.delete(0, "end")
            outage_entry.delete(0, "end")
            refresh_list()

        tk.Button(self.body, text="Log Complaint", command=submit, bg=ACCENT, fg="white",
                  relief="flat").pack(anchor="w", pady=6)

        tk.Label(self.body, text="Recent Complaints", bg=BG, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(14, 2))
        columns = ("ID", "Customer", "Description", "Outage ID", "Status", "Logged")
        tree = ttk.Treeview(self.body, columns=columns, show="headings", height=6)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.pack(fill="x")

        def refresh_list():
            for row in tree.get_children():
                tree.delete(row)
            for c in da.list_complaints():
                tree.insert("", "end", values=c)
        refresh_list()


if __name__ == "__main__":
    app = GridCareApp()
    app.mainloop()
