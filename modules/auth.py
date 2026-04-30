"""
Módulo de autenticación — pantalla de login estilo moderno/clean.
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

    /* Fondo gris muy suave — estilo Facebook */
    .stApp { background: #f0f2f5 !important; }

    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        border-radius: 6px !important;
        border: 1px solid #dddfe2 !important;
        padding: 14px 16px !important;
        font-size: 1rem !important;
        background: white !important;
        color: #1c1e21 !important;
        box-shadow: none !important;
        transition: border-color 0.15s, box-shadow 0.15s !important;
        height: 52px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1877f2 !important;
        box-shadow: 0 0 0 2px rgba(24,119,242,0.2) !important;
    }
    .stTextInput > div > div > input::placeholder { color: #90949c !important; font-size: 1rem !important; }
    .stTextInput label { display: none !important; }

    /* Botón principal */
    .stButton > button[kind="primary"] {
        width: 100% !important;
        border-radius: 8px !important;
        background: linear-gradient(180deg, #1a77f2 0%, #1565c0 100%) !important;
        border: none !important;
        color: white !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        height: 52px !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 2px 6px rgba(24,119,242,0.4) !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #166fe5 0%, #1255aa 100%) !important;
        box-shadow: 0 4px 12px rgba(24,119,242,0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* Ocultar label del form */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* Mensajes de error */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
        font-size: 0.88rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Layout: columna centrada
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

        # Logo + nombre del sistema
        st.markdown("""
        <div style="text-align:center; margin-bottom:28px;">
            <div style="
                width: 76px; height: 76px;
                background: linear-gradient(145deg, #0a1628, #1d4ed8);
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                margin: 0 auto 18px;
                box-shadow: 0 4px 18px rgba(24,119,242,0.35);
                font-size: 36px;
            ">🔬</div>
            <div style="font-size:1.65rem; font-weight:800; color:#0a1628;
                        letter-spacing:-0.03em; line-height:1.1;">
                SGC Laboratorio
            </div>
            <div style="font-size:0.95rem; color:#65676b; margin-top:6px; font-weight:400;">
                Sistema de Gestión de Calidad
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card blanca
        st.markdown("""
        <div style="
            background: white;
            border-radius: 10px;
            padding: 28px 28px 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1), 0 0 0 1px rgba(0,0,0,0.04);
        ">
        """, unsafe_allow_html=True)

        with st.form("_login_form", clear_on_submit=False):
            st.text_input("u", placeholder="Usuario", key="_u", label_visibility="collapsed")
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.text_input("p", placeholder="Contraseña", type="password", key="_p", label_visibility="collapsed")
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            ingresar = st.form_submit_button("Iniciar sesión", use_container_width=True, type="primary")

        st.markdown("</div>", unsafe_allow_html=True)

        # Chips de funcionalidades
        st.markdown("""
        <div style="
            display:flex; justify-content:center; gap:10px;
            flex-wrap:wrap; margin-top:22px; margin-bottom:4px;
        ">
            <span style="background:white; border:1px solid #dddfe2; border-radius:20px;
                         padding:5px 13px; font-size:0.72rem; color:#65676b; font-weight:500;
                         box-shadow:0 1px 3px rgba(0,0,0,0.06);">🧪 Westgard</span>
            <span style="background:white; border:1px solid #dddfe2; border-radius:20px;
                         padding:5px 13px; font-size:0.72rem; color:#65676b; font-weight:500;
                         box-shadow:0 1px 3px rgba(0,0,0,0.06);">📊 EP15-A3</span>
            <span style="background:white; border:1px solid #dddfe2; border-radius:20px;
                         padding:5px 13px; font-size:0.72rem; color:#65676b; font-weight:500;
                         box-shadow:0 1px 3px rgba(0,0,0,0.06);">🌐 PEEC</span>
            <span style="background:white; border:1px solid #dddfe2; border-radius:20px;
                         padding:5px 13px; font-size:0.72rem; color:#65676b; font-weight:500;
                         box-shadow:0 1px 3px rgba(0,0,0,0.06);">☁️ Nube 24/7</span>
        </div>
        <div style="text-align:center; color:#bcc0c4; font-size:0.68rem; margin-top:20px;">
            v2.0 · Acceso seguro · Datos protegidos
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
            st.error("El usuario o la contraseña que ingresaste es incorrecta.")


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
                <div style="color:white; font-weight:700; font-size:0.88rem;">{user}</div>
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
