# Equipment Runtime & Maintenance Tracker

A local Python application that queries a WinCC OA PostgreSQL historian database to calculate equipment run hours and auto-generates a weekly PDF maintenance report.

## Prerequisites

- Python 3.10+
- PostgreSQL access to the WinCC OA historian database
- Network connectivity to the database server (or running locally)

## Installation

```bash
cd maintenance_tracker
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

## Configuration

1. Copy the environment template:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` with your actual database credentials:
   ```
   DB_HOST=your-db-host
   DB_PORT=5432
   DB_NAME=winccoa_db
   DB_USER=winccoa
   DB_PASSWORD=your-password
   ```

## Initial Setup — Deploy SQL Function

Run this **once** to create the `get_equipment_run_hours` stored function in the database:

```bash
python db/setup.py
```

You should see: `[setup] Function 'get_equipment_run_hours' deployed successfully.`

## Updating Equipment Data

Edit `equipment.py` to update:

- **`last_maintenance`** — set to the date when maintenance was last performed
- **`notes`** — add a short description of what was done during maintenance
- **`maintenance_interval_hours`** — adjust the maintenance interval if needed

## Updating Signal Tag Names

Edit `db/queries.py` and replace the placeholder signal names with your real WinCC OA tag names. Each function has a `# TODO: replace with real WinCC OA tag name` comment marking the placeholder.

Example — change:
```python
"System1:PUMP_01.running"  # TODO: replace with real WinCC OA tag name
```
to your actual tag:
```python
"YourSystem:ActualPump01.RunningFeedback"
```

## Running Manually

```bash
python main.py
```

This will:
1. Connect to the database
2. Query run hours for each equipment since its last maintenance
3. Compute derived maintenance metrics (hours remaining, % consumed, projected next maintenance)
4. Generate a PDF report in the `reports/` directory

## Setting Up Windows Task Scheduler

1. Open Task Scheduler (`taskschd.msc`)
2. Click **Create Task** (not "Create Basic Task")
3. **General** tab: Name = "Maintenance Report", check "Run whether user is logged on or not"
4. **Triggers** tab: New → Weekly → Monday at 06:00 AM
5. **Actions** tab: New → Start a program
   - Program/script: `C:\maintenance_tracker\scheduler.bat`
   - Start in: `C:\maintenance_tracker`
6. Click OK and enter your Windows password when prompted

## Where Reports Are Saved

Generated PDF reports are saved to the `reports/` directory with the naming convention:

```
reports/maintenance_report_YYYY-MM-DD.pdf
```

Logs are written to `logs/run.log` and (when run via scheduler) `logs/weekly_run.log`.

## Adding New Equipment

To add a new piece of equipment:

1. **`equipment.py`** — Add a new entry to the `EQUIPMENT` list following the existing pattern
2. **`db/queries.py`** — Add a new `get_run_hours_<equipment>()` function with the real signal tag name
3. **`main.py`** — Add explicit `results.append(build_result(...))` and lifetime query calls for the new equipment, matching the pattern of existing entries

## Project Structure

```
maintenance_tracker/
├── db/
│   ├── setup.py          # Deploys the SQL function to PostgreSQL (run once)
│   └── queries.py        # One hardcoded query function per equipment
├── report/
│   └── generator.py      # PDF generation with ReportLab
├── logs/
│   └── .gitkeep
├── reports/              # Generated PDFs saved here
│   └── .gitkeep
├── equipment.py          # All equipment data hardcoded here
├── main.py               # Orchestrator / entry point
├── scheduler.bat         # Windows Task Scheduler batch file
├── .env                  # DB credentials (not committed)
├── .env.example          # Template for .env
├── requirements.txt
└── README.md
```
