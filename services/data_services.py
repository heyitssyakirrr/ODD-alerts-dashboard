"""
This file contains the backend data logic for the dashboard.

There are 2 modes:

1. Mock mode
   - USE_MOCK_DATA = True
   - the app uses sample rows for testing 

2. DuckDB mode
   - USE_MOCK_DATA = False
   - the app reads parquet files directly using DuckDB

Later when parquet files are ready:
- change USE_MOCK_DATA to False
- update PARQUET_GLOB if needed
- update DATE_COLUMN to the actual date column name in parquet file
"""

from collections import defaultdict
import duckdb

# =========================================================
# CONFIGURATION
# =========================================================

# Later, change it to False to use DuckDB + parquet.
USE_MOCK_DATA = True

# Path to all parquet files.
# This recursive pattern means DuckDB will read all parquet files
# inside parquet/ and all subfolders.

PARQUET_GLOB = "parquet/**/*.parquet"

# Change this later to the real date column inside the parquet file.
DATE_COLUMN = "date"

# =========================================================
# MOCK DATA
# =========================================================

# This sample data is used only for UI development for now.
MOCK_ROWS = [
    {"reference_no": "REF015", "date": "2025-09-01"},
    {"reference_no": "REF016", "date": "2025-09-02"},
    {"reference_no": "REF001", "date": "2025-10-02"},
    {"reference_no": "REF017", "date": "2025-10-03"},
    {"reference_no": "REF001", "date": "2025-10-10"},
    {"reference_no": "REF001", "date": "2025-11-15"},
    {"reference_no": "REF001", "date": "2025-12-20"},
    {"reference_no": "REF001", "date": "2025-12-31"},
    {"reference_no": "REF002", "date": "2026-01-01"},
    {"reference_no": "REF004", "date": "2026-01-02"},
    {"reference_no": "REF005", "date": "2026-02-10"},
    {"reference_no": "REF006", "date": "2026-02-10"},
    {"reference_no": "REF007", "date": "2026-02-11"},
    {"reference_no": "REF008", "date": "2026-03-01"},
    {"reference_no": "REF009", "date": "2026-03-02"},
    {"reference_no": "REF010", "date": "2026-03-02"},
    {"reference_no": "REF011", "date": "2026-03-15"},
    {"reference_no": "REF012", "date": "2026-04-01"},
    {"reference_no": "REF013", "date": "2026-04-01"},
    {"reference_no": "REF014", "date": "2026-04-05"},
]

# =========================================================
# DUCKDB HELPER
# =========================================================

def get_connection():
    """
    Create a DuckDB in-memory connection.

    Why use this:
    - We only need DuckDB to query parquet files directly
    - We are not storing permanent tables inside DuckDB yet
    """
    return duckdb.connect(database=":memory:")

# =========================================================
# YEAR SUMMARY
# =========================================================

def get_years():
    """
    Return year-level row counts.

    Output format:
    [
        {"year": "2026", "total_rows": 12},
        {"year": "2025", "total_rows": 8}
    ]

    Business logic:
    - Each date corresponds to one parquet file
    - First count rows per date
    - Then sum those date totals into year totals
    """

    # -----------------------------
    # MOCK MODE
    # -----------------------------
    if USE_MOCK_DATA:
        # Step 1: count rows per date
        date_counts = defaultdict(int)

        for row in MOCK_ROWS:
            date_counts[row["date"]] += 1

        # Step 2: sum date row counts into year totals
        year_counts = defaultdict(int)

        for date_value, row_count in date_counts.items():
            year_key = date_value[:4]  # YYYY
            year_counts[year_key] += row_count

        return [
            {"year": year, "total_rows": total}
            for year, total in sorted(year_counts.items(), reverse=True)
        ]

    # -----------------------------
    # DUCKDB MODE
    # -----------------------------
    query = f"""
        -- Step 1: count rows per date
        WITH date_level AS (
            SELECT
                CAST({DATE_COLUMN} AS DATE) AS file_date,
                COUNT(*) AS date_rows
            FROM read_parquet(
                '{PARQUET_GLOB}',
                hive_partitioning = true,
                filename = true
            )
            GROUP BY file_date
        )

        -- Step 2: sum date row counts into year totals
        SELECT
            strftime(file_date, '%Y') AS year,
            SUM(date_rows) AS total_rows
        FROM date_level
        GROUP BY year
        ORDER BY year DESC
    """

    con = get_connection()
    rows = con.execute(query).fetchall()
    con.close()

    return [
        {"year": row[0], "total_rows": row[1]}
        for row in rows
    ]

# =========================================================
# MONTH SUMMARY INSIDE ONE YEAR
# =========================================================

def get_months_by_year(selected_year):
    """
    Return month-level row counts for one selected year.

    Example input:
        selected_year = "2026"

    Example output:
    [
        {"month": "2026-04", "total_rows": 3},
        {"month": "2026-03", "total_rows": 4},
        {"month": "2026-02", "total_rows": 3},
        {"month": "2026-01", "total_rows": 2}
    ]

    Business logic:
    - First count rows per date
    - Then sum those date totals into month totals
    - Only return months inside the selected year
    """

    # -----------------------------
    # MOCK MODE
    # -----------------------------
    if USE_MOCK_DATA:
        # Step 1: count rows per date
        date_counts = defaultdict(int)

        for row in MOCK_ROWS:
            date_counts[row["date"]] += 1

        # Step 2: sum date row counts into month totals for one selected year
        month_counts = defaultdict(int)

        for date_value, row_count in date_counts.items():
            if date_value.startswith(selected_year):
                month_key = date_value[:7]  # YYYY-MM
                month_counts[month_key] += row_count

        return [
            {"month": month, "total_rows": total}
            for month, total in sorted(month_counts.items(), reverse=True)
        ]

    # -----------------------------
    # DUCKDB MODE
    # -----------------------------
    query = f"""
        -- Step 1: count rows per date
        WITH date_level AS (
            SELECT
                CAST({DATE_COLUMN} AS DATE) AS file_date,
                COUNT(*) AS date_rows
            FROM read_parquet(
                '{PARQUET_GLOB}',
                hive_partitioning = true,
                filename = true
            )
            GROUP BY file_date
        )

        -- Step 2: sum date row counts into month totals for the selected year
        SELECT
            strftime(file_date, '%Y-%m') AS month,
            SUM(date_rows) AS total_rows
        FROM date_level
        WHERE strftime(file_date, '%Y') = ?
        GROUP BY month
        ORDER BY month DESC
    """

    con = get_connection()
    rows = con.execute(query, [selected_year]).fetchall()
    con.close()

    return [
        {"month": row[0], "total_rows": row[1]}
        for row in rows
    ]

# =========================================================
# DATE SUMMARY INSIDE ONE MONTH
# =========================================================

def get_dates_by_month(selected_month):
    """
    Return date-level row counts for one selected month.

    Example input:
        selected_month = "2026-03"

    Example output:
    [
        {"date": "2026-03-15", "total_rows": 1},
        {"date": "2026-03-02", "total_rows": 2},
        {"date": "2026-03-01", "total_rows": 1}
    ]

    Business logic:
    - Each date corresponds to one parquet file
    - Date total rows = row count of that date parquet file
    """

    # -----------------------------
    # MOCK MODE
    # -----------------------------
    if USE_MOCK_DATA:
        date_counts = defaultdict(int)

        for row in MOCK_ROWS:
            if row["date"].startswith(selected_month):
                date_counts[row["date"]] += 1

        return [
            {"date": date_value, "total_rows": total}
            for date_value, total in sorted(date_counts.items(), reverse=True)
        ]

    # -----------------------------
    # DUCKDB MODE
    # -----------------------------
    query = f"""
        SELECT
            CAST({DATE_COLUMN} AS DATE) AS file_date,
            COUNT(*) AS total_rows
        FROM read_parquet(
            '{PARQUET_GLOB}',
            hive_partitioning = true,
            filename = true
        )
        WHERE strftime(CAST({DATE_COLUMN} AS DATE), '%Y-%m') = ?
        GROUP BY file_date
        ORDER BY file_date DESC
    """

    con = get_connection()
    rows = con.execute(query, [selected_month]).fetchall()
    con.close()

    return [
        {"date": str(row[0]), "total_rows": row[1]}
        for row in rows
    ]