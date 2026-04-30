"""
Controles Diarios: registro con turno, Westgard en tiempo real,
alerta de email automática en rechazo y regularización retroactiva.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date, time, datetime, timedelta

from database.database import init_db, get_session
from database import crud
from database.models import NivelLote, TURNOS
from modules.westgard import evaluar_westgard, emoji_resultado, color_resultado, RESULTADO_RECHAZO, RESULTADO_ADVERTENCIA
from modules.email_alerts import alerta_rechazo
from modules.page_utils import setup_page

st.set_page_config(page_title="Controles Diarios", page_icon="📋", layout="wide")
init_db()
setup_page()


def main():
    st.title("📋 Controles Diarios de Calidad")
    tab_reg, tab_consulta, tab_retro = st.tabs([
        "📝 Registrar Control", "🔍 Consultar / Historial", "🕐 Regularización (Retroactivo)"
    ])
    db = get_session()
    try:
        with tab_reg:
            _tab_registrar(db, es_retroactivo=False)
        with tab_consulta:
            _tab_consulta(db)
        with tab_retro:
            _tab_registrar(db, es_retroactivo=True)
    finally:
        db.close()


# ─── FORMULARIO DE REGISTRO ───────────────────────────────────────────────────

def _tab_registrar(db, es_retroactivo: bool):
    if es_retroactivo:
        st.subheader("🕐 Regularización — Registro Retroactivo")
        st.info("Use esta sección para registrar controles de días pasados. "
                "El sistema verificará que no exista un duplicado exacto en esa fecha/hora.")
    else:
        st.subheader("Registrar Control del Día")

    suf = "_r" if es_retroactivo else ""

    # ── Selección jerárquica ─────────────────────────────────────────────────
    areas = crud.listar_areas(db)
    if not areas:
        st.warning("No hay áreas configuradas. Vaya a ⚙️ Configuración.")
        return

    col1, col2, col3 = st.columns(3)
    area_opts = {a.nombre: a.id for a in areas}
    area_sel = col1.selectbox("Área *", list(area_opts.keys()), key=f"area{suf}")

    equipos = crud.listar_equipos(db, area_id=area_opts[area_sel])
    if not equipos:
        col2.warning("Sin equipos en esta área.")
        return
    eq_opts = {e.nombre: e.id for e in equipos}
    eq_sel = col2.selectbox("Equipo *", list(eq_opts.keys()), key=f"eq{suf}")

    materiales = crud.listar_materiales(db, equipo_id=eq_opts[eq_sel])
    if not materiales:
        col3.warning("Sin analitos en este equipo.")
        return
    mat_opts = {f"{m.analito} [{m.proveedor}]": m.id for m in materiales}
    mat_sel = col3.selectbox("Analito *", list(mat_opts.keys()), key=f"mat{suf}")

    material_id = mat_opts[mat_sel]
    material = next(m for m in materiales if m.id == material_id)

    # ── Lote activo ──────────────────────────────────────────────────────────
    lote = crud.get_lote_activo(db, material_id)
    if not lote:
        st.error("Este analito no tiene lote activo vigente. Registre un lote en ⚙️ Configuración.")
        return
    if lote.fecha_vencimiento < date.today():
        st.error("⚠️ El lote está VENCIDO.")
        return

    st.info(f"**Lote activo:** `{lote.numero_lote}` — Vence: `{lote.fecha_vencimiento}`")

    # ── Nivel ────────────────────────────────────────────────────────────────
    niveles_disponibles = {f"Nivel {nv.nivel}": nv.id for nv in lote.niveles}
    if not niveles_disponibles:
        st.error("El lote no tiene niveles configurados.")
        return

    col1, col2 = st.columns(2)
    nivel_sel = col1.selectbox("Nivel de control *", list(niveles_disponibles.keys()), key=f"nivel{suf}")
    nivel_lote_id = niveles_disponibles[nivel_sel]
    nivel_lote: NivelLote = next(nv for nv in lote.niveles if nv.id == nivel_lote_id)
    col2.markdown(
        f"**Referencia** — X̄: `{nivel_lote.media}` | s: `{nivel_lote.de}` | "
        f"Rango: `{nivel_lote.valor_minimo}` – `{nivel_lote.valor_maximo}` {material.unidad or ''}"
    )

    # ── Fecha / hora / turno / personal ─────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    if es_retroactivo:
        fecha_ctrl = col1.date_input("Fecha *", value=date.today() - timedelta(days=1),
                                     max_value=date.today(), key=f"fecha{suf}")
    else:
        fecha_ctrl = col1.date_input("Fecha *", value=date.today(),
                                     max_value=date.today(), key=f"fecha{suf}")
    hora_ctrl = col2.time_input("Hora *",
                                value=datetime.now().time().replace(second=0, microsecond=0),
                                key=f"hora{suf}")
    turno_sel = col3.selectbox("Turno *", TURNOS, key=f"turno{suf}")

    personal = crud.listar_personal(db)
    if not personal:
        st.warning("No hay personal configurado.")
        return
    pers_opts = {f"{p.apellido}, {p.nombre}": p.id for p in personal}
    pers_sel = col4.selectbox("Personal *", list(pers_opts.keys()), key=f"pers{suf}")

    # ── Valor medido ──────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 2])
    valor = col1.number_input(
        f"Valor medido ({material.unidad or 'u'}) *",
        format="%.4f", step=0.01, key=f"valor{suf}"
    )
    comentario = col2.text_area("Comentario (opcional)", height=68, key=f"coment{suf}")

    # ── Preview Westgard en tiempo real ──────────────────────────────────────
    if valor != 0.0:
        hist = crud.historial_zscores(db, nivel_lote_id)
        otros = crud.zscores_mismo_run(db, material_id, fecha_ctrl, hora_ctrl, nivel_lote.nivel, lote.id)
        preview = evaluar_westgard(valor, nivel_lote.media, nivel_lote.de, hist, otros or None)
        color = color_resultado(preview.resultado)
        wg_class = {"OK": "wg-ok", "ADVERTENCIA": "wg-warn", "RECHAZO": "wg-rej"}.get(preview.resultado, "wg-ok")
        st.markdown(
            f'<div class="wg-box {wg_class}">'
            f'<b>{emoji_resultado(preview.resultado)} Westgard (preview):</b> {preview.resultado}'
            + (f' — Regla <code>{preview.regla_violada}</code>' if preview.regla_violada else '')
            + f'<br><small>z-score: <b>{preview.zscore:.3f}</b> &nbsp;·&nbsp; {preview.descripcion}</small>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

    # ── Guardar ───────────────────────────────────────────────────────────────
    if st.button("💾 Guardar Control", key=f"btn{suf}", type="primary"):
        if valor == 0.0:
            st.error("Ingrese el valor medido (distinto de cero).")
        else:
            control, err = crud.registrar_control_diario(
                db=db,
                material_id=material_id,
                lote_id=lote.id,
                nivel_lote_id=nivel_lote_id,
                personal_id=pers_opts[pers_sel],
                fecha=fecha_ctrl,
                hora=hora_ctrl,
                valor=valor,
                comentario=comentario,
                es_retroactivo=es_retroactivo,
                turno=turno_sel,
            )
            if err:
                st.error(f"⚠️ {err}")
            else:
                em = emoji_resultado(control.resultado)
                st.success(
                    f"{em} Control guardado. **{control.resultado}**"
                    + (f" — Regla `{control.regla_violada}`" if control.regla_violada else "")
                    + f"  (z = {control.zscore:.3f})"
                )
                if control.resultado == RESULTADO_RECHAZO:
                    st.error("🛑 **RECHAZO**: No libere resultados de pacientes hasta registrar la acción correctiva.")
                    # Enviar alerta por email
                    pers_obj = next(p for p in personal if p.id == pers_opts[pers_sel])
                    ok_mail, msg_mail = alerta_rechazo(
                        analito=material.analito,
                        area=material.equipo.area.nombre,
                        equipo=material.equipo.nombre,
                        nivel=nivel_lote.nivel,
                        valor=valor,
                        unidad=material.unidad or "",
                        zscore=control.zscore,
                        regla=control.regla_violada or "—",
                        personal=f"{pers_obj.apellido}, {pers_obj.nombre}",
                        fecha=fecha_ctrl,
                        hora=hora_ctrl,
                    )
                    if ok_mail:
                        st.info(f"📧 {msg_mail}")
                    st.markdown("👉 Registre la acción correctiva en la página **🔧 Acciones Correctivas**.")
                elif control.resultado == RESULTADO_ADVERTENCIA:
                    st.warning("⚠️ **ADVERTENCIA 1-2s**: Monitoree la tendencia en el próximo control.")


# ─── CONSULTA / HISTORIAL ─────────────────────────────────────────────────────

def _tab_consulta(db):
    st.subheader("Historial de Controles")

    col1, col2, col3, col4 = st.columns(4)
    areas = crud.listar_areas(db)
    area_opts = {"Todas": None} | {a.nombre: a.id for a in areas}
    area_f = col1.selectbox("Área", list(area_opts.keys()), key="cf_area")
    equipos_f = crud.listar_equipos(db, area_id=area_opts[area_f])
    eq_opts_f = {"Todos": None} | {e.nombre: e.id for e in equipos_f}
    eq_f = col2.selectbox("Equipo", list(eq_opts_f.keys()), key="cf_eq")
    mats_f = crud.listar_materiales(db, equipo_id=eq_opts_f[eq_f])
    mat_opts_f = {"Todos": None} | {m.analito: m.id for m in mats_f}
    mat_f = col3.selectbox("Analito", list(mat_opts_f.keys()), key="cf_mat")
    nivel_f = col4.selectbox("Nivel", ["Todos", 1, 2, 3], key="cf_nivel")

    col1, col2 = st.columns(2)
    fecha_desde = col1.date_input("Desde", value=date.today() - timedelta(days=30), key="cf_desde")
    fecha_hasta = col2.date_input("Hasta", value=date.today(), key="cf_hasta")

    controles = crud.listar_controles_diarios(
        db,
        material_id=mat_opts_f[mat_f],
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        nivel=None if nivel_f == "Todos" else int(nivel_f),
    )
    if mat_opts_f[mat_f] is None and eq_opts_f[eq_f] is not None:
        ids_mat = {m.id for m in mats_f}
        controles = [c for c in controles if c.material_id in ids_mat]

    if not controles:
        st.info("No hay controles con estos filtros.")
        return

    filas = []
    for c in controles:
        mat = c.material
        ac = c.accion_correctiva
        filas.append({
            "ID": c.id,
            "Fecha": c.fecha,
            "Hora": c.hora.strftime("%H:%M"),
            "Turno": c.turno or "—",
            "Área": mat.equipo.area.nombre,
            "Equipo": mat.equipo.nombre,
            "Analito": mat.analito,
            "Nivel": c.nivel_lote.nivel,
            "Valor": c.valor,
            "Unidad": mat.unidad or "",
            "z-score": round(c.zscore, 3) if c.zscore is not None else "",
            "Resultado": c.resultado,
            "Regla": c.regla_violada or "—",
            "AC": "✅" if ac else ("⚠️" if c.resultado == "RECHAZO" else "—"),
            "Retro.": "Sí" if c.es_retroactivo else "No",
            "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
        })

    df = pd.DataFrame(filas)

    def _estilo(val):
        return {
            "OK": "background-color:#d4edda; color:#155724",
            "ADVERTENCIA": "background-color:#fff3cd; color:#856404",
            "RECHAZO": "background-color:#f8d7da; color:#721c24",
        }.get(val, "")

    st.dataframe(df.style.applymap(_estilo, subset=["Resultado"]),
                 use_container_width=True, hide_index=True)

    total = len(controles)
    rej = sum(1 for c in controles if c.resultado == "RECHAZO")
    adv = sum(1 for c in controles if c.resultado == "ADVERTENCIA")
    sin_ac = sum(1 for c in controles if c.resultado == "RECHAZO" and not c.accion_correctiva)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total)
    col2.metric("Rechazos", rej)
    col3.metric("Tasa rechazo", f"{rej/total*100:.1f}%")
    col4.metric("Sin acción correctiva", sin_ac, delta=f"{sin_ac} pendiente(s)" if sin_ac else None, delta_color="inverse")

    try:
        import io
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("⬇️ Descargar Excel", buf.getvalue(), "controles_diarios.xlsx")
    except Exception:
        pass

    with st.expander("🗑️ Eliminar control (corrección de errores)"):
        ctrl_id = st.number_input("ID del control a eliminar", min_value=1, step=1, key="del_ctrl")
        motivo  = st.text_input("Motivo de eliminación *", key="del_motivo")
        if st.button("Eliminar control", key="btn_del_ctrl"):
            if not motivo.strip():
                st.error("Debe indicar el motivo.")
            else:
                ok_del = crud.eliminar_control_diario(db, int(ctrl_id))
                st.success(f"Control ID {ctrl_id} eliminado.") if ok_del else st.error("No se encontró el control.")
                if ok_del:
                    st.rerun()


if __name__ == "__main__":
    main()
