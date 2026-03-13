"""
Deploy the get_equipment_run_hours SQL function to the PostgreSQL database.

Run this script ONCE during initial setup:
    python db/setup.py

It connects to the WinCC OA historian database using credentials from .env
and creates (or replaces) the stored function that calculates equipment
run hours from event-driven signal data.
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

# Load .env from the maintenance_tracker root directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))  # loads from project root

SQL_FUNCTION = r"""
CREATE OR REPLACE FUNCTION get_equipment_run_hours(
    p_element_name TEXT,
    p_start_ns     BIGINT,
    p_end_ns       BIGINT,
    p_debounce_ns  BIGINT
)
RETURNS TABLE (
    run_seconds  NUMERIC,
    sample_count BIGINT
) AS $$
DECLARE
    v_element_id BIGINT;
    v_union_sql  TEXT := '';
    v_first      BOOLEAN := TRUE;
    v_sql        TEXT;
    r            RECORD;
BEGIN
    SELECT element_id INTO v_element_id
      FROM elements
     WHERE element_name = p_element_name
     LIMIT 1;

    IF v_element_id IS NULL THEN
        RAISE EXCEPTION 'Element not found: %', p_element_name;
    END IF;

    FOR r IN
        SELECT s.segment_id
          FROM segments s
          JOIN elements_to_archive_groups etag ON etag.group_name = s.group_name
         WHERE etag.element_id = v_element_id
           AND s.status IN (0, 1, 2, 5)
           AND s.end_time   > p_start_ns
           AND s.start_time < p_end_ns
         ORDER BY s.start_time ASC
    LOOP
        IF NOT v_first THEN
            v_union_sql := v_union_sql || ' UNION ALL ';
        END IF;
        v_union_sql := v_union_sql || format(
            'SELECT ts, value_number::NUMERIC AS val
               FROM _event_%s_a
              WHERE element_id = %s
                AND ts BETWEEN %s AND %s
                AND value_number IS NOT NULL',
            r.segment_id, v_element_id, p_start_ns, p_end_ns
        );
        v_first := FALSE;
    END LOOP;

    IF v_union_sql = '' THEN
        RETURN QUERY SELECT 0::NUMERIC, 0::BIGINT;
        RETURN;
    END IF;

    v_sql := format($q$
        WITH
        raw_events AS (
            SELECT ts, val FROM (%s) s ORDER BY ts ASC
        ),
        transitions AS (
            SELECT
                val,
                LAG(val) OVER (ORDER BY ts) AS prev_val,
                ts - LAG(ts) OVER (ORDER BY ts) AS duration_ns
            FROM raw_events
        ),
        qualifying AS (
            SELECT duration_ns FROM transitions
             WHERE prev_val = 1 AND duration_ns >= %s
        ),
        last_event AS (
            SELECT val, ts FROM raw_events ORDER BY ts DESC LIMIT 1
        ),
        open_interval AS (
            SELECT CASE
                WHEN l.val = 1 AND (%s - l.ts) >= %s THEN (%s - l.ts)
                ELSE 0
            END AS duration_ns FROM last_event l
        )
        SELECT
            ROUND((COALESCE((SELECT SUM(duration_ns) FROM qualifying), 0)
                 + (SELECT duration_ns FROM open_interval)) / 1e9, 2) AS run_seconds,
            (SELECT COUNT(*) FROM qualifying) AS sample_count
    $q$,
        v_union_sql,
        p_debounce_ns,
        p_end_ns, p_debounce_ns, p_end_ns
    );

    RETURN QUERY EXECUTE v_sql;
END;
$$ LANGUAGE plpgsql;
"""


def main():
    """Connect to the database and deploy the SQL function."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "winccoa"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "AthenaHistorianStation123"),
        )
        conn.autocommit = True
        print("[setup] Connected to database.")

        with conn.cursor() as cur:
            cur.execute(SQL_FUNCTION)

        print("[setup] Function 'get_equipment_run_hours' deployed successfully.")
        conn.close()

    except psycopg2.Error as e:
        print(f"[setup] ERROR — database operation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[setup] ERROR — unexpected failure: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
