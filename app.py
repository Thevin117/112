import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
import plotly.express as px

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

st.set_page_config(page_title="Manufacturing Dashboard", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    connection_url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(connection_url)

    query = text("""
        select
            log_date,
            machine_name,
            line_code,
            running_time_hours,
            downtime_hours,
            cycle_time_sec_per_unit,
            required_output_units,
            actual_output_units,
            calculated_yield_pct,
            availability_pct,
            performance_pct
        from public.production_logs_enriched
        order by log_date, machine_name
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    return df


st.title("Manufacturing Performance Dashboard")

try:
    df = load_data()

    if df.empty:
        st.warning("No data found in production_logs_enriched.")
        st.stop()

    df["log_date"] = pd.to_datetime(df["log_date"])

    # Sidebar filters
    st.sidebar.header("Filters")

    machine_options = sorted(df["machine_name"].dropna().unique().tolist())
    selected_machine = st.sidebar.multiselect(
        "Select Machine",
        options=machine_options,
        default=machine_options,
    )

    min_date = df["log_date"].min().date()
    max_date = df["log_date"].max().date()

    start_date = st.sidebar.date_input("Start Date", min_date)
    end_date = st.sidebar.date_input("End Date", max_date)

    # Apply filters
    filtered_df = df[df["machine_name"].isin(selected_machine)].copy()
    filtered_df = filtered_df[
        (filtered_df["log_date"] >= pd.to_datetime(start_date))
        & (filtered_df["log_date"] <= pd.to_datetime(end_date))
    ]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    # KPI calculations
    avg_yield = filtered_df["calculated_yield_pct"].mean()
    avg_availability = filtered_df["availability_pct"].mean()
    avg_performance = filtered_df["performance_pct"].mean()

    machine_summary = (
        filtered_df.groupby("machine_name", as_index=False)[
            ["calculated_yield_pct", "availability_pct", "performance_pct"]
        ]
        .mean()
        .round(2)
        .sort_values("availability_pct")
    )

    worst_machine = machine_summary.iloc[0]

    # Top alert
    st.warning(
        f"🚨 Worst Machine: {worst_machine['machine_name']} | "
        f"Availability: {worst_machine['availability_pct']}%"
    )

    # KPI cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Average Yield (%)", f"{avg_yield:.2f}")
    c2.metric("Average Availability (%)", f"{avg_availability:.2f}")
    c3.metric("Average Performance (%)", f"{avg_performance:.2f}")

    if avg_availability < 90:
        st.error("⚠️ Availability below target")
    else:
        st.success("✅ Availability within target")

    # Problem machines
    st.subheader("Problem Machines")
    problems = machine_summary[machine_summary["availability_pct"] < 90]

    if problems.empty:
        st.success("No machines with availability below 90%.")
    else:
        st.error("Machines with low availability detected!")
        st.dataframe(
            problems[
                [
                    "machine_name",
                    "availability_pct",
                    "calculated_yield_pct",
                    "performance_pct",
                ]
            ],
            width="stretch",
        )

    # Machine comparison table
    st.subheader("Machine Comparison")
    st.dataframe(machine_summary, width="stretch")

    # Yield chart
    st.subheader("Average Yield by Machine")
    fig_yield = px.bar(
        machine_summary,
        x="machine_name",
        y="calculated_yield_pct",
        color="machine_name",
        text="calculated_yield_pct",
        color_discrete_sequence=["#4CAF50", "#2196F3", "#FF9800"],
    )
    fig_yield.update_traces(textposition="outside")
    fig_yield.update_layout(
        showlegend=False,
        xaxis_title="Machine",
        yaxis_title="Yield (%)",
    )
    st.plotly_chart(fig_yield, width="stretch")

    # Availability chart
    st.subheader("Average Availability by Machine")
    fig_availability = px.bar(
        machine_summary,
        x="machine_name",
        y="availability_pct",
        color="machine_name",
        text="availability_pct",
        color_discrete_sequence=["#EF5350", "#42A5F5", "#66BB6A"],
    )
    fig_availability.update_traces(textposition="outside")
    fig_availability.update_layout(
        showlegend=False,
        xaxis_title="Machine",
        yaxis_title="Availability (%)",
    )
    st.plotly_chart(fig_availability, width="stretch")

    # Performance chart
    st.subheader("Average Performance by Machine")
    fig_performance = px.bar(
        machine_summary,
        x="machine_name",
        y="performance_pct",
        color="machine_name",
        text="performance_pct",
        color_discrete_sequence=["#AB47BC", "#26C6DA", "#FFA726"],
    )
    fig_performance.update_traces(textposition="outside")
    fig_performance.update_layout(
        showlegend=False,
        xaxis_title="Machine",
        yaxis_title="Performance (%)",
    )
    st.plotly_chart(fig_performance, width="stretch")

    # Downtime vs running time
    st.subheader("Downtime vs Running Time")
    time_summary = (
        filtered_df.groupby("machine_name", as_index=False)[
            ["running_time_hours", "downtime_hours"]
        ]
        .mean()
        .round(2)
    )

    fig_time = px.bar(
        time_summary,
        x="machine_name",
        y=["running_time_hours", "downtime_hours"],
        barmode="group",
        color_discrete_sequence=["#42A5F5", "#EF5350"],
    )
    fig_time.update_layout(
        xaxis_title="Machine",
        yaxis_title="Hours",
        legend_title="Time Type",
    )
    st.plotly_chart(fig_time, width="stretch")

    # Daily trend
    st.subheader("Daily KPI Trend")
    daily_summary = (
        filtered_df.groupby("log_date", as_index=False)[
            ["calculated_yield_pct", "availability_pct", "performance_pct"]
        ]
        .mean()
        .round(2)
    )

    fig_trend = px.line(
        daily_summary,
        x="log_date",
        y=["calculated_yield_pct", "availability_pct", "performance_pct"],
        markers=True,
        title="Daily KPI Trend",
    )
    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Percentage (%)",
        legend_title="Metrics",
    )
    st.plotly_chart(fig_trend, width="stretch")

    st.markdown("**Target Availability: 90%**")

    # Raw data at bottom
    st.subheader("Raw Data")
    st.dataframe(filtered_df, width="stretch")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")