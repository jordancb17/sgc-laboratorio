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


def _kpi_card(icon, value, label, sub, color_class):
    return f"""
    <div class="kpi-card {color_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""


def _dashboard(db):
    hoy = date.today()

    # ── Header elegante ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="section-header">
        <h2>🔬 Dashboard — Control de Calidad</h2>
        <p>Sistema de Gestión de Calidad · {hoy.strftime('%A %d de %B de %Y').capitalize()}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filtro por área ────────────────────────────────────────────────────
    areas = crud.listar_areas(db)
    area_opts = {"🏥 Todas las áreas": None} | {f"📍 {a.nombre}": a.id for a in areas}
    area_sel  = st.selectbox("", list(area_opts.keys()), key="dash_area",
                              label_visibility="collapsed")
    area_id_fil = area_opts[area_sel]

    controles_hoy_all = crud.listar_controles_diarios(db, fecha_desde=hoy, fecha_hasta=hoy)
    if area_id_fil is not None:
        controles_hoy = [c for c in controles_hoy_all if c.material.equipo.area_id == area_id_fil]
    else:
        controles_hoy = controles_hoy_all

    rechazos_hoy = [c for c in controles_hoy if c.resultado == "RECHAZO"]
    advert_hoy   = [c for c in controles_hoy if c.resultado == "ADVERTENCIA"]
    ok_hoy       = [c for c in controles_hoy if c.resultado == "OK"]
    lotes_vencer = crud.lotes_por_vencer(db, dias=30)

    sin_ac = crud.controles_sin_accion_correctiva(db)
    tasa   = f"{len(rechazos_hoy)/len(controles_hoy)*100:.0f}%" if controles_hoy else "—"

    # ── KPI Cards HTML ─────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(_kpi_card("🧪", len(controles_hoy), "Controles Hoy",
                              f"✅ {len(ok_hoy)} aceptados", "kpi-blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(_kpi_card("✅", len(ok_hoy), "Resultados OK",
                              f"Tasa: {tasa}", "kpi-green"), unsafe_allow_html=True)
    with c3:
        st.markdown(_kpi_card("⚠️", len(advert_hoy), "Advertencias",
                              "Regla 1-2s detectada", "kpi-amber"), unsafe_allow_html=True)
    with c4:
        st.markdown(_kpi_card("🛑", len(rechazos_hoy), "Rechazos",
                              "Requieren acción", "kpi-red"), unsafe_allow_html=True)
    with c5:
        st.markdown(_kpi_card("📦", len(lotes_vencer), "Lotes por Vencer",
                              "Próximos 30 días", "kpi-amber"), unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Alertas ─────────────────────────────────────────────────────────
    if rechazos_hoy:
        with st.container():
            st.error(f"🛑 **{len(rechazos_hoy)} RECHAZO(S) HOY** — No libere resultados de pacientes sin acción correctiva.")
            for c in rechazos_hoy:
                m = c.material
                st.markdown(
                    f"&emsp;▸ **{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}** "
                    f"Nivel {c.nivel_lote.nivel} — Regla `{c.regla_violada}` — "
                    f"Valor: **{c.valor}** {m.unidad or ''} (z = {c.zscore:.2f})"
                )

    if sin_ac:
        st.warning(f"📋 **{len(sin_ac)} rechazo(s) sin acción correctiva registrada.** Vaya a 🔧 Acciones Correctivas.")

    if advert_hoy:
        st.warning(f"⚠️ **{len(advert_hoy)} advertencia(s) hoy** — Monitoree la tendencia en el próximo control.")

    if lotes_vencer:
        with st.expander(f"📦 {len(lotes_vencer)} lote(s) próximos a vencer", expanded=False):
            for lote in lotes_vencer:
                dias_rest = (lote.fecha_vencimiento - hoy).days
                m = lote.material
                color = "#dc2626" if dias_rest <= 7 else "#d97706" if dias_rest <= 14 else "#2563eb"
                icono = "🔴" if dias_rest <= 7 else "🟡" if dias_rest <= 14 else "🔵"
                st.markdown(
                    f"{icono} **{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}** — "
                    f"Lote `{lote.numero_lote}` — vence `{lote.fecha_vencimiento}` "
                    f"(<span style='color:{color};font-weight:700'>{dias_rest} día(s)</span>)",
                    unsafe_allow_html=True,
                )

    if not rechazos_hoy and not advert_hoy and controles_hoy:
        st.success("✅ Todos los controles del día dentro de los límites de aceptación.")

    # ── Gráficos lado a lado ────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col_graf1, col_graf2 = st.columns([3, 2])

    # Gráfico barras — últimos 7 días
    with col_graf1:
        st.markdown("#### 📊 Controles — Últimos 7 días")
        fecha_desde = hoy - timedelta(days=6)
        controles_sem = crud.listar_controles_diarios(db, fecha_desde=fecha_desde, fecha_hasta=hoy)

        if controles_sem:
            if area_id_fil:
                controles_sem = [c for c in controles_sem if c.material.equipo.area_id == area_id_fil]

            import plotly.graph_objects as go
            from collections import defaultdict

            por_dia = defaultdict(lambda: {"OK": 0, "ADVERTENCIA": 0, "RECHAZO": 0})
            for c in controles_sem:
                por_dia[str(c.fecha)][c.resultado] = por_dia[str(c.fecha)].get(c.resultado, 0) + 1

            dias = sorted(por_dia.keys())
            # Mostrar solo día/mes
            dias_labels = [d[5:] for d in dias]

            fig = go.Figure()
            fig.add_bar(name="✅ OK",          x=dias_labels, y=[por_dia[d].get("OK",0) for d in dias],
                        marker_color="#10b981", marker_line_width=0)
            fig.add_bar(name="⚠️ Advertencia", x=dias_labels, y=[por_dia[d].get("ADVERTENCIA",0) for d in dias],
                        marker_color="#f59e0b", marker_line_width=0)
            fig.add_bar(name="🛑 Rechazo",     x=dias_labels, y=[por_dia[d].get("RECHAZO",0) for d in dias],
                        marker_color="#ef4444", marker_line_width=0)

            fig.update_layout(
                barmode="stack",
                height=300,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12)),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=12)),
                yaxis=dict(gridcolor="#f1f5f9", title="N° controles", tickfont=dict(size=11)),
                hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#e2e8f0"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay controles en los últimos 7 días.")

    # Gráfico dona — distribución del día
    with col_graf2:
        st.markdown("#### 🎯 Distribución del Día")
        if controles_hoy:
            import plotly.graph_objects as go
            labels = ["✅ OK", "⚠️ Advertencia", "🛑 Rechazo"]
            values = [len(ok_hoy), len(advert_hoy), len(rechazos_hoy)]
            colors = ["#10b981", "#f59e0b", "#ef4444"]

            # Filtrar ceros
            lv = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
            if lv:
                labels_f, values_f, colors_f = zip(*lv)
                fig2 = go.Figure(go.Pie(
                    labels=list(labels_f), values=list(values_f),
                    marker_colors=list(colors_f),
                    hole=0.55,
                    textinfo="label+percent",
                    textfont=dict(size=13),
                    hovertemplate="%{label}: %{value} controles<extra></extra>",
                ))
                fig2.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=10),
                    showlegend=False,
                    paper_bgcolor="white",
                    annotations=[dict(
                        text=f"<b>{len(controles_hoy)}</b><br><span style='font-size:10px'>total</span>",
                        x=0.5, y=0.5, font_size=20, showarrow=False,
                    )],
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin controles registrados hoy.")

    # ── Tabla resumen últimos 7 días ────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("#### 📋 Últimos controles registrados")

    controles_sem_full = crud.listar_controles_diarios(db, fecha_desde=hoy-timedelta(days=6), fecha_hasta=hoy)
    if area_id_fil:
        controles_sem_full = [c for c in controles_sem_full if c.material.equipo.area_id == area_id_fil]

    if controles_sem_full:
        import pandas as pd
        filas = []
        for c in controles_sem_full[:50]:  # últimos 50
            m = c.material
            filas.append({
                "Fecha": c.fecha,
                "Hora": c.hora.strftime("%H:%M"),
                "Turno": c.turno or "—",
                "Área": m.equipo.area.nombre,
                "Analito": m.analito,
                "Nv": c.nivel_lote.nivel,
                "Valor": c.valor,
                "z": f"{c.zscore:.2f}" if c.zscore is not None else "",
                "Resultado": c.resultado,
                "Regla": c.regla_violada or "—",
                "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
            })
        df = pd.DataFrame(filas)

        def _color(val):
            return {
                "OK":          "background-color:#d1fae5; color:#065f46; font-weight:600",
                "ADVERTENCIA": "background-color:#fef3c7; color:#78350f; font-weight:600",
                "RECHAZO":     "background-color:#fee2e2; color:#7f1d1d; font-weight:600",
            }.get(val, "")

        st.dataframe(df.style.applymap(_color, subset=["Resultado"]),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No hay controles registrados en los últimos 7 días.")

    # ── Footer ──────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center; color:#94a3b8; font-size:0.75rem;'>"
        f"🔬 SGC Laboratorio Clínico &nbsp;·&nbsp; Westgard · EP15-A3 · Control Externo "
        f"&nbsp;·&nbsp; {hoy}</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
