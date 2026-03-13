"""
Equipment Runtime & Maintenance Tracker — Orchestrator

Entry point for the application. Queries each equipment's run hours from
the WinCC OA historian database, computes maintenance metrics, and generates
a PDF report.

Usage:
    python main.py
"""

import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from db.queries import (
    get_connection,
    get_run_hours_fn_0504,
    get_run_hours_fn_0501b,
    get_run_hours_fn_0501a,
    get_run_hours_fn_0801a3,
    get_run_hours_fn_0801a4,
    get_run_hours_p_0801a1,
    get_run_hours_p_0801a2,
    get_run_hours_p_0802a,
    get_run_hours_p_0802b,
    get_run_hours_fn_1702,
    get_run_hours_p_1701,
    get_run_hours_fn_2002,
    get_run_hours_p_2001,
)
from db.setup import SQL_FUNCTION
from equipment import EQUIPMENT, DEBOUNCE_SECONDS
from report.generator import generate_report

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
load_dotenv()

log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(log_dir, "run.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------
def build_result(equip: dict, query_result: dict, now: datetime) -> dict:
    """Compute all derived maintenance metrics for one piece of equipment."""
    run_hours_since_maint = query_result["run_hours"]
    sample_count = query_result["sample_count"]

    interval = equip["maintenance_interval_hours"]
    hours_remaining = max(interval - run_hours_since_maint, 0.0)
    pct_consumed = round((run_hours_since_maint / interval) * 100, 1) if interval > 0 else 0.0

    days_since_maint = (now - equip["last_maintenance"]).total_seconds() / 86400
    avg_daily_hours = (run_hours_since_maint / days_since_maint) if days_since_maint > 0 else 0.0

    if avg_daily_hours > 0:
        days_to_next = hours_remaining / avg_daily_hours
        # Cap at 10 years to avoid OverflowError on date arithmetic
        if days_to_next > 3650:
            projected_date = None
        else:
            projected_date = now + __import__("datetime").timedelta(days=days_to_next)
    else:
        projected_date = None

    return {
        "id": equip["id"],
        "label": equip["label"],
        "type": equip["type"],
        "commissioned": equip["commissioned"],
        "last_maintenance": equip["last_maintenance"],
        "maintenance_interval_hours": interval,
        "notes": equip["notes"],
        "run_hours_since_maintenance": round(run_hours_since_maint, 2),
        "run_hours_lifetime": 0.0,  # populated below
        "sample_count": sample_count,
        "hours_remaining": round(hours_remaining, 2),
        "pct_consumed": pct_consumed,
        "days_since_maintenance": round(days_since_maint, 1),
        "avg_daily_hours": round(avg_daily_hours, 2),
        "projected_maintenance_date": projected_date,
        "alert_critical": pct_consumed >= 90,
        "alert_warning": pct_consumed >= 75,
    }


def safe_query(func, conn, equip, now, debounce_s):
    """Run a query function with error handling — returns zeroed result on failure."""
    try:
        result = func(conn, equip["last_maintenance"], now, debounce_s)
        logger.info(
            "  %s: %.2f run hours (%d samples)",
            equip["id"],
            result["run_hours"],
            result["sample_count"],
        )
        return result
    except Exception as e:
        logger.error("  %s: query failed — %s. Setting run hours to 0.0", equip["id"], e)
        return {"run_hours": 0.0, "sample_count": 0}


def safe_lifetime_query(func, conn, equip, now, debounce_s):
    """Query lifetime run hours (from commissioned date) with error handling."""
    try:
        result = func(conn, equip["commissioned"], now, debounce_s)
        return result["run_hours"]
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    logger.info("=" * 60)
    logger.info("Equipment Runtime & Maintenance Tracker")
    logger.info("=" * 60)

    now = datetime.now(timezone.utc)
    logger.info("Report timestamp: %s", now.isoformat())

    # Connect to the database
    try:
        conn = get_connection()
        logger.info("Connected to database.")
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Ensure the SQL function exists (auto-deploy if missing)
    # ------------------------------------------------------------------
    try:
        conn.commit()  # close any open transaction before changing autocommit
        conn.autocommit = True
        with conn.cursor() as deploy_cur:
            deploy_cur.execute(SQL_FUNCTION)
        conn.autocommit = False
        logger.info("SQL function get_equipment_run_hours deployed.")
    except Exception as e:
        logger.error("Failed to verify/deploy SQL function: %s", e)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Query each equipment explicitly — no loops, no dispatch
    # ------------------------------------------------------------------
    logger.info("Querying equipment run hours since last maintenance...")

    query_fns = [
        get_run_hours_fn_0504,
        get_run_hours_fn_0501b,
        get_run_hours_fn_0501a,
        get_run_hours_fn_0801a3,
        get_run_hours_fn_0801a4,
        get_run_hours_p_0801a1,
        get_run_hours_p_0801a2,
        get_run_hours_p_0802a,
        get_run_hours_p_0802b,
        get_run_hours_fn_1702,
        get_run_hours_p_1701,
        get_run_hours_fn_2002,
        get_run_hours_p_2001,
    ]

    results = []
    for equip, fn in zip(EQUIPMENT, query_fns):
        result = safe_query(fn, conn, equip, now, DEBOUNCE_SECONDS)
        results.append(build_result(equip, result, now))

    conn.close()
    logger.info("Database connection closed.")

    # ------------------------------------------------------------------
    # Generate the PDF report
    # ------------------------------------------------------------------
    logger.info("Generating PDF report...")
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)

    filename = f"maintenance_report_{now.strftime('%Y-%m-%d')}.pdf"
    filepath = os.path.join(report_dir, filename)

    generate_report(results, filepath, now)
    logger.info("Report saved to: %s", filepath)
    logger.info("Done.")


if __name__ == "__main__":
    main()
