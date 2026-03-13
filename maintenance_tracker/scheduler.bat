@echo off
REM ============================================================
REM Equipment Maintenance Report — Weekly Scheduler
REM ============================================================
REM
REM Windows Task Scheduler settings:
REM   Trigger  : Weekly, every Monday at 06:00 AM
REM   Action   : Start a program — scheduler.bat
REM   Start in : C:\maintenance_tracker
REM   Security : Run whether user is logged in or not
REM              Run with highest privileges
REM
REM To set up:
REM   1. Open Task Scheduler (taskschd.msc)
REM   2. Create Task (not Basic Task)
REM   3. General tab: Name = "Maintenance Report", check "Run whether
REM      user is logged on or not"
REM   4. Triggers tab: New > Weekly > Monday at 06:00
REM   5. Actions tab: New > Start a program
REM        Program/script: C:\maintenance_tracker\scheduler.bat
REM        Start in: C:\maintenance_tracker
REM   6. OK and enter your Windows password when prompted
REM ============================================================

cd /d C:\maintenance_tracker
call venv\Scripts\activate
python main.py >> logs\weekly_run.log 2>&1
