import sqlite3

import pandas as pd
from pathlib import Path

DB_PATH = Path("data.db")
SCHEMA_PATH = Path("schema.sql")
CSV_PATH = Path("cell-count.csv")


def load(csv_path: Path = CSV_PATH, db_path: Path = DB_PATH) -> None:
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"subject": "subject_id"})

    projects_df = df[["subject_id", "project"]].drop_duplicates(subset=["subject_id"])
    patients_df = df[
        ["subject_id", "condition", "age", "sex", "treatment", "response"]
    ].drop_duplicates(subset=["subject_id"])
    patients_df["response"] = patients_df["response"].fillna("unknown")
    treatments_df = df[
        [
            "subject_id",
            "sample",
            "sample_type",
            "time_from_treatment_start",
            "b_cell",
            "cd8_t_cell",
            "cd4_t_cell",
            "nk_cell",
            "monocyte",
        ]
    ]

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_PATH.read_text())

        projects_df.to_sql("projects", conn, if_exists="append", index=False)
        patients_df.to_sql("patients", conn, if_exists="append", index=False)
        treatments_df.to_sql("treatments", conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    load()
