"""
SGC Laboratorio Clínico — Dashboard principal
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from datetime import date, timedelta

st.set_page_config(
    page_title="SGC Laboratorio Clínico",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database.database import init_db, get_session
from database import crud
from modules.page_utils import setup_page
from modules import backup as bk

init_db()
setup_page()
try:
    bk.auto_backup()
except Exception:
    pass


def main():
    db = get_session()
    try:
        _dashboard(db)
    finally:
        db.close()


# ─── HERO BANNER ─────────────────────────────────────────────────────────────

def _hero(hoy: date):
    dia_str = hoy.strftime("%A %d de %B de %Y").capitalize()
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #050e22 0%, #0a1f4e 40%, #0d2b6e 70%, #0f3080 100%);
        border-radius: 20px;
        padding: 36px 40px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 40px rgba(5,14,34,0.55);
    ">
        <!-- Decorative SVG atoms -->
        <svg style="position:absolute;top:-20px;right:-20px;opacity:0.07;pointer-events:none;"
             width="380" height="320" viewBox="0 0 380 320">
            <!-- Atom 1 -->
            <circle cx="190" cy="160" r="10" fill="#38bdf8"/>
            <ellipse cx="190" cy="160" rx="120" ry="45" fill="none" stroke="#38bdf8" stroke-width="2"/>
            <ellipse cx="190" cy="160" rx="120" ry="45" fill="none" stroke="#38bdf8" stroke-width="2"
                     transform="rotate(60 190 160)"/>
            <ellipse cx="190" cy="160" rx="120" ry="45" fill="none" stroke="#38bdf8" stroke-width="2"
                     transform="rotate(120 190 160)"/>
            <!-- Small circles (electrons) -->
            <circle cx="310" cy="160" r="5" fill="#93c5fd"/>
            <circle cx="131" cy="117" r="5" fill="#93c5fd"/>
            <circle cx="131" cy="203" r="5" fill="#93c5fd"/>
            <!-- DNA helix suggestion -->
            <path d="M20,40 Q60,60 20,80 Q60,100 20,120 Q60,140 20,160" fill="none" stroke="#6366f1" stroke-width="2.5"/>
            <path d="M60,40 Q20,60 60,80 Q20,100 60,120 Q20,140 60,160" fill="none" stroke="#818cf8" stroke-width="2.5"/>
            <line x1="20" y1="40" x2="60" y2="40" stroke="#a5b4fc" stroke-width="1.5"/>
            <line x1="25" y1="60" x2="55" y2="60" stroke="#a5b4fc" stroke-width="1.5"/>
            <line x1="20" y1="80" x2="60" y2="80" stroke="#a5b4fc" stroke-width="1.5"/>
            <line x1="25" y1="100" x2="55" y2="100" stroke="#a5b4fc" stroke-width="1.5"/>
            <line x1="20" y1="120" x2="60" y2="120" stroke="#a5b4fc" stroke-width="1.5"/>
            <line x1="25" y1="140" x2="55" y2="140" stroke="#a5b4fc" stroke-width="1.5"/>
            <line x1="20" y1="160" x2="60" y2="160" stroke="#a5b4fc" stroke-width="1.5"/>
            <!-- Hexagons (molecular structure) -->
            <polygon points="320,240 340,228 360,240 360,264 340,276 320,264" fill="none" stroke="#22d3ee" stroke-width="1.5"/>
            <polygon points="280,240 300,228 320,240 320,264 300,276 280,264" fill="none" stroke="#22d3ee" stroke-width="1.5"/>
            <polygon points="300,208 320,196 340,208 340,232 320,244 300,232" fill="none" stroke="#22d3ee" stroke-width="1.5"/>
        </svg>

        <div style="position:relative;z-index:2;">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:18px;">
                <div style="
                    background:linear-gradient(145deg,#0ea5e9,#6366f1);
                    border-radius:16px; width:56px; height:56px;
                    display:flex;align-items:center;justify-content:center;
                    font-size:30px; flex-shrink:0;
                    box-shadow:0 4px 18px rgba(14,165,233,0.5);
                ">🔬</div>
                <div>
                    <div style="font-size:1.55rem;font-weight:800;color:white;
                                letter-spacing:-0.03em;line-height:1.1;">
                        Sistema de Gestión de Calidad
                    </div>
                    <div style="font-size:0.82rem;color:rgba(255,255,255,0.55);
                                margin-top:4px;font-weight:400;letter-spacing:0.02em;">
                        Laboratorio Clínico &nbsp;·&nbsp; {dia_str}
                    </div>
                </div>
            </div>

            <!-- Módulos chips -->
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;">
                {_chip("🧪","Westgard","#0ea5e9")}
                {_chip("📈","Levey-Jennings","#6366f1")}
                {_chip("📐","EP15-A3","#10b981")}
                {_chip("🌐","Control Externo","#f59e0b")}
                {_chip("📄","Inf. Corrida","#ec4899")}
                {_chip("📐","Índice Sigma","#8b5cf6")}
                {_chip("🎯","Calibraciones","#14b8a6")}
                {_chip("🔩","Mantenimiento","#64748b")}
                {_chip("📥","Carga Masiva","#f97316")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _chip(icon, label, color):
    return f"""
    <div style="
        background:rgba(255,255,255,0.08);
        border:1px solid rgba(255,255,255,0.15);
        border-left:3px solid {color};
        border-radius:8px; padding:5px 12px;
        display:flex;align-items:center;gap:7px;
    ">
        <span style="font-size:0.85rem;">{icon}</span>
        <span style="font-size:0.7rem;font-weight:600;color:rgba(255,255,255,0.8);
                     letter-spacing:0.04em;">{label}</span>
    </div>"""


# ─── KPI CARD ────────────────────────────────────────────────────────────────

def _kpi(icon, value, label, sub, cls):
    return f"""
    <div class="kpi-card {cls}">
        <span class="kpi-icon">{icon}</span>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

def _dashboard(db):
    hoy = date.today()
    _hero(hoy)

    # ── Filtro de área ─────────────────────────────────────────────────────
    areas = crud.listar_areas(db)
    area_opts = {"🏥 Todas las áreas": None} | {f"📍 {a.nombre}": a.id for a in areas}
    area_sel = st.selectbox("", list(area_opts.keys()), key="dash_area",
                            label_visibility="collapsed")
    area_id_fil = area_opts[area_sel]

    # ── Datos del día ──────────────────────────────────────────────────────
    controles_hoy_all = crud.listar_controles_diarios(db, fecha_desde=hoy, fecha_hasta=hoy)
    controles_hoy = (
        [c for c in controles_hoy_all if c.material.equipo.area_id == area_id_fil]
        if area_id_fil else controles_hoy_all
    )
    rechazos_hoy  = [c for c in controles_hoy if c.resultado == "RECHAZO"]
    advert_hoy    = [c for c in controles_hoy if c.resultado == "ADVERTENCIA"]
    ok_hoy        = [c for c in controles_hoy if c.resultado == "OK"]
    lotes_vencer  = crud.lotes_por_vencer(db, dias=30)
    sin_ac        = crud.controles_sin_accion_correctiva(db)
    tasa          = f"{len(rechazos_hoy)/len(controles_hoy)*100:.0f}%" if controles_hoy else "—"

    # ── KPI Cards ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(_kpi("🧪", len(controles_hoy), "Controles Hoy",
                         f"{len(ok_hoy)} aceptados", "kpi-blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(_kpi("✅", len(ok_hoy), "Resultados OK",
                         f"Tasa: {tasa}", "kpi-green"), unsafe_allow_html=True)
    with c3:
        st.markdown(_kpi("⚠️", len(advert_hoy), "Advertencias",
                         "Monitorear tendencia", "kpi-amber"), unsafe_allow_html=True)
    with c4:
        st.markdown(_kpi("🛑", len(rechazos_hoy), "Rechazos",
                         "Requieren AC", "kpi-red"), unsafe_allow_html=True)
    with c5:
        st.markdown(_kpi("📋", len(sin_ac), "Sin Acción Correct.",
                         "Rechazos pendientes", "kpi-purple"), unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Alertas ────────────────────────────────────────────────────────────
    if rechazos_hoy:
        st.error(f"🛑 **{len(rechazos_hoy)} RECHAZO(S) HOY** — No libere resultados de pacientes sin acción correctiva.")
        for c in rechazos_hoy:
            m = c.material
            st.markdown(
                f"&emsp;▸ **{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}** "
                f"Nivel {c.nivel_lote.nivel} — Regla `{c.regla_violada}` — "
                f"Valor: **{c.valor}** {m.unidad or ''} (z = {c.zscore:.2f})"
            )

    if sin_ac:
        st.warning(f"📋 **{len(sin_ac)} rechazo(s) sin acción correctiva.** Vaya a 🔧 Acciones Correctivas.")

    if advert_hoy:
        st.warning(f"⚠️ **{len(advert_hoy)} advertencia(s) hoy** — Monitoree tendencia en el próximo control.")

    if lotes_vencer:
        with st.expander(f"📦 {len(lotes_vencer)} lote(s) por vencer en 30 días", expanded=False):
            for lote in lotes_vencer:
                dias_rest = (lote.fecha_vencimiento - hoy).days
                m = lote.material
                icono = "🔴" if dias_rest <= 7 else "🟡" if dias_rest <= 14 else "🔵"
                color = "#dc2626" if dias_rest <= 7 else "#d97706" if dias_rest <= 14 else "#2563eb"
                st.markdown(
                    f"{icono} **{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}** — "
                    f"Lote `{lote.numero_lote}` — vence `{lote.fecha_vencimiento}` "
                    f"(<span style='color:{color};font-weight:700'>{dias_rest}d</span>)",
                    unsafe_allow_html=True,
                )

    if not rechazos_hoy and not advert_hoy and controles_hoy:
        st.success("✅ Todos los controles del día dentro de los límites de aceptación.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Gráficos ───────────────────────────────────────────────────────────
    col_g1, col_g2 = st.columns([3, 2])

    with col_g1:
        _grafico_semana(db, hoy, area_id_fil)

    with col_g2:
        _grafico_dona(controles_hoy, ok_hoy, advert_hoy, rechazos_hoy)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Accesos rápidos ────────────────────────────────────────────────────
    st.markdown("#### 🚀 Accesos Rápidos")
    _accesos_rapidos()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Últimos registros ──────────────────────────────────────────────────
    _tabla_ultimos(db, hoy, area_id_fil)

    # ── Footer ─────────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#94a3b8;font-size:0.72rem;'>"
        "🔬 SGC Laboratorio Clínico &nbsp;·&nbsp; ISO 15189 · Westgard · EP15-A3 · PEEC "
        f"&nbsp;·&nbsp; v3.0 &nbsp;·&nbsp; {hoy}</p>",
        unsafe_allow_html=True,
    )


def _grafico_semana(db, hoy, area_id_fil):
    st.markdown("#### 📊 Controles — Últimos 7 Días")
    fecha_desde = hoy - timedelta(days=6)
    controles_sem = crud.listar_controles_diarios(db, fecha_desde=fecha_desde, fecha_hasta=hoy)
    if area_id_fil:
        controles_sem = [c for c in controles_sem if c.material.equipo.area_id == area_id_fil]

    if not controles_sem:
        st.info("Sin controles en los últimos 7 días.")
        return

    import plotly.graph_objects as go
    from collections import defaultdict
    por_dia = defaultdict(lambda: {"OK": 0, "ADVERTENCIA": 0, "RECHAZO": 0})
    for c in controles_sem:
        por_dia[str(c.fecha)][c.resultado] = por_dia[str(c.fecha)].get(c.resultado, 0) + 1

    dias = sorted(por_dia.keys())
    dias_labels = [d[5:] for d in dias]  # MM-DD

    fig = go.Figure()
    fig.add_bar(name="✅ OK",          x=dias_labels,
                y=[por_dia[d].get("OK", 0) for d in dias],
                marker_color="#10b981", marker_line_width=0)
    fig.add_bar(name="⚠️ Advertencia", x=dias_labels,
                y=[por_dia[d].get("ADVERTENCIA", 0) for d in dias],
                marker_color="#f59e0b", marker_line_width=0)
    fig.add_bar(name="🛑 Rechazo",     x=dias_labels,
                y=[por_dia[d].get("RECHAZO", 0) for d in dias],
                marker_color="#ef4444", marker_line_width=0)

    fig.update_layout(
        barmode="stack", height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12)),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(0,0,0,0.05)", tickfont=dict(size=12)),
        yaxis=dict(gridcolor="rgba(0,0,0,0.05)", title="N° controles", tickfont=dict(size=11)),
        hoverlabel=dict(font_size=13),
    )
    st.plotly_chart(fig, use_container_width=True)


def _grafico_dona(controles_hoy, ok_hoy, advert_hoy, rechazos_hoy):
    st.markdown("#### 🎯 Distribución del Día")
    if not controles_hoy:
        st.info("Sin controles hoy.")
        return

    import plotly.graph_objects as go
    pairs = [
        ("✅ OK", len(ok_hoy), "#10b981"),
        ("⚠️ Advertencia", len(advert_hoy), "#f59e0b"),
        ("🛑 Rechazo", len(rechazos_hoy), "#ef4444"),
    ]
    pairs_f = [(l, v, c) for l, v, c in pairs if v > 0]
    if not pairs_f:
        st.info("Sin datos.")
        return

    labels, values, colors = zip(*pairs_f)
    fig = go.Figure(go.Pie(
        labels=list(labels), values=list(values),
        marker_colors=list(colors),
        hole=0.58,
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{len(controles_hoy)}</b>",
            x=0.5, y=0.5, font_size=26, showarrow=False, font_color="#0a1628",
        )],
    )
    st.plotly_chart(fig, use_container_width=True)


def _accesos_rapidos():
    modulos = [
        ("📋", "Controles Diarios",    "Registrar control del turno",          "#0ea5e9"),
        ("📥", "Carga Masiva",         "Ingresar valores históricos en lote",   "#f97316"),
        ("📊", "Reportes",             "Levey-Jennings y reporte mensual",      "#8b5cf6"),
        ("📄", "Informe de Corrida",   "Informe formal ISO 15189 / CAP",        "#ec4899"),
        ("🔧", "Acciones Correctivas", "Gestionar rechazos pendientes",         "#dc2626"),
        ("🎯", "Calibraciones",        "Registrar calibración de equipo",       "#14b8a6"),
        ("🔩", "Mantenimiento",        "Bitácora de mantenimiento",             "#64748b"),
        ("⚙️", "Configuración",        "Equipos, analitos y lotes",            "#10b981"),
    ]

    cols = st.columns(4)
    for i, (icon, nombre, desc, color) in enumerate(modulos):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="
                background:var(--surface,#fff);
                border:1px solid var(--border,#e2e8f0);
                border-left:4px solid {color};
                border-radius:12px; padding:14px 16px;
                margin-bottom:10px;
                transition:all 0.2s;
            ">
                <div style="font-size:1.4rem;margin-bottom:6px;">{icon}</div>
                <div style="font-size:0.88rem;font-weight:700;
                            color:var(--txt-primary,#0a1628);margin-bottom:2px;">{nombre}</div>
                <div style="font-size:0.72rem;color:var(--txt-muted,#94a3b8);">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


def _tabla_ultimos(db, hoy, area_id_fil):
    st.markdown("#### 📋 Últimos 50 Controles Registrados")
    controles = crud.listar_controles_diarios(
        db, fecha_desde=hoy - timedelta(days=6), fecha_hasta=hoy
    )
    if area_id_fil:
        controles = [c for c in controles if c.material.equipo.area_id == area_id_fil]

    if not controles:
        st.info("No hay controles registrados en los últimos 7 días.")
        return

    import pandas as pd
    filas = []
    for c in controles[:50]:
        m = c.material
        filas.append({
            "Fecha":    c.fecha,
            "Hora":     c.hora.strftime("%H:%M"),
            "Turno":    c.turno or "—",
            "Área":     m.equipo.area.nombre,
            "Analito":  m.analito,
            "Nv":       c.nivel_lote.nivel,
            "Valor":    c.valor,
            "z":        round(c.zscore, 2) if c.zscore is not None else "",
            "Resultado":c.resultado,
            "Regla":    c.regla_violada or "—",
            "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
        })

    df = pd.DataFrame(filas)

    def _color(val):
        return {
            "OK":          "background-color:#d1fae5;color:#065f46;font-weight:600",
            "ADVERTENCIA": "background-color:#fef3c7;color:#78350f;font-weight:600",
            "RECHAZO":     "background-color:#fee2e2;color:#7f1d1d;font-weight:700",
        }.get(val, "")

    st.dataframe(df.style.applymap(_color, subset=["Resultado"]),
                 use_container_width=True, hide_index=True)

    # Excel export
    import io
    buf = io.BytesIO()
    with __import__("pandas").ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Controles")
    st.download_button("📥 Descargar Excel", buf.getvalue(),
                       file_name=f"controles_{hoy}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="dl_dash_excel")


if __name__ == "__main__":
    main()
