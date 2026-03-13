"""
Diagnostic script — inspect raw signal data for a given element.
Usage: python debug_signal.py
"""

import os
from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def main():
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", 5432),
        dbname=os.environ.get("DB_NAME", "winccoa"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "AthenaHistorianStation123"),
    )

    # Test with FN-0504's signal
    signal = "System1:Z0506.G3.MTR-0103_RUNNING"

    with conn.cursor() as cur:
        # 1. Find the element
        cur.execute("SELECT element_id FROM elements WHERE element_name = %s LIMIT 1", (signal,))
        row = cur.fetchone()
        if not row:
            print(f"[!] Element NOT FOUND: {signal}")
            conn.close()
            return
        element_id = row[0]
        print(f"[1] Element found: {signal} -> element_id={element_id}")

        # 2. Find matching segments
        cur.execute("""
            SELECT s.segment_id, s.group_name, s.status, s.start_time, s.end_time
              FROM segments s
              JOIN elements_to_archive_groups etag ON etag.group_name = s.group_name
             WHERE etag.element_id = %s
               AND s.status IN (0, 1, 2, 5)
             ORDER BY s.start_time ASC
        """, (element_id,))
        segments = cur.fetchall()
        print(f"[2] Matching segments: {len(segments)}")
        for seg in segments[:5]:
            print(f"    segment_id={seg[0]}, group={seg[1]}, status={seg[2]}, "
                  f"start={seg[3]}, end={seg[4]}")
        if len(segments) > 5:
            print(f"    ... and {len(segments) - 5} more")

        if not segments:
            print("[!] No segments found — no data to query!")
            conn.close()
            return

        # 3. Check columns in the first event table
        first_seg = segments[0][0]
        table_name = f"_event_{first_seg}_a"
        print(f"\n[3] Inspecting table: {table_name}")

        cur.execute(f"""
            SELECT column_name, data_type
              FROM information_schema.columns
             WHERE table_name = %s
             ORDER BY ordinal_position
        """, (table_name,))
        columns = cur.fetchall()
        print("    Columns:")
        for col in columns:
            print(f"      {col[0]} ({col[1]})")

        # 4. Sample raw rows for this element
        print(f"\n[4] Sample rows from {table_name} for element_id={element_id}:")
        cur.execute(f"""
            SELECT * FROM {table_name}
             WHERE element_id = %s
             ORDER BY ts ASC
             LIMIT 20
        """, (element_id,))
        sample_rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        print(f"    Columns: {col_names}")
        for row in sample_rows:
            print(f"    {row}")

        # 5. Check distinct value_number values
        print(f"\n[5] Distinct value_number values (first segment):")
        cur.execute(f"""
            SELECT value_number, COUNT(*)
              FROM {table_name}
             WHERE element_id = %s
             GROUP BY value_number
             ORDER BY COUNT(*) DESC
             LIMIT 10
        """, (element_id,))
        for row in cur.fetchall():
            print(f"    value_number={row[0]}, count={row[1]}")

        # 6. Total event count across all segments
        print(f"\n[6] Total events across all segments:")
        total = 0
        for seg in segments:
            tbl = f"_event_{seg[0]}_a"
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tbl} WHERE element_id = %s", (element_id,))
                cnt = cur.fetchone()[0]
                total += cnt
                if cnt > 0:
                    print(f"    {tbl}: {cnt} rows")
            except Exception as e:
                print(f"    {tbl}: ERROR — {e}")
                conn.rollback()
        print(f"    TOTAL: {total} events")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
