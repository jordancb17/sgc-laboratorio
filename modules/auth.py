"""
Módulo de autenticación — login profesional con glassmorphism.
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

    /* Fondo con textura y gradiente rico */
    .stApp {
        background:
            radial-gradient(ellipse at 15% 40%, rgba(14,165,233,0.12) 0%, transparent 55%),
            radial-gradient(ellipse at 85% 15%, rgba(99,102,241,0.10) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 85%, rgba(16,185,129,0.06) 0%, transparent 45%),
            linear-gradient(135deg, #050d1a 0%, #0a1628 35%, #0d2347 65%, #0f172a 100%) !important;
        min-height: 100vh !important;
    }

    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Inputs elegantes oscuros */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 1.5px solid rgba(255,255,255,0.12) !important;
        padding: 14px 18px !important;
        font-size: 0.95rem !important;
        background: rgba(255,255,255,0.06) !important;
        color: white !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.2) !important;
        transition: all 0.2s !important;
        height: 50px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(14,165,233,0.7) !important;
        background: rgba(255,255,255,0.10) !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.15), inset 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.35) !important;
        font-size: 0.92rem !important;
    }
    .stTextInput label { display: none !important; }

    /* Botón principal premium */
    .stButton > button[kind="primary"] {
        width: 100% !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 50%, #4f46e5 100%) !important;
        border: none !important;
        color: white !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        height: 50px !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 20px rgba(14,165,233,0.4), 0 1px 3px rgba(0,0,0,0.3) !important;
        transition: all 0.25s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #6366f1 100%) !important;
        box-shadow: 0 8px 28px rgba(14,165,233,0.5), 0 2px 6px rgba(0,0,0,0.3) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 10px rgba(14,165,233,0.3) !important;
    }

    /* Form sin estilos propios */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* Error */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        font-size: 0.85rem !important;
        background: rgba(239,68,68,0.15) !important;
        border: 1px solid rgba(239,68,68,0.3) !important;
        color: #fca5a5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout centrado
    _, col, _ = st.columns([1, 1.1, 1])

    with col:
        st.markdown("<div style='height:52px'></div>", unsafe_allow_html=True)

        # Logo y branding arriba
        st.markdown("""
        <div style="text-align:center; margin-bottom:32px;">
            <div style="
                width:80px; height:80px;
                background: linear-gradient(145deg,#0ea5e9,#4f46e5);
                border-radius:22px;
                display:flex; align-items:center; justify-content:center;
                margin:0 auto 20px;
                font-size:38px;
                box-shadow:
                    0 8px 32px rgba(14,165,233,0.45),
                    0 0 0 1px rgba(255,255,255,0.08),
                    inset 0 1px 0 rgba(255,255,255,0.2);
                transform: rotate(-4deg);
            ">🔬</div>

            <div style="
                font-size:1.55rem; font-weight:800; color:white;
                letter-spacing:-0.025em; line-height:1.15;
                text-shadow: 0 2px 12px rgba(0,0,0,0.3);
            ">SGC Laboratorio Clínico</div>

            <div style="
                font-size:0.82rem; color:rgba(255,255,255,0.5);
                margin-top:8px; font-weight:400; letter-spacing:0.03em;
            ">SISTEMA DE GESTIÓN DE CALIDAD</div>
        </div>
        """, unsafe_allow_html=True)

        # Card con glassmorphism
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 20px;
            padding: 36px 32px 28px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow:
                0 24px 64px rgba(0,0,0,0.4),
                0 1px 0 rgba(255,255,255,0.08) inset;
        ">
            <div style="
                font-size:1.05rem; font-weight:600; color:rgba(255,255,255,0.9);
                margin-bottom:24px; text-align:center; letter-spacing:0.01em;
            ">Bienvenido — ingrese sus credenciales</div>
        """, unsafe_allow_html=True)

        with st.form("_login_form", clear_on_submit=False):
            st.text_input("u", placeholder="👤  Usuario", key="_u",
                          label_visibility="collapsed")
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.text_input("p", placeholder="🔒  Contraseña", type="password", key="_p",
                          label_visibility="collapsed")
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            ingresar = st.form_submit_button(
                "INICIAR SESIÓN", use_container_width=True, type="primary")

        st.markdown("</div>", unsafe_allow_html=True)

        # Divisor
        st.markdown("""
        <div style="
            display:flex; align-items:center; gap:14px;
            margin:26px 0 20px;
        ">
            <div style="flex:1; height:1px; background:rgba(255,255,255,0.08);"></div>
            <div style="font-size:0.7rem; color:rgba(255,255,255,0.25); white-space:nowrap;
                        font-weight:500; letter-spacing:0.08em;">
                MÓDULOS DISPONIBLES
            </div>
            <div style="flex:1; height:1px; background:rgba(255,255,255,0.08);"></div>
        </div>

        <!-- Chips de módulos -->
        <div style="display:flex; justify-content:center; gap:8px; flex-wrap:wrap;">
            <div style="
                background:rgba(14,165,233,0.12); border:1px solid rgba(14,165,233,0.25);
                border-radius:8px; padding:7px 13px; text-align:center;
            ">
                <div style="font-size:1rem;">🧪</div>
                <div style="font-size:0.62rem; color:rgba(255,255,255,0.55);
                            font-weight:600; letter-spacing:0.05em; margin-top:2px;">
                    WESTGARD
                </div>
            </div>
            <div style="
                background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
                border-radius:8px; padding:7px 13px; text-align:center;
            ">
                <div style="font-size:1rem;">📊</div>
                <div style="font-size:0.62rem; color:rgba(255,255,255,0.55);
                            font-weight:600; letter-spacing:0.05em; margin-top:2px;">
                    EP15-A3
                </div>
            </div>
            <div style="
                background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.25);
                border-radius:8px; padding:7px 13px; text-align:center;
            ">
                <div style="font-size:1rem;">🌐</div>
                <div style="font-size:0.62rem; color:rgba(255,255,255,0.55);
                            font-weight:600; letter-spacing:0.05em; margin-top:2px;">
                    PEEC
                </div>
            </div>
            <div style="
                background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.25);
                border-radius:8px; padding:7px 13px; text-align:center;
            ">
                <div style="font-size:1rem;">🔧</div>
                <div style="font-size:0.62rem; color:rgba(255,255,255,0.55);
                            font-weight:600; letter-spacing:0.05em; margin-top:2px;">
                    ACCIONES
                </div>
            </div>
            <div style="
                background:rgba(239,68,68,0.10); border:1px solid rgba(239,68,68,0.22);
                border-radius:8px; padding:7px 13px; text-align:center;
            ">
                <div style="font-size:1rem;">☁️</div>
                <div style="font-size:0.62rem; color:rgba(255,255,255,0.55);
                            font-weight:600; letter-spacing:0.05em; margin-top:2px;">
                    NUBE 24/7
                </div>
            </div>
        </div>

        <div style="
            text-align:center; color:rgba(255,255,255,0.18);
            font-size:0.68rem; margin-top:28px; letter-spacing:0.05em;
        ">
            v2.0 &nbsp;·&nbsp; ACCESO SEGURO &nbsp;·&nbsp; DATOS PROTEGIDOS
        </div>
        """, unsafe_allow_html=True)

    if ingresar:
        usuario    = st.session_state.get("_u", "")
        contrasena = st.session_state.get("_p", "")
        creds = _get_credentials()
        if usuario in creds and creds[usuario] == contrasena:
            st.session_state["_auth_ok"]   = True
            st.session_state["_auth_user"] = usuario
            st.rerun()
        else:
            with col:
                st.error("Usuario o contraseña incorrectos.")


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
            margin:12px 8px 8px;
            padding:12px 14px;
            background:linear-gradient(135deg,rgba(14,165,233,0.15),rgba(56,189,248,0.08));
            border-radius:12px;
            border:1px solid rgba(14,165,233,0.2);
            display:flex; align-items:center; gap:12px;
        ">
            <div style="
                background:linear-gradient(135deg,#0ea5e9,#4f46e5);
                border-radius:50%; width:38px; height:38px; flex-shrink:0;
                display:flex; align-items:center; justify-content:center;
                font-size:17px; box-shadow:0 3px 8px rgba(14,165,233,0.3);
            ">👤</div>
            <div>
                <div style="color:white;font-weight:700;font-size:0.88rem;">{user}</div>
                <div style="color:#38bdf8;font-size:0.7rem;font-weight:500;">
                    <span style="display:inline-block;width:6px;height:6px;
                    background:#10b981;border-radius:50%;margin-right:4px;
                    vertical-align:middle;"></span>Sesión activa
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="_logout_btn"):
            logout()
