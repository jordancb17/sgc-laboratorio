"""
Utilidades comunes: setup, page header, y helpers de rendimiento.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import streamlit.components.v1 as components
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
        # ── Logo + nombre del sistema ─────────────────────────────────────────
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
            " margin:0 10px 6px;'></div>"
        )

        # ── Reloj en tiempo real (JavaScript en iframe) ───────────────────────
        components.html(
            """
            <html>
            <body style="margin:0;padding:0;background:#060d1c;overflow:hidden;">
            <div id="clk" style="
                font-family:'Courier New',Courier,monospace;
                font-size:1.18rem;
                font-weight:700;
                color:#93c5fd;
                text-align:center;
                padding:8px 0 3px;
                letter-spacing:0.09em;
            "></div>
            <div id="dt" style="
                font-size:0.67rem;
                color:#4a6fa5;
                text-align:center;
                letter-spacing:0.05em;
                padding-bottom:8px;
            "></div>
            <script>
            var D=['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];
            var M=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
            function tick(){
                var n=new Date();
                var hh=String(n.getHours()).padStart(2,'0');
                var mm=String(n.getMinutes()).padStart(2,'0');
                var ss=String(n.getSeconds()).padStart(2,'0');
                document.getElementById('clk').textContent=hh+':'+mm+':'+ss;
                var dd=String(n.getDate()).padStart(2,'0');
                document.getElementById('dt').textContent=
                    D[n.getDay()]+' '+dd+' '+M[n.getMonth()]+' '+n.getFullYear();
            }
            tick(); setInterval(tick,1000);
            </script>
            </body>
            </html>
            """,
            height=66,
        )

        # ── Selector de tema ──────────────────────────────────────────────────
        st.html("<div style='padding:2px 10px 0;'>")
        st.selectbox(
            "Tema de interfaz",
            ["🌙 Oscuro", "☀️ Claro"],
            key="tema_app",
            label_visibility="collapsed",
            help="Cambia entre tema oscuro y claro. El sidebar permanece siempre oscuro.",
        )
        st.html("</div>")

        # ── Divisor inferior ──────────────────────────────────────────────────
        st.html(
            "<div style='height:1px;"
            " background:linear-gradient(90deg,transparent,rgba(255,255,255,0.10),transparent);"
            " margin:6px 10px 8px;'></div>"
        )
