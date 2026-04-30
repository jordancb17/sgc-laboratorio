"""
SGC Laboratorio Clínico — Dashboard principal
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from datetime import date, datetime, timedelta

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


# ─── HERO BANNER ──────────────────────────────────────────────────────────────

def _hero(hoy: date):
    dia_str = hoy.strftime("%A %d de %B de %Y").capitalize()
    chips = (
        _chip("🧪", "Westgard", "#0ea5e9")
        + _chip("📈", "Levey-Jennings", "#6366f1")
        + _chip("📐", "EP15-A3", "#10b981")
        + _chip("🌐", "Control Externo", "#f59e0b")
        + _chip("📄", "Inf. Corrida", "#ec4899")
        + _chip("📐", "Índice Sigma", "#8b5cf6")
        + _chip("🎯", "Calibraciones", "#14b8a6")
        + _chip("🔩", "Mantenimiento", "#64748b")
        + _chip("📥", "Carga Masiva", "#f97316")
    )
    st.html(
        "<div style='background:linear-gradient(135deg,#050e22 0%,#0a1f4e 40%,"
        "#0d2b6e 70%,#0f3080 100%); border-radius:20px; padding:28px 32px;"
        " margin-bottom:24px; position:relative; overflow:hidden;"
        " box-shadow:0 8px 40px rgba(5,14,34,0.55);'>"
        "<div style='position:relative; z-index:2;'>"
        "<div style='display:flex; align-items:center; gap:16px; margin-bottom:14px;'>"
        "<div style='background:linear-gradient(145deg,#0ea5e9,#6366f1);"
        " border-radius:16px; width:52px; height:52px;"
        " display:flex; align-items:center; justify-content:center;"
        " font-size:28px; flex-shrink:0;"
        " box-shadow:0 4px 18px rgba(14,165,233,0.5);'>🔬</div>"
        "<div>"
        "<div style='font-size:1.45rem; font-weight:800; color:white;"
        " letter-spacing:-0.03em; line-height:1.1;'>Sistema de Gestión de Calidad</div>"
        f"<div style='font-size:0.8rem; color:rgba(255,255,255,0.55);"
        f" margin-top:3px; font-weight:400;'>Laboratorio Clínico &nbsp;·&nbsp; {dia_str}</div>"
        "</div>"
        "</div>"
        f"<div style='display:flex; flex-wrap:wrap; gap:7px; margin-top:4px;'>{chips}</div>"
        "</div>"
        "</div>"
    )


def _chip(icon: str, label: str, color: str) -> str:
    return (
        f"<div style='background:rgba(255,255,255,0.08);"
        f" border:1px solid rgba(255,255,255,0.15);"
        f" border-left:3px solid {color};"
        f" border-radius:8px; padding:5px 11px;"
        f" display:inline-flex; align-items:center; gap:6px;'>"
        f"<span style='font-size:0.82rem;'>{icon}</span>"
        f"<span style='font-size:0.68rem; font-weight:600;"
        f" color:rgba(255,255,255,0.8); letter-spacing:0.03em;'>{label}</span>"
        f"</div>"
    )


# ─── KPI CARD ─────────────────────────────────────────────────────────────────

def _kpi(icon: str, value, label: str, sub: str, cls: str) -> str:
    return (
        f"<div class='kpi-card kpi-solid {cls}'>"
        f"<span class='kpi-icon'>{icon}</span>"
        f"<div class='kpi-value'>{value}</div>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-sub'>{sub}</div>"
        f"</div>"
    )


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

def _dashboard(db):
    hoy = date.today()
    _hero(hoy)

    # ── Filtro de área ─────────────────────────────────────────────────────
    areas = crud.listar_areas(db)
    area_opts = {"🏥 Todas las áreas": None} | {f"📍 {a.nombre}": a.id for a in areas}
    area_sel = st.selectbox("", list(area_opts.keys()), key="dash_area",
                            label_visibility="collapsed")
    area_id_fil = area_opts[area_sel]

    # ── Datos ──────────────────────────────────────────────────────────────
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

    pct_ok = f"{len(ok_hoy)/len(controles_hoy)*100:.0f}%" if controles_hoy else "—"

    hora_actual = datetime.now().hour
    if 7 <= hora_actual < 14:
        turno_actual = "MAÑANA"
    elif 14 <= hora_actual < 22:
        turno_actual = "TARDE"
    else:
        turno_actual = "NOCHE"

    # ── KPI Cards — fila 1 ─────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.html(_kpi("🧪", len(controles_hoy), "Controles Totales",
                     f"{len(ok_hoy)} dentro de rango", "kpi-s-blue"))
    with c2:
        st.html(_kpi("✅", len(ok_hoy), "Dentro de Rango",
                     "Resultados aceptables", "kpi-s-green"))
    with c3:
        st.html(_kpi("⚠️", len(advert_hoy), "Advertencia",
                     "Monitorear tendencia", "kpi-s-amber"))
    with c4:
        st.html(_kpi("🛑", len(rechazos_hoy), "Fuera de Rango",
                     "Requieren acción correctiva", "kpi-s-red"))

    st.html("<div style='height:10px'></div>")

    # ── KPI Cards — fila 2 ─────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.html(_kpi("📋", len(sin_ac), "Sin Acción Correctiva",
                     "Rechazos pendientes", "kpi-s-purple"))
    with c6:
        st.html(_kpi("📦", len(lotes_vencer), "Lotes por Vencer",
                     "Próximos 30 días", "kpi-s-teal"))
    with c7:
        st.html(_kpi("🎯", pct_ok, "% Efectividad",
                     "Controles dentro de límites", "kpi-s-indigo"))
    with c8:
        st.html(_kpi("🕐", turno_actual, "Turno Actual",
                     datetime.now().strftime("%H:%M"), "kpi-s-navy"))

    st.html("<div class='divider'></div>")

    # ── Alertas ────────────────────────────────────────────────────────────
    if rechazos_hoy:
        st.error(f"🛑 **{len(rechazos_hoy)} RECHAZO(S) HOY** — No libere resultados sin acción correctiva.")
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

    st.html("<div class='divider'></div>")

    # ── Gráficos ───────────────────────────────────────────────────────────
    col_g1, col_g2 = st.columns([3, 2])
    with col_g1:
        _grafico_semana(db, hoy, area_id_fil)
    with col_g2:
        _grafico_dona(controles_hoy, ok_hoy, advert_hoy, rechazos_hoy)

    st.html("<div class='divider'></div>")

    # ── Accesos rápidos ────────────────────────────────────────────────────
    st.markdown("#### 🚀 Accesos Rápidos")
    _accesos_rapidos()

    st.html("<div class='divider'></div>")

    # ── Últimos registros ──────────────────────────────────────────────────
    _tabla_ultimos(db, hoy, area_id_fil)

    # ── Footer ─────────────────────────────────────────────────────────────
    st.html(
        "<div style='text-align:center; color:rgba(255,255,255,0.25);"
        " font-size:0.72rem; padding:24px 0 8px;'>"
        "🔬 SGC Laboratorio Clínico &nbsp;·&nbsp;"
        " ISO 15189 · Westgard · EP15-A3 · PEEC"
        f" &nbsp;·&nbsp; v3.1 &nbsp;·&nbsp; {hoy}"
        "</div>"
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
    dias_labels = [d[5:] for d in dias]

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
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=12, color="#94a3b8")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="N° controles",
                   tickfont=dict(size=11, color="#94a3b8"), title_font=dict(color="#94a3b8")),
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
        textfont=dict(size=12, color="white"),
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{len(controles_hoy)}</b>",
            x=0.5, y=0.5, font_size=26, showarrow=False, font_color="white",
        )],
    )
    st.plotly_chart(fig, use_container_width=True)


def _accesos_rapidos():
    modulos = [
        ("📋", "Controles Diarios",    "Registrar control del turno",         "#0ea5e9"),
        ("📥", "Carga Masiva",         "Ingresar valores históricos en lote",  "#f97316"),
        ("📊", "Reportes",             "Levey-Jennings y reporte mensual",     "#8b5cf6"),
        ("📄", "Informe de Corrida",   "Informe formal ISO 15189 / CAP",       "#ec4899"),
        ("🔧", "Acciones Correctivas", "Gestionar rechazos pendientes",        "#dc2626"),
        ("🎯", "Calibraciones",        "Registrar calibración de equipo",      "#14b8a6"),
        ("🔩", "Mantenimiento",        "Bitácora de mantenimiento",            "#64748b"),
        ("⚙️", "Configuración",        "Equipos, analitos y lotes",           "#10b981"),
    ]

    cols = st.columns(4)
    for i, (icon, nombre, desc, color) in enumerate(modulos):
        with cols[i % 4]:
            st.html(
                f"<div style='background:rgba(255,255,255,0.05);"
                f" border:1px solid rgba(255,255,255,0.08);"
                f" border-left:4px solid {color};"
                f" border-radius:12px; padding:14px 16px; margin-bottom:10px;'>"
                f"<div style='font-size:1.4rem; margin-bottom:6px;'>{icon}</div>"
                f"<div style='font-size:0.88rem; font-weight:700;"
                f" color:white; margin-bottom:2px;'>{nombre}</div>"
                f"<div style='font-size:0.72rem; color:rgba(255,255,255,0.45);'>{desc}</div>"
                f"</div>"
            )


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
            "Fecha":     c.fecha,
            "Hora":      c.hora.strftime("%H:%M"),
            "Turno":     c.turno or "—",
            "Área":      m.equipo.area.nombre,
            "Analito":   m.analito,
            "Nv":        c.nivel_lote.nivel,
            "Valor":     c.valor,
            "z":         round(c.zscore, 2) if c.zscore is not None else "",
            "Resultado": c.resultado,
            "Regla":     c.regla_violada or "—",
            "Personal":  f"{c.personal.apellido}, {c.personal.nombre}",
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
