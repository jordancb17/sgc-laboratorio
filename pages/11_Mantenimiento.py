"""
Bitácora de Mantenimiento de Equipos — preventivo, correctivo y verificaciones.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.database import init_db, get_session
from database import crud
from database.models import TIPOS_MANTENIMIENTO, RESULTADOS_MANTENIMIENTO
from modules.page_utils import setup_page, page_header

st.set_page_config(page_title="Mantenimiento", page_icon="🔩", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="🔩",
        title="Bitácora de Mantenimiento de Equipos",
        subtitle="Registro de mantenimientos preventivos, correctivos y verificaciones por equipo",
        badge="Mantenimiento y Confiabilidad",
    )

    db = get_session()
    try:
        tab_reg, tab_hist, tab_prox = st.tabs([
            "📝 Registrar Mantenimiento", "📋 Historial", "⏰ Próximos Mantenimientos"
        ])
        with tab_reg:
            _tab_registro(db)
        with tab_hist:
            _tab_historial(db)
        with tab_prox:
            _tab_proximos(db)
    finally:
        db.close()


def _tab_registro(db):
    st.markdown("#### Nuevo Mantenimiento")

    equipos = crud.listar_equipos(db)
    if not equipos:
        st.warning("No hay equipos registrados.")
        return

    personal = crud.listar_personal(db)

    with st.form("form_mantenimiento"):
        col1, col2 = st.columns(2)
        eq_opts    = {f"{e.area.nombre} › {e.nombre} [{e.marca or '—'}]": e.id for e in equipos}
        pers_opts  = {f"{p.apellido}, {p.nombre}": p.id for p in personal} if personal else {}

        equipo_sel = col1.selectbox("Equipo / Analizador *", list(eq_opts.keys()))
        tipo_sel   = col2.selectbox("Tipo de mantenimiento *", TIPOS_MANTENIMIENTO)

        col3, col4 = st.columns(2)
        fecha_mant = col3.date_input("Fecha *", value=date.today(), max_value=date.today())
        resultado  = col4.selectbox("Resultado *", RESULTADOS_MANTENIMIENTO)

        descripcion = st.text_area(
            "Descripción del mantenimiento *", height=100,
            placeholder="Describa detalladamente las actividades realizadas: partes cambiadas, "
                        "limpiezas, ajustes, verificaciones, etc."
        )

        col5, col6 = st.columns(2)
        prox_fecha = col5.date_input("Próximo mantenimiento programado",
                                     value=date.today() + timedelta(days=30),
                                     min_value=date.today())
        pers_sel = None
        if pers_opts:
            pers_label = col6.selectbox("Responsable", list(pers_opts.keys()), key="mant_pers")
            pers_sel = pers_opts[pers_label]

        submitted = st.form_submit_button("💾 Guardar Mantenimiento", type="primary", use_container_width=True)
        if submitted:
            if not descripcion.strip():
                st.error("La descripción es obligatoria.")
            else:
                try:
                    crud.registrar_mantenimiento(
                        db=db,
                        equipo_id=eq_opts[equipo_sel],
                        personal_id=pers_sel,
                        fecha=fecha_mant,
                        tipo=tipo_sel,
                        descripcion=descripcion,
                        resultado=resultado,
                        proxima_fecha=prox_fecha,
                    )
                    st.success(f"✅ Mantenimiento registrado — **{resultado}**.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def _tab_historial(db):
    st.markdown("#### Historial de Mantenimientos")

    equipos = crud.listar_equipos(db)
    if not equipos:
        st.info("No hay equipos registrados.")
        return

    col1, col2, col3 = st.columns(3)
    eq_opts = {"Todos los equipos": None} | {
        f"{e.area.nombre} › {e.nombre}": e.id for e in equipos
    }
    eq_sel  = col1.selectbox("Filtrar por equipo", list(eq_opts.keys()), key="hist_mant_eq")
    f_desde = col2.date_input("Desde", value=date.today() - timedelta(days=90), key="hist_mant_desde")
    f_hasta = col3.date_input("Hasta", value=date.today(), key="hist_mant_hasta")

    mantenimientos = crud.listar_mantenimientos(
        db, equipo_id=eq_opts[eq_sel], fecha_desde=f_desde, fecha_hasta=f_hasta
    )

    if not mantenimientos:
        st.info("No hay mantenimientos registrados en el período seleccionado.")
        return

    completados = sum(1 for m in mantenimientos if m.resultado == "COMPLETADO")
    pendientes  = sum(1 for m in mantenimientos if "PENDIENTE" in m.resultado)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(mantenimientos))
    c2.metric("✅ Completados", completados)
    c3.metric("⚠️ Pendientes / En proceso", pendientes)

    filas = []
    for m in mantenimientos:
        dias_prox = (m.proxima_fecha - date.today()).days if m.proxima_fecha else None
        filas.append({
            "Fecha": m.fecha.strftime("%d/%m/%Y"),
            "Equipo": m.equipo.nombre,
            "Área": m.equipo.area.nombre,
            "Tipo": m.tipo,
            "Descripción": (m.descripcion or "")[:70],
            "Resultado": m.resultado,
            "Próximo": m.proxima_fecha.strftime("%d/%m/%Y") if m.proxima_fecha else "—",
            "Días restantes": dias_prox if dias_prox is not None else "—",
            "Responsable": f"{m.personal.apellido}, {m.personal.nombre}" if m.personal else "—",
        })

    df = pd.DataFrame(filas)

    def _color(val):
        if val == "COMPLETADO":              return "background-color:#d1fae5;color:#065f46;font-weight:700"
        if "PENDIENTE" in str(val):          return "background-color:#fef3c7;color:#78350f;font-weight:600"
        if "EN PROCESO" in str(val):         return "background-color:#dbeafe;color:#1e40af;font-weight:600"
        return ""

    st.dataframe(df.style.applymap(_color, subset=["Resultado"]),
                 use_container_width=True, hide_index=True)

    buf = _to_excel(df)
    st.download_button("📥 Exportar a Excel", data=buf,
                       file_name=f"mantenimiento_{date.today()}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _tab_proximos(db):
    st.markdown("#### Mantenimientos Próximos (30 días)")

    proximos = crud.proximos_mantenimientos(db, dias=30)

    if not proximos:
        st.success("✅ No hay mantenimientos programados en los próximos 30 días.")
        return

    hoy = date.today()
    for m in proximos:
        if not m.proxima_fecha:
            continue
        dias = (m.proxima_fecha - hoy).days
        color = "#dc2626" if dias <= 7 else "#d97706" if dias <= 14 else "#2563eb"
        icono = "🔴" if dias <= 7 else "🟡" if dias <= 14 else "🔵"
        st.markdown(
            f"{icono} **{m.equipo.area.nombre} › {m.equipo.nombre}** — "
            f"Tipo: *{m.tipo}* — Fecha: `{m.proxima_fecha}` — "
            f"<span style='color:{color};font-weight:700'>{dias} día(s)</span>",
            unsafe_allow_html=True,
        )


def _to_excel(df: pd.DataFrame) -> bytes:
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Mantenimiento")
    return buf.getvalue()


if __name__ == "__main__":
    main()
