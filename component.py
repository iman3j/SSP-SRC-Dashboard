import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io
import numpy as np
import re

from config import IBC_COLORS_DEFAULT, COLOR_PALETTE, PLOTLY_LAYOUT
from data_loader import fmt_currency, badge_class


# ── Month Comparison Section
def render_month_comparison(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown('<div class="section-header">📅 Month-over-Month Comparison</div>', unsafe_allow_html=True)

    curr_billing = df.attrs.get("current_billing_col")
    prev_billing = df.attrs.get("prev_billing_col")
    curr_cash    = df.attrs.get("current_cash_col")
    prev_cash    = df.attrs.get("prev_cash_col")
    curr_stubs   = df.attrs.get("current_stubs_col")
    prev_stubs   = df.attrs.get("prev_stubs_col")

    if not curr_billing or not prev_billing:
        st.info("Month comparison ke liye kam az kam 2 months ka data chahiye.")
        return

    curr_month = curr_billing.replace("Billing", "").strip(" '")
    prev_month = prev_billing.replace("Billing", "").strip(" '")

    curr_bill_val  = float(df[curr_billing].sum()) if curr_billing and curr_billing in df.columns else 0
    prev_bill_val  = float(df[prev_billing].sum()) if prev_billing and prev_billing in df.columns else 0
    curr_cash_val  = float(df[curr_cash].sum())    if curr_cash    and curr_cash    in df.columns else 0
    prev_cash_val  = float(df[prev_cash].sum())    if prev_cash    and prev_cash    in df.columns else 0
    curr_stubs_val = float(df[curr_stubs].sum())   if curr_stubs   and curr_stubs   in df.columns else 0
    prev_stubs_val = float(df[prev_stubs].sum())   if prev_stubs   and prev_stubs   in df.columns else 0

    def pct_change(curr, prev):
        if prev == 0: return 0
        return ((curr - prev) / prev) * 100

    def arrow(chg):
        if chg > 0: return f"▲ +{chg:.1f}%", "#3fb950"
        if chg < 0: return f"▼ {chg:.1f}%",  "#f85149"
        return "→ 0%", "#8b949e"

    bill_arrow,  bill_color  = arrow(pct_change(curr_bill_val,  prev_bill_val))
    cash_arrow,  cash_color  = arrow(pct_change(curr_cash_val,  prev_cash_val))
    stubs_arrow, stubs_color = arrow(pct_change(curr_stubs_val, prev_stubs_val))

    c1, c2, c3 = st.columns(3)
    for col, label, curr_val, prev_val, arr, arr_color in [
        (c1, "💳 Billing",  curr_bill_val,  prev_bill_val,  bill_arrow,  bill_color),
        (c2, "💰 Recovery", curr_cash_val,  prev_cash_val,  cash_arrow,  cash_color),
        (c3, "🧾 Stubs",    curr_stubs_val, prev_stubs_val, stubs_arrow, stubs_color),
    ]:
        with col:
            is_stubs = "Stubs" in label
            curr_fmt = f"{int(curr_val):,}" if is_stubs else fmt_currency(curr_val)
            prev_fmt = f"{int(prev_val):,}" if is_stubs else fmt_currency(prev_val)
            st.markdown(
                f'<div class="kpi-card blue">'
                f'<div class="kpi-label">{label}</div>'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px">'
                f'<div><div style="font-size:0.65rem;color:#8b949e;margin-bottom:2px">{prev_month}</div>'
                f'<div style="font-family:Space Mono,monospace;font-size:1.1rem;color:#8b949e">{prev_fmt}</div></div>'
                f'<div style="font-size:1.4rem;color:#30363d">→</div>'
                f'<div><div style="font-size:0.65rem;color:#8b949e;margin-bottom:2px">{curr_month}</div>'
                f'<div style="font-family:Space Mono,monospace;font-size:1.1rem;color:#e6edf3">{curr_fmt}</div></div>'
                f'</div>'
                f'<div style="margin-top:10px;font-size:0.85rem;font-weight:700;color:{arr_color}">{arr}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure()
    categories = ["Billing", "Recovery", "Stubs Count"]
    fig.add_trace(go.Bar(
        name=prev_month, x=categories, y=[prev_bill_val, prev_cash_val, prev_stubs_val],
        marker_color="#8b949e", marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>" + prev_month + ": %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name=curr_month, x=categories, y=[curr_bill_val, curr_cash_val, curr_stubs_val],
        marker_color="#58a6ff", marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>" + curr_month + ": %{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"📊 {prev_month} vs {curr_month} Comparison", font=dict(size=14, color="#e6edf3")),
        barmode="group", yaxis_title="Amount / Count",
        **PLOTLY_LAYOUT, height=320,
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ── KPI Cards 
def render_kpi_cards(df: pd.DataFrame) -> None:
    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    def safe_nunique(col):
        if col not in df.columns: return 0
        val = df[col].nunique()
        return int(val.iloc[0]) if isinstance(val, pd.Series) else int(val)

    def safe_sum(col):
        if col not in df.columns: return 0.0
        val = df[col].sum()
        return float(val.iloc[0]) if isinstance(val, pd.Series) else float(val)

    def safe_count(mask_series):
        val = mask_series.sum()
        return int(val.iloc[0]) if isinstance(val, pd.Series) else int(val)

    total_consumers = safe_nunique("Contract Account")
    total_billed    = safe_sum("Amount Billed")
    total_recovered = safe_sum("Amount Recovered")
    total_dues      = safe_sum("Dues")
    total_cases     = safe_sum("Case Assigned")
    total_stubs     = safe_sum("Stub Collected")
    recovery_rate   = (total_recovered / total_billed) if total_billed > 0 else 0.0
    perf_rate       = (total_stubs / total_cases)      if total_cases  > 0 else 0.0
    non_paid        = safe_count(df["Stub Collected"] == 0) if "Stub Collected" in df.columns else 0
    non_paid_pct    = (non_paid / total_consumers * 100) if total_consumers > 0 else 0.0

    auto_paid     = 0
    auto_paid_pct = 0.0
    cash_date_col     = next((c for c in df.columns if "cash" in c.lower() and "date" in c.lower()), None)
    assigned_date_col = next((c for c in df.columns if "assign" in c.lower() and "date" in c.lower()), None)
    if cash_date_col and assigned_date_col:
        try:
            cash_dt     = pd.to_datetime(df[cash_date_col].astype(str).str.strip(),     dayfirst=True, errors="coerce")
            assigned_dt = pd.to_datetime(df[assigned_date_col].astype(str).str.strip(), dayfirst=True, errors="coerce")
            auto_mask   = cash_dt.notna() & assigned_dt.notna() & (cash_dt < assigned_dt)
            auto_paid     = safe_count(auto_mask)
            auto_paid_pct = (auto_paid / total_consumers * 100) if total_consumers > 0 else 0.0
        except Exception:
            pass

    paid_after = max(0, int(total_stubs) - auto_paid)
    rr_badge   = badge_class(recovery_rate)
    pr_badge   = badge_class(perf_rate)

    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    for col, color, label, value, sub, b_cls, b_txt in [
        (k1, "blue",   "Total Consumers",      f"{total_consumers:,}",        "Unique Accounts",             None,     None),
        (k2, "yellow", "Total Billing",         fmt_currency(total_billed),    f"{total_billed:,.0f} PKR",    None,     None),
        (k3, "green",  "Total Recovered",       fmt_currency(total_recovered), f"{total_recovered:,.0f} PKR", None,     None),
        (k4, "teal",   "Total Stubs",           f"{int(total_stubs):,}",       "Cash Received Count",         None,     None),
        (k5, "purple", "Recovery Rate (RR)",    f"{recovery_rate:.1%}",        "Recovered / Billed",          rr_badge,
            "Good" if recovery_rate >= 0.80 else ("Moderate" if recovery_rate >= 0.55 else "Low")),
        (k6, "orange", "Performance Rate (PR)", f"{perf_rate:.1%}",            "Stubs / Cases",               pr_badge,
            "Good" if perf_rate >= 0.80 else ("Moderate" if perf_rate >= 0.55 else "Low")),
    ]:
        badge_html = f'<div class="kpi-badge {b_cls}">{b_txt}</div>' if b_cls is not None else ""
        with col:
            st.markdown(
                f'<div class="kpi-card {color}"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div>'
                f'{badge_html}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns(4)
    for col, color, label, value, sub, b_cls, b_txt in [
        (p1, "red",   "Total Dues",            fmt_currency(total_dues),  f"{total_dues:,.0f} PKR",          "danger", "Outstanding"),
        (p2, "red",   "Non-Paid Consumers",    f"{non_paid:,}",           f"{non_paid_pct:.1f}% of total",   "danger", "Unpaid"),
        (p3, "green", "Auto-Paid Consumers",   f"{auto_paid:,}",          f"{auto_paid_pct:.1f}% of total",  "",       "Before Assignment"),
        (p4, "blue",  "Paid After Assignment",  f"{paid_after:,}",         "Cash Date ≥ Assigned Date",       "",       "Post Assignment"),
    ]:
        badge_html = f'<div class="kpi-badge {b_cls}">{b_txt}</div>' if b_cls is not None else ""
        with col:
            st.markdown(
                f'<div class="kpi-card {color}"><div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div>'
                f'{badge_html}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ── IBC Group Aggregation 
def build_ibc_group(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    agg_dict = {}
    for col in ["Amount Billed", "Amount Recovered", "Case Assigned", "Stub Collected", "Dues"]:
        if col in df.columns:
            agg_dict[col] = "sum"

    grp = df.groupby("IBC Name", as_index=False).agg(agg_dict)

    if "Contract Account" in df.columns:
        cust = df.groupby("IBC Name")["Contract Account"].nunique().reset_index()
        cust.columns = ["IBC Name", "Customers"]
        grp = grp.merge(cust, on="IBC Name", how="left")
    else:
        grp["Customers"] = 0

    grp.rename(columns={
        "Amount Billed":    "Amount_Billed",
        "Amount Recovered": "Amount_Recovered",
        "Case Assigned":    "Cases",
        "Stub Collected":   "Stubs",
        "Dues":             "Total_Dues",
    }, inplace=True)

    for col in ["Amount_Billed", "Amount_Recovered", "Cases", "Stubs", "Customers", "Total_Dues"]:
        if col not in grp.columns:
            grp[col] = 0

    grp["Recovery_Rate"] = (grp["Amount_Recovered"] / grp["Amount_Billed"].replace(0, pd.NA)).fillna(0)
    return grp.sort_values("Total_Dues", ascending=False)


# ── Charts 
def chart_dues_per_ibc(ibc_group: pd.DataFrame) -> None:
    colors = [IBC_COLORS_DEFAULT.get(n, "#f85149") for n in ibc_group["IBC Name"]]
    fig = go.Figure(go.Bar(
        x=ibc_group["Total_Dues"], y=ibc_group["IBC Name"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[fmt_currency(v) for v in ibc_group["Total_Dues"]],
        textposition="outside", textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>%{y}</b><br>Dues: PKR %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(title=dict(text="💸 Total Dues per IBC", font=dict(size=14, color="#e6edf3")),
                      xaxis_title="Total Dues (PKR)", **PLOTLY_LAYOUT, height=340)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


def chart_recovered_per_ibc(ibc_group: pd.DataFrame) -> None:
    colors = [IBC_COLORS_DEFAULT.get(n, "#58a6ff") for n in ibc_group["IBC Name"]]
    fig = go.Figure(go.Bar(
        x=ibc_group["Amount_Recovered"], y=ibc_group["IBC Name"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[fmt_currency(v) for v in ibc_group["Amount_Recovered"]],
        textposition="outside", textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>%{y}</b><br>Recovered: PKR %{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(title=dict(text="💰 Amount Recovered per IBC", font=dict(size=14, color="#e6edf3")),
                      xaxis_title="Amount Recovered (PKR)", **PLOTLY_LAYOUT, height=340)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


def chart_recovery_rate(ibc_group: pd.DataFrame) -> None:
    rr = ibc_group.sort_values("Recovery_Rate", ascending=True)
    bar_colors = ["#3fb950" if r >= 0.80 else ("#d29922" if r >= 0.55 else "#f85149") for r in rr["Recovery_Rate"]]
    fig = go.Figure(go.Bar(
        x=rr["Recovery_Rate"] * 100, y=rr["IBC Name"], orientation="h",
        marker=dict(color=bar_colors, line=dict(width=0)),
        text=[f"{v:.1%}" for v in rr["Recovery_Rate"]],
        textposition="outside", textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>%{y}</b><br>Recovery Rate: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=80, line_dash="dash", line_color="#8b949e", line_width=1,
                  annotation_text="Target 80%", annotation_font_color="#8b949e", annotation_position="top right")
    max_rr = rr["Recovery_Rate"].max() if not rr.empty else 1
    fig.update_layout(
        title=dict(text="🎯 Recovery Rate (%) by IBC", font=dict(size=14, color="#e6edf3")),
        xaxis_title="Recovery Rate (%)",
        xaxis=dict(range=[0, max(max_rr * 110, 110)], **PLOTLY_LAYOUT.get("xaxis", {})),
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "xaxis"}, height=320,
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


def chart_customer_distribution(ibc_group: pd.DataFrame, total_customers) -> None:
    total_customers = int(total_customers.iloc[0]) if isinstance(total_customers, pd.Series) else int(total_customers)
    fig = go.Figure(go.Pie(
        labels=ibc_group["IBC Name"], values=ibc_group["Customers"], hole=0.55,
        marker=dict(colors=COLOR_PALETTE[:len(ibc_group)], line=dict(color="#0d1117", width=2)),
        textinfo="label+percent", textfont=dict(color="#e6edf3", size=11),
        hovertemplate="<b>%{label}</b><br>Consumers: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="👥 Consumer Distribution by IBC", font=dict(size=14, color="#e6edf3")),
        annotations=[dict(text=f"{total_customers:,}<br><span style='font-size:10px'>Consumers</span>",
                          x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#e6edf3")],
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")}, height=320,
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ── IBC Summary Table 
def render_ibc_summary(ibc_group: pd.DataFrame) -> None:
    st.markdown('<div class="section-header">IBC Performance Summary</div>', unsafe_allow_html=True)
    s = ibc_group.copy()
    s["Performance Rate"] = (s["Stubs"] / s["Cases"].replace(0, np.nan)).fillna(0)
    display = pd.DataFrame({
        "IBC Name":         s["IBC Name"],
        "Consumers":        s["Customers"].map("{:,}".format),
        "Total Dues":       s["Total_Dues"].map(lambda x: f"PKR {x:,.0f}"),
        "Amount Billed":    s["Amount_Billed"].map(lambda x: f"PKR {x:,.0f}"),
        "Amount Recovered": s["Amount_Recovered"].map(lambda x: f"PKR {x:,.0f}"),
        "Recovery Rate":    s["Recovery_Rate"].map("{:.1%}".format),
        "Cases":            s["Cases"].map("{:,}".format),
        "Stubs":            s["Stubs"].map("{:,}".format),
        "Performance Rate": s["Performance Rate"].map("{:.1%}".format),
    })
    st.dataframe(display, use_container_width=True, hide_index=True)


# ── Scheme Eligibility Summary
def render_scheme_summary(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown('<div class="section-header">📋 Scheme / Remarks Summary</div>', unsafe_allow_html=True)

    remarks_col = next((c for c in df.columns if "remark" in c.lower()), None)
    if not remarks_col:
        st.info("Remarks column not found.")
        return

    scheme_counts = df[remarks_col].value_counts().reset_index()
    scheme_counts.columns = ["Remarks", "Count"]

    colors = ["#58a6ff", "#3fb950", "#a371f7", "#f78166", "#d29922", "#39c5cf"]
    fig = go.Figure(go.Bar(
        x=scheme_counts["Count"], y=scheme_counts["Remarks"], orientation="h",
        marker=dict(color=colors[:len(scheme_counts)], line=dict(width=0)),
        text=scheme_counts["Count"],
        textposition="outside", textfont=dict(color="#c9d1d9", size=11),
        hovertemplate="<b>%{y}</b><br>Count: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="📋 Consumer Count by Scheme/Remarks", font=dict(size=14, color="#e6edf3")),
        xaxis_title="Number of Consumers", **PLOTLY_LAYOUT, height=320,
    )
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)


# ── Export Buttons 
def render_export_buttons(df: pd.DataFrame, ibc_group: pd.DataFrame, key_suffix: str = "0") -> None:
    st.markdown("---")
    st.markdown('<div class="section-header">📥 Export Data</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            summary_export = ibc_group.copy()
            summary_export.rename(columns={
                "Amount_Billed":    "Amount Billed",
                "Amount_Recovered": "Amount Recovered",
                "Cases":            "Cases",
                "Stubs":            "Stubs",
                "Total_Dues":       "Total Dues",
            }, inplace=True)
            summary_export.to_excel(writer, sheet_name="IBC Summary", index=False)
            df.to_excel(writer, sheet_name="Consumer Detail", index=False)
        excel_buffer.seek(0)
        st.download_button(
            "📊 Download Excel Report",
            data=excel_buffer,
            file_name="src_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"btn_export_excel_main_{key_suffix}",
        )

# __ Smart Customer Segmentation 
def render_consumer_segmentation(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown('<div class="Section-Header">🎯 Smart Consumer Segmentation</div>',unsafe_allow_html=True)

    # ── Categorize consumers — vectorized
    df_seg = df.copy()
    df_seg = df_seg.loc[:, ~df_seg.columns.duplicated(keep="first")]

    # Numeric columns safely extract karo
    cash = pd.to_numeric(df_seg.get("Amount Recovered", pd.Series(0, index=df_seg.index)), errors="coerce").fillna(0)
    dues = pd.to_numeric(df_seg.get("Dues",             pd.Series(0, index=df_seg.index)), errors="coerce").fillna(0)
    lpa  = pd.to_numeric(df_seg.get("LPA",              pd.Series(0, index=df_seg.index)), errors="coerce").fillna(0)

    # Vectorized categorization
    conditions = [
        cash > 0,
        (cash == 0) & (lpa > 0),
        (cash == 0) & (lpa == 0) & (dues > 0),
    ]
    choices = [
        "✅ Regular Payer",
        "⚠️ Lapsed Payer",
        "🔴 Chronic Non-Payer",
    ]
    df_seg["Category"] = np.select(conditions, choices, default="⚪ No History")

    # ── Summary cards 
    cat_counts = df_seg["Category"].value_counts()
    total      = len(df_seg)

    st.markdown('<div class="section-header">Consumer Category Breakdown</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, cat, color in [
        (c1, "✅ Regular Payer",      "green"),
        (c2, "⚠️ Lapsed Payer",       "yellow"),
        (c3, "🔴 Chronic Non-Payer",  "red"),
        (c4, "⚪ No History",          "blue"),
    ]:
        count = int(cat_counts.get(cat, 0))
        pct   = (count / total * 100) if total > 0 else 0
        with col:
            st.markdown(
                f'<div class="kpi-card {color}">'
                f'<div class="kpi-label">{cat}</div>'
                f'<div class="kpi-value">{count:,}</div>'
                f'<div class="kpi-sub">{pct:.1f}% of total</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filter & Export Section
    st.markdown('<div class="section-header">🔽 Filter & Export Cases</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        selected_cat = st.selectbox(
            "Consumer Category",
            ["All", "✅ Regular Payer", "⚠️ Lapsed Payer", "🔴 Chronic Non-Payer", "⚪ No History"],
            index=0,
            key="seg_category",
        )

    with f2:
        ibc_options = ["All IBCs"] + sorted(df_seg["IBC Name"].dropna().unique().tolist()) if "IBC Name" in df_seg.columns else ["All IBCs"]
        selected_seg_ibc = st.selectbox("IBC Name", ibc_options, index=0, key="seg_ibc")

    with f3:
        max_cases   = len(df_seg)
        num_cases   = st.number_input(
            "How many Cases Do You Want",
            min_value=1,
            max_value=max_cases,
            value=min(100, max_cases),
            step=50,
            key="seg_num_cases",
        )

    with f4:
        sort_by = st.selectbox(
            "Sort by",
            ["Dues (High to Low)", "Dues (Low to High)", "LPA (High to Low)", "No Sort"],
            index=0,
            key="seg_sort",
        )

    # ── Apply filters 
    filtered = df_seg.copy()

    if selected_cat != "All":
        filtered = filtered[filtered["Category"] == selected_cat]

    if selected_seg_ibc != "All IBCs":
        filtered = filtered[filtered["IBC Name"] == selected_seg_ibc]

    # Sort
    if "Dues (High to Low)" in sort_by and "Dues" in filtered.columns:
        filtered = filtered.sort_values("Dues", ascending=False)
    elif "Dues (Low to High)" in sort_by and "Dues" in filtered.columns:
        filtered = filtered.sort_values("Dues", ascending=True)
    elif "LPA (High to Low)" in sort_by and "LPA" in filtered.columns:
        filtered = filtered.sort_values("LPA", ascending=False)

    # Limit to selected number
    filtered = filtered.head(int(num_cases))

    st.caption(f"📋 Showing {len(filtered):,} cases — Category: **{selected_cat}** | IBC: **{selected_seg_ibc}**")

    # ── Display table 
    cols_to_show = [c for c in [
        "Category", "Contract Account", "Customer Name", "Customer Address",
        "IBC Name", "Cycle Day", "Amount Billed", "Amount Recovered",
        "Dues", "LPA", "LPD", "Status", "REMARKS"
    ] if c in filtered.columns]

    st.dataframe(
        filtered[cols_to_show].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount Billed":    st.column_config.NumberColumn("Billed (PKR)",    format="PKR %,.0f"),
            "Amount Recovered": st.column_config.NumberColumn("Recovered (PKR)", format="PKR %,.0f"),
            "Dues":             st.column_config.NumberColumn("Dues (PKR)",      format="PKR %,.0f"),
            "LPA":              st.column_config.NumberColumn("Last Paid (PKR)", format="PKR %,.0f"),
            "Category":         st.column_config.TextColumn("Category"),
        },
    )

    # ── Export filtered cases 
    st.markdown("<br>", unsafe_allow_html=True)
    ex1, ex2 = st.columns(2)

    with ex1:
        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            filtered[cols_to_show].reset_index(drop=True).to_excel(
                writer, sheet_name="Filtered Cases", index=False
            )
        buf.seek(0)
        fname = f"{selected_cat.replace('✅','').replace('⚠️','').replace('🔴','').replace('⚪','').strip()}_{selected_seg_ibc}_{int(num_cases)}_cases.xlsx"
        st.download_button(
            "📥 Download Excel — Filtered Cases",
            data=buf,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="btn_seg_excel",
        )

    with ex2:
        st.download_button(
            "📄 Download CSV — Filtered Cases",
            data=filtered[cols_to_show].to_csv(index=False).encode("utf-8"),
            file_name=fname.replace(".xlsx", ".csv"),
            mime="text/csv",
            use_container_width=True,
            key="btn_seg_csv",
        )

def render_executive_summary(df: pd.DataFrame) -> None:
    st.markdown("---")
    st.markdown('<div class="section-header">📊 Executive Summary — IBC wise KPIs</div>', unsafe_allow_html=True)

    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # ── Detect month columns 
    MONTHS = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)"
    billing_cols = sorted([c for c in df.columns if re.search(rf"billing.*{MONTHS}", c.lower())])
    cash_cols    = sorted([c for c in df.columns if re.search(rf"^cash.*{MONTHS}", c.lower()) and "date" not in c.lower()])
    stubs_cols   = sorted([c for c in df.columns if re.search(rf"^stubs.*{MONTHS}", c.lower()) and "uni" not in c.lower()])

    curr_bill_col  = billing_cols[-1]  if billing_cols           else None
    prev_bill_col  = billing_cols[-2]  if len(billing_cols) >= 2 else None
    curr_cash_col  = cash_cols[-1]     if cash_cols              else None
    prev_cash_col  = cash_cols[-2]     if len(cash_cols)  >= 2  else None
    curr_stubs_col = stubs_cols[-1]    if stubs_cols             else None
    prev_stubs_col = stubs_cols[-2]    if len(stubs_cols) >= 2  else None

    curr_month = (curr_cash_col or "").replace("Cash","").strip(" '") if curr_cash_col else "CM"
    prev_month = (prev_cash_col or "").replace("Cash","").strip(" '") if prev_cash_col else "LM"

    curr_days = 31
    prev_days = 30

    if "IBC Name" not in df.columns:
        st.warning("IBC Name column not found.")
        return

    # ── Get Target RR + Potential Target 
    try:
        from ibc_manager import get_target_rr, get_potential_target
        target_rr_map        = get_target_rr()
        potential_target_map = get_potential_target()
    except Exception:
        target_rr_map        = {}
        potential_target_map = {}

    # ── Vectorized groupby 
    agg_dict = {"IBC Name": "count"}
    agg_dict["IBC Name"] = "count"

    def safe_agg(col):
        return (col, "sum") if col and col in df.columns else ("IBC Name", "count")

    grp = df.groupby("IBC Name", as_index=False).agg(
        Cases    =("IBC Name",       "count"),
        Dues     =safe_agg("Dues"),
        Billing  =safe_agg(curr_bill_col),
        Cash     =safe_agg(curr_cash_col),
        LM_Cash  =safe_agg(prev_cash_col),
        Stubs    =safe_agg(curr_stubs_col),
        LM_Stubs =safe_agg(prev_stubs_col),
    )

    # Ensure numeric
    for col in ["Dues", "Billing", "Cash", "LM_Cash", "Stubs", "LM_Stubs"]:
        if col not in grp.columns:
            grp[col] = 0.0
        grp[col] = pd.to_numeric(grp[col], errors="coerce").fillna(0)

    total_cash_all = grp["Cash"].sum() if grp["Cash"].sum() > 0 else 1

    grp["Stubs_Var"]    = grp["Stubs"]   - grp["LM_Stubs"]
    grp["PR"]           = (grp["Stubs"]   / grp["Cases"].replace(0, pd.NA)).fillna(0)
    grp["RR"]           = (grp["Cash"]    / grp["Billing"].replace(0, pd.NA)).fillna(0)
    grp["Contribution"] = (grp["Cash"]    / total_cash_all)
    grp["Target_RR"]    = grp["IBC Name"].map(lambda x: float(target_rr_map.get(x, 80.0)) / 100)
    grp["RR_Deficit"]   = grp["RR"]       - grp["Target_RR"]
    grp["Target_Amt"]   = grp["Billing"]  * grp["Target_RR"]
    grp["Amt_Deficit"]  = grp["Target_Amt"] - grp["Cash"]
    grp["Tgt_Achv"]     = (grp["Cash"]    / grp["Target_Amt"].replace(0, pd.NA)).fillna(0)
    grp["Avg_Stub_Rec"] = (grp["Cash"]    / grp["Stubs"].replace(0, pd.NA)).fillna(0)
    grp["Pot_Tgt"]      = grp["IBC Name"].map(lambda x: float(potential_target_map.get(x, 0.0)))
    grp["Pot_Deficit"]  = grp["Pot_Tgt"]  - grp["Cash"]
    grp["Pot_Achv"]     = (grp["Cash"]    / grp["Pot_Tgt"].replace(0, pd.NA)).fillna(0)
    grp["Pot_RR"]       = (grp["Pot_Tgt"] / grp["Billing"].replace(0, pd.NA)).fillna(0)
    grp["Pot_RR_Def"]   = grp["Pot_RR"]   - grp["RR"]
    grp["Surplus_LM"]   = grp["Cash"]     - grp["LM_Cash"]
    grp["Prev_Avg_Day"] = grp["LM_Cash"]  / prev_days
    grp["Curr_Avg_Day"] = grp["Cash"]     / curr_days
    grp = grp.fillna(0)
    
    # ── Grand Total row add karo ─────────────────────────────────────────────
    grand_total = pd.DataFrame([{
        "IBC Name":  "🏁 GRAND TOTAL",
        "Cases":     grp["Cases"].sum(),
        "Dues":      grp["Dues"].sum(),
        "Billing":   grp["Billing"].sum(),
        "Cash":      grp["Cash"].sum(),
        "LM_Cash":   grp["LM_Cash"].sum(),
        "Stubs":     grp["Stubs"].sum(),
        "LM_Stubs":  grp["LM_Stubs"].sum(),
        "Stubs_Var": grp["Stubs"].sum() - grp["LM_Stubs"].sum(),
        "PR":        (grp["Stubs"].sum() / grp["Cases"].sum())  if grp["Cases"].sum()  > 0 else 0,
        "RR":        (grp["Cash"].sum()  / grp["Billing"].sum()) if grp["Billing"].sum() > 0 else 0,
        "Contribution": 1.0,
        "Target_RR": grp["Target_RR"].mean(),
        "RR_Deficit": grp["Target_RR"].mean() - ((grp["Cash"].sum() / grp["Billing"].sum()) if grp["Billing"].sum() > 0 else 0),
        "Target_Amt": grp["Target_Amt"].sum(),
        "Amt_Deficit": grp["Amt_Deficit"].sum(),
        "Tgt_Achv":  (grp["Cash"].sum() / grp["Target_Amt"].sum())   if grp["Target_Amt"].sum()  > 0 else 0,
        "Avg_Stub_Rec": (grp["Cash"].sum() / grp["Stubs"].sum())     if grp["Stubs"].sum()       > 0 else 0,
        "Pot_Tgt":   grp["Pot_Tgt"].sum(),
        "Pot_Deficit": grp["Pot_Deficit"].sum(),
        "Pot_Achv":  (grp["Cash"].sum() / grp["Pot_Tgt"].sum())      if grp["Pot_Tgt"].sum()     > 0 else 0,
        "Pot_RR":    (grp["Pot_Tgt"].sum() / grp["Billing"].sum())   if grp["Billing"].sum()     > 0 else 0,
        "Pot_RR_Def": 0,
        "Surplus_LM": grp["Surplus_LM"].sum(),
        "Prev_Avg_Day": grp["LM_Cash"].sum() / prev_days,
        "Curr_Avg_Day": grp["Cash"].sum()    / curr_days,
    }])
    grand_total["Pot_RR_Def"] = grand_total["Pot_RR"] - grand_total["RR"]

    grp_with_total = pd.concat([grp, grand_total], ignore_index=True)

    # ── Totals 
    total_cases    = int(grp["Cases"].sum())
    total_dues     = grp["Dues"].sum()
    total_billing  = grp["Billing"].sum()
    total_cash     = grp["Cash"].sum()
    total_lm_cash  = grp["LM_Cash"].sum()
    total_stubs    = int(grp["Stubs"].sum())
    total_lm_stubs = int(grp["LM_Stubs"].sum())
    total_stubs_v  = total_stubs - total_lm_stubs
    total_pr       = (total_stubs  / total_cases)   if total_cases   > 0 else 0
    total_rr       = (total_cash   / total_billing) if total_billing > 0 else 0
    total_tgt_rr   = grp["Target_RR"].mean()
    total_tgt_amt  = grp["Target_Amt"].sum()
    total_amt_def  = grp["Amt_Deficit"].sum()
    total_tgt_achv = (total_cash  / total_tgt_amt)  if total_tgt_amt > 0 else 0
    total_avg_stub = (total_cash  / total_stubs)     if total_stubs   > 0 else 0
    total_pot_tgt  = grp["Pot_Tgt"].sum()
    total_pot_def  = grp["Pot_Deficit"].sum()
    total_pot_achv = (total_cash  / total_pot_tgt)  if total_pot_tgt > 0 else 0
    total_pot_rr   = (total_pot_tgt / total_billing) if total_billing > 0 else 0
    total_surplus  = total_cash   - total_lm_cash
    total_apr_avg  = total_lm_cash / prev_days
    total_may_avg  = total_cash    / curr_days

    # ── KPI Cards 
    st.markdown('<div class="section-header">Key Performance Indicators</div>', unsafe_allow_html=True)

    def kpi(col, color, label, value, sub=""):
        with col:
            st.markdown(
                f'<div class="kpi-card {color}">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'<div class="kpi-sub">{sub}</div>'
                f'</div>', unsafe_allow_html=True,
            )

    r1 = st.columns(4)
    kpi(r1[0], "blue",   "Total Cases",          f"{total_cases:,}",           "All IBCs")
    kpi(r1[1], "red",    "Total Dues",            fmt_currency(total_dues),      "Outstanding")
    kpi(r1[2], "yellow", f"Billing {curr_month}", fmt_currency(total_billing),   "Current Month")
    kpi(r1[3], "green",  f"Cash {curr_month}",    fmt_currency(total_cash),      "Recovered")
    st.markdown("<br>", unsafe_allow_html=True)

    r2 = st.columns(4)
    kpi(r2[0], "teal",   "Stubs",           f"{total_stubs:,}",                          f"{curr_month}")
    kpi(r2[1], "blue",   "LM Stubs",        f"{total_lm_stubs:,}",                       f"{prev_month}")
    kpi(r2[2], "green" if total_stubs_v >= 0 else "red",
               "Stubs Variance",  f"{'▲' if total_stubs_v>=0 else '▼'} {abs(total_stubs_v):,}", "vs Last Month")
    kpi(r2[3], "purple", "Performance Rate", f"{total_pr*100:.1f}%",                     "Stubs / Cases")
    st.markdown("<br>", unsafe_allow_html=True)

    r3 = st.columns(4)
    kpi(r3[0], "green",  "Recovery Rate",    f"{total_rr*100:.1f}%",                     "Cash / Billing")
    kpi(r3[1], "blue",   "Contribution",     "100%",                                     "Portfolio Total")
    kpi(r3[2], "yellow", "Target RR (Avg)",  f"{total_tgt_rr*100:.1f}%",                 "IBC Average")
    kpi(r3[3], "red" if total_rr < total_tgt_rr else "green",
               "RR Deficit",       f"{abs((total_tgt_rr - total_rr)*100):.1f}%",         "Target - Actual")
    st.markdown("<br>", unsafe_allow_html=True)

    r4 = st.columns(4)
    kpi(r4[0], "yellow", "Target Amount",    fmt_currency(total_tgt_amt),                "Billing × Target RR")
    kpi(r4[1], "red",    "Amount Deficit",   fmt_currency(total_amt_def),                "Target - Cash")
    kpi(r4[2], "green" if total_tgt_achv >= 1 else "yellow",
               "Target Achievement", f"{total_tgt_achv*100:.1f}%",                      "Cash / Target Amt")
    kpi(r4[3], "teal",   "Avg Stub Recovery", fmt_currency(total_avg_stub),              "Cash / Stubs")
    st.markdown("<br>", unsafe_allow_html=True)

    r5 = st.columns(4)
    kpi(r5[0], "purple", "Potential Target",  fmt_currency(total_pot_tgt),               "Manually Set")
    kpi(r5[1], "red",    "Potential Deficit", fmt_currency(total_pot_def),               "Potential - Cash")
    kpi(r5[2], "green" if total_pot_achv >= 1 else "yellow",
               "Potential Achv %",  f"{total_pot_achv*100:.1f}%",                       "Cash / Potential")
    kpi(r5[3], "blue",   "Potential RR %",    f"{total_pot_rr*100:.1f}%",               "Potential / Billing")
    st.markdown("<br>", unsafe_allow_html=True)

    r6 = st.columns(4)
    kpi(r6[0], "red",    "Potential RR Deficit", f"{(total_pot_rr-total_rr)*100:.1f}%", "Potential RR - RR")
    kpi(r6[1], "green" if total_surplus >= 0 else "red",
               "Surplus/Deficit LM", fmt_currency(total_surplus),                       f"Cash vs {prev_month}")
    kpi(r6[2], "blue",   f"{prev_month} Avg/Day", fmt_currency(total_apr_avg),          "Per day avg")
    kpi(r6[3], "teal",   f"{curr_month} Avg/Day", fmt_currency(total_may_avg),          "Per day avg")
    st.markdown("<br>", unsafe_allow_html=True)

    r7 = st.columns(4)
    kpi(r7[0], "purple", f"LM Cash {prev_month}", fmt_currency(total_lm_cash),          "Last Month Recovery")
    kpi(r7[1], "green" if (total_may_avg - total_apr_avg) >= 0 else "red",
               "Day Avg Variance",  fmt_currency(total_may_avg - total_apr_avg),        f"{curr_month} vs {prev_month}")
    kpi(r7[2], "yellow", "Target % Achv (RR)",  f"{total_tgt_achv*100:.1f}%",           "Cash / Target Amt")
    kpi(r7[3], "blue",   "Target % Achv (Pot)", f"{total_pot_achv*100:.1f}%",           "Cash / Potential")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── IBC Table 
    st.markdown('<div class="section-header">IBC-wise Detailed Summary</div>', unsafe_allow_html=True)

    disp = grp_with_total[["IBC Name", "Cases", "Dues", "Billing", "Cash", "LM_Cash",
                "Stubs", "LM_Stubs", "Stubs_Var", "PR", "RR",
                "Contribution", "Target_RR", "RR_Deficit", "Target_Amt",
                "Amt_Deficit", "Tgt_Achv", "Avg_Stub_Rec", "Pot_Tgt",
                "Pot_Deficit", "Pot_Achv", "Pot_RR", "Pot_RR_Def",
                "Surplus_LM", "Prev_Avg_Day", "Curr_Avg_Day"]].copy()

    disp.columns = [
        "IBC", "Cases", "Dues", f"Billing {curr_month}", f"Cash {curr_month}",
        f"Cash {prev_month}", "Stubs", "LM Stubs", "Stubs Var",
        "PR %", "RR %", "Contribution %", "Target RR %", "RR Deficit",
        "Target Amount", "Amount Deficit", "Target Achv %", "Avg Stub Rec",
        "Potential Target", "Pot Deficit", "Pot Achv %", "Pot RR %",
        "Pot RR Deficit", "Surplus/Deficit LM",
        f"{prev_month} Avg/Day", f"{curr_month} Avg/Day",
    ]

    # Format
    money_c = [f"Billing {curr_month}", f"Cash {curr_month}", f"Cash {prev_month}",
               "Dues", "Target Amount", "Amount Deficit", "Avg Stub Rec",
               "Potential Target", "Pot Deficit", "Surplus/Deficit LM",
               f"{prev_month} Avg/Day", f"{curr_month} Avg/Day"]
    pct_c   = ["PR %", "RR %", "Contribution %", "Target RR %", "RR Deficit",
               "Target Achv %", "Pot Achv %", "Pot RR %", "Pot RR Deficit"]

    for c in money_c:
        if c in disp.columns:
            disp[c] = disp[c].apply(fmt_currency)
    for c in pct_c:
        if c in disp.columns:
            disp[c] = disp[c].apply(lambda x: f"{x*100:.1f}%")
    disp["Cases"]     = disp["Cases"].apply(lambda x: f"{int(x):,}")
    disp["Stubs"]     = disp["Stubs"].apply(lambda x: f"{int(x):,}")
    disp["LM Stubs"]  = disp["LM Stubs"].apply(lambda x: f"{int(x):,}")
    disp["Stubs Var"] = grp_with_total["Stubs_Var"].apply(lambda x: f"{'▲' if x>=0 else '▼'} {abs(int(x)):,}")

    st.dataframe(disp, use_container_width=True, hide_index=True)

    # ── Charts 
    st.markdown('<div class="section-header">Visual Analysis</div>', unsafe_allow_html=True)

    ch1, ch2 = st.columns(2)
    with ch1:
        bar_colors = ["#22c55e" if r >= t else "#ef4444"
                      for r, t in zip(grp["RR"], grp["Target_RR"])]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="RR %", x=grp["IBC Name"], y=grp["RR"]*100,
            marker_color=bar_colors, marker_line_width=0,
            text=[f"{r*100:.1f}%" for r in grp["RR"]],
            textposition="outside", textfont=dict(color="#c9d1d9", size=10),
        ))
        fig.add_trace(go.Scatter(
            name="Target RR", x=grp["IBC Name"], y=grp["Target_RR"]*100,
            mode="lines+markers", line=dict(color="#f59e0b", dash="dash", width=2),
            marker=dict(size=8),
        ))
        fig.update_layout(
            title=dict(text=f"📈 RR% vs Target — {curr_month}", font=dict(size=13, color="#e6edf3")),
            yaxis_title="Rate %", **PLOTLY_LAYOUT, height=300,
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name=f"Cash {prev_month}", x=grp["IBC Name"], y=grp["LM_Cash"],
            marker_color="#8b949e", marker_line_width=0,
        ))
        fig2.add_trace(go.Bar(
            name=f"Cash {curr_month}", x=grp["IBC Name"], y=grp["Cash"],
            marker_color="#3fb950", marker_line_width=0,
        ))
        fig2.update_layout(
            title=dict(text=f"💰 Cash: {prev_month} vs {curr_month}", font=dict(size=13, color="#e6edf3")),
            barmode="group", yaxis_title="PKR", **PLOTLY_LAYOUT, height=300,
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    ch3, ch4 = st.columns(2)
    with ch3:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name=f"Stubs {prev_month}", x=grp["IBC Name"], y=grp["LM_Stubs"],
            marker_color="#8b949e", marker_line_width=0,
        ))
        fig3.add_trace(go.Bar(
            name=f"Stubs {curr_month}", x=grp["IBC Name"], y=grp["Stubs"],
            marker_color="#58a6ff", marker_line_width=0,
        ))
        fig3.update_layout(
            title=dict(text=f"🧾 Stubs: {prev_month} vs {curr_month}", font=dict(size=13, color="#e6edf3")),
            barmode="group", yaxis_title="Count", **PLOTLY_LAYOUT, height=300,
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with ch4:
        fig4 = go.Figure(go.Bar(
            x=grp["IBC Name"], y=grp["Contribution"]*100,
            marker_color="#a371f7", marker_line_width=0,
            text=[f"{c*100:.1f}%" for c in grp["Contribution"]],
            textposition="outside", textfont=dict(color="#c9d1d9", size=10),
        ))
        fig4.update_layout(
            title=dict(text="📊 Contribution % to Total Recovery", font=dict(size=13, color="#e6edf3")),
            yaxis_title="%", **PLOTLY_LAYOUT, height=300,
        )
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Export 
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        grp.to_excel(writer, sheet_name="Executive Summary", index=False)
    buf.seek(0)
    st.download_button(
        "📥 Download Executive Summary",
        data=buf,
        file_name=f"Executive_Summary_{curr_month}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
        key="btn_exec_summary_dl",
    )