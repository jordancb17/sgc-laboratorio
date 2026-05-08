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
from modules.page_utils import setup_page, page_header
from modules.cache import cached_areas, cached_equipos, cached_materiales, cached_personal

st.set_page_config(page_title="Controles Diarios", page_icon="📋", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="📋",
        title="Controles Diarios de Calidad",
        subtitle="Registro, evaluación Westgard en tiempo real e historial de controles internos",
        badge="Control Interno",
    )
    tab_reg, tab_panel, tab_consulta, tab_retro = st.tabs([
        "📝 Analito Individual", "🧩 Panel / Grupo", "🔍 Consultar / Historial", "🕐 Regularización (Retroactivo)"
    ])
    with tab_reg:
        _tab_registrar(es_retroactivo=False)
    with tab_panel:
        _tab_panel()
    with tab_consulta:
        _tab_consulta()
    with tab_retro:
        _tab_registrar(es_retroactivo=True)


# ─── FORMULARIO DE REGISTRO ───────────────────────────────────────────────────

@st.fragment
def _tab_registrar(es_retroactivo: bool):
    # ── Datos de referencia desde caché (sin consulta DB) ────────────────────
    areas_c = cached_areas()
    if not areas_c:
        st.warning("No hay áreas configuradas. Vaya a ⚙️ Configuración.")
        return

    db = get_session()
    try:
        if es_retroactivo:
            st.subheader("🕐 Regularización — Registro Retroactivo")
            st.info("Use esta sección para registrar controles de días pasados. "
                    "El sistema verificará que no exista un duplicado exacto en esa fecha/hora.")
        else:
            st.subheader("Registrar Control del Día")

        suf = "_r" if es_retroactivo else ""

        # ── Área / Equipo / Analito (caché — sin DB) ─────────────────────────
        col1, col2, col3 = st.columns(3)
        area_opts = {a["nombre"]: a["id"] for a in areas_c}
        area_sel  = col1.selectbox("Área *", list(area_opts.keys()), key=f"area{suf}")

        equipos_c = cached_equipos(area_id=area_opts[area_sel])
        if not equipos_c:
            col2.warning("Sin equipos en esta área.")
            return
        eq_opts = {e["nombre"]: e["id"] for e in equipos_c}
        eq_sel  = col2.selectbox("Equipo *", list(eq_opts.keys()), key=f"eq{suf}")

        mats_c = cached_materiales(equipo_id=eq_opts[eq_sel])
        if not mats_c:
            col3.warning("Sin analitos en este equipo.")
            return
        mat_opts    = {f"{m['analito']} [{m['proveedor']}]": m["id"] for m in mats_c}
        mat_sel     = col3.selectbox("Analito *", list(mat_opts.keys()), key=f"mat{suf}")
        material_id = mat_opts[mat_sel]
        mat_d       = next(m for m in mats_c if m["id"] == material_id)   # dict

        # ── Lote activo (DB — query única con selectinload) ───────────────────
        lote = crud.get_lote_activo(db, material_id)
        if not lote:
            st.error("Este analito no tiene lote activo vigente. Registre un lote en ⚙️ Configuración.")
            return
        if lote.fecha_vencimiento < date.today():
            st.error("⚠️ El lote está VENCIDO.")
            return

        st.info(f"**Lote activo:** `{lote.numero_lote}` — Vence: `{lote.fecha_vencimiento}`")

        niveles_disponibles = {f"Nivel {nv.nivel}": nv.id for nv in lote.niveles}
        if not niveles_disponibles:
            st.error("El lote no tiene niveles configurados.")
            return

        col1, col2 = st.columns(2)
        nivel_sel     = col1.selectbox("Nivel de control *", list(niveles_disponibles.keys()), key=f"nivel{suf}")
        nivel_lote_id = niveles_disponibles[nivel_sel]
        nivel_lote: NivelLote = next(nv for nv in lote.niveles if nv.id == nivel_lote_id)
        col2.markdown(
            f"**Referencia** — X̄: `{nivel_lote.media}` | s: `{nivel_lote.de}` | "
            f"Rango: `{nivel_lote.valor_minimo}` – `{nivel_lote.valor_maximo}` {mat_d['unidad']}"
        )

        # ── Fecha / hora / turno / personal ─────────────────────────────────
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

        # Personal desde caché
        personal_c = cached_personal()
        if not personal_c:
            st.warning("No hay personal configurado.")
            return
        pers_opts = {f"{p['apellido']}, {p['nombre']}": p["id"] for p in personal_c}
        pers_sel  = col4.selectbox("Personal *", list(pers_opts.keys()), key=f"pers{suf}")

        # ── Valor medido ─────────────────────────────────────────────────────
        col1, col2 = st.columns([1, 2])
        valor      = col1.number_input(
            f"Valor medido ({mat_d['unidad'] or 'u'}) *",
            format="%.4f", step=0.01, key=f"valor{suf}"
        )
        comentario = col2.text_area("Comentario (opcional)", height=68, key=f"coment{suf}")

        # ── Preview Westgard en tiempo real ──────────────────────────────────
        if valor != 0.0:
            hist    = crud.historial_zscores(db, nivel_lote_id)
            otros   = crud.zscores_mismo_run(db, material_id, fecha_ctrl, hora_ctrl, nivel_lote.nivel, lote.id)
            preview = evaluar_westgard(valor, nivel_lote.media, nivel_lote.de, hist, otros or None)
            wg_cls  = {"OK": "wg-ok", "ADVERTENCIA": "wg-warn", "RECHAZO": "wg-rej"}.get(preview.resultado, "wg-ok")
            st.markdown(
                f'<div class="wg-box {wg_cls}">'
                f'<b>{emoji_resultado(preview.resultado)} Westgard (preview):</b> {preview.resultado}'
                + (f' — Regla <code>{preview.regla_violada}</code>' if preview.regla_violada else '')
                + f'<br><small>z-score: <b>{preview.zscore:.3f}</b> &nbsp;·&nbsp; {preview.descripcion}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

        # ── Guardar ──────────────────────────────────────────────────────────
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
                        pers_d = next(p for p in personal_c if p["id"] == pers_opts[pers_sel])
                        ok_mail, msg_mail = alerta_rechazo(
                            analito=mat_d["analito"],
                            area=area_sel,
                            equipo=eq_sel,
                            nivel=nivel_lote.nivel,
                            valor=valor,
                            unidad=mat_d["unidad"],
                            zscore=control.zscore,
                            regla=control.regla_violada or "—",
                            personal=f"{pers_d['apellido']}, {pers_d['nombre']}",
                            fecha=fecha_ctrl,
                            hora=hora_ctrl,
                        )
                        if ok_mail:
                            st.info(f"📧 {msg_mail}")
                        st.markdown("👉 Registre la acción correctiva en la página **🔧 Acciones Correctivas**.")
                    elif control.resultado == RESULTADO_ADVERTENCIA:
                        st.warning("⚠️ **ADVERTENCIA 1-2s**: Monitoree la tendencia en el próximo control.")
    finally:
        db.close()


# ─── REGISTRO POR PANEL ──────────────────────────────────────────────────────

@st.fragment
def _tab_panel():
    db = get_session()
    try:
        st.subheader("🧩 Registrar Control por Panel")
        st.info(
            "Ingrese los resultados de **todos los parámetros** del panel de una sola vez. "
            "Ideal para Hemograma, Gases Arteriales, Electrolitos y otros paneles multi-analito."
        )

        # Áreas y equipos desde caché — sin DB
        areas_c_p = cached_areas()
        if not areas_c_p:
            st.warning("No hay áreas configuradas.")
            return

        col1, col2, col3 = st.columns(3)
        area_opts  = {a["nombre"]: a["id"] for a in areas_c_p}
        area_sel_p = col1.selectbox("Área *", list(area_opts.keys()), key="pan_area")

        equipos_cp = cached_equipos(area_id=area_opts[area_sel_p])
        if not equipos_cp:
            col2.warning("Sin equipos en esta área.")
            return
        eq_opts_p = {e["nombre"]: e["id"] for e in equipos_cp}
        eq_sel_p  = col2.selectbox("Equipo *", list(eq_opts_p.keys()), key="pan_eq")

        grupos_p = crud.listar_grupos(db, equipo_id=eq_opts_p[eq_sel_p])
        if not grupos_p:
            col3.warning("Sin grupos en este equipo. Créelos en ⚙️ Configuración → Grupos.")
            return
        grp_opts_p = {g.nombre: g.id for g in grupos_p}
        grp_sel_p = col3.selectbox("Panel / Grupo *", list(grp_opts_p.keys()), key="pan_grp")

        grupo_p = next(g for g in grupos_p if g.id == grp_opts_p[grp_sel_p])
        mats_panel = [m for m in grupo_p.materiales if m.activo]

        if not mats_panel:
            st.warning("El grupo seleccionado no tiene analitos activos.")
            return

        # ── Fecha / hora / turno / personal ─────────────────────────────────
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        fecha_p  = col1.date_input("Fecha *", value=date.today(), max_value=date.today(), key="pan_fecha")
        hora_p   = col2.time_input("Hora *", value=datetime.now().time().replace(second=0, microsecond=0), key="pan_hora")
        turno_p  = col3.selectbox("Turno *", TURNOS, key="pan_turno")
        # Personal desde caché
        personal_cp = cached_personal()
        if not personal_cp:
            st.warning("No hay personal configurado.")
            return
        pers_opts_p = {f"{p['apellido']}, {p['nombre']}": p["id"] for p in personal_cp}
        pers_sel_p  = col4.selectbox("Personal *", list(pers_opts_p.keys()), key="pan_pers")
        comentario_p = st.text_input("Comentario general (opcional)", key="pan_coment")

        # ── Batch: un query para todos los lotes (sin N+1) ───────────────────
        st.markdown("---")
        lotes_bulk = crud.get_lotes_activos_bulk(db, [m.id for m in mats_panel])
        sin_lote   = [m.analito for m in mats_panel if m.id not in lotes_bulk]
        if sin_lote:
            st.warning(f"⚠️ Sin lote activo: {', '.join(sin_lote)}. Regístrelos en ⚙️ Configuración → Lotes.")

        filas_panel = []
        for m in mats_panel:
            lote = lotes_bulk.get(m.id)
            if not lote:
                continue
            filas_panel.append({"mat": m, "lote": lote,
                                 "niveles": {nv.nivel: nv for nv in lote.niveles}})

        if not filas_panel:
            st.error("Ningún analito del panel tiene lote activo.")
            return

        niveles_disponibles = sorted({nv for fp in filas_panel for nv in fp["niveles"].keys()})
        st.caption(
            f"**{grupo_p.nombre}** — {len(filas_panel)} analito(s) con lote | "
            f"Niveles: {', '.join(str(n) for n in niveles_disponibles)}"
        )

        # ── data_editor por nivel ─────────────────────────────────────────────
        nivel_tabs = st.tabs([f"📊 Nivel {n}" for n in niveles_disponibles])
        _save_gen  = st.session_state.get("_pan_save_gen", 0)

        for tab_idx, nivel_num in enumerate(niveles_disponibles):
            with nivel_tabs[tab_idx]:
                fps_nivel = [fp for fp in filas_panel if nivel_num in fp["niveles"]]
                if not fps_nivel:
                    st.info(f"Ningún analito tiene configurado el Nivel {nivel_num}.")
                    continue

                df_entrada = pd.DataFrame([{
                    "Analito":       fp["mat"].analito,
                    "Unidad":        fp["mat"].unidad or "—",
                    "X̄":             fp["niveles"][nivel_num].media,
                    "s":             fp["niveles"][nivel_num].de,
                    "Rango":         f"{fp['niveles'][nivel_num].valor_minimo} – {fp['niveles'][nivel_num].valor_maximo}",
                    "Valor medido":  0.0,
                } for fp in fps_nivel])

                edited_nv = st.data_editor(
                    df_entrada,
                    column_config={
                        "Analito":      st.column_config.TextColumn("Analito",       disabled=True, width="medium"),
                        "Unidad":       st.column_config.TextColumn("Unidad",        disabled=True, width="small"),
                        "X̄":            st.column_config.NumberColumn("X̄",           disabled=True, format="%.4f", width="small"),
                        "s":            st.column_config.NumberColumn("s",            disabled=True, format="%.4f", width="small"),
                        "Rango":        st.column_config.TextColumn("Rango",          disabled=True, width="medium"),
                        "Valor medido": st.column_config.NumberColumn("Valor medido", format="%.4f", width="medium"),
                    },
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    key=f"pan_ed_{grp_opts_p[grp_sel_p]}_{nivel_num}_{_save_gen}",
                )

                col_prev, col_save = st.columns(2)

                # ── Preview Westgard (sin guardar) ────────────────────────────
                if col_prev.button(f"📊 Previsualizar Westgard", key=f"btn_prev_nv{nivel_num}"):
                    filas_prev = []
                    for fp, (_, row) in zip(fps_nivel, edited_nv.iterrows()):
                        val = float(row["Valor medido"])
                        if val == 0.0:
                            continue
                        m  = fp["mat"]
                        nl = fp["niveles"][nivel_num]
                        hist  = crud.historial_zscores(db, nl.id)
                        otros = crud.zscores_mismo_run(db, m.id, fecha_p, hora_p, nivel_num, fp["lote"].id)
                        prev  = evaluar_westgard(val, nl.media, nl.de, hist, otros or None)
                        filas_prev.append({
                            "Analito":   m.analito,
                            "Valor":     val,
                            "z-score":   round(prev.zscore, 3),
                            "Resultado": prev.resultado,
                            "Regla":     prev.regla_violada or "—",
                        })
                    if filas_prev:
                        def _col_res(v):
                            return {"OK": "background-color:#d4edda;color:#155724",
                                    "ADVERTENCIA": "background-color:#fff3cd;color:#856404",
                                    "RECHAZO": "background-color:#f8d7da;color:#721c24"}.get(v, "")
                        st.dataframe(
                            pd.DataFrame(filas_prev).style.applymap(_col_res, subset=["Resultado"]),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("Ingrese al menos un valor distinto de 0.")

                # ── Guardar nivel ─────────────────────────────────────────────
                if col_save.button(f"💾 Guardar Nivel {nivel_num}", key=f"btn_pan_nv{nivel_num}", type="primary"):
                    guardados_nv, errores_nv = [], []
                    for fp, (_, row) in zip(fps_nivel, edited_nv.iterrows()):
                        val = float(row["Valor medido"])
                        if val == 0.0:
                            continue
                        m  = fp["mat"]
                        nl = fp["niveles"][nivel_num]
                        ctrl, err = crud.registrar_control_diario(
                            db=db, material_id=m.id, lote_id=fp["lote"].id,
                            nivel_lote_id=nl.id, personal_id=pers_opts_p[pers_sel_p],
                            fecha=fecha_p, hora=hora_p, valor=val,
                            comentario=comentario_p, turno=turno_p, es_retroactivo=False,
                        )
                        if err:
                            errores_nv.append(f"**{m.analito}**: {err}")
                        else:
                            guardados_nv.append((m, nl, ctrl))

                    if guardados_nv:
                        rechazos_nv = [x for x in guardados_nv if x[2].resultado == RESULTADO_RECHAZO]
                        advert_nv   = [x for x in guardados_nv if x[2].resultado == RESULTADO_ADVERTENCIA]
                        ok_nv       = [x for x in guardados_nv if x[2].resultado == "OK"]
                        st.success(
                            f"✅ Nivel {nivel_num} guardado — "
                            f"{len(ok_nv)} OK · {len(advert_nv)} Adv · {len(rechazos_nv)} Rech"
                        )
                        filas_res = [{
                            "Analito":   m.analito,
                            "Valor":     ctrl.valor,
                            "z":         round(ctrl.zscore, 3),
                            "Resultado": ctrl.resultado,
                            "Regla":     ctrl.regla_violada or "—",
                        } for m, nl, ctrl in guardados_nv]
                        def _c(v):
                            return {"OK":"background-color:#d4edda;color:#155724",
                                    "ADVERTENCIA":"background-color:#fff3cd;color:#856404",
                                    "RECHAZO":"background-color:#f8d7da;color:#721c24"}.get(v,"")
                        st.dataframe(
                            pd.DataFrame(filas_res).style.applymap(_c, subset=["Resultado"]),
                            use_container_width=True, hide_index=True,
                        )
                        if rechazos_nv:
                            st.error("🛑 RECHAZO detectado. No libere muestras hasta registrar acción correctiva.")
                            pers_dp = next(p for p in personal_cp if p["id"] == pers_opts_p[pers_sel_p])
                            for m, nl, ctrl in rechazos_nv:
                                alerta_rechazo(
                                    analito=m.analito,
                                    area=area_sel_p,
                                    equipo=eq_sel_p,
                                    nivel=nivel_num,
                                    valor=ctrl.valor, unidad=m.unidad or "",
                                    zscore=ctrl.zscore, regla=ctrl.regla_violada or "—",
                                    personal=f"{pers_dp['apellido']}, {pers_dp['nombre']}",
                                    fecha=fecha_p, hora=hora_p,
                                )
                        st.session_state["_pan_save_gen"] = _save_gen + 1
                        st.rerun()
                    for e in errores_nv:
                        st.warning(e)
    finally:
        db.close()


# ─── CONSULTA / HISTORIAL ─────────────────────────────────────────────────────

@st.fragment
def _tab_consulta():
    db = get_session()
    try:
        st.subheader("Historial de Controles")

        col1, col2, col3, col4 = st.columns(4)
        # Dropdowns de filtro desde caché — sin consultas DB
        areas_cf   = cached_areas()
        area_opts  = {"Todas": None} | {a["nombre"]: a["id"] for a in areas_cf}
        area_f     = col1.selectbox("Área", list(area_opts.keys()), key="cf_area")

        equipos_cf = cached_equipos(area_id=area_opts[area_f])
        eq_opts_f  = {"Todos": None} | {e["nombre"]: e["id"] for e in equipos_cf}
        eq_f       = col2.selectbox("Equipo", list(eq_opts_f.keys()), key="cf_eq")

        mats_cf    = cached_materiales(equipo_id=eq_opts_f[eq_f])
        mat_opts_f = {"Todos": None} | {m["analito"]: m["id"] for m in mats_cf}
        mat_f      = col3.selectbox("Analito", list(mat_opts_f.keys()), key="cf_mat")
        nivel_f    = col4.selectbox("Nivel", ["Todos", 1, 2, 3], key="cf_nivel")

        col1, col2 = st.columns(2)
        fecha_desde = col1.date_input("Desde", value=date.today() - timedelta(days=30), key="cf_desde")
        fecha_hasta = col2.date_input("Hasta", value=date.today(), key="cf_hasta")

        # Filtro por equipo resuelto en SQL (equipo_id) — no más post-filtrado Python
        controles = crud.listar_controles_diarios(
            db,
            material_id=mat_opts_f[mat_f],
            equipo_id=eq_opts_f[eq_f],          # ★ filtro SQL, reemplaza el if/list-comp
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            nivel=None if nivel_f == "Todos" else int(nivel_f),
        )

        if not controles:
            st.info("No hay controles con estos filtros.")
            return

        filas = []
        for c in controles:
            mat = c.material      # already eager-loaded
            ac  = c.accion_correctiva
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
        col4.metric("Sin acción correctiva", sin_ac,
                    delta=f"{sin_ac} pendiente(s)" if sin_ac else None, delta_color="inverse")

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
    finally:
        db.close()


if __name__ == "__main__":
    main()
