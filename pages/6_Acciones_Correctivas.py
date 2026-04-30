"""
Página de Acciones Correctivas:
  - Lista de rechazos sin acción registrada (pendientes)
  - Registro de acción correctiva
  - Historial y seguimiento
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from database.database import init_db, get_session
from database import crud
from database.models import CAUSAS_PROBABLES, RESULTADOS_AC
from modules.page_utils import setup_page

st.set_page_config(page_title="Acciones Correctivas", page_icon="🔧", layout="wide")
init_db()
setup_page()


def main():
    st.title("🔧 Acciones Correctivas")

    db = get_session()
    try:
        tab_pend, tab_reg, tab_historial = st.tabs([
            "⚠️ Pendientes", "📝 Registrar Acción", "📋 Historial"
        ])
        with tab_pend:
            _tab_pendientes(db)
        with tab_reg:
            _tab_registrar(db)
        with tab_historial:
            _tab_historial(db)
    finally:
        db.close()


# ─── PENDIENTES ───────────────────────────────────────────────────────────────

def _tab_pendientes(db):
    st.subheader("Rechazos sin Acción Correctiva Registrada")

    sin_ac = crud.controles_sin_accion_correctiva(db)
    if not sin_ac:
        st.success("✅ No hay rechazos pendientes de acción correctiva.")
        return

    st.error(f"**{len(sin_ac)} rechazo(s) requieren acción correctiva.**")

    filas = []
    for c in sin_ac:
        mat = c.material
        dias = (date.today() - c.fecha).days
        filas.append({
            "ID Control": c.id,
            "Fecha": c.fecha,
            "Días pendiente": dias,
            "Área": mat.equipo.area.nombre,
            "Equipo": mat.equipo.nombre,
            "Analito": mat.analito,
            "Nivel": c.nivel_lote.nivel,
            "Valor": c.valor,
            "z-score": round(c.zscore, 3) if c.zscore else "",
            "Regla": c.regla_violada or "—",
            "Turno": c.turno or "—",
            "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
        })

    df = pd.DataFrame(filas)

    def _color_dias(val):
        if isinstance(val, int):
            if val > 7: return "background-color:#fee2e2; color:#7f1d1d; font-weight:bold"
            if val > 3: return "background-color:#fff3cd; color:#78350f"
        return ""

    st.dataframe(df.style.applymap(_color_dias, subset=["Días pendiente"]),
                 use_container_width=True, hide_index=True)

    st.info("👉 Vaya a la pestaña **Registrar Acción** para documentar la acción correctiva.")


# ─── REGISTRAR ────────────────────────────────────────────────────────────────

def _tab_registrar(db):
    st.subheader("Registrar Acción Correctiva")

    sin_ac = crud.controles_sin_accion_correctiva(db)
    personal = crud.listar_personal(db)

    if not personal:
        st.warning("No hay personal configurado.")
        return

    pers_opts = {f"{p.apellido}, {p.nombre}": p.id for p in personal}

    # Selector de control rechazado
    if sin_ac:
        ctrl_opts = {
            f"[{c.fecha}] {c.material.analito} Nv{c.nivel_lote.nivel} — {c.material.equipo.nombre} (z={c.zscore:.2f}, Regla:{c.regla_violada})": c.id
            for c in sin_ac
        }
        st.markdown("**Seleccione un rechazo pendiente o ingrese el ID manualmente:**")
        ctrl_sel = st.selectbox("Rechazo pendiente", ["(Ingresar ID manual)"] + list(ctrl_opts.keys()))
        if ctrl_sel != "(Ingresar ID manual)":
            ctrl_id = ctrl_opts[ctrl_sel]
        else:
            ctrl_id = st.number_input("ID del control rechazado", min_value=1, step=1)
    else:
        st.info("No hay rechazos pendientes. Ingrese el ID manualmente si desea actualizar una acción.")
        ctrl_id = st.number_input("ID del control", min_value=1, step=1)

    # Mostrar info del control seleccionado
    if ctrl_id:
        ctrl = db.query(__import__('database.models', fromlist=['ControlDiario']).ControlDiario).filter_by(id=int(ctrl_id)).first()
        if ctrl:
            mat = ctrl.material
            st.markdown(f"""
            <div style="background:#fef2f2; border-left:4px solid #dc2626; border-radius:8px; padding:12px 16px; margin:8px 0;">
                <b>❌ Control rechazado</b> —
                {mat.equipo.area.nombre} › {mat.equipo.nombre} › <b>{mat.analito}</b>
                Nivel {ctrl.nivel_lote.nivel} &nbsp;|&nbsp;
                Valor: <b>{ctrl.valor}</b> {mat.unidad or ''} &nbsp;|&nbsp;
                z = {ctrl.zscore:.3f} &nbsp;|&nbsp;
                Regla: <b>{ctrl.regla_violada}</b> &nbsp;|&nbsp;
                {ctrl.fecha} {ctrl.hora.strftime("%H:%M")}
            </div>
            """, unsafe_allow_html=True)

            ac_existente = crud.get_accion_correctiva_por_control(db, int(ctrl_id))
            if ac_existente:
                st.warning(f"⚠️ Ya existe una acción registrada (estado: **{ac_existente.resultado}**). Se actualizará si guarda.")

    with st.form("form_ac"):
        col1, col2 = st.columns(2)
        pers_sel = col1.selectbox("Personal que registra *", list(pers_opts.keys()))
        resultado_sel = col2.selectbox("Estado de la acción *", RESULTADOS_AC)

        causa = st.selectbox("Causa probable *", CAUSAS_PROBABLES)
        accion = st.text_area("Acción tomada * (descripción detallada)", height=100,
                              placeholder="Describa qué se hizo para corregir el problema...")
        col1, col2 = st.columns(2)
        req_rep = col1.checkbox("¿Requiere repetición del control?", value=True)
        fecha_ac = col2.date_input("Fecha de la acción", value=date.today())
        hora_ac = col1.time_input("Hora de la acción", value=datetime.now().time().replace(second=0, microsecond=0))
        obs = st.text_area("Observaciones adicionales", height=60)

        if st.form_submit_button("💾 Guardar Acción Correctiva", type="primary"):
            if not accion.strip():
                st.error("La descripción de la acción es obligatoria.")
            else:
                ac, err = crud.registrar_accion_correctiva(
                    db=db,
                    control_id=int(ctrl_id),
                    personal_id=pers_opts[pers_sel],
                    fecha=fecha_ac,
                    hora=hora_ac,
                    causa_probable=causa,
                    accion_tomada=accion,
                    resultado=resultado_sel,
                    requiere_repeticion=req_rep,
                    observaciones=obs,
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"✅ Acción correctiva registrada. Estado: **{ac.resultado}**")
                    st.rerun()


# ─── HISTORIAL ────────────────────────────────────────────────────────────────

def _tab_historial(db):
    st.subheader("Historial de Acciones Correctivas")

    col1, col2, col3 = st.columns(3)
    resultado_f = col1.selectbox("Filtrar por estado", ["Todos"] + RESULTADOS_AC)
    fecha_desde = col2.date_input("Desde", value=date.today() - timedelta(days=90))
    fecha_hasta = col3.date_input("Hasta", value=date.today())

    acciones = crud.listar_acciones_correctivas(
        db,
        resultado=None if resultado_f == "Todos" else resultado_f,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )

    if not acciones:
        st.info("No hay acciones correctivas en ese período.")
        return

    filas = []
    for ac in acciones:
        ctrl = ac.control
        mat = ctrl.material
        filas.append({
            "ID AC": ac.id,
            "Fecha AC": ac.fecha,
            "Área": mat.equipo.area.nombre,
            "Analito": mat.analito,
            "Nivel": ctrl.nivel_lote.nivel,
            "Regla": ctrl.regla_violada or "—",
            "Causa": ac.causa_probable or "—",
            "Acción": (ac.accion_tomada or "")[:60] + ("…" if len(ac.accion_tomada or "") > 60 else ""),
            "Estado": ac.resultado,
            "Rep. control": "Sí" if ac.requiere_repeticion_control else "No",
            "Personal": f"{ac.personal.apellido}, {ac.personal.nombre}",
        })

    df = pd.DataFrame(filas)

    def _color_estado(val):
        return {
            "RESUELTO": "background-color:#d4edda; color:#155724",
            "PENDIENTE": "background-color:#fff3cd; color:#856404",
            "ESCALADO A SUPERVISIÓN": "background-color:#f8d7da; color:#721c24",
        }.get(val, "")

    st.dataframe(df.style.applymap(_color_estado, subset=["Estado"]),
                 use_container_width=True, hide_index=True)

    # KPIs
    total = len(acciones)
    resueltas = sum(1 for a in acciones if a.resultado == "RESUELTO")
    pendientes = sum(1 for a in acciones if a.resultado == "PENDIENTE")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total acciones", total)
    col2.metric("✅ Resueltas", resueltas)
    col3.metric("⏳ Pendientes", pendientes)

    try:
        import io
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("⬇️ Descargar Excel", buf.getvalue(), "acciones_correctivas.xlsx")
    except Exception:
        pass


if __name__ == "__main__":
    main()
