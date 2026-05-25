import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DB_PATH = Path("data.db")
BOXPLOT_PATH = Path("relative_frequency.png")

POPULATION_ORDER = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]

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
SELECT sample, total_count, 'monocyte', monocyte,
       100.0 * monocyte / total_count
FROM summary
ORDER BY sample, population
"""

STATISTICAL_ANALYSIS_SQL = """
WITH summary AS (
    SELECT
        t.sample,
        p.response,
        t.b_cell,
        t.cd8_t_cell,
        t.cd4_t_cell,
        t.nk_cell,
        t.monocyte,
        (t.b_cell + t.cd8_t_cell + t.cd4_t_cell + t.nk_cell + t.monocyte) AS total_count
    FROM treatments t
    JOIN patients p ON p.subject_id = t.subject_id
    WHERE p.condition = 'melanoma'
      AND p.treatment = 'miraclib'
      AND t.sample_type = 'PBMC'
      AND p.response IN ('yes', 'no')
),
population_frequencies AS (
    SELECT sample, response, 'b_cell' AS population,
           100.0 * b_cell / total_count AS percentage
    FROM summary
    UNION ALL
    SELECT sample, response, 'cd8_t_cell', 100.0 * cd8_t_cell / total_count FROM summary
    UNION ALL
    SELECT sample, response, 'cd4_t_cell', 100.0 * cd4_t_cell / total_count FROM summary
    UNION ALL
    SELECT sample, response, 'nk_cell', 100.0 * nk_cell / total_count FROM summary
    UNION ALL
    SELECT sample, response, 'monocyte', 100.0 * monocyte / total_count FROM summary
)
SELECT sample, response, population, percentage
FROM population_frequencies
ORDER BY population
"""

def fetch_summary(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(SUMMARY_SQL).fetchall()
    finally:
        conn.close()

def fetch_statistical_analysis(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(STATISTICAL_ANALYSIS_SQL, conn)
    finally:
        conn.close()

    df["response"] = df["response"].map(
        {"yes": "Responder", "no": "Non-responder"}
    )
    df["population"] = pd.Categorical(
        df["population"], categories=POPULATION_ORDER, ordered=True
    )
    return df


def display_summary(rows: list[sqlite3.Row]) -> None:
    columns = ("sample", "total_count", "population", "count", "percentage")
    widths = [15, 15, 15, 15, 15]
    header = "".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['sample']:<15}"
            f"{row['total_count']:<15}"
            f"{row['population']:<15}"
            f"{row['count']:<15}"
            f"{row['percentage']:<15.2f}"
        )

def plot_statistical_analysis(df: pd.DataFrame, output_path: Path = BOXPLOT_PATH):
    responses = ["Responder", "Non-responder"]
    data = [
        df.loc[(df["population"] == p) & (df["response"] == r), "percentage"]
        for p in POPULATION_ORDER
        for r in responses
    ]
    labels = [f"{p}\n{r}" for p in POPULATION_ORDER for r in responses]

    plt.boxplot(data, tick_labels=labels)
    plt.ylabel("percentage")
    plt.savefig(output_path)
    plt.close()
    return output_path


def main():
    summary_rows = fetch_summary()
    try:
        display_summary(summary_rows)
    except BrokenPipeError:
        sys.exit(0)

    df = fetch_statistical_analysis()
    plot_statistical_analysis(df)


if __name__ == "__main__":
    main()
