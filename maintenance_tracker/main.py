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

import psycopg2
from dotenv import load_dotenv

from equipment import DEBOUNCE_SECONDS, EQUIPMENT
from db.queries import (
    get_run_hours_pump_01,
    get_run_hours_pump_02,
    get_run_hours_fan_01,
    get_run_hours_fan_02,
    get_run_hours_air_comp_01,
    get_run_hours_pump_03,
    get_run_hours_fan_03,
    get_run_hours_air_comp_02,
    get_run_hours_conv_01,
    get_run_hours_mixer_01,
)
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
# Database connection
# ---------------------------------------------------------------------------
def get_connection():
    """Create and return a psycopg2 connection using .env credentials."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "winccoa_db"),
        user=os.getenv("DB_USER", "winccoa"),
        password=os.getenv("DB_PASSWORD", ""),
    )


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
    # Query each equipment explicitly — no loops, no dispatch
    # ------------------------------------------------------------------
    logger.info("Querying equipment run hours since last maintenance...")

    results = []

    # PUMP-01
    results.append(build_result(
        EQUIPMENT[0],
        safe_query(get_run_hours_pump_01, conn, EQUIPMENT[0], now, DEBOUNCE_SECONDS),
        now,
    ))
    # PUMP-02
    results.append(build_result(
        EQUIPMENT[1],
        safe_query(get_run_hours_pump_02, conn, EQUIPMENT[1], now, DEBOUNCE_SECONDS),
        now,
    ))
    # FAN-01
    results.append(build_result(
        EQUIPMENT[2],
        safe_query(get_run_hours_fan_01, conn, EQUIPMENT[2], now, DEBOUNCE_SECONDS),
        now,
    ))
    # FAN-02
    results.append(build_result(
        EQUIPMENT[3],
        safe_query(get_run_hours_fan_02, conn, EQUIPMENT[3], now, DEBOUNCE_SECONDS),
        now,
    ))
    # AIR-COMP-01
    results.append(build_result(
        EQUIPMENT[4],
        safe_query(get_run_hours_air_comp_01, conn, EQUIPMENT[4], now, DEBOUNCE_SECONDS),
        now,
    ))
    # PUMP-03
    results.append(build_result(
        EQUIPMENT[5],
        safe_query(get_run_hours_pump_03, conn, EQUIPMENT[5], now, DEBOUNCE_SECONDS),
        now,
    ))
    # FAN-03
    results.append(build_result(
        EQUIPMENT[6],
        safe_query(get_run_hours_fan_03, conn, EQUIPMENT[6], now, DEBOUNCE_SECONDS),
        now,
    ))
    # AIR-COMP-02
    results.append(build_result(
        EQUIPMENT[7],
        safe_query(get_run_hours_air_comp_02, conn, EQUIPMENT[7], now, DEBOUNCE_SECONDS),
        now,
    ))
    # CONV-01
    results.append(build_result(
        EQUIPMENT[8],
        safe_query(get_run_hours_conv_01, conn, EQUIPMENT[8], now, DEBOUNCE_SECONDS),
        now,
    ))
    # MIXER-01
    results.append(build_result(
        EQUIPMENT[9],
        safe_query(get_run_hours_mixer_01, conn, EQUIPMENT[9], now, DEBOUNCE_SECONDS),
        now,
    ))

    # ------------------------------------------------------------------
    # Query lifetime hours for each equipment
    # ------------------------------------------------------------------
    logger.info("Querying lifetime run hours...")

    results[0]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_pump_01, conn, EQUIPMENT[0], now, DEBOUNCE_SECONDS
    )
    results[1]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_pump_02, conn, EQUIPMENT[1], now, DEBOUNCE_SECONDS
    )
    results[2]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_fan_01, conn, EQUIPMENT[2], now, DEBOUNCE_SECONDS
    )
    results[3]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_fan_02, conn, EQUIPMENT[3], now, DEBOUNCE_SECONDS
    )
    results[4]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_air_comp_01, conn, EQUIPMENT[4], now, DEBOUNCE_SECONDS
    )
    results[5]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_pump_03, conn, EQUIPMENT[5], now, DEBOUNCE_SECONDS
    )
    results[6]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_fan_03, conn, EQUIPMENT[6], now, DEBOUNCE_SECONDS
    )
    results[7]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_air_comp_02, conn, EQUIPMENT[7], now, DEBOUNCE_SECONDS
    )
    results[8]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_conv_01, conn, EQUIPMENT[8], now, DEBOUNCE_SECONDS
    )
    results[9]["run_hours_lifetime"] = safe_lifetime_query(
        get_run_hours_mixer_01, conn, EQUIPMENT[9], now, DEBOUNCE_SECONDS
    )

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
