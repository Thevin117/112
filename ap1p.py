import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

# 1. Force the connection variables from Secrets
try:
    # We use .get() to avoid crashing if a secret is missing
    host = st.secrets["DB_HOST"]
    port = st.secrets["DB_PORT"]
    dbname = st.secrets["DB_NAME"]
    user = st.secrets["DB_USER"]  # This should be the full string with the ID
    password = st.secrets["DB_PASSWORD"]

    # Percent-encode the password (fixes @ or # symbols)
    safe_password = urllib.parse.quote_plus(password)

    # Manual connection string construction
    conn_url = f"postgresql://{user}:{safe_password}@{host}:{port}/{dbname}"
    engine = create_engine(conn_url)
except Exception as e:
    st.error(f"Missing configuration in Secrets: {e}")

# 2. Page Setup
st.set_page_config(page_title="Manufacturing Dashboard", layout="wide")

# 3. Data Loading
@st.cache_data(ttl=600)
def load_data():
    # Make sure this table name 'production_logs' exists in your Supabase
    query = "SELECT * FROM production_logs" 
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df
    except Exception as e:
        # If it fails, this will show you EXACTLY what username the app sent
        st.error(f"Authentication failed for user: {user}")
        st.error(f"Technical error: {e}")
        return pd.DataFrame()

# 4. Run the data pull
df = load_data()

# Show the data if successful
if not df.empty:
    st.success("Successfully connected to Supabase!")
    st.dataframe(df)
else:
    st.warning("Dashboard is empty. Check the error message above.")
# Your dashboard logic (charts, filters, etc.) starts here...

# ---------- THEME ----------
BG = "#0B1220"
CARD = "#111827"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
BLUE = "#3B82F6"
GREEN = "#22C55E"
AMBER = "#F59E0B"
RED = "#EF4444"
PURPLE = "#A855F7"
CYAN = "#06B6D4"
BORDER = "#1F2937"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #111827 0%, #0F172A 100%);
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] * {{
        color: {TEXT} !important;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    .dashboard-title {{
        font-size: 3rem;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }}

    .dashboard-subtitle {{
        color: {MUTED};
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }}

    .glass-card {{
        background: linear-gradient(180deg, rgba(17,24,39,0.95) 0%, rgba(15,23,42,0.95) 100%);
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 1rem 1.2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    }}

    .kpi-card {{
        background: linear-gradient(180deg, rgba(17,24,39,1) 0%, rgba(15,23,42,1) 100%);
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 1rem 1.2rem;
        min-height: 120px;
        box-shadow: 0 10px 22px rgba(0,0,0,0.22);
    }}

    .kpi-label {{
        color: {MUTED};
        font-size: 0.95rem;
        margin-bottom: 0.4rem;
    }}

    .kpi-value {{
        color: {TEXT};
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
    }}

    .kpi-good {{
        border-left: 5px solid {GREEN};
    }}

    .kpi-warn {{
        border-left: 5px solid {AMBER};
    }}

    .kpi-bad {{
        border-left: 5px solid {RED};
    }}

    .pill {{
        display: inline-block;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        font-size: 0.9rem;
        font-weight: 600;
    }}

    .pill-red {{
        background: rgba(239,68,68,0.15);
        color: #FCA5A5;
        border: 1px solid rgba(239,68,68,0.35);
    }}

    .pill-green {{
        background: rgba(34,197,94,0.15);
        color: #86EFAC;
        border: 1px solid rgba(34,197,94,0.35);
    }}

    .pill-amber {{
        background: rgba(245,158,11,0.15);
        color: #FCD34D;
        border: 1px solid rgba(245,158,11,0.35);
    }}

    .section-title {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {TEXT};
        margin: 0.5rem 0 1rem 0;
    }}

    div[data-testid="stMetric"] {{
        background: transparent !important;
        border: none !important;
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 16px;
        overflow: hidden;
    }}

    .small-note {{
        color: {MUTED};
        font-size: 0.9rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


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


def kpi_card(label: str, value: float, threshold_good=None, threshold_warn=None, suffix="%"):
    card_class = "kpi-good"
    if threshold_good is not None and value < threshold_good:
        card_class = "kpi-bad"
    elif threshold_warn is not None and value < threshold_warn:
        card_class = "kpi-warn"

    st.markdown(
        f"""
        <div class="kpi-card {card_class}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value:.2f}{suffix}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig, title=None):
    fig.update_layout(
        title=title,
        paper_bgcolor=BG,
        plot_bgcolor=CARD,
        font=dict(color=TEXT),
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color=TEXT,
            linecolor=BORDER,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(156,163,175,0.12)",
            zeroline=False,
            color=TEXT,
            linecolor=BORDER,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT)
        ),
    )
    return fig


try:
    df = load_data()

    if df.empty:
        st.warning("No data found in production_logs_enriched.")
        st.stop()

    df["log_date"] = pd.to_datetime(df["log_date"])

    # ---------- SIDEBAR ----------
    st.sidebar.markdown("## Filters")

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

    filtered_df = df[df["machine_name"].isin(selected_machine)].copy()
    filtered_df = filtered_df[
        (filtered_df["log_date"] >= pd.to_datetime(start_date))
        & (filtered_df["log_date"] <= pd.to_datetime(end_date))
    ]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
        st.stop()

    avg_yield = filtered_df["calculated_yield_pct"].mean()
    avg_availability = filtered_df["availability_pct"].mean()
    avg_performance = filtered_df["performance_pct"].mean()
    avg_output = filtered_df["actual_output_units"].mean()

    machine_summary = (
        filtered_df.groupby("machine_name", as_index=False)[
            ["calculated_yield_pct", "availability_pct", "performance_pct",
             "running_time_hours", "downtime_hours", "actual_output_units"]
        ]
        .mean()
        .round(2)
        .sort_values("availability_pct")
    )

    worst_machine = machine_summary.iloc[0]

    line_summary = (
        filtered_df.groupby("line_code", as_index=False)[
            ["calculated_yield_pct", "availability_pct", "performance_pct", "actual_output_units"]
        ]
        .mean()
        .round(2)
        .sort_values("line_code")
    )

    problems = machine_summary[machine_summary["availability_pct"] < 90]

    # ---------- HEADER ----------
    st.markdown('<div class="dashboard-title">Manufacturing Performance Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-subtitle">Monitor manufacturing performance using yield, availability, and performance KPIs from structured production logs.</div>',
        unsafe_allow_html=True
    )

    alert_class = "pill-red" if worst_machine["availability_pct"] < 90 else "pill-amber"
    st.markdown(
        f"""
        <div class="glass-card">
            <span class="pill {alert_class}">
                🚨 Key Finding: {worst_machine['machine_name']} is the weakest machine | Availability: {worst_machine['availability_pct']}%
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # ---------- KPI CARDS ----------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("Average Yield", avg_yield, threshold_good=95, threshold_warn=97)
    with k2:
        kpi_card("Average Availability", avg_availability, threshold_good=90, threshold_warn=95)
    with k3:
        kpi_card("Average Performance", avg_performance, threshold_good=95, threshold_warn=97)
    with k4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-good">
                <div class="kpi-label">Average Output</div>
                <div class="kpi-value">{avg_output:.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # ---------- TOP INSIGHT ROW ----------
    left, right = st.columns([2.2, 1])

    with left:
        st.markdown('<div class="section-title">Daily KPI Trend</div>', unsafe_allow_html=True)
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
            color_discrete_map={
                "calculated_yield_pct": GREEN,
                "availability_pct": BLUE,
                "performance_pct": PURPLE,
            },
        )
        fig_trend = chart_layout(fig_trend)
        fig_trend.update_layout(legend_title_text="")
        st.plotly_chart(fig_trend, width="stretch")

    with right:
        st.markdown('<div class="section-title">Critical Issues</div>', unsafe_allow_html=True)

        if problems.empty:
            st.markdown(
                '<div class="glass-card"><span class="pill pill-green">✅ No machine below 90% availability</span></div>',
                unsafe_allow_html=True,
            )
        else:
            for _, row in problems.iterrows():
                st.markdown(
                    f"""
                    <div class="glass-card" style="margin-bottom: 12px;">
                        <div style="font-weight:700; font-size:1.05rem; color:{TEXT};">{row['machine_name']}</div>
                        <div class="small-note">Availability issue detected</div>
                        <div style="margin-top:8px;">
                            <span class="pill pill-red">Availability: {row['availability_pct']}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            f"""
            <div class="glass-card" style="margin-top: 12px;">
                <div style="font-weight:700; color:{TEXT};">Selected Period</div>
                <div class="small-note">{start_date} → {end_date}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # ---------- COMPARISON ROW ----------
    c_left, c_right = st.columns(2)

    with c_left:
        st.markdown('<div class="section-title">Machine Availability Comparison</div>', unsafe_allow_html=True)
        fig_availability = px.bar(
            machine_summary,
            x="machine_name",
            y="availability_pct",
            color="machine_name",
            text="availability_pct",
            color_discrete_sequence=[BLUE, RED, CYAN],
        )
        fig_availability.update_traces(textposition="outside")
        fig_availability = chart_layout(fig_availability)
        fig_availability.update_layout(showlegend=False, xaxis_title="Machine", yaxis_title="Availability (%)")
        st.plotly_chart(fig_availability, width="stretch")

    with c_right:
        st.markdown('<div class="section-title">Yield by Machine</div>', unsafe_allow_html=True)
        fig_yield = px.bar(
            machine_summary,
            x="machine_name",
            y="calculated_yield_pct",
            color="machine_name",
            text="calculated_yield_pct",
            color_discrete_sequence=[GREEN, AMBER, PURPLE],
        )
        fig_yield.update_traces(textposition="outside")
        fig_yield = chart_layout(fig_yield)
        fig_yield.update_layout(showlegend=False, xaxis_title="Machine", yaxis_title="Yield (%)")
        st.plotly_chart(fig_yield, width="stretch")

    st.write("")

    # ---------- SECOND COMPARISON ROW ----------
    d_left, d_right = st.columns(2)

    with d_left:
        st.markdown('<div class="section-title">Downtime vs Running Time</div>', unsafe_allow_html=True)
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
            color_discrete_sequence=[CYAN, RED],
        )
        fig_time = chart_layout(fig_time)
        fig_time.update_layout(xaxis_title="Machine", yaxis_title="Hours", legend_title="Time")
        st.plotly_chart(fig_time, width="stretch")

    with d_right:
        st.markdown('<div class="section-title">Line Comparison</div>', unsafe_allow_html=True)
        fig_line = px.bar(
            line_summary,
            x="line_code",
            y=["calculated_yield_pct", "availability_pct", "performance_pct"],
            barmode="group",
            color_discrete_sequence=[GREEN, BLUE, PURPLE],
        )
        fig_line = chart_layout(fig_line)
        fig_line.update_layout(xaxis_title="Line", yaxis_title="Percentage (%)", legend_title="Metric")
        st.plotly_chart(fig_line, width="stretch")

    st.write("")

    # ---------- TABLE SECTION ----------
    t_left, t_right = st.columns([1.4, 1])

    with t_left:
        st.markdown('<div class="section-title">Machine Ranking</div>', unsafe_allow_html=True)
        ranking = machine_summary[
            ["machine_name", "availability_pct", "calculated_yield_pct", "performance_pct", "downtime_hours"]
        ].copy()
        st.dataframe(ranking, width="stretch")

    with t_right:
        st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)
        best_machine = machine_summary.sort_values("availability_pct", ascending=False).iloc[0]

        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom: 12px;">
                <div style="font-weight:700; color:{TEXT};">Best Machine</div>
                <div style="font-size:1.1rem; margin-top:6px; color:{TEXT};">{best_machine['machine_name']}</div>
                <div class="small-note">Availability: {best_machine['availability_pct']}%</div>
            </div>

            <div class="glass-card" style="margin-bottom: 12px;">
                <div style="font-weight:700; color:{TEXT};">Worst Machine</div>
                <div style="font-size:1.1rem; margin-top:6px; color:{TEXT};">{worst_machine['machine_name']}</div>
                <div class="small-note">Availability: {worst_machine['availability_pct']}%</div>
            </div>

            <div class="glass-card">
                <div style="font-weight:700; color:{TEXT};">What this system solves</div>
                <div class="small-note" style="margin-top:8px;">
                    Converts manually collected production logs into KPI-based operational visibility, helping teams identify weak machines, downtime-related losses, and performance gaps faster.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # ---------- RAW DATA ----------
    with st.expander("View Raw Production Data"):
        st.dataframe(filtered_df, width="stretch")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
