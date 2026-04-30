"""
Utilidades comunes para todas las páginas.
Llamar setup_page() al inicio de cada página, después de st.set_page_config().
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from modules.styles import inject_css
from modules.auth import require_auth, render_sidebar_user


def setup_page():
    """Inyecta CSS + verifica autenticación + renderiza sidebar."""
    inject_css()
    require_auth()
    _render_sidebar_brand()
    render_sidebar_user()


def _render_sidebar_brand():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 20px 16px 12px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="
                    background: rgba(255,255,255,0.15);
                    border-radius: 10px;
                    width: 44px; height: 44px; flex-shrink: 0;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 24px;
                ">🔬</div>
                <div>
                    <div style="color:white; font-weight:700; font-size:1rem; line-height:1.2;">
                        SGC Lab
                    </div>
                    <div style="color:#93c5fd; font-size:0.72rem; line-height:1.4;">
                        Control de Calidad
                    </div>
                </div>
            </div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.12); margin:0 16px 6px;">
        """, unsafe_allow_html=True)
