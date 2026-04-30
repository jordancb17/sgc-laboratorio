import streamlit as st

MAIN_CSS = """
<style>
/* ── Fondo general ─────────────────────────────────────────────────── */
.stApp { background-color: #f1f5f9 !important; }

/* ── Sidebar ───────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(170deg, #0f172a 0%, #1e3a8a 65%, #1d4ed8 100%) !important;
    border-right: 1px solid #1e40af !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] a { color: #cbd5e1 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: white !important; }

/* Nav links */
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
    border-radius: 8px !important;
    padding: 6px 10px !important;
    color: #cbd5e1 !important;
    transition: all 0.15s !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover {
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
}
section[data-testid="stSidebar"] [aria-current="page"],
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] [aria-selected="true"] {
    background: rgba(255,255,255,0.18) !important;
    color: white !important;
    font-weight: 600 !important;
}

/* ── Layout ────────────────────────────────────────────────────────── */
.main .block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Títulos ───────────────────────────────────────────────────────── */
h1 {
    color: #0f172a !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
    letter-spacing: -0.02em !important;
    padding-bottom: 0.75rem !important;
    border-bottom: 2px solid #e2e8f0 !important;
    margin-bottom: 1.25rem !important;
}
h2 { color: #1e293b !important; font-weight: 600 !important; font-size: 1.15rem !important; margin-top: 0.5rem !important; }
h3 { color: #334155 !important; font-weight: 600 !important; font-size: 1rem !important; }

/* ── Métricas ──────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: white !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 4px 12px rgba(0,0,0,0.04) !important;
    border-left: 4px solid #2563eb !important;
    transition: box-shadow 0.2s !important;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.85rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-weight: 600 !important;
    font-size: 0.76rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

/* ── Tabs ──────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px !important;
    background: white !important;
    padding: 4px !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07) !important;
    border: 1px solid #e2e8f0 !important;
    margin-bottom: 1.25rem !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    padding: 7px 16px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    color: #64748b !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    color: white !important;
    box-shadow: 0 2px 6px rgba(37,99,235,0.3) !important;
    font-weight: 600 !important;
}

/* ── Botones ───────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(37,99,235,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1e40af, #2563eb) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    border: 1.5px solid #e2e8f0 !important;
    background: white !important;
    color: #374151 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #2563eb !important;
    color: #2563eb !important;
    background: #eff6ff !important;
}

/* ── Formularios ───────────────────────────────────────────────────── */
[data-testid="stForm"] {
    background: white !important;
    padding: 1.5rem !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    border: 1px solid #e2e8f0 !important;
}

/* ── Inputs ────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    border-radius: 8px !important;
    border: 1.5px solid #d1d5db !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    outline: none !important;
}

/* ── Expanders ─────────────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: #f8fafc !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    border: 1px solid #e2e8f0 !important;
    padding: 10px 16px !important;
}

/* ── DataFrames ────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
    border: 1px solid #e2e8f0 !important;
}

/* ── Alertas ───────────────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* ── Divisores ─────────────────────────────────────────────────────── */
hr { border-color: #e2e8f0 !important; margin: 1rem 0 !important; }

/* ── Caja resultado Westgard ───────────────────────────────────────── */
.wg-box {
    padding: 14px 18px;
    border-radius: 10px;
    margin: 10px 0;
    border-left: 5px solid;
    font-size: 0.9rem;
}
.wg-ok   { background: #f0fdf4; border-left-color: #16a34a; color: #14532d; }
.wg-warn { background: #fffbeb; border-left-color: #d97706; color: #78350f; }
.wg-rej  { background: #fef2f2; border-left-color: #dc2626; color: #7f1d1d; }

/* ── Login page ────────────────────────────────────────────────────── */
.login-card {
    background: white;
    border-radius: 16px;
    padding: 40px 36px 32px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.1), 0 4px 20px rgba(0,0,0,0.06);
    text-align: center;
    border: 1px solid #e2e8f0;
}
.login-card .icon { font-size: 52px; margin-bottom: 14px; }
.login-card .title { font-size: 1.4rem; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
.login-card .subtitle { font-size: 0.85rem; color: #64748b; margin-bottom: 28px; padding-bottom: 24px; border-bottom: 1px solid #f1f5f9; }
.login-card .version { font-size: 0.72rem; color: #94a3b8; margin-top: 20px; }
</style>
"""

def inject_css():
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
