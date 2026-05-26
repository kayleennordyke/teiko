import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import (
    BONUS_AVG_B_CELL_SQL,
    DB_PATH,
    POPULATION_ORDER,
    SUBSET_BY_PROJECT_SQL,
    SUBSET_BY_RESPONSE_SQL,
    SUBSET_BY_SEX_SQL,
    SUBSET_TOTAL_SAMPLES_SQL,
    SUMMARY_SQL,
    fetch_statistical_analysis,
    summarize_response_comparison,
)
from load_data import load

st.set_page_config(page_title="Teiko Cell Counts", layout="wide")
st.title("Teiko Teiknical - Kayleen Nordyke")

@st.cache_resource
def ensure_database() -> Path:
    if not DB_PATH.exists():
        load()
    return DB_PATH

def get_connection(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def response_label(value: str) -> str:
    if value == "yes":
        return "Responder"
    if value == "no":
        return "Non-responder"
    return value

def make_response_boxplot(df: pd.DataFrame):
    fig = px.box(
        df,
        x="population",
        y="percentage",
        color="response",
        category_orders={
            "population": list(POPULATION_ORDER),
            "response": ["Responder", "Non-responder"],
        },
        labels={
            "population": "Immune cell population",
            "percentage": "Relative frequency (%)",
            "response": "Treatment response",
        },
        title="Melanoma | miraclib | PBMC — responders vs non-responders",
        color_discrete_map={
            "Responder": "#4c72b0",
            "Non-responder": "#dd8452",
        },
    )
    fig.update_layout(
        boxmode="group",
        legend_title_text="Response",
        xaxis_tickangle=-30,
        hovermode="closest",
    )
    return fig


ensure_database()

tab_part2, tab_part3, tab_part4, tab_bonus = st.tabs(
    ["Part 2", "Part 3", "Part 4", "Bonus"]
)

with tab_part2:
    st.header("Initial Analysis - Data Overview")
    st.caption("Summary table of the relative frequency of each cell population.")
    conn = get_connection(DB_PATH)
    summary_df = pd.read_sql_query(SUMMARY_SQL, conn)
    conn.close()
    st.metric("Rows in summary table", f"{len(summary_df):,}")
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

with tab_part3:
    st.header("Statistical Analysis")
    st.caption("Melanoma patients on miraclib; `response` yes = responder, no = non-responder; PBMC samples at baseline (day 0).")

    freq_df = fetch_statistical_analysis()
    comparison_df = summarize_response_comparison(freq_df)
    largest = comparison_df.loc[comparison_df["mean_difference"].abs().idxmax()]

    st.subheader("Mean and standard deviation (%)")
    st.dataframe(
        comparison_df.rename(
            columns={
                "responder_mean": "responder mean",
                "responder_std": "responder std",
                "non_responder_mean": "non-responder mean",
                "non_responder_std": "non-responder std",
                "mean_difference": "mean difference",
            }
        ).style.format(
            {
                "responder mean": "{:.2f}",
                "responder std": "{:.2f}",
                "non-responder mean": "{:.2f}",
                "non-responder std": "{:.2f}",
                "mean difference": "{:+.2f}",
            }
        ),
        use_container_width=True,
    )

    st.info(
        f"Largest mean gap: **{largest['population']}** "
        f"({largest['mean_difference']:+.2f} percentage points). "
        "See boxplot below for spread."
    )

    st.subheader("Boxplot by population")
    st.plotly_chart(make_response_boxplot(freq_df), use_container_width=True)

with tab_part4:
    st.header("Data Subset Analysis")
    st.caption("Samples at `time_from_treatment_start = 0` from patients who have been treated with miraclib.")

    conn = get_connection(DB_PATH)
    total = conn.execute(SUBSET_TOTAL_SAMPLES_SQL).fetchone()[0]
    st.metric("Total baseline samples", total)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Samples by project")
        st.dataframe(
            pd.read_sql_query(SUBSET_BY_PROJECT_SQL, conn),
            hide_index=True,
            use_container_width=True,
        )
    with col2:
        st.subheader("Subjects by response")
        response_df = pd.read_sql_query(SUBSET_BY_RESPONSE_SQL, conn)
        response_df["response"] = response_df["response"].map(response_label)
        st.dataframe(response_df, hide_index=True, use_container_width=True)
    with col3:
        st.subheader("Subjects by sex")
        st.dataframe(
            pd.read_sql_query(SUBSET_BY_SEX_SQL, conn),
            hide_index=True,
            use_container_width=True,
        )
    conn.close()

with tab_bonus:
    st.header("Average Number of B Cells")
    st.caption("Average raw B cell count for melanoma males responders at baseline (day 0).")

    conn = get_connection(DB_PATH)
    row = conn.execute(BONUS_AVG_B_CELL_SQL).fetchone()
    conn.close()
    st.metric("Average B cells", f"{row[0]:.2f}")
    st.caption(f"Based on {row[1]} samples.")
