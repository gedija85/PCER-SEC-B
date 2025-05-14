import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# ---------- DATABASE ----------
conn = sqlite3.connect('pcer.db')
cursor = conn.cursor()

# Registration Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pc_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        university_id TEXT NOT NULL,
        phone TEXT NOT NULL,
        pc_serial TEXT NOT NULL UNIQUE,
        registration_time TEXT NOT NULL
    )
""")

# Verification Record Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pc_serial TEXT NOT NULL,
        phone TEXT NOT NULL,
        verification_time TEXT NOT NULL,
        gate TEXT NOT NULL,
        verification_type TEXT NOT NULL CHECK (verification_type IN ('ENTRY', 'EXIT'))
    )
""")
conn.commit()

# ---------- APPLICATION LOGIC ----------
class PCERApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCER - PERSONAL COMPUTER ENTRY REGISTRATION")
        self.root.geometry("1000x600")
        self.root.configure(bg="#f0f0f0")

        self.inputs = {}
        self.step = 0
        self.steps = [
            ("ENTER STUDENT NAME", "name"),
            ("ENTER ID NUMBER (ETS----/--)", "university_id"),
            ("ENTER PHONE NUMBER", "phone"),
            ("ENTER SERIAL NUMBER", "pc_serial"),
            ("SELECT EXIT GATE", "exit_gate")
        ]
        self.mode = tk.StringVar(value="register")
        self.exit_gate = tk.StringVar(value="KILLINTO GATE")

        self.build_interface()

    def build_interface(self):
        self.label = tk.Label(self.root, text="", font=('Segoe UI', 14, 'bold'), bg="#f0f0f0")
        self.label.pack(pady=20)

        self.input_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.input_frame.pack(pady=5)

        self.entry = ttk.Entry(self.input_frame, font=('Segoe UI', 12), width=40)
        self.entry.pack(pady=5, side="left", padx=(0, 20))

        tk.Label(self.input_frame, text="EXIT GATE:", font=('Segoe UI', 11, 'bold'), bg="#f0f0f0").pack(side="left", padx=10)
        ttk.Radiobutton(self.input_frame, text="KILLINTO GATE", variable=self.exit_gate, value="KILLINTO GATE").pack(side="left", padx=5)
        ttk.Radiobutton(self.input_frame, text="TULUDIMTU GATE", variable=self.exit_gate, value="TULUDIMTU GATE").pack(side="left", padx=5)

        self.btn_next = ttk.Button(self.root, text="NEXT", command=self.next_step)
        self.btn_next.pack(pady=15)

        self.mode_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.mode_frame.pack(pady=10)
        tk.Label(self.mode_frame, text="MODE:", font=('Segoe UI', 11, 'bold'), bg="#f0f0f0").pack(side='left', padx=10)
        ttk.Radiobutton(self.mode_frame, text="REGISTER", variable=self.mode, value="register").pack(side='left', padx=10)
        ttk.Radiobutton(self.mode_frame, text="VERIFY ENTRY", variable=self.mode, value="entry").pack(side='left', padx=10)
        ttk.Radiobutton(self.mode_frame, text="VERIFY EXIT", variable=self.mode, value="exit").pack(side='left', padx=10)

        self.btn_new = ttk.Button(self.root, text="NEW", command=self.reset_ui)
        self.btn_new.pack(pady=10)

        self.btn_records = ttk.Button(self.root, text="RECORDS", command=self.show_exit_records)
        self.btn_records.pack(pady=10)

        self.tree_frame = tk.Frame(self.root)
        self.tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.reset_ui()

    def reset_ui(self):
        self.step = 0
        self.inputs.clear()
        self.label.config(text=self.steps[self.step][0])
        self.entry.delete(0, tk.END)
        self.entry.focus_set()

    def next_step(self):
        key = self.steps[self.step][1]

        if key == "exit_gate":
            self.inputs["exit_gate"] = self.exit_gate.get()
        else:
            value = self.entry.get().strip()
            if not value:
                messagebox.showerror("Missing Input", "This field cannot be empty.")
                return
            self.inputs[key] = value.upper()
            self.entry.delete(0, tk.END)

        self.step += 1

        if self.step < len(self.steps):
            self.label.config(text=self.steps[self.step][0])
        else:
            mode = self.mode.get()
            if mode == "register":
                self.register_pc()
            elif mode == "entry":
                self.verify_pc("ENTRY")
            elif mode == "exit":
                self.verify_pc("EXIT")
            self.reset_ui()

    def register_pc(self):
        now = datetime.now().isoformat()
        try:
            cursor.execute("""
                INSERT INTO pc_registry (name, university_id, phone, pc_serial, registration_time)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.inputs["name"],
                self.inputs["university_id"],
                self.inputs["phone"],
                self.inputs["pc_serial"],
                now
            ))
            conn.commit()
            messagebox.showinfo("Success", f"REGISTERED: {self.inputs['name']} ({self.inputs['university_id']})")
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "This PC has already been registered.")

    def get_last_verification_type(self, pc_serial):
        cursor.execute("""
            SELECT verification_type FROM verification_record
            WHERE LOWER(pc_serial) = ?
            ORDER BY id DESC LIMIT 1
        """, (pc_serial.lower(),))
        result = cursor.fetchone()
        return result[0] if result else None

    def verify_pc(self, v_type):
        pc_serial = self.inputs["pc_serial"].lower()
        phone = self.inputs["phone"].lower()

        # Check if PC is registered
        cursor.execute("""
            SELECT name, university_id FROM pc_registry
            WHERE LOWER(pc_serial) = ? AND LOWER(phone) = ?
        """, (pc_serial, phone))
        record = cursor.fetchone()

        if not record:
            messagebox.showerror("Not Found", "No such PC registration found.")
            return

        # Logical verification: check last verification type
        last_type = self.get_last_verification_type(pc_serial)

        if v_type == "ENTRY" and last_type == "ENTRY":
            messagebox.showerror("Invalid Action", "You already entered. Cannot enter again before exiting.")
            return
        if v_type == "EXIT":
            if last_type != "ENTRY":
                messagebox.showerror("Invalid Action", "You must enter before you can exit.")
                return

        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO verification_record (pc_serial, phone, verification_time, gate, verification_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.inputs["pc_serial"],
            self.inputs["phone"],
            now,
            self.exit_gate.get(),
            v_type
        ))
        conn.commit()
        messagebox.showinfo(f"{v_type} Verified", f"{v_type} recorded for {record[0]} ({record[1]}) at {now}")

    def show_exit_records(self):
        for widget in self.tree_frame.winfo_children():
            widget.destroy()

        # LEFT PANEL - REGISTERED
        left_frame = tk.Frame(self.tree_frame, bg="#f0f0f0")
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        tk.Label(left_frame, text="REGISTERED", font=('Segoe UI', 12, 'bold'), bg="#f0f0f0").pack(pady=5)

        columns_left = ("Name", "ID", "Phone", "PC Serial")
        tree_left = ttk.Treeview(left_frame, columns=columns_left, show="headings", height=10)
        tree_left.pack(expand=True, fill="both", padx=5)
        for col in columns_left:
            tree_left.heading(col, text=col)
            tree_left.column(col, width=120)
        cursor.execute("SELECT name, university_id, phone, pc_serial FROM pc_registry ORDER BY registration_time DESC")
        for row in cursor.fetchall():
            tree_left.insert("", tk.END, values=row)

        # RIGHT PANEL - VERIFIED
        right_frame = tk.Frame(self.tree_frame, bg="#f0f0f0")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        tk.Label(right_frame, text="VERIFIED", font=('Segoe UI', 12, 'bold'), bg="#f0f0f0").pack(pady=5)
        search_frame = tk.Frame(right_frame, bg="#f0f0f0")
        search_frame.pack(pady=5)
        tk.Label(search_frame, text="ID:", font=('Segoe UI', 10), bg="#f0f0f0").pack(side="left")
        self.search_id_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_id_var, width=25).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Retrieve Info", command=self.retrieve_verified_info).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Show Verified Date List", command=self.show_verified_dates).pack(pady=5)

        self.verified_tree = ttk.Treeview(right_frame, columns=("List", "Type", "Time", "Day", "Month", "Year"), show="headings", height=10)
        for col in ("List", "Type", "Time", "Day", "Month", "Year"):
            self.verified_tree.heading(col, text=col)
            self.verified_tree.column(col, width=90)
        self.verified_tree.pack(expand=True, fill="both", padx=5, pady=5)

    def retrieve_verified_info(self):
        self.verified_tree.delete(*self.verified_tree.get_children())
        id_input = self.search_id_var.get().strip().upper()
        if not id_input:
            messagebox.showwarning("Input Required", "Please enter an ID number.")
            return
        cursor.execute("""
            SELECT DISTINCT verification_time, verification_type FROM verification_record
            WHERE phone IN (
                SELECT phone FROM pc_registry WHERE university_id = ?
            )
            ORDER BY verification_time DESC
        """, (id_input,))
        records = cursor.fetchall()
        for i, row in enumerate(records, 1):
            dt = datetime.fromisoformat(row[0])
            self.verified_tree.insert("", tk.END, values=(
                i, row[1], dt.strftime("%H:%M"), dt.strftime("%A"), dt.strftime("%B"), dt.strftime("%Y")
            ))

    def show_verified_dates(self):
        self.retrieve_verified_info()

# ---------- RUN ----------
root = tk.Tk()
app = PCERApp(root)
root.mainloop()
conn.close()
