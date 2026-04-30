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
    st.title("🔬 Dashboard — Control de Calidad")

    db = get_session()
    try:
        _dashboard(db)
    finally:
        db.close()


def _dashboard(db):
    hoy = date.today()

    # Filtro por área
    areas = crud.listar_areas(db)
    area_opts = {"Todas las áreas": None} | {a.nombre: a.id for a in areas}
    area_sel = st.selectbox("Filtrar por área", list(area_opts.keys()), key="dash_area")
    area_id_fil = area_opts[area_sel]

    controles_hoy_all = crud.listar_controles_diarios(db, fecha_desde=hoy, fecha_hasta=hoy)
    if area_id_fil is not None:
        controles_hoy = [c for c in controles_hoy_all if c.material.equipo.area_id == area_id_fil]
    else:
        controles_hoy = controles_hoy_all
    rechazos_hoy  = [c for c in controles_hoy if c.resultado == "RECHAZO"]
    advert_hoy    = [c for c in controles_hoy if c.resultado == "ADVERTENCIA"]
    lotes_vencer  = crud.lotes_por_vencer(db, dias=30)

    # ── KPIs ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Controles hoy", len(controles_hoy))
    col2.metric("❌ Rechazos hoy",    len(rechazos_hoy),
                delta=f"{len(rechazos_hoy)} rechazo(s)" if rechazos_hoy else None,
                delta_color="inverse")
    col3.metric("⚠️ Advertencias hoy", len(advert_hoy))
    col4.metric("📦 Lotes por vencer", len(lotes_vencer),
                help="Lotes que vencen en los próximos 30 días")

    st.markdown("---")

    # ── Alertas ───────────────────────────────────────────────────────────
    if rechazos_hoy:
        st.error(f"🛑 **{len(rechazos_hoy)} RECHAZO(S) HOY** — Tome acción correctiva antes de liberar resultados.")
        for c in rechazos_hoy:
            mat = c.material
            st.markdown(
                f"&nbsp;&nbsp;&nbsp;• **{mat.equipo.area.nombre} › {mat.equipo.nombre} › {mat.analito}** "
                f"(Nivel {c.nivel_lote.nivel}) — Regla `{c.regla_violada}` — "
                f"Valor: **{c.valor}** {mat.unidad or ''} &nbsp;(z = {c.zscore:.2f})"
            )

    if advert_hoy:
        st.warning(f"⚠️ **{len(advert_hoy)} advertencia(s) hoy** — Regla 1-2s. Monitoree la tendencia.")

    if lotes_vencer:
        with st.expander(f"📦 {len(lotes_vencer)} lote(s) próximos a vencer (30 días)", expanded=bool(lotes_vencer)):
            for lote in lotes_vencer:
                dias_rest = (lote.fecha_vencimiento - hoy).days
                mat = lote.material
                color = "#dc2626" if dias_rest <= 7 else "#d97706" if dias_rest <= 14 else "#2563eb"
                st.markdown(
                    f"<span style='color:{color}; font-weight:600;'>●</span> "
                    f"**{mat.equipo.area.nombre} › {mat.equipo.nombre} › {mat.analito}** — "
                    f"Lote `{lote.numero_lote}` — vence `{lote.fecha_vencimiento}` "
                    f"(<b>{dias_rest} día(s)</b>)",
                    unsafe_allow_html=True,
                )

    if not rechazos_hoy and not advert_hoy:
        st.success("✅ Todos los controles del día dentro de los límites de aceptación.")

    st.markdown("---")

    # ── Gráfico resumen 7 días ────────────────────────────────────────────
    st.subheader("Resumen — Últimos 7 días")

    fecha_desde = hoy - timedelta(days=6)
    controles_sem = crud.listar_controles_diarios(db, fecha_desde=fecha_desde, fecha_hasta=hoy)

    if controles_sem:
        import plotly.graph_objects as go
        from collections import defaultdict

        por_dia: dict = defaultdict(lambda: {"OK": 0, "ADVERTENCIA": 0, "RECHAZO": 0})
        for c in controles_sem:
            por_dia[str(c.fecha)][c.resultado] = por_dia[str(c.fecha)].get(c.resultado, 0) + 1

        dias_labels = sorted(por_dia.keys())
        oks   = [por_dia[d].get("OK", 0)          for d in dias_labels]
        warns = [por_dia[d].get("ADVERTENCIA", 0)  for d in dias_labels]
        rejs  = [por_dia[d].get("RECHAZO", 0)      for d in dias_labels]

        fig = go.Figure(data=[
            go.Bar(name="✅ OK",          x=dias_labels, y=oks,   marker_color="#16a34a"),
            go.Bar(name="⚠️ Advertencia", x=dias_labels, y=warns, marker_color="#d97706"),
            go.Bar(name="❌ Rechazo",     x=dias_labels, y=rejs,  marker_color="#dc2626"),
        ])
        fig.update_layout(
            barmode="stack",
            height=280,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(gridcolor="#f1f5f9"),
            yaxis=dict(gridcolor="#f1f5f9", title="N° controles"),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        # Tabla compacta
        import pandas as pd
        filas = []
        for c in controles_sem:
            mat = c.material
            filas.append({
                "Fecha": c.fecha,
                "Hora": c.hora.strftime("%H:%M"),
                "Área": mat.equipo.area.nombre,
                "Equipo": mat.equipo.nombre,
                "Analito": mat.analito,
                "Nv": c.nivel_lote.nivel,
                "Valor": c.valor,
                "U": mat.unidad or "",
                "z": f"{c.zscore:.2f}" if c.zscore is not None else "",
                "Resultado": c.resultado,
                "Regla": c.regla_violada or "—",
                "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
            })
        df = pd.DataFrame(filas)

        def _color(val):
            return {
                "OK": "background-color:#d4edda; color:#155724",
                "ADVERTENCIA": "background-color:#fff3cd; color:#856404",
                "RECHAZO": "background-color:#f8d7da; color:#721c24",
            }.get(val, "")

        st.dataframe(
            df.style.applymap(_color, subset=["Resultado"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hay controles registrados en los últimos 7 días.")

    st.markdown("---")
    st.caption(
        f"🔬 SGC Laboratorio Clínico &nbsp;·&nbsp; "
        f"Westgard · EP15-A3 · Control Externo &nbsp;·&nbsp; "
        f"Base de datos: `lab_qms/data/lab_qms.db` &nbsp;·&nbsp; {hoy}"
    )


if __name__ == "__main__":
    main()
