# Equipment Runtime & Maintenance Tracker

A self-contained Python application that connects to a **WinCC OA PostgreSQL historian** database, calculates equipment run hours from event-driven signal data, and auto-generates a professional **weekly PDF maintenance report** with color-coded alerts.

No GUI — all equipment data is hardcoded in Python. Designed to run unattended on a Windows machine via Task Scheduler.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [First-Time Database Setup](#first-time-database-setup)
- [Running the Report](#running-the-report)
- [Understanding the PDF Report](#understanding-the-pdf-report)
- [Customizing Equipment](#customizing-equipment)
- [Configuring Signal Tag Names](#configuring-signal-tag-names)
- [Scheduling Weekly Reports (Windows)](#scheduling-weekly-reports-windows)
- [Adding New Equipment](#adding-new-equipment)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## How It Works

```
 ┌────────────────────┐       ┌──────────────────────┐       ┌──────────────┐
 │   equipment.py     │       │  WinCC OA PostgreSQL  │       │  PDF Report  │
 │  (equipment data,  │──────▶│   Historian Database  │──────▶│  with alerts │
 │   maint. dates)    │       │  (get_equipment_      │       │  & metrics   │
 │                    │       │   run_hours function)  │       │              │
 └────────────────────┘       └──────────────────────┘       └──────────────┘
```

1. **equipment.py** holds all equipment metadata — IDs, labels, maintenance dates, and intervals.
2. **main.py** queries the database for each equipment's run hours since last maintenance and since commissioning (lifetime hours).
3. A deployed **SQL function** (`get_equipment_run_hours`) handles all the heavy computation inside PostgreSQL — scanning dynamic `_event_<segment_id>_a` tables, detecting ON/OFF transitions with `LAG()` window functions, applying debounce filtering, and handling open-ended intervals.
4. **main.py** computes derived metrics in Python: hours remaining, % consumed, projected next maintenance date, and alert flags.
5. **report/generator.py** renders a professional PDF with ReportLab — color-coded rows, progress bars, and notes.

### Key Design Decisions

- **All timestamps are nanoseconds since epoch** (BIGINT) — the WinCC OA historian standard.
- **Event-driven data** — rows only exist when signal values change, not at fixed sample intervals.
- **No dynamic dispatch** — every equipment has its own explicit query function and explicit call in `main.py` for maximum readability and debuggability.
- **Graceful error handling** — if a signal query fails, that equipment gets 0.0 hours and the report still generates.
- **Fully offline** — no internet dependency.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or higher |
| **PostgreSQL** | Access to the WinCC OA historian database |
| **Network** | Connectivity to the database server (or localhost) |
| **OS** | Windows (for Task Scheduler automation); runs on any OS manually |

---

## Quick Start

```bash
# 1. Clone and navigate to the project
cd maintenance_tracker

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
copy .env.example .env         # Windows
# cp .env.example .env         # Linux/macOS
# Then edit .env with your database credentials

# 5. Deploy the SQL function (one time only)
python db/setup.py

# 6. Replace placeholder signal tag names in db/queries.py with real ones

# 7. Generate your first report
python main.py
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your database credentials:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=winccoa_db
DB_USER=winccoa
DB_PASSWORD=your-password-here
```

The `.env` file is excluded from version control via `.gitignore` — credentials are never committed.

---

## First-Time Database Setup

Run this **once** to deploy the `get_equipment_run_hours` stored function to PostgreSQL:

```bash
python db/setup.py
```

Expected output:
```
[setup] Connected to database.
[setup] Function 'get_equipment_run_hours' deployed successfully.
```

This function handles:
- Resolving signal tag names to element IDs
- Finding all relevant segments that overlap the query time range
- Building a dynamic `UNION ALL` across `_event_<segment_id>_a` tables
- Detecting ON/OFF transitions using `LAG()` window functions
- Filtering noise with a configurable debounce threshold (default: 30 seconds)
- Handling open-ended intervals (signal still HIGH at query end time)

You can re-run `db/setup.py` safely — it uses `CREATE OR REPLACE FUNCTION`.

---

## Running the Report

```bash
python main.py
```

This will:

1. Connect to the PostgreSQL database
2. Query run hours for each equipment since its last maintenance date
3. Query lifetime run hours for each equipment (since commissioning)
4. Compute derived metrics per equipment:
   - **Hours remaining** until next maintenance
   - **% consumed** of maintenance interval
   - **Average daily run hours**
   - **Projected next maintenance date**
   - **Alert flags** (warning at 75%, critical at 90%)
5. Generate a PDF report saved to `reports/maintenance_report_YYYY-MM-DD.pdf`
6. Log all progress to console and `logs/run.log`

---

## Understanding the PDF Report

The generated report includes:

### Header
- Facility name and generation timestamp
- Reporting period ("As of" date)

### Summary Table

Each row represents one piece of equipment with these columns:

| Column | Description |
|--------|-------------|
| Equip ID | Equipment identifier (e.g., PUMP-01) |
| Label | Human-readable name |
| Last Maint. | Date of last maintenance |
| Hrs Since Maint. | Run hours accumulated since last maintenance |
| Lifetime Hrs | Total run hours since commissioning |
| Interval (hrs) | Maintenance interval in hours |
| Hrs Remaining | Hours left until maintenance is due |
| % Consumed | Percentage of maintenance interval used |
| Progress | Visual progress bar |
| Projected Next Maint. | Estimated date when maintenance will be due |
| Status | OK / WARNING / CRITICAL |

### Row Color Coding

| Color | Condition | Meaning |
|-------|-----------|---------|
| **Red** | >= 90% consumed | Maintenance is overdue or imminent |
| **Yellow** | >= 75% consumed | Maintenance should be planned soon |
| **Green** | < 75% consumed | Healthy — no action needed |

### Notes Section
Lists any equipment with non-empty notes (e.g., "Replaced bearing last service").

### Footer
Page number, generation timestamp, and "Confidential — Internal Use Only" on every page.

---

## Customizing Equipment

Edit **`equipment.py`** — this is the only file you need to touch for routine updates.

### After performing maintenance:

Update the `last_maintenance` date and optionally add `notes`:

```python
{
    "id": "PUMP-01",
    "label": "Cooling Water Pump 1",
    "type": "pump",
    "commissioned": datetime(2021, 3, 15, tzinfo=timezone.utc),
    "last_maintenance": datetime(2025, 3, 10, tzinfo=timezone.utc),  # <-- update this
    "maintenance_interval_hours": 2000,
    "notes": "Replaced bearing and mechanical seal",                  # <-- update this
},
```

Then re-run `python main.py` to generate an updated report.

### Adjusting debounce threshold:

The `DEBOUNCE_SECONDS` value (default: 30) filters out signal transitions shorter than this duration to reject electrical noise and false starts. Adjust if needed:

```python
DEBOUNCE_SECONDS = 30  # seconds — increase if seeing false run counts
```

---

## Configuring Signal Tag Names

Edit **`db/queries.py`** and replace placeholder signal names with your real WinCC OA tag names.

Each query function has a clearly marked placeholder:

```python
def get_run_hours_pump_01(conn, start_dt, end_dt, debounce_s):
    """PUMP-01 — single running feedback signal"""
    return _query_single_signal(
        conn,
        "System1:PUMP_01.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )
```

Replace with your actual tag name:

```python
        "MyPlant:CWP01.RunFeedback",  # Cooling water pump 1 running signal
```

The tag name must exactly match the `element_name` value in the WinCC OA `elements` table.

---

## Scheduling Weekly Reports (Windows)

A `scheduler.bat` file is included for Windows Task Scheduler automation.

### Setup steps:

1. Open Task Scheduler (`Win+R` → `taskschd.msc`)
2. Click **Create Task** (not "Create Basic Task")
3. **General** tab:
   - Name: `Maintenance Report`
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"
4. **Triggers** tab:
   - New → Weekly → Monday at 06:00 AM
5. **Actions** tab:
   - New → Start a program
   - Program/script: `C:\maintenance_tracker\scheduler.bat`
   - Start in: `C:\maintenance_tracker`
6. Click OK and enter your Windows password when prompted

Scheduler output is appended to `logs/weekly_run.log`.

---

## Adding New Equipment

Three files need updates (following the existing patterns exactly):

### 1. `equipment.py` — Add the equipment entry

```python
{
    "id": "PUMP-04",
    "label": "Booster Pump 4",
    "type": "pump",
    "commissioned": datetime(2023, 1, 15, tzinfo=timezone.utc),
    "last_maintenance": datetime(2025, 2, 1, tzinfo=timezone.utc),
    "maintenance_interval_hours": 2000,
    "notes": "",
},
```

### 2. `db/queries.py` — Add a query function

```python
def get_run_hours_pump_04(conn, start_dt, end_dt, debounce_s):
    """PUMP-04 — booster pump running feedback"""
    return _query_single_signal(
        conn,
        "MyPlant:BST_PUMP_04.running",  # your real tag name
        start_dt,
        end_dt,
        debounce_s,
    )
```

### 3. `main.py` — Add explicit query calls

Add the import:
```python
from db.queries import get_run_hours_pump_04
```

Add the maintenance query:
```python
results.append(build_result(
    EQUIPMENT[10],  # index of your new entry
    safe_query(get_run_hours_pump_04, conn, EQUIPMENT[10], now, DEBOUNCE_SECONDS),
    now,
))
```

Add the lifetime query:
```python
results[10]["run_hours_lifetime"] = safe_lifetime_query(
    get_run_hours_pump_04, conn, EQUIPMENT[10], now, DEBOUNCE_SECONDS
)
```

---

## Project Structure

```
maintenance_tracker/
├── db/
│   ├── __init__.py
│   ├── setup.py            # Deploys the SQL function to PostgreSQL (run once)
│   └── queries.py           # One hardcoded query function per equipment
├── report/
│   ├── __init__.py
│   └── generator.py         # PDF generation with ReportLab
├── logs/
│   └── .gitkeep             # Run logs saved here
├── reports/
│   └── .gitkeep             # Generated PDFs saved here
├── equipment.py              # All equipment data hardcoded here (edit this)
├── main.py                   # Orchestrator — entry point
├── scheduler.bat             # Windows Task Scheduler batch file
├── .env                      # DB credentials (not committed)
├── .env.example              # Template for .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `[setup] ERROR — database operation failed` | Check your `.env` credentials and verify PostgreSQL is reachable |
| `Element not found: System1:PUMP_01.running` | Replace placeholder tag names in `db/queries.py` with your real WinCC OA tags |
| Report shows 0.0 hours for all equipment | Verify tag names match `element_name` values in the `elements` table |
| `ModuleNotFoundError: No module named 'psycopg2'` | Activate your virtual environment and run `pip install -r requirements.txt` |
| PDF has no data rows | Check that `equipment.py` has entries and `main.py` has matching query calls |
| Task Scheduler doesn't run | Verify the path in `scheduler.bat`, ensure "Run whether user is logged on or not" is checked, and check `logs/weekly_run.log` for errors |
| Query returns unexpected run hours | Try adjusting `DEBOUNCE_SECONDS` in `equipment.py` — a higher value filters out more short-duration noise |
