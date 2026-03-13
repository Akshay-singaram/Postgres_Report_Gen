import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ.get("DB_NAME", "winccoa"),
        user=os.environ.get("DB_USER", "winccoa"),
        password=os.environ.get("DB_PASSWORD", "")
    )


def to_ns(dt) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def _query_single_signal(conn, signal: str, start_dt, end_dt, debounce_s: int) -> dict:
    """Base function — calls the SQL function for one binary signal.
    Returns dict with run_hours and sample_count."""
    debounce_ns = debounce_s * 1_000_000_000
    with conn.cursor() as cur:
        cur.execute(
            "SELECT run_seconds, sample_count FROM get_equipment_run_hours(%s, %s, %s, %s)",
            (signal, to_ns(start_dt), to_ns(end_dt), debounce_ns)
        )
        row = cur.fetchone()
        run_seconds = float(row[0]) if row else 0.0
        sample_count = int(row[1]) if row else 0
    return {
        "run_hours": round(run_seconds / 3600, 2),
        "sample_count": sample_count
    }


def get_run_hours_fn_0504(conn, start_dt, end_dt, debounce_s):
    """FN-0504 — VFD/Fan running feedback"""
    return _query_single_signal(
        conn, "System1:Z0506.G3.MTR-0103_RUNNING", start_dt, end_dt, debounce_s
    )


def get_run_hours_fn_0501b(conn, start_dt, end_dt, debounce_s):
    """FN-0501B — VFD/Fan running feedback"""
    return _query_single_signal(
        conn, "System1:Z0506.G3.MTR-0101_RUNNING", start_dt, end_dt, debounce_s
    )


def get_run_hours_fn_0501a(conn, start_dt, end_dt, debounce_s):
    """FN-0501A — VFD/Fan running feedback"""
    return _query_single_signal(
        conn, "System1:Z0506.G3.MTR-0102_RUNNING", start_dt, end_dt, debounce_s
    )


def get_run_hours_fn_0801a3(conn, start_dt, end_dt, debounce_s):
    """FN-0801A.3 — Fan status state (bool, 1=running)"""
    return _query_single_signal(
        conn, "System1:BPCS-FN-0801A3.Status.State", start_dt, end_dt, debounce_s
    )


def get_run_hours_fn_0801a4(conn, start_dt, end_dt, debounce_s):
    """FN-0801A.4 — Fan status state (bool, 1=running)"""
    return _query_single_signal(
        conn, "System1:BPCS-FN-0801A4.Status.State", start_dt, end_dt, debounce_s
    )


def get_run_hours_p_0801a1(conn, start_dt, end_dt, debounce_s):
    """P-0801A.1 — Pump status state (bool, 1=running)"""
    return _query_single_signal(
        conn, "System1:BPCS-P-0801A1.Status.State", start_dt, end_dt, debounce_s
    )


def get_run_hours_p_0801a2(conn, start_dt, end_dt, debounce_s):
    """P-0801A.2 — Pump status state (bool, 1=running)"""
    return _query_single_signal(
        conn, "System1:BPCS-P-0801A2.Status.State", start_dt, end_dt, debounce_s
    )


def get_run_hours_p_0802a(conn, start_dt, end_dt, debounce_s):
    """P-0802A — Pump running feedback"""
    return _query_single_signal(
        conn, "System1:BPCS-P-0802A.Status.Running", start_dt, end_dt, debounce_s
    )


def get_run_hours_p_0802b(conn, start_dt, end_dt, debounce_s):
    """P-0802B — Pump running feedback"""
    return _query_single_signal(
        conn, "System1:BPCS-P-0802B.Status.Running", start_dt, end_dt, debounce_s
    )


def get_run_hours_fn_1702(conn, start_dt, end_dt, debounce_s):
    """FN-1702 — Fan running feedback"""
    return _query_single_signal(
        conn, "System1:BPCS-FN-1702.Status.Running", start_dt, end_dt, debounce_s
    )


def get_run_hours_p_1701(conn, start_dt, end_dt, debounce_s):
    """P-1701 — Pump running feedback"""
    return _query_single_signal(
        conn, "System1:BPCS-P-1701.Status.Running", start_dt, end_dt, debounce_s
    )


def get_run_hours_fn_2002(conn, start_dt, end_dt, debounce_s):
    """FN-2002 — Fan running feedback"""
    return _query_single_signal(
        conn, "System1:BPCS-FN-2002.Status.Running", start_dt, end_dt, debounce_s
    )


def get_run_hours_p_2001(conn, start_dt, end_dt, debounce_s):
    """P-2001 — Pump running feedback"""
    return _query_single_signal(
        conn, "System1:BPCS-P-2001.Status.Running", start_dt, end_dt, debounce_s
    )
