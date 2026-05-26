import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DB_PATH = Path("data.db")
BOXPLOT_PATH = Path("relative_frequency.png")
OUTPUT_DIR = Path("outputs")

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

def summarize_response_comparison(df: pd.DataFrame):
    """Mean and std dev of relative frequencies between responders and non-responders."""
    rows = []

    for population in POPULATION_ORDER:
        responders = df.loc[
            (df["population"] == population) & (df["response"] == "Responder"),
            "percentage",
        ]
        non_responders = df.loc[
            (df["population"] == population) & (df["response"] == "Non-responder"),
            "percentage",
        ]
        rows.append(
            {
                "population": population,
                "responder_mean": responders.mean(),
                "responder_std": responders.std(),
                "non_responder_mean": non_responders.mean(),
                "non_responder_std": non_responders.std(),
                "mean_difference": responders.mean() - non_responders.mean(),
            }
        )

    return pd.DataFrame(rows)


def display_response_comparison(df: pd.DataFrame) -> pd.DataFrame:
    results = summarize_response_comparison(df)
    significant_difference = results.loc[results["mean_difference"].abs().idxmax()]

    print(
        "\n----------------------------------------------------------" +
        "\nPART 3: Responder vs non-responder comparison (melanoma miraclib PBMC)" +
        "\n----------------------------------------------------------\n"
    )
    print("Relative frequency per sample: mean and standard deviation.\n")

    header = (
        f"{'population':<15}"
        f"{'resp mean':<15}{'resp std':<15}"
        f"{'nonresp mean':<15}{'nonresp std':<15}"
        f"{'diff':<15}"
    )
    print(header)
    print("-" * len(header))
    for _, row in results.iterrows():
        print(
            f"{row['population']:<15}"
            f"{row['responder_mean']:<15.2f}{row['responder_std']:<15.2f}"
            f"{row['non_responder_mean']:<15.2f}{row['non_responder_std']:<15.2f}"
            f"{row['mean_difference']:<15.2f}"
        )

    print(
        f"\nLargest mean gap: {significant_difference['population']} " +
        f"({significant_difference['mean_difference']:+.2f} difference between means)" +
        f" with the largest stdev of {significant_difference['responder_std']:.2f}" +
        " \nalso Bob should direct Yah D'yada to the box plots for more visual analysis."
    )
    return results

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

# region BONUS
BONUS_AVG_B_CELL_SQL = """
SELECT
    ROUND(AVG(t.b_cell), 2) AS avg_b_cell,
    COUNT(*) AS sample_count
FROM treatments t
JOIN patients p ON p.subject_id = t.subject_id
WHERE p.condition = 'melanoma'
  AND p.sex = 'M'
  AND p.response = 'yes'
  AND t.time_from_treatment_start = 0
"""

BONUS_COHORT_DIAGNOSTICS_SQL = """
SELECT
    COUNT(*) AS samples_in_cohort,
    SUM(CASE WHEN t.b_cell IS NULL THEN 1 ELSE 0 END) AS null_b_cell,
    SUM(CASE WHEN p.response = 'unknown' THEN 1 ELSE 0 END) AS unknown_response,
    SUM(CASE WHEN p.response NOT IN ('yes', 'no', 'unknown') THEN 1 ELSE 0 END) AS other_response
FROM treatments t
JOIN patients p ON p.subject_id = t.subject_id
WHERE p.condition = 'melanoma'
  AND p.sex = 'M'
  AND t.time_from_treatment_start = 0
"""


def display_bonus_analysis(db_path: Path = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        result = conn.execute(BONUS_AVG_B_CELL_SQL).fetchone()
        diag = conn.execute(BONUS_COHORT_DIAGNOSTICS_SQL).fetchone()

        print(
            "\n----------------------------------------------------------" +
            "\nBONUS: Average B cells (for melanoma males for responders at time = 0)" +
            "\n----------------------------------------------------------\n"
        )
        print(f"Average B cells: {result['avg_b_cell']:.2f}")
        print(f"# of samples: {result['sample_count']}\n")

    finally:
        conn.close()
# endregion


def write_pipeline_outputs(db_path: Path = DB_PATH) -> list[Path]:
    """Write to csv & png"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    written: list[Path] = []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        summary_path = OUTPUT_DIR / "population_summary.csv"
        pd.read_sql_query(SUMMARY_SQL, conn).to_csv(summary_path, index=False)
        written.append(summary_path)

        pd.read_sql_query(SUBSET_BY_PROJECT_SQL, conn).to_csv(
            OUTPUT_DIR / "baseline_by_project.csv", index=False
        )
        written.append(OUTPUT_DIR / "baseline_by_project.csv")

        pd.read_sql_query(SUBSET_BY_RESPONSE_SQL, conn).to_csv(
            OUTPUT_DIR / "baseline_by_response.csv", index=False
        )
        written.append(OUTPUT_DIR / "baseline_by_response.csv")

        pd.read_sql_query(SUBSET_BY_SEX_SQL, conn).to_csv(
            OUTPUT_DIR / "baseline_by_sex.csv", index=False
        )
        written.append(OUTPUT_DIR / "baseline_by_sex.csv")

        bonus_row = conn.execute(BONUS_AVG_B_CELL_SQL).fetchone()
        bonus_path = OUTPUT_DIR / "bonus_avg_b_cell.txt"
        bonus_path.write_text(
            f"avg_b_cell={bonus_row['avg_b_cell']}\n"
            f"sample_count={bonus_row['sample_count']}\n"
        )
        written.append(bonus_path)
    finally:
        conn.close()

    freq_df = fetch_statistical_analysis(db_path)
    comparison_path = OUTPUT_DIR / "response_comparison.csv"
    summarize_response_comparison(freq_df).to_csv(comparison_path, index=False)
    written.append(comparison_path)

    plot_statistical_analysis(freq_df)
    written.append(BOXPLOT_PATH)

    return written


def main():
    summary_rows = fetch_summary()
    # part 2
    display_summary(summary_rows)
    # part 3
    df = fetch_statistical_analysis()
    plot_statistical_analysis(df)
    display_response_comparison(df)
    # part 4
    display_data_subset_analysis()
    # bonus
    display_bonus_analysis()

if __name__ == "__main__":
    main()
