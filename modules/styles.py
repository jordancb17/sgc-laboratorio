import streamlit as st

MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ══════════════════════════════════════════════════════════════
   BASE
══════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #f0f4f8 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ══════════════════════════════════════════════════════════════
   SIDEBAR — Azul marino clínico
══════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #0d2347 50%, #0f3460 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.25) !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label { color: #94a3b8 !important; font-size: 0.82rem !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }

/* Nav links */
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
    border-radius: 10px !important;
    margin: 2px 8px !important;
    padding: 9px 14px !important;
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #e2e8f0 !important;
    transform: translateX(3px) !important;
}
section[data-testid="stSidebar"] [aria-current="page"] {
    background: linear-gradient(135deg, rgba(14,165,233,0.25), rgba(56,189,248,0.15)) !important;
    color: #38bdf8 !important;
    border-left: 3px solid #38bdf8 !important;
    font-weight: 600 !important;
}

/* ══════════════════════════════════════════════════════════════
   LAYOUT PRINCIPAL
══════════════════════════════════════════════════════════════ */
.main .block-container {
    padding: 1.75rem 2.25rem 3rem !important;
    max-width: 1500px !important;
}

/* ══════════════════════════════════════════════════════════════
   TIPOGRAFÍA
══════════════════════════════════════════════════════════════ */
h1 {
    color: #0a1628 !important;
    font-weight: 800 !important;
    font-size: 1.75rem !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0.25rem !important;
    line-height: 1.2 !important;
}
h2 { color: #1e293b !important; font-weight: 700 !important; font-size: 1.15rem !important; margin-top: 0.75rem !important; }
h3 { color: #334155 !important; font-weight: 600 !important; font-size: 1rem !important; }
p  { color: #475569 !important; font-size: 0.9rem !important; }

/* ══════════════════════════════════════════════════════════════
   MÉTRICAS — Tarjetas con colores según categoría
══════════════════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: white !important;
    border-radius: 16px !important;
    padding: 1.25rem 1.5rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04) !important;
    transition: all 0.25s ease !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.10), 0 0 0 1px rgba(0,0,0,0.04) !important;
    transform: translateY(-2px) !important;
}
[data-testid="metric-container"]::before {
    content: '' !important;
    position: absolute !important;
    top: 0; left: 0; right: 0 !important;
    height: 4px !important;
    background: linear-gradient(90deg, #0ea5e9, #38bdf8) !important;
    border-radius: 16px 16px 0 0 !important;
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #0a1628 !important;
    letter-spacing: -0.03em !important;
    line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-weight: 600 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 4px !important;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; font-weight: 600 !important; }

/* ══════════════════════════════════════════════════════════════
   TABS — Estilo pill moderno
══════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: white !important;
    padding: 5px 6px !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04) !important;
    margin-bottom: 1.5rem !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: #64748b !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #0ea5e9 !important; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0a1628, #0d2d6b) !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0 3px 10px rgba(10,22,40,0.3) !important;
}

/* ══════════════════════════════════════════════════════════════
   BOTONES
══════════════════════════════════════════════════════════════ */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0a1628 0%, #0d2d6b 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 3px 10px rgba(10,22,40,0.3) !important;
    padding: 0.55rem 1.5rem !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0d2347 0%, #1e40af 100%) !important;
    box-shadow: 0 6px 18px rgba(10,22,40,0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    border: 1.5px solid #e2e8f0 !important;
    background: white !important;
    color: #374151 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #0ea5e9 !important;
    color: #0ea5e9 !important;
    background: #f0f9ff !important;
}

/* ══════════════════════════════════════════════════════════════
   FORMULARIOS Y INPUTS
══════════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
    background: white !important;
    padding: 1.75rem !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04) !important;
}
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
    font-size: 0.9rem !important;
    background: #fafbfc !important;
    transition: all 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #0ea5e9 !important;
    box-shadow: 0 0 0 3px rgba(14,165,233,0.12) !important;
    background: white !important;
}

/* ══════════════════════════════════════════════════════════════
   DATAFRAMES / TABLAS
══════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04) !important;
}

/* ══════════════════════════════════════════════════════════════
   EXPANDERS
══════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader {
    background: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #374151 !important;
    border: 1px solid #e2e8f0 !important;
    padding: 12px 16px !important;
    transition: all 0.2s !important;
}
.streamlit-expanderHeader:hover { border-color: #0ea5e9 !important; color: #0ea5e9 !important; }

/* ══════════════════════════════════════════════════════════════
   ALERTAS
══════════════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
}

/* ══════════════════════════════════════════════════════════════
   DIVISORES
══════════════════════════════════════════════════════════════ */
hr { border-color: #e2e8f0 !important; margin: 1.25rem 0 !important; opacity: 0.7 !important; }

/* ══════════════════════════════════════════════════════════════
   CAJAS WESTGARD — resultado en tiempo real
══════════════════════════════════════════════════════════════ */
.wg-box {
    padding: 14px 20px;
    border-radius: 12px;
    margin: 12px 0;
    border-left: 5px solid;
    font-size: 0.88rem;
    font-weight: 500;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}
.wg-ok   { background: linear-gradient(135deg,#f0fdf4,#dcfce7); border-left-color:#16a34a; color:#14532d; }
.wg-warn { background: linear-gradient(135deg,#fffbeb,#fef3c7); border-left-color:#d97706; color:#78350f; }
.wg-rej  { background: linear-gradient(135deg,#fef2f2,#fee2e2); border-left-color:#dc2626; color:#7f1d1d; }

/* ══════════════════════════════════════════════════════════════
   TARJETAS HTML PERSONALIZADAS
══════════════════════════════════════════════════════════════ */
.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    text-align: center;
    transition: all 0.25s;
    border-top: 4px solid;
    height: 100%;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
.kpi-card .kpi-icon { font-size: 2.2rem; margin-bottom: 8px; }
.kpi-card .kpi-value { font-size: 2.4rem; font-weight: 800; line-height: 1; margin-bottom: 4px; letter-spacing: -0.03em; }
.kpi-card .kpi-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.7; }
.kpi-card .kpi-sub { font-size: 0.78rem; margin-top: 6px; opacity: 0.6; }

.kpi-blue  { border-top-color: #0ea5e9; color: #0c4a6e; }
.kpi-green { border-top-color: #10b981; color: #064e3b; }
.kpi-amber { border-top-color: #f59e0b; color: #78350f; }
.kpi-red   { border-top-color: #ef4444; color: #7f1d1d; }

/* Sección header con gradiente */
.section-header {
    background: linear-gradient(135deg, #0a1628 0%, #0d2d6b 100%);
    color: white;
    padding: 1.25rem 1.75rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 16px rgba(10,22,40,0.25);
}
.section-header h2 { color: white !important; margin: 0 !important; font-size: 1.1rem !important; }
.section-header p  { color: rgba(255,255,255,0.7) !important; margin: 4px 0 0 !important; font-size: 0.82rem !important; }

/* Separador elegante */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #e2e8f0 20%, #e2e8f0 80%, transparent);
    margin: 1.5rem 0;
}

/* ══════════════════════════════════════════════════════════════
   LOGIN PAGE
══════════════════════════════════════════════════════════════ */
.login-wrapper {
    min-height: 100vh;
    background: linear-gradient(135deg, #0a1628 0%, #0d2347 50%, #0f3460 100%);
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: white;
    border-radius: 24px;
    padding: 48px 44px 40px;
    box-shadow: 0 32px 80px rgba(0,0,0,0.35), 0 4px 24px rgba(0,0,0,0.15);
    text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
    max-width: 420px;
    width: 100%;
}
.login-card .icon { font-size: 56px; margin-bottom: 16px; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.15)); }
.login-card .title { font-size: 1.5rem; font-weight: 800; color: #0a1628; margin-bottom: 4px; letter-spacing: -0.02em; }
.login-card .subtitle { font-size: 0.83rem; color: #64748b; margin-bottom: 32px; padding-bottom: 28px; border-bottom: 1px solid #f1f5f9; }
.login-card .badge {
    display: inline-block;
    background: linear-gradient(135deg,#eff6ff,#dbeafe);
    color: #1d4ed8;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 20px;
    border: 1px solid #bfdbfe;
}
.login-card .version { font-size: 0.72rem; color: #94a3b8; margin-top: 20px; }
</style>
"""

def inject_css():
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
