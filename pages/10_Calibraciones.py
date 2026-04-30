"""
Registro de Calibraciones por equipo — trazabilidad requerida por ISO 15189.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.database import init_db, get_session
from database import crud
from database.models import TIPOS_CALIBRACION, RESULTADOS_CALIBRACION
from modules.page_utils import setup_page, page_header

st.set_page_config(page_title="Calibraciones", page_icon="🎯", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="🎯",
        title="Registro de Calibraciones",
        subtitle="Trazabilidad de calibraciones por equipo — requerido por ISO 15189 / CLIA",
        badge="Trazabilidad Metrológica",
    )

    db = get_session()
    try:
        tab_reg, tab_hist, tab_prox = st.tabs([
            "📝 Registrar Calibración", "📋 Historial", "⏰ Próximas Calibraciones"
        ])
        with tab_reg:
            _tab_registro(db)
        with tab_hist:
            _tab_historial(db)
        with tab_prox:
            _tab_proximas(db)
    finally:
        db.close()


def _tab_registro(db):
    st.markdown("#### Nueva Calibración")
    st.caption("Complete los datos de la calibración realizada.")

    equipos = crud.listar_equipos(db)
    if not equipos:
        st.warning("No hay equipos registrados.")
        return

    personal = crud.listar_personal(db)

    with st.form("form_calibracion"):
        col1, col2 = st.columns(2)

        eq_opts   = {f"{e.area.nombre} › {e.nombre} [{e.marca or '—'}]": e.id for e in equipos}
        pers_opts = {f"{p.apellido}, {p.nombre}": p.id for p in personal} if personal else {}

        equipo_sel = col1.selectbox("Equipo / Analizador *", list(eq_opts.keys()))
        tipo_sel   = col2.selectbox("Tipo de calibración *", TIPOS_CALIBRACION)

        col3, col4 = st.columns(2)
        fecha_cal  = col3.date_input("Fecha de calibración *", value=date.today(), max_value=date.today())
        resultado  = col4.selectbox("Resultado *", RESULTADOS_CALIBRACION)

        col5, col6 = st.columns(2)
        lote_cal   = col5.text_input("Lote del calibrador", placeholder="ej. LOT-CAL-2024-001")
        prox_fecha = col6.date_input("Próxima calibración programada",
                                     value=date.today() + timedelta(days=30),
                                     min_value=date.today())

        pers_sel = None
        if pers_opts:
            pers_label = col1.selectbox("Responsable", list(pers_opts.keys()), key="cal_pers")
            pers_sel = pers_opts[pers_label]

        obs = st.text_area("Observaciones / Acciones tomadas", height=90,
                           placeholder="Describa cualquier incidencia, parámetros obtenidos o acciones realizadas")

        submitted = st.form_submit_button("💾 Guardar Calibración", type="primary", use_container_width=True)
        if submitted:
            try:
                crud.registrar_calibracion(
                    db=db,
                    equipo_id=eq_opts[equipo_sel],
                    personal_id=pers_sel,
                    fecha=fecha_cal,
                    tipo=tipo_sel,
                    lote_calibrador=lote_cal,
                    resultado=resultado,
                    observaciones=obs,
                    proxima_calibracion=prox_fecha,
                )
                icon = "✅" if resultado == "APROBADA" else "❌"
                st.success(f"{icon} Calibración registrada — **{resultado}**.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


def _tab_historial(db):
    st.markdown("#### Historial de Calibraciones")

    equipos = crud.listar_equipos(db)
    if not equipos:
        st.info("No hay equipos registrados.")
        return

    col1, col2, col3 = st.columns(3)
    eq_opts = {"Todos los equipos": None} | {
        f"{e.area.nombre} › {e.nombre}": e.id for e in equipos
    }
    eq_sel = col1.selectbox("Filtrar por equipo", list(eq_opts.keys()), key="hist_cal_eq")
    f_desde = col2.date_input("Desde", value=date.today() - timedelta(days=90), key="hist_cal_desde")
    f_hasta = col3.date_input("Hasta", value=date.today(), key="hist_cal_hasta")

    calibraciones = crud.listar_calibraciones(
        db, equipo_id=eq_opts[eq_sel], fecha_desde=f_desde, fecha_hasta=f_hasta
    )

    if not calibraciones:
        st.info("No hay calibraciones registradas en el período seleccionado.")
        return

    aprobadas = sum(1 for c in calibraciones if c.resultado == "APROBADA")
    rechazadas = sum(1 for c in calibraciones if c.resultado == "RECHAZADA")
    col_a, col_r, col_t = st.columns(3)
    col_a.metric("✅ Aprobadas", aprobadas)
    col_r.metric("❌ Rechazadas", rechazadas)
    col_t.metric("Total", len(calibraciones))

    filas = []
    for c in calibraciones:
        filas.append({
            "Fecha": c.fecha.strftime("%d/%m/%Y"),
            "Equipo": c.equipo.nombre,
            "Área": c.equipo.area.nombre,
            "Tipo": c.tipo,
            "Lote calibrador": c.lote_calibrador or "—",
            "Resultado": c.resultado,
            "Próxima": c.proxima_calibracion.strftime("%d/%m/%Y") if c.proxima_calibracion else "—",
            "Responsable": f"{c.personal.apellido}, {c.personal.nombre}" if c.personal else "—",
            "Observaciones": (c.observaciones or "")[:60],
        })

    df = pd.DataFrame(filas)

    def _color(val):
        if val == "APROBADA":   return "background-color:#d1fae5;color:#065f46;font-weight:700"
        if val == "RECHAZADA":  return "background-color:#fee2e2;color:#7f1d1d;font-weight:700"
        return "background-color:#fef3c7;color:#78350f;font-weight:600"

    st.dataframe(df.style.applymap(_color, subset=["Resultado"]),
                 use_container_width=True, hide_index=True)

    # Excel export
    buf = _to_excel(df)
    st.download_button("📥 Exportar a Excel", data=buf,
                       file_name=f"calibraciones_{date.today()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _tab_proximas(db):
    st.markdown("#### Calibraciones Próximas (30 días)")

    proximas = crud.proximas_calibraciones(db, dias=30)

    if not proximas:
        st.success("✅ No hay calibraciones programadas en los próximos 30 días.")
        return

    hoy = date.today()
    for c in proximas:
        dias = (c.proxima_calibracion - hoy).days
        color = "#dc2626" if dias <= 7 else "#d97706" if dias <= 14 else "#2563eb"
        icono = "🔴" if dias <= 7 else "🟡" if dias <= 14 else "🔵"
        st.markdown(
            f"{icono} **{c.equipo.area.nombre} › {c.equipo.nombre}** — "
            f"Próxima calibración: `{c.proxima_calibracion}` — "
            f"<span style='color:{color};font-weight:700'>{dias} día(s)</span>",
            unsafe_allow_html=True,
        )


def _to_excel(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Calibraciones")
    return buf.getvalue()


if __name__ == "__main__":
    main()
