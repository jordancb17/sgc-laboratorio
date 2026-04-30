"""
Módulo de autenticación — pantalla de login profesional.
Credenciales en .streamlit/secrets.toml bajo [credentials].
"""

import streamlit as st
from modules.styles import inject_css


def _get_credentials() -> dict:
    try:
        return dict(st.secrets["credentials"])
    except Exception:
        return {"admin": "Lab2024"}


def require_auth() -> str:
    if st.session_state.get("_auth_ok"):
        return st.session_state.get("_auth_user", "admin")
    _show_login()
    st.stop()


def _show_login():
    inject_css()
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }

    /* Fondo con gradiente degradado oscuro */
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #0d2347 40%, #0f3460 70%, #1a1a4e 100%) !important;
    }
    .main .block-container {
        padding-top: 0 !important;
        max-width: 480px !important;
        margin: auto !important;
    }

    /* Partículas decorativas */
    .login-bg-decoration {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        pointer-events: none; z-index: 0;
        background:
            radial-gradient(ellipse at 20% 50%, rgba(14,165,233,0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 20%, rgba(56,189,248,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 60% 80%, rgba(99,102,241,0.05) 0%, transparent 50%);
    }

    /* Card de login */
    .login-outer {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 85vh;
        padding: 20px;
    }
    .login-card-pro {
        background: rgba(255,255,255,0.97);
        border-radius: 24px;
        padding: 52px 48px 44px;
        box-shadow:
            0 32px 80px rgba(0,0,0,0.4),
            0 0 0 1px rgba(255,255,255,0.08),
            inset 0 1px 0 rgba(255,255,255,0.5);
        text-align: center;
        width: 100%;
        backdrop-filter: blur(20px);
    }

    /* Logo circular */
    .login-logo {
        width: 84px; height: 84px;
        background: linear-gradient(135deg, #0a1628 0%, #0d2d6b 100%);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 22px;
        font-size: 38px;
        box-shadow: 0 8px 24px rgba(10,22,40,0.4), 0 0 0 4px rgba(14,165,233,0.2);
    }

    /* Badge versión */
    .login-badge {
        display: inline-block;
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        color: #1d4ed8;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 4px 14px;
        border-radius: 20px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 16px;
        border: 1px solid #bfdbfe;
    }

    .login-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0a1628;
        margin-bottom: 6px;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    .login-subtitle {
        font-size: 0.84rem;
        color: #64748b;
        margin-bottom: 0;
        font-weight: 400;
    }
    .login-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0 30%, #e2e8f0 70%, transparent);
        margin: 28px 0 26px;
    }

    /* Features strip */
    .login-features {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 28px;
        flex-wrap: wrap;
    }
    .login-feature {
        display: flex;
        align-items: center;
        gap: 5px;
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 500;
    }

    .login-footer {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 24px;
        padding-top: 18px;
        border-top: 1px solid #f1f5f9;
    }

    /* Ajustar inputs dentro de login */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #e2e8f0 !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        background: #f8fafc !important;
        transition: all 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 0 4px rgba(14,165,233,0.1) !important;
        background: white !important;
    }
    .stTextInput label {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #374151 !important;
        letter-spacing: 0.02em !important;
    }
    .stButton > button[kind="primary"] {
        border-radius: 12px !important;
        padding: 13px !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #0a1628 0%, #0d2d6b 60%, #1d4ed8 100%) !important;
        box-shadow: 0 4px 16px rgba(10,22,40,0.35) !important;
        letter-spacing: 0.02em !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 8px 24px rgba(10,22,40,0.45) !important;
        transform: translateY(-1px) !important;
    }
    </style>

    <div class="login-bg-decoration"></div>
    """, unsafe_allow_html=True)

    # Espaciado superior
    st.markdown("<br>", unsafe_allow_html=True)

    # Card completa
    st.markdown("""
    <div class="login-card-pro">
        <div class="login-logo">🔬</div>
        <div class="login-badge">⚕️ Sistema de Gestión de Calidad</div>
        <div class="login-title">SGC Laboratorio Clínico</div>
        <div class="login-subtitle">Ingrese sus credenciales para acceder al sistema</div>
        <div class="login-divider"></div>
        <div class="login-features">
            <div class="login-feature">🧪 Westgard Multi-Regla</div>
            <div class="login-feature">📊 EP15-A3 CLSI</div>
            <div class="login-feature">🌐 Control Externo</div>
            <div class="login-feature">☁️ Nube 24/7</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Formulario (fuera del HTML para que Streamlit lo procese)
    with st.form("_login_form", clear_on_submit=False):
        st.markdown("<br>", unsafe_allow_html=True)
        usuario   = st.text_input("👤  Usuario", placeholder="Ingrese su usuario")
        contrasena = st.text_input("🔒  Contraseña", type="password", placeholder="••••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        ingresar  = st.form_submit_button("🔑  Iniciar Sesión", use_container_width=True, type="primary")

    if ingresar:
        creds = _get_credentials()
        if usuario in creds and creds[usuario] == contrasena:
            st.session_state["_auth_ok"] = True
            st.session_state["_auth_user"] = usuario
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos. Intente nuevamente.")

    st.markdown("""
    <div style="text-align:center; color:rgba(255,255,255,0.35); font-size:0.7rem; margin-top:20px;">
        v2.0 &nbsp;·&nbsp; Westgard &nbsp;·&nbsp; EP15-A3 &nbsp;·&nbsp; PEEC &nbsp;·&nbsp; Acceso seguro
    </div>
    """, unsafe_allow_html=True)


def logout():
    for k in ["_auth_ok", "_auth_user"]:
        st.session_state.pop(k, None)
    st.rerun()


def get_current_user() -> str:
    return st.session_state.get("_auth_user", "")


def render_sidebar_user():
    user = get_current_user()
    with st.sidebar:
        st.markdown(f"""
        <div style="
            margin: 12px 8px 8px;
            padding: 12px 14px;
            background: linear-gradient(135deg, rgba(14,165,233,0.15), rgba(56,189,248,0.08));
            border-radius: 12px;
            border: 1px solid rgba(14,165,233,0.2);
            display: flex; align-items: center; gap: 12px;
        ">
            <div style="
                background: linear-gradient(135deg,#0ea5e9,#38bdf8);
                border-radius: 50%;
                width: 38px; height: 38px; flex-shrink: 0;
                display: flex; align-items: center; justify-content: center;
                font-size: 17px;
                box-shadow: 0 3px 8px rgba(14,165,233,0.3);
            ">👤</div>
            <div>
                <div style="color:white; font-weight:700; font-size:0.88rem; letter-spacing:0.01em;">{user}</div>
                <div style="color:#38bdf8; font-size:0.7rem; font-weight:500;">
                    <span style="display:inline-block; width:6px; height:6px; background:#10b981;
                    border-radius:50%; margin-right:4px; vertical-align:middle;"></span>
                    Sesión activa
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Cerrar sesión", use_container_width=True, key="_logout_btn"):
            logout()
