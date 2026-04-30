"""
Módulo de autenticación simple basado en st.secrets.
Las credenciales se definen en .streamlit/secrets.toml:

  [credentials]
  admin    = "MiContraseña"
  laboratorio = "OtraContraseña"
"""

import streamlit as st
from modules.styles import inject_css


def _get_credentials() -> dict:
    try:
        return dict(st.secrets["credentials"])
    except Exception:
        return {"admin": "Lab2024"}


def require_auth() -> str:
    """Verifica autenticación. Si no está logueado, muestra login y detiene la página."""
    if st.session_state.get("_auth_ok"):
        return st.session_state.get("_auth_user", "admin")
    _show_login()
    st.stop()


def _show_login():
    inject_css()
    # Ocultar sidebar en la pantalla de login
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] { display: none !important; }
    .main .block-container { padding-top: 0 !important; max-width: 500px; margin: auto; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="login-card">
        <div class="icon">🔬</div>
        <div class="title">SGC Laboratorio Clínico</div>
        <div class="subtitle">Sistema de Gestión de Calidad</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("_login_form"):
        usuario = st.text_input("Usuario", placeholder="usuario")
        contrasena = st.text_input("Contraseña", type="password", placeholder="••••••••")
        ingresar = st.form_submit_button("Iniciar Sesión", use_container_width=True, type="primary")

    if ingresar:
        creds = _get_credentials()
        if usuario in creds and creds[usuario] == contrasena:
            st.session_state["_auth_ok"] = True
            st.session_state["_auth_user"] = usuario
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    st.markdown(
        '<p style="text-align:center; color:#94a3b8; font-size:0.72rem; margin-top:16px;">'
        "v1.0.0 &nbsp;·&nbsp; Westgard &nbsp;·&nbsp; EP15-A3 &nbsp;·&nbsp; Control Externo</p>",
        unsafe_allow_html=True,
    )


def logout():
    for k in ["_auth_ok", "_auth_user"]:
        st.session_state.pop(k, None)
    st.rerun()


def get_current_user() -> str:
    return st.session_state.get("_auth_user", "admin")


def render_sidebar_user():
    user = get_current_user()
    with st.sidebar:
        st.markdown(f"""
        <div style="
            margin: 8px 0 6px;
            padding: 10px 14px;
            background: rgba(255,255,255,0.08);
            border-radius: 10px;
            display: flex; align-items: center; gap: 10px;
        ">
            <div style="
                background: rgba(255,255,255,0.2); border-radius: 50%;
                width: 34px; height: 34px; flex-shrink: 0;
                display: flex; align-items: center; justify-content: center;
                font-size: 16px;
            ">👤</div>
            <div>
                <div style="color:white; font-weight:600; font-size:0.85rem;">{user}</div>
                <div style="color:#93c5fd; font-size:0.71rem;">● Conectado</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Cerrar sesión", use_container_width=True, key="_logout_btn"):
            logout()
