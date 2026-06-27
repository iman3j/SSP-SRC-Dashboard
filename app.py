"""
SRC Portfolio Recovery Dashboard
=================================
Run with: streamlit run app.py
"""

import time
import streamlit as st
import pandas as pd

from config      import CYCLE_DAYS, CUSTOM_CSS, STATUS_OPTIONS, REMARKS_OPTIONS
from data_loader import load_data
from auth        import require_login, logout
from ibc_manager import (
    get_clusters, get_all_ibcs, get_ibc_colors,
    get_cluster_options, get_color_list,
    render_settings_page,
)
from component   import (
    build_ibc_group,
    chart_dues_per_ibc,
    chart_recovered_per_ibc,
    chart_recovery_rate,
    chart_customer_distribution,
    render_executive_summary,
    render_month_comparison,
    render_consumer_segmentation,
    render_export_buttons,
)

# ── Page Config
st.set_page_config(
    page_title="SRC Portfolio Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Login Gate
if not require_login():
    st.stop()

# ── Page State 
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"

# ── Sidebar 
with st.sidebar:
    st.markdown("## ⚡ SRC Dashboard")

    user_name = st.session_state.get("user_name", "Admin")
    st.markdown(
        f"<div style='background:#1c2333;border:1px solid #30363d;border-radius:8px;"
        f"padding:10px 14px;margin-bottom:12px'>"
        f"<div style='font-size:0.7rem;color:#8b949e'>Logged in as</div>"
        f"<div style='font-size:0.9rem;font-weight:600;color:#e6edf3'>👤 {user_name}</div>"
        f"</div>", unsafe_allow_html=True,
    )

    col_logout, col_settings = st.columns(2)
    with col_logout:
        if st.button("🚪 Logout", use_container_width=True, key="btn_logout"):
            logout()
    with col_settings:
        if st.button("⚙️ Settings", use_container_width=True, key="btn_settings"):
            st.session_state["page"] = (
                "settings" if st.session_state["page"] == "dashboard" else "dashboard"
            )
            st.rerun()

    st.markdown("---")

    uploaded_file = None
    selected_cluster = "All Clusters"
    selected_ibc     = "All IBCs"
    selected_cycle   = "All Cycle Days"
    selected_status  = "All Status"
    selected_remarks = "All Remarks"
    auto_refresh     = False

    if st.session_state["page"] == "dashboard":
        uploaded_file = st.file_uploader(
            "Upload SRC Dataset",
            type=None,
            help="Supported: xlsx, xls, xlsb, csv",
        )

        st.markdown("---")
        st.markdown("### 🔍 Filters")

        cluster_options  = get_cluster_options()
        selected_cluster = st.selectbox("Cluster",   cluster_options, index=0, key="sel_cluster")

        clusters = get_clusters()
        if selected_cluster == "All Clusters":
            ibc_opts = ["All IBCs"] + get_all_ibcs()
        else:
            ibc_opts = ["All IBCs"] + clusters.get(selected_cluster, [])

        selected_ibc     = st.selectbox("IBC Name",   ibc_opts,        index=0, key="sel_ibc")
        selected_cycle   = st.selectbox("Cycle Day",  CYCLE_DAYS,      index=0, key="sel_cycle")
        selected_status  = st.selectbox("Due Status", STATUS_OPTIONS,  index=0, key="sel_status")
        selected_remarks = st.selectbox("Remarks",    REMARKS_OPTIONS, index=0, key="sel_remarks")

        st.markdown("---")
        auto_refresh = st.toggle("Auto-refresh (30s)", value=False)
        if auto_refresh:
            st.caption("Refreshes every 30 seconds.")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.72rem;color:#6e7681;text-align:center'>"
        "SRC Portfolio Monitor<br>v2.0 · Built with Streamlit</div>",
        unsafe_allow_html=True,
    )

# ── Settings Page 
if st.session_state["page"] == "settings":
    render_settings_page()
    st.stop()

# ── Load Data
file_source = uploaded_file if uploaded_file else "src_data.xlsx"
df_raw = load_data(file_source)
df_raw = df_raw.loc[:, ~df_raw.columns.duplicated(keep="first")]
df     = df_raw.copy()

# ── Apply Filters 
clusters = get_clusters()

if selected_cluster != "All Clusters" and "IBC Name" in df.columns:
    df = df[df["IBC Name"].isin(clusters.get(selected_cluster, []))]

if selected_ibc != "All IBCs" and "IBC Name" in df.columns:
    df = df[df["IBC Name"] == selected_ibc]

if selected_cycle != "All Cycle Days" and "Cycle Day" in df.columns:
    df = df[df["Cycle Day"] == selected_cycle]

if selected_status != "All Status" and "Status" in df.columns:
    df = df[df["Status"].astype(str).str.strip() == selected_status]

if selected_remarks != "All Remarks":
    rem_col = next((c for c in df.columns if "remark" in c.lower()), None)
    if rem_col:
        df = df[df[rem_col].astype(str).str.strip() == selected_remarks]

if auto_refresh:
    time.sleep(0.1)
    st.cache_data.clear()

# ── Header
title_col, status_col = st.columns([4, 1])
with title_col:
    st.markdown(
        '<div class="dashboard-title">⚡ SRC Portfolio Dashboard</div>'
        '<div class="dashboard-subtitle">Electric Utility · SRC Recovery Monitor · Karachi</div>',
        unsafe_allow_html=True,
    )
with status_col:
    lbl = selected_cluster if selected_cluster != "All Clusters" else "All Clusters"
    if selected_ibc != "All IBCs":
        lbl += f" · {selected_ibc}"
    st.markdown(
        f'<div style="text-align:right;padding-top:14px;font-size:0.78rem;color:#8b949e">'
        f'<span class="status-dot"></span>Live · {lbl}</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Executive Summary — 28 KPI Cards + IBC Table + Charts 
render_executive_summary(df)

# ── Rest of Dashboard 
if "IBC Name" in df.columns:
    render_month_comparison(df)
    render_consumer_segmentation(df)

    ibc_group = build_ibc_group(df)

    if "run_count" not in st.session_state:
        st.session_state["run_count"] = 0
    st.session_state["run_count"] += 1
    render_export_buttons(df, ibc_group, key_suffix=str(st.session_state["run_count"]))
else:
    st.error("❌ 'IBC Name' column not found.")

# ── Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:0.72rem;color:#6e7681;padding:8px 0'>"
    "⚡ SRC Portfolio Recovery Dashboard · Built with Streamlit & Plotly"
    "</div>", unsafe_allow_html=True,
)