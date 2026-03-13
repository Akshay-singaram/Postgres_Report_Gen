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

    -- Data is 1-second sampled: each row with val=1 represents 1 second of runtime.
    -- Count all rows where value_number = 1 to get total run seconds.
    v_sql := format($q$
        WITH
        raw_events AS (
            SELECT ts, val FROM (%s) s
        )
        SELECT
            COUNT(*)::NUMERIC AS run_seconds,
            COUNT(*)          AS sample_count
          FROM raw_events
         WHERE val = 1
    $q$,
        v_union_sql
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
