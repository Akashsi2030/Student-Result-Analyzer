from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

APP_DIR = Path(__file__).resolve().parent
CSV_PATH = APP_DIR / "students.csv"
SUBJECTS = ["Maths", "Science", "English"]
BASE_COLUMNS = ["RollNo", "Name"] + SUBJECTS
ATTENDANCE_COLUMN = "Attendance"
PASS_MARK = 33
GRADE_ORDER = ["A+", "A", "B", "C", "D", "F"]

# -------------------- Data handling --------------------
def load_data(path=CSV_PATH):
    """Load CSV and support the original file format without Attendance."""
    if not path.exists():
        pd.DataFrame(columns=BASE_COLUMNS + [ATTENDANCE_COLUMN]).to_csv(path, index=False)
    df = pd.read_csv(path)
    missing = [c for c in BASE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required CSV columns: " + ", ".join(missing))
    df = df.copy()
    df["RollNo"] = df["RollNo"].fillna("").astype(str).str.strip()
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    for subject in SUBJECTS:
        df[subject] = pd.to_numeric(df[subject], errors="raise")
    # Backward compatibility: old students.csv files did not have attendance.
    if ATTENDANCE_COLUMN not in df.columns:
        df[ATTENDANCE_COLUMN] = 100.0
    df[ATTENDANCE_COLUMN] = pd.to_numeric(df[ATTENDANCE_COLUMN], errors="coerce").fillna(100.0)
    if not df.empty:
        if ((df[SUBJECTS] < 0) | (df[SUBJECTS] > 100)).any().any():
            raise ValueError("Subject marks must be between 0 and 100.")
        if ((df[ATTENDANCE_COLUMN] < 0) | (df[ATTENDANCE_COLUMN] > 100)).any():
            raise ValueError("Attendance must be between 0 and 100.")
    return df[BASE_COLUMNS + [ATTENDANCE_COLUMN]]


def grade_for(percentage):
    if percentage >= 90: return "A+"
    if percentage >= 75: return "A"
    if percentage >= 60: return "B"
    if percentage >= 45: return "C"
    if percentage >= PASS_MARK: return "D"
    return "F"


def compute_results(df):
    """Calculate totals, average percentage, grade and pass/fail with NumPy."""
    df = df.copy()
    if df.empty:
        for c in ["Total", "Percentage", "Grade", "Result"]:
            df[c] = pd.Series(dtype="object")
        return df
    marks = df[SUBJECTS].to_numpy(dtype=float)
    df["Total"] = np.sum(marks, axis=1).astype(int)
    df["Percentage"] = np.round(np.mean(marks, axis=1), 2)
    df["Grade"] = df["Percentage"].apply(grade_for)
    df["Result"] = np.where((df[SUBJECTS] >= PASS_MARK).all(axis=1), "Pass", "Fail")
    return df


# -------------------- Main UI --------------------
class App(tk.Tk):
    NAVY = "#172554"
    BLUE = "#2563EB"
    BG = "#F3F6FB"
    TEXT = "#172033"
    MUTED = "#64748B"
    GREEN = "#15803D"
    RED = "#B91C1C"
    WHITE = "#FFFFFF"

    def __init__(self):
        super().__init__()
        self.title("Student Result Analyzer | Academic Management")
        self.geometry("1280x790")
        self.minsize(1000, 650)
        self.configure(bg=self.BG)
        try:
            self.df = compute_results(load_data())
        except Exception as exc:
            messagebox.showerror("Unable to load data", f"Please check students.csv.\n\n{exc}")
            self.destroy()
            return
        self.filtered_df = self.df.copy()
        self.setup_styles()
        self.build_ui()
        self.refresh_table()
        self.update_stats()

    def setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground=self.TEXT, rowheight=32, borderwidth=0,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#E8EEF8", foreground=self.NAVY,
                        font=("Segoe UI", 9, "bold"), padding=(7, 10), relief="flat")
        style.map("Treeview", background=[("selected", "#DBEAFE")],
                  foreground=[("selected", self.NAVY)])
        style.configure("TCombobox", padding=5)

    def build_ui(self):
        header = tk.Frame(self, bg=self.NAVY, padx=26, pady=18)
        header.pack(fill="x")
        left = tk.Frame(header, bg=self.NAVY)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="STUDENT RESULT ANALYZER", bg=self.NAVY, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(left, text="Academic Performance Management System  •  Python Mini Project",
                 bg=self.NAVY, fg="#CBD5E1", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        tk.Label(header, text="●  CSV CONNECTED", bg=self.NAVY, fg="#BBF7D0",
                 font=("Segoe UI", 9, "bold")).pack(side="right")

        body = tk.Frame(self, bg=self.BG, padx=22, pady=18)
        body.pack(fill="both", expand=True)

        self.stat_vars = {k: tk.StringVar(value="—") for k in
                          ["students", "average", "pass_rate", "attendance"]}
        cards = tk.Frame(body, bg=self.BG)
        cards.pack(fill="x", pady=(0, 16))
        card_specs = [
            ("TOTAL STUDENTS", "students", "Student records"),
            ("CLASS AVERAGE", "average", "Average percentage"),
            ("PASS RATE", "pass_rate", "Passed all subjects"),
            ("AVG. ATTENDANCE", "attendance", "Recorded attendance"),
        ]
        for i, (heading, key, note) in enumerate(card_specs):
            card = tk.Frame(cards, bg="white", highlightbackground="#E2E8F0",
                            highlightthickness=1, padx=16, pady=12)
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            cards.grid_columnconfigure(i, weight=1, uniform="cards")
            tk.Label(card, text=heading, bg="white", fg=self.MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            tk.Label(card, textvariable=self.stat_vars[key], bg="white", fg=self.NAVY,
                     font=("Segoe UI", 21, "bold")).pack(anchor="w", pady=(5, 0))
            tk.Label(card, text=note, bg="white", fg="#94A3B8",
                     font=("Segoe UI", 9)).pack(anchor="w")

        panel = tk.Frame(body, bg="white", highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(fill="both", expand=True)
        toolbar = tk.Frame(panel, bg="white", padx=14, pady=12)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="Student Records", bg="white", fg=self.TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        self.count_label = tk.Label(toolbar, text="", bg="white", fg=self.MUTED,
                                    font=("Segoe UI", 9))
        self.count_label.pack(side="left", padx=10)

        actions = tk.Frame(toolbar, bg="white")
        actions.pack(side="right")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(actions, textvariable=self.search_var, width=23,
                                     relief="solid", bd=1, font=("Segoe UI", 9))
        self.search_entry.pack(side="left", ipady=6, padx=(0, 7))
        self.search_entry.insert(0, "Search name or roll no...")
        self.search_entry.config(fg="#94A3B8")
        self.search_entry.bind("<FocusIn>", self.clear_placeholder)
        self.search_entry.bind("<FocusOut>", self.restore_placeholder)
        self.search_entry.bind("<KeyRelease>", lambda _e: self.apply_filter())
        self.make_button(actions, "Search", self.apply_filter, "secondary").pack(side="left", padx=(0, 6))
        self.make_button(actions, "+ Add Student", self.add_dialog, "primary").pack(side="left")

        table_frame = tk.Frame(panel, bg="white")
        table_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.columns = ["RollNo", "Name"] + SUBJECTS + ["Total", "Percentage", "Grade", "Result", ATTENDANCE_COLUMN]
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        widths = {"RollNo": 68, "Name": 155, "Maths": 72, "Science": 72, "English": 72,
                  "Total": 72, "Percentage": 90, "Grade": 65, "Result": 70, "Attendance": 100}
        for col in self.columns:
            self.tree.heading(col, text=("Attendance %" if col == ATTENDANCE_COLUMN else col))
            self.tree.column(col, width=widths.get(col, 80), anchor="w" if col == "Name" else "center",
                             minwidth=58, stretch=(col == "Name"))
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.tag_configure("pass", foreground=self.GREEN)
        self.tree.tag_configure("fail", foreground=self.RED)
        self.tree.bind("<Double-1>", lambda _e: self.edit_dialog())

        footer = tk.Frame(body, bg=self.BG, pady=10)
        footer.pack(fill="x")
        tk.Label(footer, text="Tip: double-click a student to edit. Select a row for its report card.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9)).pack(side="left")
        right = tk.Frame(footer, bg=self.BG)
        right.pack(side="right")
        self.make_button(right, "Analytics", self.show_analytics, "secondary").pack(side="left", padx=3)
        self.make_button(right, "Attendance", self.show_attendance_summary, "secondary").pack(side="left", padx=3)
        self.make_button(right, "Export Reports", self.export_reports, "secondary").pack(side="left", padx=3)
        self.make_button(right, "View Result", self.search_selected, "secondary").pack(side="left", padx=3)
        self.make_button(right, "Edit", self.edit_dialog, "secondary").pack(side="left", padx=3)
        self.make_button(right, "Delete", self.delete_selected, "danger").pack(side="left", padx=3)

    def make_button(self, parent, label, command, kind="secondary"):
        colors = {
            "primary": (self.BLUE, "white", "#1D4ED8"),
            "secondary": ("#E8EEF8", self.NAVY, "#D7E3F7"),
            "danger": ("#FEE2E2", self.RED, "#FECACA"),
        }
        bg, fg, active = colors[kind]
        return tk.Button(parent, text=label, command=command, bg=bg, fg=fg,
                         activebackground=active, activeforeground=fg, relief="flat", bd=0,
                         padx=10, pady=7, cursor="hand2", font=("Segoe UI", 9, "bold"))

    def clear_placeholder(self, _event=None):
        if self.search_entry.get() == "Search name or roll no...":
            self.search_entry.delete(0, "end")
            self.search_entry.config(fg=self.TEXT)

    def restore_placeholder(self, _event=None):
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, "Search name or roll no...")
            self.search_entry.config(fg="#94A3B8")

    def persist_data(self):
        self.df[BASE_COLUMNS + [ATTENDANCE_COLUMN]].to_csv(CSV_PATH, index=False)

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for _, row in self.filtered_df.iterrows():
            vals = []
            for col in self.columns:
                if col == "Percentage":
                    vals.append(f"{float(row[col]):.2f}%")
                elif col == ATTENDANCE_COLUMN:
                    vals.append(f"{float(row[col]):.1f}%")
                else:
                    vals.append(row[col])
            self.tree.insert("", "end", values=vals,
                             tags=("pass" if row["Result"] == "Pass" else "fail",))
        self.count_label.config(text=f"{len(self.filtered_df)} shown")

    def update_stats(self):
        total = len(self.df)
        self.stat_vars["students"].set(str(total))
        self.stat_vars["average"].set(f"{self.df['Percentage'].mean():.1f}%" if total else "—")
        self.stat_vars["pass_rate"].set(f"{self.df['Result'].eq('Pass').mean() * 100:.0f}%" if total else "—")
        self.stat_vars["attendance"].set(f"{self.df[ATTENDANCE_COLUMN].mean():.1f}%" if total else "—")

    def apply_filter(self):
        query = self.search_var.get().strip().lower()
        if query == "search name or roll no...":
            query = ""
        if query:
            mask = (self.df["Name"].str.lower().str.contains(query, na=False) |
                    self.df["RollNo"].str.lower().str.contains(query, na=False))
            self.filtered_df = self.df[mask].copy()
        else:
            self.filtered_df = self.df.copy()
        self.refresh_table()

    def selected_roll_no(self):
        selected = self.tree.selection()
        return str(self.tree.item(selected[0])["values"][0]) if selected else None

    def search_selected(self):
        roll = self.selected_roll_no()
        if roll is None:
            messagebox.showinfo("Select a student", "Please select a student row first.", parent=self)
        else:
            self.show_result(roll)

    def show_result(self, roll_no):
        rows = self.df[self.df["RollNo"].astype(str) == str(roll_no)]
        if rows.empty:
            return
        r = rows.iloc[0]
        win = tk.Toplevel(self)
        win.title("Student Result Card")
        win.configure(bg="white")
        win.resizable(False, False)
        win.transient(self)
        box = tk.Frame(win, bg="white", padx=26, pady=22)
        box.pack(fill="both", expand=True)
        tk.Label(box, text="STUDENT RESULT CARD", bg="white", fg=self.BLUE,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(box, text=r["Name"], bg="white", fg=self.NAVY,
                 font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(7, 2))
        tk.Label(box, text=f"Roll No: {r['RollNo']}   •   Attendance: {r[ATTENDANCE_COLUMN]:.1f}%",
                 bg="white", fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 14))
        for subject in SUBJECTS:
            line = tk.Frame(box, bg="#F8FAFC", padx=12, pady=8)
            line.pack(fill="x", pady=3)
            tk.Label(line, text=subject, bg="#F8FAFC", fg=self.TEXT, width=14,
                     anchor="w", font=("Segoe UI", 10)).pack(side="left")
            tk.Label(line, text=f"{r[subject]} / 100", bg="#F8FAFC", fg=self.TEXT,
                     font=("Segoe UI", 10, "bold")).pack(side="right")
        tk.Label(box, text=f"Total: {r['Total']} / 300    •    Percentage: {r['Percentage']:.2f}%",
                 bg="white", fg=self.NAVY, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(13, 5))
        tk.Label(box, text=f"Grade: {r['Grade']}    |    Result: {r['Result']}",
                 bg="white", fg=self.GREEN if r["Result"] == "Pass" else self.RED,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.make_button(box, "Close", win.destroy, "secondary").pack(anchor="e", pady=(16, 0))
        win.update_idletasks()
        win.geometry(f"{max(400, win.winfo_reqwidth())}x{win.winfo_reqheight()}")

    def open_form(self, title, prefill=None, on_save=None):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg="white")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        outer = tk.Frame(win, bg="white", padx=24, pady=20)
        outer.pack(fill="both", expand=True)
        tk.Label(outer, text=title, bg="white", fg=self.NAVY,
                 font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))
        fields = ["RollNo", "Name"] + SUBJECTS + [ATTENDANCE_COLUMN]
        entries = {}
        for i, field in enumerate(fields, start=1):
            label = {"RollNo": "Roll Number", ATTENDANCE_COLUMN: "Attendance (%)"}.get(field, field)
            tk.Label(outer, text=label, bg="white", fg=self.TEXT,
                     font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", padx=(0, 18), pady=6)
            entry = tk.Entry(outer, width=30, relief="solid", bd=1, font=("Segoe UI", 10))
            entry.grid(row=i, column=1, sticky="ew", ipady=5, pady=6)
            if prefill is not None:
                entry.insert(0, str(prefill[field]))
            elif field == ATTENDANCE_COLUMN:
                entry.insert(0, "100")
            entries[field] = entry
        tk.Label(outer, text="Marks: 0–100 each. Attendance: 0–100%.",
                 bg="white", fg=self.MUTED, font=("Segoe UI", 9)).grid(
                     row=len(fields)+1, column=0, columnspan=2, sticky="w", pady=(7, 12))

        def save():
            roll = entries["RollNo"].get().strip()
            name = entries["Name"].get().strip()
            if not roll or not name:
                messagebox.showerror("Missing details", "Roll number and name are required.", parent=win)
                return
            try:
                marks = {s: int(entries[s].get().strip()) for s in SUBJECTS}
                attendance = float(entries[ATTENDANCE_COLUMN].get().strip())
            except ValueError:
                messagebox.showerror("Invalid input", "Marks must be whole numbers and attendance must be numeric.", parent=win)
                return
            if any(mark < 0 or mark > 100 for mark in marks.values()):
                messagebox.showerror("Invalid marks", "Each subject mark must be between 0 and 100.", parent=win)
                return
            if not 0 <= attendance <= 100:
                messagebox.showerror("Invalid attendance", "Attendance must be between 0 and 100.", parent=win)
                return
            values = {"RollNo": roll, "Name": name, **marks, ATTENDANCE_COLUMN: attendance}
            if on_save(values) is not False:
                win.destroy()

        buttons = tk.Frame(outer, bg="white")
        buttons.grid(row=len(fields)+2, column=0, columnspan=2, sticky="e", pady=(4, 0))
        self.make_button(buttons, "Cancel", win.destroy, "secondary").pack(side="left", padx=(0, 8))
        self.make_button(buttons, "Save Student", save, "primary").pack(side="left")
        entries["RollNo"].focus_set()

    def add_dialog(self):
        def save(values):
            if self.df["RollNo"].astype(str).eq(values["RollNo"]).any():
                messagebox.showerror("Duplicate roll number", "That roll number already exists.", parent=self)
                return False
            source = pd.concat([self.df[BASE_COLUMNS + [ATTENDANCE_COLUMN]], pd.DataFrame([values])],
                               ignore_index=True)
            self.df = compute_results(source)
            self.persist_data()
            self.apply_filter()
            self.update_stats()
            return True
        self.open_form("Add Student", on_save=save)

    def edit_dialog(self):
        roll = self.selected_roll_no()
        if roll is None:
            messagebox.showwarning("Select a student", "Select a student row before editing.", parent=self)
            return
        row = self.df[self.df["RollNo"].astype(str) == roll].iloc[0]
        def save(values):
            duplicate = self.df[(self.df["RollNo"].astype(str) == values["RollNo"]) &
                                (self.df["RollNo"].astype(str) != roll)]
            if not duplicate.empty:
                messagebox.showerror("Duplicate roll number", "That roll number belongs to another student.", parent=self)
                return False
            idx = self.df.index[self.df["RollNo"].astype(str) == roll][0]
            for key, value in values.items():
                self.df.loc[idx, key] = value
            self.df = compute_results(self.df[BASE_COLUMNS + [ATTENDANCE_COLUMN]])
            self.persist_data()
            self.apply_filter()
            self.update_stats()
            return True
        self.open_form("Edit Student", prefill=row, on_save=save)

    def delete_selected(self):
        roll = self.selected_roll_no()
        if roll is None:
            messagebox.showwarning("Select a student", "Select a student row before deleting.", parent=self)
            return
        name = self.df.loc[self.df["RollNo"].astype(str) == roll, "Name"].iloc[0]
        if messagebox.askyesno("Confirm deletion", f"Delete {name} (Roll No. {roll})?",
                               parent=self):
            self.df = self.df[self.df["RollNo"].astype(str) != roll].copy()
            self.persist_data()
            self.apply_filter()
            self.update_stats()

    # -------------------- Analytics and attendance --------------------
    def show_analytics(self):
        if self.df.empty:
            messagebox.showinfo("No data", "Add students before opening analytics.", parent=self)
            return
        win = tk.Toplevel(self)
        win.title("Academic Performance Analytics")
        win.geometry("760x570")
        win.configure(bg="white")
        tk.Label(win, text="Academic Performance Analytics", bg="white", fg=self.NAVY,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=(16, 3))
        avg = self.df[SUBJECTS].mean().round(1)
        grade_counts = self.df["Grade"].value_counts().reindex(GRADE_ORDER, fill_value=0)
        fig, axes = plt.subplots(1, 2, figsize=(9, 4.3), facecolor="white")
        axes[0].bar(avg.index, avg.values)
        axes[0].set_title("Average Marks by Subject")
        axes[0].set_ylim(0, 100)
        axes[0].set_ylabel("Average marks / 100")
        axes[0].grid(axis="y", alpha=.25)
        axes[1].bar(grade_counts.index, grade_counts.values)
        axes[1].set_title("Grade Distribution")
        axes[1].set_ylabel("Number of students")
        axes[1].grid(axis="y", alpha=.25)
        for ax in axes:
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
        fig.tight_layout()
        # Embed chart into the analytics window, avoiding a separate popup.
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=8)
        plt.close(fig)
        top = self.df.sort_values("Percentage", ascending=False).head(3)
        text = "Top performers: " + ("  •  ".join(
            f"{r['Name']} ({r['Percentage']:.1f}%)" for _, r in top.iterrows()) if not top.empty else "No records")
        tk.Label(win, text=text, bg="white", fg=self.MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(0, 14))

    def show_attendance_summary(self):
        if self.df.empty:
            messagebox.showinfo("No data", "Add students before viewing attendance.", parent=self)
            return
        avg = self.df[ATTENDANCE_COLUMN].mean()
        below = self.df[self.df[ATTENDANCE_COLUMN] < 75].sort_values(ATTENDANCE_COLUMN)
        lines = [f"Class average attendance: {avg:.1f}%",
                 f"Students with attendance below 75%: {len(below)}", ""]
        if below.empty:
            lines.append("All students have attendance of at least 75%.")
        else:
            lines.append("Students to follow up:")
            lines.extend(f"• {r['Name']} (Roll {r['RollNo']}): {r[ATTENDANCE_COLUMN]:.1f}%"
                         for _, r in below.iterrows())
        messagebox.showinfo("Attendance Summary", "\n".join(lines), parent=self)

    # -------------------- Reports / export --------------------
    def export_reports(self):
        if self.df.empty:
            messagebox.showinfo("No data", "There are no student records to export.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Export student reports",
            defaultextension=".xlsx",
            filetypes=[("Excel workbook", "*.xlsx"), ("CSV file", "*.csv"),
                       ("PDF report", "*.pdf")],
            initialfile="student_result_report.xlsx")
        if not path:
            return
        target = Path(path)
        try:
            report = self.df.copy()
            report["Percentage"] = report["Percentage"].map(lambda x: round(float(x), 2))
            if target.suffix.lower() == ".csv":
                report.to_csv(target, index=False)
            elif target.suffix.lower() == ".xlsx":
                try:
                    with pd.ExcelWriter(target, engine="openpyxl") as writer:
                        report.to_excel(writer, sheet_name="Student Results", index=False)
                        subject_summary = pd.DataFrame({
                            "Subject": SUBJECTS,
                            "Average Marks": [round(float(self.df[s].mean()), 2) for s in SUBJECTS]
                        })
                        subject_summary.to_excel(writer, sheet_name="Subject Analysis", index=False)
                except ImportError:
                    messagebox.showerror("Excel dependency missing",
                                         "Install openpyxl using:\npip install openpyxl", parent=self)
                    return
            elif target.suffix.lower() == ".pdf":
                self.export_pdf(target)
            else:
                messagebox.showerror("Unsupported format", "Choose XLSX, CSV, or PDF.", parent=self)
                return
            messagebox.showinfo("Export complete", f"Report saved successfully:\n{target}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export failed", f"Could not create the report.\n\n{exc}", parent=self)

    def export_pdf(self, target):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            raise RuntimeError("PDF export requires ReportLab. Install it with:\npip install reportlab")
        doc = SimpleDocTemplate(str(target), pagesize=landscape(A4),
                                rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Student Result Analyzer", styles["Title"]),
            Paragraph("Academic Performance Report", styles["Heading2"]),
            Paragraph(f"Students: {len(self.df)} | Class average: {self.df['Percentage'].mean():.2f}% | "
                      f"Pass rate: {self.df['Result'].eq('Pass').mean()*100:.1f}% | "
                      f"Average attendance: {self.df[ATTENDANCE_COLUMN].mean():.1f}%", styles["Normal"]),
            Spacer(1, 14)
        ]
        headers = ["Roll No", "Name"] + SUBJECTS + ["Total", "Percent", "Grade", "Result", "Attendance"]
        rows = [headers]
        for _, r in self.df.iterrows():
            rows.append([str(r["RollNo"]), str(r["Name"])] +
                        [str(int(r[s])) for s in SUBJECTS] +
                        [str(int(r["Total"])), f"{r['Percentage']:.2f}%", str(r["Grade"]),
                         str(r["Result"]), f"{r[ATTENDANCE_COLUMN]:.1f}%"])
        table = Table(rows, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172554")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6FB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)
        doc.build(story)


if __name__ == "__main__":
    app = App()
    if app.winfo_exists():
        app.mainloop()
