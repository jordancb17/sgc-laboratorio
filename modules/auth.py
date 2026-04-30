"""
Módulo de autenticación — pantalla de login profesional para SGC Laboratorio.
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
    # ── CSS exclusivo de la pantalla de login ────────────────────────────────
    st.markdown("""
    <style>
    /* Ocultar sidebar */
    section[data-testid="stSidebar"] { display: none !important; }

    /* Fondo oscuro con gradiente */
    .stApp {
        background:
            radial-gradient(ellipse at 20% 50%, rgba(14,165,233,0.10) 0%, transparent 55%),
            radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.10) 0%, transparent 50%),
            linear-gradient(135deg, #050c1a 0%, #091628 35%, #0d2040 65%, #0f172a 100%) !important;
        min-height: 100vh !important;
    }

    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* Inputs del formulario de login */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid rgba(255,255,255,0.12) !important;
        padding: 14px 18px !important;
        font-size: 0.95rem !important;
        background: rgba(255,255,255,0.06) !important;
        color: white !important;
        transition: all 0.2s !important;
        height: 52px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(56,189,248,0.7) !important;
        background: rgba(255,255,255,0.10) !important;
        box-shadow: 0 0 0 3px rgba(14,165,233,0.18) !important;
        outline: none !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.30) !important;
        font-size: 0.9rem !important;
    }
    .stTextInput label { display: none !important; }

    /* Botón primario de login */
    .stButton > button[kind="primary"] {
        width: 100% !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 55%, #4f46e5 100%) !important;
        border: none !important;
        color: white !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        height: 52px !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 22px rgba(14,165,233,0.45) !important;
        transition: all 0.22s !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 55%, #6366f1 100%) !important;
        box-shadow: 0 8px 30px rgba(14,165,233,0.55) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* Form sin borde */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* Alert de error */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        font-size: 0.85rem !important;
        background: rgba(239,68,68,0.15) !important;
        border: 1px solid rgba(239,68,68,0.3) !important;
        color: #fca5a5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Layout: 3 columnas para centrar ─────────────────────────────────────
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.05, 1])

    with col:
        # ── LOGO + TÍTULO (todo en un solo bloque HTML) ──────────────────────
        st.markdown("""
        <div style="text-align:center; margin-bottom:28px;">

            <!-- Logo con SVG de microscopio estilizado -->
            <div style="
                width:88px; height:88px;
                background: linear-gradient(145deg, #0ea5e9, #6366f1);
                border-radius:24px;
                display:flex; align-items:center; justify-content:center;
                margin:0 auto 22px;
                box-shadow: 0 10px 40px rgba(14,165,233,0.5),
                            0 0 0 1px rgba(255,255,255,0.08),
                            inset 0 1px 0 rgba(255,255,255,0.18);
                position:relative; overflow:hidden;
            ">
                <!-- Reflejo interno -->
                <div style="
                    position:absolute; top:8px; left:10px;
                    width:30px; height:12px;
                    background:rgba(255,255,255,0.15);
                    border-radius:20px;
                    transform:rotate(-20deg);
                "></div>
                <span style="font-size:42px; line-height:1; position:relative; z-index:2;">🔬</span>
            </div>

            <div style="
                font-size:1.6rem; font-weight:800; color:white;
                letter-spacing:-0.03em; line-height:1.1;
                text-shadow: 0 2px 16px rgba(0,0,0,0.4);
                margin-bottom:6px;
            ">SGC Laboratorio Clínico</div>

            <div style="
                font-size:0.72rem; color:rgba(255,255,255,0.38);
                font-weight:600; letter-spacing:0.12em;
                text-transform:uppercase;
            ">Sistema de Gestión de Calidad</div>

        </div>
        """, unsafe_allow_html=True)

        # ── CARD glassmorphism (sólo la capa visual, sin envolver Streamlit) ──
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.055);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 20px;
            padding: 32px 32px 8px;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            box-shadow: 0 24px 60px rgba(0,0,0,0.45),
                        inset 0 1px 0 rgba(255,255,255,0.07);
            margin-bottom: 0;
        ">
            <div style="
                font-size:0.95rem; font-weight:600; color:rgba(255,255,255,0.88);
                margin-bottom:22px; text-align:center; letter-spacing:0.01em;
            ">Bienvenido — ingrese sus credenciales</div>
        </div>
        """, unsafe_allow_html=True)

        # ── FORMULARIO Streamlit (fuera del HTML) ────────────────────────────
        # Capa de fondo para que el form parezca continuar la card
        st.markdown("""
        <div style="
            background: rgba(255,255,255,0.055);
            border: 1px solid rgba(255,255,255,0.10);
            border-top: none;
            border-radius: 0 0 20px 20px;
            padding: 0 32px 28px;
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            box-shadow: 0 24px 60px rgba(0,0,0,0.45);
            margin-top:-2px;
        ">
        </div>
        """, unsafe_allow_html=True)

        with st.form("_login_form", clear_on_submit=False):
            usuario_input = st.text_input("usuario", placeholder="👤  Usuario",
                                          key="_u", label_visibility="collapsed")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            pass_input = st.text_input("clave", placeholder="🔒  Contraseña",
                                       type="password", key="_p",
                                       label_visibility="collapsed")
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            ingresar = st.form_submit_button(
                "INICIAR SESIÓN", use_container_width=True, type="primary")

        # ── CHIPS de módulos ─────────────────────────────────────────────────
        st.markdown("""
        <div style="margin:24px 0 16px;">
            <div style="
                display:flex; align-items:center; gap:12px; margin-bottom:16px;
            ">
                <div style="flex:1; height:1px; background:rgba(255,255,255,0.07);"></div>
                <div style="font-size:0.62rem; color:rgba(255,255,255,0.22);
                            font-weight:700; letter-spacing:0.10em; white-space:nowrap;">
                    MÓDULOS DISPONIBLES
                </div>
                <div style="flex:1; height:1px; background:rgba(255,255,255,0.07);"></div>
            </div>

            <div style="display:flex; justify-content:center; gap:7px; flex-wrap:wrap;">
                <div style="background:rgba(14,165,233,0.12);border:1px solid rgba(14,165,233,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">🧪</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">WESTGARD</div>
                </div>
                <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">📊</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">EP15-A3</div>
                </div>
                <div style="background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">🌐</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">PEEC</div>
                </div>
                <div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">📄</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">CORRIDAS</div>
                </div>
                <div style="background:rgba(139,92,246,0.12);border:1px solid rgba(139,92,246,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">📐</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">SIGMA</div>
                </div>
                <div style="background:rgba(20,184,166,0.12);border:1px solid rgba(20,184,166,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">🎯</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">CALIBR.</div>
                </div>
                <div style="background:rgba(249,115,22,0.12);border:1px solid rgba(249,115,22,0.25);
                            border-radius:9px;padding:8px 12px;text-align:center;min-width:72px;">
                    <div style="font-size:1.1rem;">📥</div>
                    <div style="font-size:0.58rem;color:rgba(255,255,255,0.5);
                                font-weight:700;letter-spacing:0.06em;margin-top:3px;">MASIVO</div>
                </div>
            </div>

            <div style="text-align:center;color:rgba(255,255,255,0.16);
                        font-size:0.62rem;margin-top:24px;letter-spacing:0.06em;">
                v3.0 &nbsp;·&nbsp; ISO 15189 / CAP / CLIA &nbsp;·&nbsp; DATOS PROTEGIDOS
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Lógica de autenticación ──────────────────────────────────────────────
    if ingresar:
        usuario    = st.session_state.get("_u", "").strip()
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
            margin: 10px 8px 8px;
            padding: 12px 14px;
            background: linear-gradient(135deg, rgba(14,165,233,0.12), rgba(56,189,248,0.06));
            border-radius: 12px;
            border: 1px solid rgba(14,165,233,0.18);
            display: flex; align-items: center; gap: 12px;
        ">
            <div style="
                background: linear-gradient(135deg, #0ea5e9, #6366f1);
                border-radius: 50%; width: 38px; height: 38px; flex-shrink: 0;
                display: flex; align-items: center; justify-content: center;
                font-size: 17px; box-shadow: 0 3px 10px rgba(14,165,233,0.35);
            ">👤</div>
            <div>
                <div style="color:white; font-weight:700; font-size:0.88rem; line-height:1.2;">{user}</div>
                <div style="color:#38bdf8; font-size:0.68rem; font-weight:500; margin-top:2px;">
                    <span style="display:inline-block;width:6px;height:6px;background:#10b981;
                    border-radius:50%;margin-right:4px;vertical-align:middle;"></span>Sesión activa
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Cerrar sesión", use_container_width=True, key="_logout_btn"):
            logout()
