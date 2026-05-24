import sqlite3
from pathlib import Path

DB_PATH = Path("data.db")

SUMMARY_SQL = """
WITH summary AS (
    SELECT
        sample,
        (b_cell + cd8_t_cell + cd4_t_cell + nk_cell + monocyte) AS total_count,
        b_cell,
        cd8_t_cell,
        cd4_t_cell,
        nk_cell,
        monocyte
    FROM treatments
)
SELECT
    sample,
    total_count,
    'b_cell' AS population,
    b_cell AS count,
    100.0 * b_cell / total_count AS percentage
FROM summary
UNION ALL
SELECT 
    sample, 
    total_count, 
    'cd8_t_cell' AS population,
    cd8_t_cell AS count,
    100.0 * cd8_t_cell / total_count AS percentage
FROM summary
UNION ALL
SELECT 
    sample, 
    total_count, 
    'cd4_t_cell' AS population,
    cd4_t_cell AS count,
    100.0 * cd4_t_cell / total_count AS percentage
FROM summary
UNION ALL
SELECT 
    sample, 
    total_count, 
    'nk_cell' AS population,
    nk_cell AS count,
    100.0 * nk_cell / total_count AS percentage
FROM summary
UNION ALL
SELECT 
    sample, 
    total_count, 
    'monocyte' AS population,
    monocyte AS count,
    100.0 * monocyte / total_count AS percentage
FROM summary
ORDER BY sample
"""


def fetch_summary(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(SUMMARY_SQL).fetchall()
    finally:
        conn.close()


def display_summary(rows: list[sqlite3.Row]):
    columns = ("sample", "total_count", "population", "count", "percentage")
    widths = [14, 14, 14, 14, 14]
    header = "".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['sample']:<14} {row['total_count']:<14} {row['population']:<14} {row['count']:<14} {row['percentage']:<14}"
        )
