# config.py — All constants and configuration for the dashboard

DEFAULT_CLUSTERS = {
    "Defence Cluster":  ["Defence", "Saddar", "Clifton"],
    "Society Cluster":  ["Garden", "Bahadurabad", "Tipu Sultan"],
}

REQUIRED_COLUMNS = {
    "Contract Account": ["contract account", "consumer no", "consumer number", "account"],
    "Customer Name":    ["customer name", "consumer name", "name"],
    "Customer Address": ["address", "customer address"],
    "IBC Name":         ["ibc name", "ibc"],
    "Cycle Day":        ["cycle day", "cycle"],
    "Dues":             ["Dues"],
    "LPA":              ["lpa", "last payment amount"],
    "LPD":              ["lpd", "last payment date"],
    "Status":           ["due status", "status"],
    "REMARKS":          ["remarks", "remark"],
}

# Month-based columns detected dynamically — no hardcoding needed

CYCLE_DAYS     = ["All Cycle Days"] + [str(i) for i in range(1, 21)]
STATUS_OPTIONS = ["All Status", "Not Due", "Overdue", "Paid"]
REMARKS_OPTIONS = ["All Remarks", "Eligible in Scheme", "Registered in Scheme",
                   "WO Scheme", "Fully Settled & Locked"]

IBC_COLORS_DEFAULT = {
    "Bahadurabad": "#58a6ff",
    "Tipu Sultan": "#39c5cf",
    "Garden":      "#3fb950",
    "Clifton":     "#a371f7",
    "Saddar":      "#f78166",
    "Defence":     "#d29922",
}

COLOR_PALETTE = [
    "#58a6ff", "#3fb950", "#a371f7", "#f78166",
    "#d29922", "#39c5cf", "#e36209", "#f85149",
    "#0ead69", "#8b949e", "#1f6feb", "#db61a2",
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#c9d1d9", size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#8b949e"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d", tickcolor="#8b949e"),
    legend=dict(
        bgcolor="rgba(22,27,34,0.9)",
        bordercolor="#30363d",
        borderwidth=1,
        font=dict(color="#c9d1d9"),
    ),
    hoverlabel=dict(bgcolor="#161b22", bordercolor="#58a6ff", font_color="#e6edf3"),
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #30363d;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] h1, h2, h3 { color: #c9d1d9 !important; }

    .kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #1c2333 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 22px 24px;
        text-align: center;
        transition: border-color 0.2s ease, transform 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover { border-color: #58a6ff; transform: translateY(-2px); }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        border-radius: 12px 12px 0 0;
    }
    .kpi-card.blue::before   { background: linear-gradient(90deg, #58a6ff, #1f6feb); }
    .kpi-card.green::before  { background: linear-gradient(90deg, #3fb950, #238636); }
    .kpi-card.yellow::before { background: linear-gradient(90deg, #d29922, #b7950b); }
    .kpi-card.purple::before { background: linear-gradient(90deg, #a371f7, #6e40c9); }
    .kpi-card.teal::before   { background: linear-gradient(90deg, #39d353, #0ead69); }
    .kpi-card.red::before    { background: linear-gradient(90deg, #f85149, #b91c1c); }
    .kpi-card.orange::before { background: linear-gradient(90deg, #e3652a, #c2440e); }

    .kpi-label {
        font-size: 0.72rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.08em;
        color: #8b949e; margin-bottom: 8px;
    }
    .kpi-value {
        font-family: 'Space Mono', monospace;
        font-size: 1.7rem; font-weight: 700;
        color: #e6edf3; line-height: 1.2;
    }
    .kpi-sub  { font-size: 0.75rem; color: #8b949e; margin-top: 4px; }
    .kpi-badge {
        display: inline-block; margin-top: 8px;
        font-size: 0.7rem; font-weight: 600;
        padding: 2px 10px; border-radius: 20px;
        background: rgba(63,185,80,0.15);
        color: #3fb950; border: 1px solid rgba(63,185,80,0.3);
    }
    .kpi-badge.warn   { background: rgba(210,153,34,0.15);  color: #d29922; border-color: rgba(210,153,34,0.3); }
    .kpi-badge.danger { background: rgba(248,81,73,0.15);   color: #f85149; border-color: rgba(248,81,73,0.3); }

    .section-header {
        font-size: 0.8rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.1em;
        color: #8b949e; border-bottom: 1px solid #21262d;
        padding-bottom: 10px; margin-bottom: 16px; margin-top: 8px;
    }
    .dashboard-title {
        font-family: 'Space Mono', monospace;
        font-size: 1.6rem; font-weight: 700;
        color: #e6edf3; letter-spacing: -0.02em;
    }
    .dashboard-subtitle { font-size: 0.82rem; color: #8b949e; margin-top: 2px; }
    .status-dot {
        display: inline-block; width: 8px; height: 8px;
        border-radius: 50%; background: #3fb950;
        margin-right: 6px; animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(63,185,80,0.4); }
        70%  { box-shadow: 0 0 0 6px rgba(63,185,80,0); }
        100% { box-shadow: 0 0 0 0 rgba(63,185,80,0); }
    }
    .chart-container {
        background: #161b22; border: 1px solid #21262d;
        border-radius: 12px; padding: 4px; margin-bottom: 16px;
    }
    hr { border-color: #21262d !important; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .stSelectbox > div > div {
        background: #161b22 !important;
        border-color: #30363d !important;
        color: #e6edf3 !important;
    }
    .stFileUploader { border: 1px dashed #30363d !important; border-radius: 10px !important; }
    .stAlert { border-radius: 10px !important; }
    .settings-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
</style>
"""