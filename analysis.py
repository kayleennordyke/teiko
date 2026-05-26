import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DB_PATH = Path("data.db")
BOXPLOT_PATH = Path("relative_frequency.png")

# region PART 2
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

def fetch_summary(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(SUMMARY_SQL).fetchall()
    finally:
        conn.close()

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
# endregion

# region PART 3
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

POPULATION_ORDER = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]

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

# endregion

# region PART 4
SUBSET_ANALYSIS_SQL = """
WITH subset AS (
    SELECT
        t.sample,
        t.subject_id,
        pr.project,
        p.response,
        p.sex
    FROM treatments t
    JOIN patients p ON p.subject_id = t.subject_id
    JOIN projects pr ON pr.subject_id = t.subject_id
    WHERE p.condition = 'melanoma'
      AND p.treatment = 'miraclib'
      AND t.sample_type = 'PBMC'
      AND t.time_from_treatment_start = 0
)
"""

SUBSET_BY_PROJECT_SQL = (
    SUBSET_ANALYSIS_SQL
    + """
SELECT project, COUNT(*) AS sample_count
FROM subset
GROUP BY project
ORDER BY project
"""
)

SUBSET_BY_RESPONSE_SQL = (
    SUBSET_ANALYSIS_SQL
    + """
SELECT response, COUNT(DISTINCT subject_id) AS subject_count
FROM subset
GROUP BY response
ORDER BY response
"""
)

SUBSET_BY_SEX_SQL = (
    SUBSET_ANALYSIS_SQL
    + """
SELECT sex, COUNT(DISTINCT subject_id) AS subject_count
FROM subset
GROUP BY sex
ORDER BY sex
"""
)

SUBSET_TOTAL_SAMPLES_SQL = (
    SUBSET_ANALYSIS_SQL + "SELECT COUNT(*) AS total_samples FROM subset"
)


def display_data_subset_analysis(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        total = conn.execute(SUBSET_TOTAL_SAMPLES_SQL).fetchone()["total_samples"]

        print(
            "\n----------------------------------------------------------" +
            "\nPART 4: DATA SUBSET ANALYSIS\n" +
            "Melanoma PBMC samples at baseline (time_from_treatment_start = 0)\n" +
            "from patients who have been treated with miraclib.\n" +
            "----------------------------------------------------------\n"
        )
        print(f"Total baseline samples: {total}\n")

        print("Samples from each project:")
        print(f"{'project':<15}{'sample_count':<15}")
        print("-" * 30)
        for row in conn.execute(SUBSET_BY_PROJECT_SQL):
            print(f"{row['project']:<15}{row['sample_count']:<15}")

        print("\nSubject by responsers/non-responsers:")
        print(f"{'response':<15}{'subject_count':<15}")
        print("-" * 30)
        for row in conn.execute(SUBSET_BY_RESPONSE_SQL):
            label = row["response"]
            if label == "yes":
                label = "Responder"
            elif label == "no":
                label = "Non-responder"
            print(f"{label:<15}{row['subject_count']:<15}")

        print("\nSubjects by males/females:")
        print(f"{'sex':<15}{'subject_count':<15}")
        print("-" * 30)
        for row in conn.execute(SUBSET_BY_SEX_SQL):
            print(f"{row['sex']:<15}{row['subject_count']:<15}")
    finally:
        conn.close()

# endregion

def main():
    summary_rows = fetch_summary()
    try:
        display_summary(summary_rows)
        display_data_subset_analysis()
    except BrokenPipeError:
        sys.exit(0)

    df = fetch_statistical_analysis()
    plot_statistical_analysis(df)

if __name__ == "__main__":
    main()
