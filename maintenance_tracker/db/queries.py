"""
Per-equipment query functions.

Each function calls the deployed get_equipment_run_hours SQL function for a
specific equipment signal. Signal tag names are placeholders — replace them
with real WinCC OA tag names before first run.

No loops, no dispatch tables — every equipment has its own explicit function
for independent readability and debugging.
"""


def to_ns(dt) -> int:
    """Convert a Python datetime to nanoseconds since epoch (BIGINT)."""
    return int(dt.timestamp() * 1_000_000_000)


def _query_single_signal(conn, signal: str, start_dt, end_dt, debounce_s: int) -> dict:
    """Call the SQL function for one signal. Returns dict with run_hours and sample_count."""
    debounce_ns = debounce_s * 1_000_000_000
    with conn.cursor() as cur:
        cur.execute(
            "SELECT run_seconds, sample_count FROM get_equipment_run_hours(%s, %s, %s, %s)",
            (signal, to_ns(start_dt), to_ns(end_dt), debounce_ns),
        )
        row = cur.fetchone()
        run_seconds = float(row[0]) if row else 0.0
        sample_count = int(row[1]) if row else 0
    return {
        "run_hours": round(run_seconds / 3600, 2),
        "sample_count": sample_count,
    }


def get_run_hours_pump_01(conn, start_dt, end_dt, debounce_s):
    """PUMP-01 — single running feedback signal"""
    return _query_single_signal(
        conn,
        "System1:PUMP_01.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_pump_02(conn, start_dt, end_dt, debounce_s):
    """PUMP-02 — single running feedback signal"""
    return _query_single_signal(
        conn,
        "System1:PUMP_02.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_fan_01(conn, start_dt, end_dt, debounce_s):
    """FAN-01 — single running feedback signal"""
    return _query_single_signal(
        conn,
        "System1:FAN_01.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_fan_02(conn, start_dt, end_dt, debounce_s):
    """FAN-02 VFD — use at_speed signal as the most accurate running indicator"""
    return _query_single_signal(
        conn,
        "System1:FAN_02.at_speed",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_air_comp_01(conn, start_dt, end_dt, debounce_s):
    """AIR-COMP-01 — compressor running feedback"""
    return _query_single_signal(
        conn,
        "System1:COMP_01.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_pump_03(conn, start_dt, end_dt, debounce_s):
    """PUMP-03 — single running feedback signal"""
    return _query_single_signal(
        conn,
        "System1:PUMP_03.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_fan_03(conn, start_dt, end_dt, debounce_s):
    """FAN-03 — single running feedback signal"""
    return _query_single_signal(
        conn,
        "System1:FAN_03.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_air_comp_02(conn, start_dt, end_dt, debounce_s):
    """AIR-COMP-02 — compressor running feedback"""
    return _query_single_signal(
        conn,
        "System1:COMP_02.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_conv_01(conn, start_dt, end_dt, debounce_s):
    """CONV-01 — conveyor running feedback"""
    return _query_single_signal(
        conn,
        "System1:CONV_01.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )


def get_run_hours_mixer_01(conn, start_dt, end_dt, debounce_s):
    """MIXER-01 — mixer running feedback"""
    return _query_single_signal(
        conn,
        "System1:MIXER_01.running",  # TODO: replace with real WinCC OA tag name
        start_dt,
        end_dt,
        debounce_s,
    )
