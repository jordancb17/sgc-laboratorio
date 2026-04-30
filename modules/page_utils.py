"""
Utilidades comunes: setup, page header, y helpers de rendimiento.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from modules.styles import inject_css
from modules.auth import require_auth, render_sidebar_user


def setup_page():
    inject_css()
    require_auth()
    _render_sidebar_brand()
    render_sidebar_user()


def page_header(icon: str, title: str, subtitle: str = "", badge: str = ""):
    badge_html = (
        f"<span class='ph-badge'>{badge}</span>" if badge else ""
    )
    st.html(
        f"<div class='page-header'>"
        f"<div class='ph-icon'>{icon}</div>"
        f"<div class='ph-text'>"
        f"<div class='ph-title'>{title}</div>"
        f"<div class='ph-sub'>{subtitle}</div>"
        f"{badge_html}"
        f"</div>"
        f"</div>"
    )


def section_divider(label: str = ""):
    if label:
        st.html(f"<div class='divider-label'>{label}</div>")
    else:
        st.html("<div class='divider'></div>")


def _render_sidebar_brand():
    with st.sidebar:
        st.html(
            "<div style='padding:22px 16px 14px;'>"
            "<div style='display:flex; align-items:center; gap:13px;'>"
            "<div style='background:linear-gradient(145deg,#0ea5e9,#4f46e5);"
            " border-radius:12px; width:46px; height:46px; flex-shrink:0;"
            " display:flex; align-items:center; justify-content:center;"
            " font-size:26px; box-shadow:0 4px 14px rgba(14,165,233,0.35);'>🔬</div>"
            "<div>"
            "<div style='color:white; font-weight:800; font-size:1.0rem;"
            " line-height:1.2; letter-spacing:-0.01em;'>SGC Laboratorio</div>"
            "<div style='color:#93c5fd; font-size:0.7rem; font-weight:500;"
            " letter-spacing:0.04em; margin-top:2px;'>SISTEMA DE GESTIÓN DE CALIDAD</div>"
            "</div>"
            "</div>"
            "</div>"
            "<div style='height:1px;"
            " background:linear-gradient(90deg,transparent,rgba(255,255,255,0.10),transparent);"
            " margin:0 10px 8px;'></div>"
        )
