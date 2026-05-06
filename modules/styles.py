import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Streamlit expone estas variables CSS en :root y las cambia al cambiar tema:
#   --background-color          (fondo principal)
#   --secondary-background-color (superficies / cards)
#   --text-color                (texto principal)
#   --primary-color             (color de acento / brand)
#
# Toda la paleta del sistema se deriva de esas cuatro variables,
# por lo que el tema claro/oscuro funciona automáticamente.
# El único elemento "constante" es el sidebar (siempre azul marino oscuro)
# como decisión de diseño de identidad clínica.
# ──────────────────────────────────────────────────────────────────────────────

MAIN_CSS = """
<style>
/* ════════════════════════════════════════════════════════════════════════════
   VARIABLES — Todo derivado de los CSS vars de Streamlit (adaptables al tema)
════════════════════════════════════════════════════════════════════════════ */
:root {
    /* ── Colores base: Streamlit los redefine al cambiar tema ── */
    --bg:        var(--background-color,           #0f172a);
    --surface:   var(--secondary-background-color, #1e293b);
    --brand:     var(--primary-color,              #0ea5e9);
    --txt:       var(--text-color,                 #e2e8f0);

    /* ── Derivados: mezclas que funcionan en claro Y oscuro ── */
    --surface-2:     color-mix(in srgb, var(--secondary-background-color,#1e293b) 70%, var(--background-color,#0f172a) 30%);
    --txt-muted:     color-mix(in srgb, var(--text-color,#e2e8f0) 45%, transparent);
    --txt-secondary: color-mix(in srgb, var(--text-color,#e2e8f0) 70%, transparent);
    --brand-dim:     color-mix(in srgb, var(--primary-color,#0ea5e9) 80%, #000 20%);
    --brand-faint:   color-mix(in srgb, var(--primary-color,#0ea5e9) 10%, transparent);
    --border:        color-mix(in srgb, var(--text-color,#e2e8f0) 12%, transparent);
    --border-soft:   color-mix(in srgb, var(--text-color,#e2e8f0)  6%, transparent);

    /* ── Sombras: siempre oscuras (visibles en ambos temas) ── */
    --shadow-sm: 0 1px 4px rgba(0,0,0,0.18), 0 0 0 1px var(--border);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.22), 0 0 0 1px var(--border);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.28);

    --radius:    14px;
    --radius-sm: 10px;

    /* ── Sidebar: constante de identidad (siempre azul marino) ── */
    --navy:      #050c1a;
    --navy-mid:  #0d2347;
    --navy-light:#1e3a5f;
}

/* ════════════════════════════════════════════════════════════════════════════
   BASE
════════════════════════════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }

.stApp {
    background: var(--bg) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--txt) !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   SIDEBAR — Azul marino clínico (siempre oscuro, independiente del tema)
════════════════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,
        #050c1a  0%,
        #091628  30%,
        #0d2040  65%,
        #0a1a35 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    box-shadow: 4px 0 30px rgba(0,0,0,0.35) !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #7fafd4 !important;
    font-size: 0.82rem !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #e2eaf4 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
    border-radius: 10px !important;
    margin: 2px 10px !important;
    padding: 10px 14px !important;
    color: #7fafd4 !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    transition: all 0.18s ease !important;
    display: flex !important;
    align-items: center !important;
    gap: 9px !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #dbeafe !important;
    padding-left: 18px !important;
}
section[data-testid="stSidebar"] [aria-current="page"] {
    background: linear-gradient(135deg,
        rgba(14,165,233,0.22) 0%,
        rgba(56,189,248,0.12) 100%) !important;
    color: #93c5fd !important;
    border-left: 3px solid #38bdf8 !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(14,165,233,0.15) !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   LAYOUT
════════════════════════════════════════════════════════════════════════════ */
.main .block-container {
    padding: 1.5rem 2.5rem 3rem !important;
    max-width: 1600px !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   TIPOGRAFÍA — usa --txt para adaptarse al tema
════════════════════════════════════════════════════════════════════════════ */
h1 {
    color: var(--txt) !important;
    font-weight: 800 !important;
    font-size: 1.7rem !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 0.2rem !important;
    line-height: 1.2 !important;
}
h2 {
    color: var(--txt) !important;
    font-weight: 700 !important;
    font-size: 1.12rem !important;
    margin-top: 0.5rem !important;
    letter-spacing: -0.01em !important;
}
h3 {
    color: var(--txt-secondary) !important;
    font-weight: 600 !important;
    font-size: 0.97rem !important;
}
p   { color: var(--txt-secondary) !important; font-size: 0.9rem !important; }

/* ════════════════════════════════════════════════════════════════════════════
   MÉTRICAS
════════════════════════════════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: var(--surface) !important;
    border-radius: var(--radius) !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: var(--shadow-sm) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    border: 1px solid var(--border) !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-2px) !important;
}
[data-testid="metric-container"]::before {
    content: '' !important;
    position: absolute !important;
    top: 0; left: 0; right: 0 !important;
    height: 3px !important;
    background: linear-gradient(90deg, var(--brand), color-mix(in srgb,var(--brand) 60%,#6366f1)) !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    color: var(--txt) !important;
    letter-spacing: -0.03em !important;
    line-height: 1.15 !important;
}
[data-testid="stMetricLabel"] {
    color: var(--txt-muted) !important;
    font-weight: 600 !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; font-weight: 600 !important; }

/* ════════════════════════════════════════════════════════════════════════════
   TABS — adaptables al tema
════════════════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 3px !important;
    background: var(--surface) !important;
    padding: 5px !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-sm) !important;
    margin-bottom: 1.5rem !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 18px !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    color: var(--txt-secondary) !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.18s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--brand) !important;
    background: var(--brand-faint) !important;
}
/* Tab activo: usa brand — visible en claro Y oscuro */
.stTabs [aria-selected="true"] {
    background: var(--brand) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 3px 10px color-mix(in srgb,var(--brand) 35%,transparent) !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   BOTONES — brand-based: funcionan en claro Y oscuro
════════════════════════════════════════════════════════════════════════════ */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--brand-dim) 0%, var(--brand) 100%) !important;
    border: none !important;
    color: #ffffff !important;
    box-shadow: 0 3px 10px color-mix(in srgb,var(--brand) 35%,transparent) !important;
    padding: 0.55rem 1.4rem !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.12) !important;
    box-shadow: 0 6px 18px color-mix(in srgb,var(--brand) 45%,transparent) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    border: 1.5px solid var(--border) !important;
    background: var(--surface) !important;
    color: var(--txt-secondary) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--brand) !important;
    color: var(--brand) !important;
    background: var(--brand-faint) !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   INPUTS Y FORMULARIOS — adaptan fondo y texto al tema
════════════════════════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
    background: var(--surface) !important;
    padding: 1.6rem 1.75rem !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
    border: 1px solid var(--border) !important;
}
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid var(--border) !important;
    font-size: 0.88rem !important;
    background: var(--surface-2) !important;
    color: var(--txt) !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb,var(--brand) 14%,transparent) !important;
    background: var(--surface) !important;
}
.stSelectbox > div > div {
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid var(--border) !important;
    background: var(--surface-2) !important;
    color: var(--txt) !important;
}
label {
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    color: var(--txt-secondary) !important;
    letter-spacing: 0.02em !important;
    text-transform: uppercase !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   DATAFRAMES
════════════════════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-sm) !important;
    border: 1px solid var(--border) !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   EXPANDERS
════════════════════════════════════════════════════════════════════════════ */
.streamlit-expanderHeader {
    background: var(--surface) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    color: var(--txt-secondary) !important;
    border: 1px solid var(--border) !important;
    padding: 12px 16px !important;
    transition: all 0.18s !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--brand) !important;
    color: var(--brand) !important;
    background: var(--brand-faint) !important;
}
.streamlit-expanderContent {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
    padding: 1rem !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   ALERTAS
════════════════════════════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    border-width: 1px !important;
    border-style: solid !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   DIVISORES
════════════════════════════════════════════════════════════════════════════ */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg,
        transparent,
        var(--border) 20%,
        var(--border) 80%,
        transparent) !important;
    margin: 1.25rem 0 !important;
}

/* ════════════════════════════════════════════════════════════════════════════
   WESTGARD — Cajas de resultado (semi-transparentes → visibles en ambos temas)
════════════════════════════════════════════════════════════════════════════ */
.wg-box {
    padding: 16px 20px;
    border-radius: var(--radius-sm);
    margin: 12px 0;
    border-left: 5px solid;
    font-size: 0.88rem;
    font-weight: 500;
    box-shadow: var(--shadow-sm);
    background: var(--surface);
}
.wg-ok   { background: rgba(22,163,74,0.11);  border-left-color: #16a34a;
           color: color-mix(in srgb,#16a34a 80%,var(--txt)); }
.wg-warn { background: rgba(217,119,6,0.11);  border-left-color: #d97706;
           color: color-mix(in srgb,#d97706 80%,var(--txt)); }
.wg-rej  { background: rgba(220,38,38,0.11);  border-left-color: #dc2626;
           color: color-mix(in srgb,#dc2626 80%,var(--txt)); }

/* ════════════════════════════════════════════════════════════════════════════
   KPI CARDS
════════════════════════════════════════════════════════════════════════════ */
.kpi-card {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 1.4rem 1.25rem;
    box-shadow: var(--shadow-sm);
    text-align: center;
    transition: transform 0.22s, box-shadow 0.22s;
    border: 1px solid var(--border);
    border-top-width: 4px;
    height: 100%;
    position: relative;
    overflow: hidden;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.kpi-card .kpi-icon  { font-size: 2rem; margin-bottom: 10px; display: block; }
.kpi-card .kpi-value { font-size: 2.2rem; font-weight: 800; line-height: 1;
                        margin-bottom: 6px; letter-spacing: -0.03em;
                        color: var(--txt); }
.kpi-card .kpi-label { font-size: 0.68rem; font-weight: 700;
                        text-transform: uppercase; letter-spacing: 0.1em;
                        color: var(--txt-muted); }
.kpi-card .kpi-sub   { font-size: 0.75rem; margin-top: 8px; color: var(--txt-muted); }
.kpi-blue  { border-top-color: #0ea5e9; }
.kpi-green { border-top-color: #10b981; }
.kpi-amber { border-top-color: #f59e0b; }
.kpi-red   { border-top-color: #ef4444; }
.kpi-purple{ border-top-color: #8b5cf6; }
.kpi-teal  { border-top-color: #14b8a6; }
.kpi-indigo{ border-top-color: #6366f1; }
.kpi-navy  { border-top-color: #1d4ed8; }

/* KPI sólidas */
.kpi-solid { border: none !important; border-top: none !important; }
.kpi-solid .kpi-value,
.kpi-solid .kpi-label,
.kpi-solid .kpi-sub { color: rgba(255,255,255,0.9) !important; }
.kpi-s-blue   { background: linear-gradient(135deg,#1d4ed8,#2563eb) !important; }
.kpi-s-green  { background: linear-gradient(135deg,#15803d,#16a34a) !important; }
.kpi-s-amber  { background: linear-gradient(135deg,#b45309,#d97706) !important; }
.kpi-s-red    { background: linear-gradient(135deg,#b91c1c,#dc2626) !important; }
.kpi-s-purple { background: linear-gradient(135deg,#7e22ce,#9333ea) !important; }
.kpi-s-teal   { background: linear-gradient(135deg,#0f766e,#0d9488) !important; }
.kpi-s-indigo { background: linear-gradient(135deg,#166534,#15803d) !important; }
.kpi-s-navy   { background: linear-gradient(135deg,#1e3a8a,#1d4ed8) !important; }

/* ════════════════════════════════════════════════════════════════════════════
   SECTION HEADER — usa superficie + borde brand (claro Y oscuro)
════════════════════════════════════════════════════════════════════════════ */
.section-header {
    background: var(--surface);
    border-left: 4px solid var(--brand);
    color: var(--txt);
    padding: 1.1rem 1.6rem;
    border-radius: 0 var(--radius) var(--radius) 0;
    margin-bottom: 1.4rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
    border-left: 4px solid var(--brand);
}
.section-header h2 { color: var(--txt) !important; margin: 0 !important; font-size: 1.08rem !important; }
.section-header p  { color: var(--txt-muted) !important; margin: 5px 0 0 !important; font-size: 0.8rem !important; }

/* ════════════════════════════════════════════════════════════════════════════
   PAGE HEADER
════════════════════════════════════════════════════════════════════════════ */
.page-header {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 1.75rem;
    padding-bottom: 1.25rem;
    border-bottom: 2px solid var(--border);
}
.page-header .ph-icon {
    font-size: 2.4rem;
    line-height: 1;
    flex-shrink: 0;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.15));
}
.page-header .ph-title {
    font-size: 1.55rem;
    font-weight: 800;
    color: var(--txt);
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0 0 4px;
}
.page-header .ph-sub {
    font-size: 0.82rem;
    color: var(--txt-muted);
    margin: 0;
    font-weight: 400;
}
.page-header .ph-badge {
    display: inline-block;
    background: var(--brand-faint);
    color: var(--brand);
    border: 1px solid color-mix(in srgb,var(--brand) 30%,transparent);
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 6px;
}

/* ════════════════════════════════════════════════════════════════════════════
   SECTION CARD
════════════════════════════════════════════════════════════════════════════ */
.section-card {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}
.section-card-title {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--txt-muted);
    margin: 0 0 1rem;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid var(--border);
}

/* ════════════════════════════════════════════════════════════════════════════
   DIVISOR CON ETIQUETA
════════════════════════════════════════════════════════════════════════════ */
.divider {
    height: 1px;
    background: linear-gradient(90deg,transparent,var(--border) 20%,var(--border) 80%,transparent);
    margin: 1.5rem 0;
}
.divider-label {
    display: flex; align-items: center; gap: 12px; margin: 1.5rem 0;
    color: var(--txt-muted); font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
}
.divider-label::before, .divider-label::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
}

/* ════════════════════════════════════════════════════════════════════════════
   BADGES DE ESTADO (semi-transparentes — visibles en claro Y oscuro)
════════════════════════════════════════════════════════════════════════════ */
.badge-ok   { display:inline-block; background:rgba(16,185,129,0.14);
              color:color-mix(in srgb,#059669 80%,var(--txt));
              border:1px solid rgba(16,185,129,0.35);
              border-radius:6px; padding:2px 10px; font-size:0.72rem; font-weight:700; }
.badge-warn { display:inline-block; background:rgba(245,158,11,0.14);
              color:color-mix(in srgb,#d97706 80%,var(--txt));
              border:1px solid rgba(245,158,11,0.35);
              border-radius:6px; padding:2px 10px; font-size:0.72rem; font-weight:700; }
.badge-rej  { display:inline-block; background:rgba(239,68,68,0.14);
              color:color-mix(in srgb,#dc2626 80%,var(--txt));
              border:1px solid rgba(239,68,68,0.35);
              border-radius:6px; padding:2px 10px; font-size:0.72rem; font-weight:700; }

/* ════════════════════════════════════════════════════════════════════════════
   TABLA DE ESTADÍSTICOS (EP15, Sigma)
════════════════════════════════════════════════════════════════════════════ */
.stat-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}
.stat-table th {
    background: var(--brand);
    color: #ffffff;
    padding: 10px 14px;
    text-align: left;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
.stat-table td {
    padding: 9px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--txt);
}
.stat-table tr:last-child td { border-bottom: none; }
.stat-table tr:nth-child(even) td { background: var(--surface-2); }

/* ════════════════════════════════════════════════════════════════════════════
   LOGIN — fondo de marca, siempre oscuro
════════════════════════════════════════════════════════════════════════════ */
.login-wrapper {
    min-height: 100vh;
    background: linear-gradient(135deg, #050c1a 0%, #0d2347 50%, #0f3460 100%);
    display: flex; align-items: center; justify-content: center;
}
</style>
"""


def inject_css():
    st.html(MAIN_CSS)
