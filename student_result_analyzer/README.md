# Student Result Analyzer & Academic Performance Management System

## Features
- Clean light-theme Tkinter dashboard
- Student add, edit, delete, and search
- Automatic total, percentage, grade, and pass/fail calculation
- Dashboard statistics and subject/grade analytics charts
- Attendance percentage field and low-attendance summary (below 75%)
- Export report as Excel (.xlsx), CSV, or PDF
- Backward-compatible with the original students.csv (missing attendance defaults to 100%)

## Requirements
Python 3.10+ recommended.

Install required packages:
```bash
pip install pandas numpy matplotlib openpyxl reportlab
```

## Run
Keep `app.py` and `students.csv` in the same folder, then run:
```bash
python app.py
```

## Notes
- Marks must be whole numbers from 0 to 100.
- Attendance is a percentage from 0 to 100.
- A student passes only if they score at least 33 in every subject.
- Attendance below 75% is flagged in the attendance summary. This is a configurable project rule, not an official college policy.
- The app saves changes to students.csv. Keep a backup before making major edits.
