import threading
import tkinter as tk
from tkinter import messagebox, ttk

import smart_attendance_zone_monitor as backend


BG = "#f6f1e8"
PANEL = "#fbf8f2"
SIDEBAR = "#1f3a5f"
SIDEBAR_ACTIVE = "#345b8c"
TEXT = "#1a1a1a"
ACCENT = "#c96f3b"
MUTED = "#6c7178"


class SmartAttendanceAdminApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Smart Attendance Admin Panel")
        self.root.geometry("1280x760")
        self.root.configure(bg=BG)

        self.admin_logged_in = False
        self.admin_username = ""

        self.camera_index_var = tk.StringVar(value="0")
        self.zone_name_var = tk.StringVar(value="Library")
        self.zone_capacity_var = tk.StringVar(value="25")
        self.status_var = tk.StringVar(value="Ready.")

        self.login_username_var = tk.StringVar(value="admin")
        self.login_password_var = tk.StringVar()

        self.init_username_var = tk.StringVar(value="admin")
        self.init_password_var = tk.StringVar()
        self.init_confirm_password_var = tk.StringVar()
        self.init_master_password_var = tk.StringVar()

        self.person_id_var = tk.StringVar()
        self.person_name_var = tk.StringVar()
        self.person_role_var = tk.StringVar(value="student")
        self.person_department_var = tk.StringVar()
        self.person_email_var = tk.StringVar()
        self.person_phone_var = tk.StringVar()
        self.person_extra_info_var = tk.StringVar()

        self.nav_buttons: dict[str, tk.Button] = {}
        self.views: dict[str, tk.Frame] = {}

        self._build_shell()
        self._show_view("dashboard")
        self.refresh_dashboard()
        self.refresh_people_table()

    def _build_shell(self) -> None:
        sidebar = tk.Frame(self.root, bg=SIDEBAR, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(24, 16))

        tk.Label(
            brand,
            text="Smart Attendance",
            bg=SIDEBAR,
            fg="white",
            font=("Segoe UI Semibold", 18),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="Admin Control Center",
            bg=SIDEBAR,
            fg="#d9e4f2",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        nav_items = [
            ("dashboard", "Dashboard"),
            ("admin", "Admin Process"),
            ("enroll", "Enroll Person"),
            ("people", "People Records"),
            ("attendance", "Attendance"),
            ("zone", "Zone Monitor"),
            ("camera", "Camera Settings"),
        ]

        for key, label in nav_items:
            button = tk.Button(
                sidebar,
                text=label,
                anchor="w",
                relief="flat",
                bg=SIDEBAR,
                fg="white",
                activebackground=SIDEBAR_ACTIVE,
                activeforeground="white",
                font=("Segoe UI", 11),
                padx=20,
                pady=12,
                command=lambda current=key: self._show_view(current),
            )
            button.pack(fill="x", pady=1)
            self.nav_buttons[key] = button

        footer = tk.Frame(sidebar, bg=SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Label(
            footer,
            textvariable=self.status_var,
            bg=SIDEBAR,
            fg="#d9e4f2",
            justify="left",
            wraplength=210,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._build_dashboard_view()
        self._build_admin_view()
        self._build_enroll_view()
        self._build_people_view()
        self._build_attendance_view()
        self._build_zone_view()
        self._build_camera_view()

    def _register_view(self, key: str, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(self.content, bg=BG)
        header = tk.Frame(frame, bg=BG)
        header.pack(fill="x", padx=28, pady=(26, 10))
        tk.Label(header, text=title, bg=BG, fg=TEXT, font=("Georgia", 24, "bold")).pack(anchor="w")
        tk.Label(header, text=subtitle, bg=BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(6, 0))
        self.views[key] = frame
        return frame

    def _card(self, parent: tk.Widget, title: str) -> tk.Frame:
        card = tk.Frame(parent, bg=PANEL, highlightbackground="#ddd4c6", highlightthickness=1)
        tk.Label(card, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=18, pady=(16, 8))
        return card

    def _build_dashboard_view(self) -> None:
        frame = self._register_view("dashboard", "Dashboard", "Overview of people, logs, and system state.")
        stats_wrap = tk.Frame(frame, bg=BG)
        stats_wrap.pack(fill="x", padx=28, pady=8)

        self.total_people_label = self._stat_card(stats_wrap, "Registered People", "0", 0)
        self.total_students_label = self._stat_card(stats_wrap, "Students", "0", 1)
        self.total_employees_label = self._stat_card(stats_wrap, "Employees", "0", 2)
        self.total_attendance_label = self._stat_card(stats_wrap, "Attendance Today", "0", 3)

        lower = tk.Frame(frame, bg=BG)
        lower.pack(fill="both", expand=True, padx=28, pady=(10, 20))

        self.dashboard_people_text = self._text_card(lower, "Recent People", side="left")
        self.dashboard_logs_text = self._text_card(lower, "Recent Logs", side="left")

    def _stat_card(self, parent: tk.Widget, title: str, value: str, column: int) -> tk.Label:
        card = tk.Frame(parent, bg=PANEL, width=210, height=110, highlightbackground="#ddd4c6", highlightthickness=1)
        card.grid(row=0, column=column, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)
        tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(16, 4))
        value_label = tk.Label(card, text=value, bg=PANEL, fg=ACCENT, font=("Georgia", 26, "bold"))
        value_label.pack(anchor="w", padx=16)
        parent.grid_columnconfigure(column, weight=1)
        return value_label

    def _text_card(self, parent: tk.Widget, title: str, side: str = "left") -> tk.Text:
        card = self._card(parent, title)
        card.pack(side=side, fill="both", expand=True, padx=8)
        text = tk.Text(card, height=18, bg="#fffdf9", fg=TEXT, relief="flat", font=("Consolas", 10))
        text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        return text

    def _build_admin_view(self) -> None:
        frame = self._register_view("admin", "Admin Process", "Initialize the admin account and sign in to unlock enrollment.")
        grid = tk.Frame(frame, bg=BG)
        grid.pack(fill="both", expand=True, padx=28, pady=12)

        init_card = self._card(grid, "Initialize Admin")
        init_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._entry_row(init_card, "Username", self.init_username_var)
        self._entry_row(init_card, "Password", self.init_password_var, show="*")
        self._entry_row(init_card, "Confirm Password", self.init_confirm_password_var, show="*")
        self._entry_row(init_card, "Master Password", self.init_master_password_var, show="*")
        tk.Button(
            init_card,
            text="Create Admin",
            bg=ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 11),
            command=self.create_admin_from_gui,
        ).pack(anchor="w", padx=18, pady=(10, 18))

        login_card = self._card(grid, "Admin Login")
        login_card.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self._entry_row(login_card, "Username", self.login_username_var)
        self._entry_row(login_card, "Password", self.login_password_var, show="*")
        tk.Button(
            login_card,
            text="Login",
            bg=SIDEBAR_ACTIVE,
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 11),
            command=self.login_admin_from_gui,
        ).pack(anchor="w", padx=18, pady=(10, 18))

        self.login_state_label = tk.Label(
            frame,
            text="Admin not logged in.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 11),
        )
        self.login_state_label.pack(anchor="w", padx=32, pady=(0, 20))

    def _build_enroll_view(self) -> None:
        frame = self._register_view("enroll", "Enroll Person", "Add student or employee details, then capture face samples.")
        card = self._card(frame, "Person Details")
        card.pack(fill="x", padx=28, pady=12)

        self._entry_row(card, "Person ID", self.person_id_var)
        self._entry_row(card, "Name", self.person_name_var)
        self._combo_row(card, "Role", self.person_role_var, ["student", "employee"])
        self._entry_row(card, "Department / Class", self.person_department_var)
        self._entry_row(card, "Email", self.person_email_var)
        self._entry_row(card, "Phone", self.person_phone_var)
        self._entry_row(card, "Extra Info", self.person_extra_info_var)

        actions = tk.Frame(card, bg=PANEL)
        actions.pack(fill="x", padx=18, pady=(6, 18))
        tk.Button(
            actions,
            text="Start Enrollment",
            bg=ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 11),
            command=self.start_enrollment,
        ).pack(side="left")
        tk.Button(
            actions,
            text="Clear Form",
            bg="#d8d2c5",
            fg=TEXT,
            relief="flat",
            font=("Segoe UI", 11),
            command=self.clear_person_form,
        ).pack(side="left", padx=10)

    def _build_people_view(self) -> None:
        frame = self._register_view("people", "People Records", "Review registered students and employees.")
        card = self._card(frame, "Registered People")
        card.pack(fill="both", expand=True, padx=28, pady=12)

        columns = ("id", "name", "role", "department", "email", "phone", "extra")
        self.people_tree = ttk.Treeview(card, columns=columns, show="headings", height=18)
        headings = {
            "id": "ID",
            "name": "Name",
            "role": "Role",
            "department": "Department/Class",
            "email": "Email",
            "phone": "Phone",
            "extra": "Extra Info",
        }
        widths = {"id": 90, "name": 150, "role": 90, "department": 140, "email": 180, "phone": 110, "extra": 150}
        for col in columns:
            self.people_tree.heading(col, text=headings[col])
            self.people_tree.column(col, width=widths[col], anchor="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#fffdf9", fieldbackground="#fffdf9", foreground=TEXT, rowheight=28)
        style.configure("Treeview.Heading", background="#e8dfd1", foreground=TEXT, font=("Segoe UI Semibold", 10))

        self.people_tree.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        tk.Button(
            card,
            text="Refresh Records",
            bg=SIDEBAR_ACTIVE,
            fg="white",
            relief="flat",
            font=("Segoe UI", 10),
            command=self.refresh_people_table,
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _build_attendance_view(self) -> None:
        frame = self._register_view("attendance", "Attendance", "Launch recognition and show saved profile details when a face matches.")
        card = self._card(frame, "Live Attendance")
        card.pack(fill="x", padx=28, pady=12)
        tk.Label(
            card,
            text="Use the camera index from Camera Settings. The webcam window opens separately and closes when you press q.",
            bg=PANEL,
            fg=MUTED,
            wraplength=800,
            justify="left",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18, pady=(0, 12))
        tk.Button(
            card,
            text="Start Attendance",
            bg=ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 11),
            command=self.start_attendance,
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def _build_zone_view(self) -> None:
        frame = self._register_view("zone", "Zone Monitor", "Count people inside a campus zone and classify crowd level.")
        card = self._card(frame, "Zone Settings")
        card.pack(fill="x", padx=28, pady=12)
        self._entry_row(card, "Zone Name", self.zone_name_var)
        self._entry_row(card, "Capacity", self.zone_capacity_var)
        tk.Button(
            card,
            text="Start Zone Monitor",
            bg=ACCENT,
            fg="white",
            relief="flat",
            font=("Segoe UI Semibold", 11),
            command=self.start_zone_monitor,
        ).pack(anchor="w", padx=18, pady=(10, 18))

    def _build_camera_view(self) -> None:
        frame = self._register_view("camera", "Camera Settings", "Choose which webcam index the admin tools should use.")
        card = self._card(frame, "Camera Configuration")
        card.pack(fill="x", padx=28, pady=12)
        self._entry_row(card, "Camera Index", self.camera_index_var)
        tk.Label(
            card,
            text="Use 0 for your main webcam. If you have multiple cameras, try 1 or 2.",
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=18, pady=(0, 12))
        tk.Button(
            card,
            text="Save Camera Setting",
            bg=SIDEBAR_ACTIVE,
            fg="white",
            relief="flat",
            font=("Segoe UI", 10),
            command=lambda: self.set_status(f"Camera index set to {self.get_camera_index()}."),
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def _entry_row(self, parent: tk.Widget, label: str, variable: tk.StringVar, show: str | None = None) -> None:
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=18, pady=6)
        tk.Label(row, text=label, bg=PANEL, fg=TEXT, width=18, anchor="w", font=("Segoe UI", 10)).pack(side="left")
        entry = tk.Entry(row, textvariable=variable, show=show or "", font=("Segoe UI", 10), relief="solid", bd=1)
        entry.pack(side="left", fill="x", expand=True, ipady=6)

    def _combo_row(self, parent: tk.Widget, label: str, variable: tk.StringVar, values: list[str]) -> None:
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=18, pady=6)
        tk.Label(row, text=label, bg=PANEL, fg=TEXT, width=18, anchor="w", font=("Segoe UI", 10)).pack(side="left")
        combo = ttk.Combobox(row, textvariable=variable, values=values, state="readonly", font=("Segoe UI", 10))
        combo.pack(side="left", fill="x", expand=True)

    def _show_view(self, key: str) -> None:
        for name, frame in self.views.items():
            if name == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        for name, button in self.nav_buttons.items():
            button.configure(bg=SIDEBAR_ACTIVE if name == key else SIDEBAR)

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def get_camera_index(self) -> int:
        try:
            return int(self.camera_index_var.get().strip())
        except ValueError as exc:
            raise RuntimeError("Camera index must be a number.") from exc

    def ensure_logged_in(self) -> None:
        if not self.admin_logged_in:
            raise RuntimeError("Admin login is required for this action.")

    def create_admin_from_gui(self) -> None:
        try:
            backend.setup_admin(
                self.init_username_var.get().strip(),
                password=self.init_password_var.get(),
                confirm_password=self.init_confirm_password_var.get(),
                master_password=self.init_master_password_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Admin Setup", str(exc))
            return

        self.login_username_var.set(self.init_username_var.get().strip())
        self.set_status("Admin account created. You can sign in now.")
        messagebox.showinfo("Admin Setup", "Admin account created successfully.")

    def login_admin_from_gui(self) -> None:
        try:
            backend.verify_admin_login(
                self.login_username_var.get().strip(),
                self.login_password_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Admin Login", str(exc))
            return

        self.admin_logged_in = True
        self.admin_username = self.login_username_var.get().strip()
        self.login_state_label.configure(text=f"Logged in as {self.admin_username}.")
        self.set_status(f"Admin session active for {self.admin_username}.")
        messagebox.showinfo("Admin Login", "Login successful.")

    def clear_person_form(self) -> None:
        self.person_id_var.set("")
        self.person_name_var.set("")
        self.person_role_var.set("student")
        self.person_department_var.set("")
        self.person_email_var.set("")
        self.person_phone_var.set("")
        self.person_extra_info_var.set("")

    def refresh_dashboard(self) -> None:
        metadata = backend.load_metadata()
        people = metadata.get("people", {})
        students = sum(1 for person in people.values() if person.get("role") == "student")
        employees = sum(1 for person in people.values() if person.get("role") == "employee")

        attendance_today = 0
        if backend.ATTENDANCE_LOG_PATH.exists():
            today_key = backend.datetime.now().strftime("%Y-%m-%d")
            with backend.ATTENDANCE_LOG_PATH.open("r", newline="", encoding="utf-8") as file:
                reader = backend.csv.DictReader(file)
                attendance_today = sum(1 for row in reader if row["timestamp"].startswith(today_key))

        self.total_people_label.configure(text=str(len(people)))
        self.total_students_label.configure(text=str(students))
        self.total_employees_label.configure(text=str(employees))
        self.total_attendance_label.configure(text=str(attendance_today))

        self.dashboard_people_text.delete("1.0", tk.END)
        if people:
            for person_id, details in list(people.items())[-8:]:
                self.dashboard_people_text.insert(
                    tk.END,
                    f"{person_id} | {details.get('name', '')} | {details.get('role', '')}\n",
                )
        else:
            self.dashboard_people_text.insert(tk.END, "No people enrolled yet.\n")

        self.dashboard_logs_text.delete("1.0", tk.END)
        if backend.ATTENDANCE_LOG_PATH.exists():
            with backend.ATTENDANCE_LOG_PATH.open("r", newline="", encoding="utf-8") as file:
                reader = list(backend.csv.DictReader(file))
                for row in reader[-8:]:
                    self.dashboard_logs_text.insert(
                        tk.END,
                        f"{row['timestamp']} | {row['name']} | {row['role']}\n",
                    )
        else:
            self.dashboard_logs_text.insert(tk.END, "No attendance logs yet.\n")

    def refresh_people_table(self) -> None:
        for item in self.people_tree.get_children():
            self.people_tree.delete(item)

        metadata = backend.load_metadata()
        for person_id, details in metadata.get("people", {}).items():
            self.people_tree.insert(
                "",
                tk.END,
                values=(
                    person_id,
                    details.get("name", ""),
                    details.get("role", ""),
                    details.get("department", ""),
                    details.get("email", ""),
                    details.get("phone", ""),
                    details.get("extra_info", ""),
                ),
            )

        self.refresh_dashboard()

    def run_in_background(self, task, success_message: str | None = None) -> None:
        def worker() -> None:
            try:
                task()
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("Error", str(exc)))
                self.root.after(0, lambda: self.set_status(f"Error: {exc}"))
                return

            if success_message:
                self.root.after(0, lambda: messagebox.showinfo("Success", success_message))
            self.root.after(0, self.refresh_people_table)
            self.root.after(0, lambda: self.set_status(success_message or "Action completed."))

        threading.Thread(target=worker, daemon=True).start()

    def start_enrollment(self) -> None:
        try:
            self.ensure_logged_in()
            person_id = self.person_id_var.get().strip()
            name = self.person_name_var.get().strip()
            role = self.person_role_var.get().strip()

            if not person_id or not name:
                raise RuntimeError("Person ID and name are required.")

            camera_index = self.get_camera_index()
        except Exception as exc:
            messagebox.showerror("Enrollment", str(exc))
            return

        self.set_status(f"Enrollment started for {name}.")

        def task() -> None:
            backend.enroll_person(
                admin_username=self.admin_username,
                person_id=person_id,
                name=name,
                role=role,
                department=self.person_department_var.get().strip(),
                email=self.person_email_var.get().strip(),
                phone=self.person_phone_var.get().strip(),
                extra_info=self.person_extra_info_var.get().strip(),
                camera_index=camera_index,
            )

        self.run_in_background(task, f"Enrollment finished for {name}.")

    def start_attendance(self) -> None:
        try:
            camera_index = self.get_camera_index()
        except Exception as exc:
            messagebox.showerror("Attendance", str(exc))
            return

        self.set_status("Attendance window opened.")
        self.run_in_background(
            lambda: backend.run_attendance(camera_index=camera_index),
            "Attendance session closed.",
        )

    def start_zone_monitor(self) -> None:
        try:
            camera_index = self.get_camera_index()
            zone_name = self.zone_name_var.get().strip() or "Zone"
            capacity = int(self.zone_capacity_var.get().strip())
        except Exception as exc:
            messagebox.showerror("Zone Monitor", str(exc))
            return

        self.set_status(f"Zone monitor started for {zone_name}.")
        self.run_in_background(
            lambda: backend.run_zone_monitor(zone_name=zone_name, max_capacity=capacity, camera_index=camera_index),
            f"Zone monitor closed for {zone_name}.",
        )


def main() -> None:
    root = tk.Tk()
    app = SmartAttendanceAdminApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
