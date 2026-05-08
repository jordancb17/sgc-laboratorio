"""
Configuración del sistema: Áreas, Equipos, Personal, Grupos de Pruebas, Analitos y Lotes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date

from database.database import init_db, get_session
from database import crud
from database.models import PANELES_PREDEFINIDOS
from modules.page_utils import setup_page, page_header
from modules.cache import invalidate_all

st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="⚙️",
        title="Configuración del Sistema",
        subtitle="Gestione áreas, equipos, personal, grupos de pruebas, analitos y lotes de control",
        badge="Administración",
    )

    tab_areas, tab_equipos, tab_personal, tab_grupos, tab_analitos, tab_lotes = st.tabs([
        "🏥 Áreas", "🔬 Equipos", "👤 Personal",
        "📋 Grupos de Pruebas", "🧪 Analitos / Materiales", "📦 Lotes",
    ])
    with tab_areas:
        _tab_areas()
    with tab_equipos:
        _tab_equipos()
    with tab_personal:
        _tab_personal()
    with tab_grupos:
        _tab_grupos()
    with tab_analitos:
        _tab_analitos()
    with tab_lotes:
        _tab_lotes()


# ─── ÁREAS ───────────────────────────────────────────────────────────────────

@st.fragment
def _tab_areas():
    db = get_session()
    try:
        _section_title("🏥 Áreas de Laboratorio",
                       "Defina las secciones o áreas del laboratorio (Hematología, Bioquímica, etc.)")

        with st.expander("➕ Registrar Nueva Área", expanded=False):
            with st.form("form_area"):
                col1, col2 = st.columns([2, 3])
                nombre = col1.text_input("Nombre del área *", placeholder="ej. Hematología")
                desc   = col2.text_input("Descripción", placeholder="Descripción breve opcional")
                submitted = st.form_submit_button("💾 Guardar Área", type="primary", use_container_width=True)
                if submitted:
                    if not nombre.strip():
                        st.error("El nombre del área es obligatorio.")
                    else:
                        try:
                            crud.crear_area(db, nombre, desc)
                            st.success(f"✅ Área **{nombre}** registrada correctamente.")
                            invalidate_all()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

        areas = crud.listar_areas(db, solo_activos=False)
        if not areas:
            _empty_state("No hay áreas registradas. Registre la primera área para comenzar.")
            return

        st.markdown(f"**{len(areas)} área(s) registrada(s)**")
        df = pd.DataFrame([{
            "ID": a.id,
            "Área": a.nombre,
            "Descripción": a.descripcion or "—",
            "Estado": "✅ Activa" if a.activo else "⛔ Inactiva",
        } for a in areas])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        _section_title("✏️ Editar o Cambiar Estado")
        area_opts_all = {f"{'✅' if a.activo else '⛔'} {a.nombre}": a.id for a in areas}
        sel_area = st.selectbox("Seleccione el área:", list(area_opts_all.keys()),
                                key="sel_area_edit", label_visibility="collapsed")
        area_id_sel = area_opts_all[sel_area]
        area_obj = next(a for a in areas if a.id == area_id_sel)

        with st.form("form_edit_area"):
            col1, col2 = st.columns([2, 3])
            nuevo_nombre = col1.text_input("Nombre *", value=area_obj.nombre)
            nueva_desc   = col2.text_input("Descripción", value=area_obj.descripcion or "")
            estado_label = "✅ Activar" if not area_obj.activo else "⛔ Desactivar"
            col_s, col_t, col_d = st.columns([2, 1.3, 1])
            guardar  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
            toggling = col_t.form_submit_button(estado_label, use_container_width=True)
            del_btn  = col_d.form_submit_button("🗑️ Eliminar", use_container_width=True)

            if guardar:
                if not nuevo_nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    try:
                        crud.actualizar_area(db, area_id_sel, nuevo_nombre, nueva_desc)
                        st.success("✅ Área actualizada correctamente.")
                        invalidate_all()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if toggling:
                nuevo_estado = crud.toggle_activo_area(db, area_id_sel)
                label = "activada ✅" if nuevo_estado else "desactivada ⛔"
                st.info(f"Área **{area_obj.nombre}** {label}.")
                invalidate_all()
                st.rerun()

            if del_btn:
                st.session_state["_confirm_del_area"] = area_id_sel

        if st.session_state.get("_confirm_del_area") == area_id_sel:
            st.warning(f"⚠️ ¿Eliminar permanentemente el área **{area_obj.nombre}**? Esta acción no se puede deshacer.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Sí, eliminar definitivamente", key="btn_area_del_yes", type="primary", use_container_width=True):
                ok, msg = crud.eliminar_area(db, area_id_sel)
                st.session_state.pop("_confirm_del_area", None)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            if c2.button("❌ Cancelar", key="btn_area_del_no", use_container_width=True):
                st.session_state.pop("_confirm_del_area", None)
                st.rerun()
    finally:
        db.close()


# ─── EQUIPOS ─────────────────────────────────────────────────────────────────

@st.fragment
def _tab_equipos():
    db = get_session()
    try:
        _section_title("🔬 Equipos / Analizadores",
                       "Registre los equipos y analizadores por área. Incluya marca, modelo y número de serie.")

        areas = crud.listar_areas(db)
        if not areas:
            st.warning("⚠️ Primero debe registrar al menos un **Área**.")
            return

        area_opts = {a.nombre: a.id for a in areas}

        with st.expander("➕ Registrar Nuevo Equipo", expanded=False):
            with st.form("form_equipo"):
                area_sel = st.selectbox("Área *", list(area_opts.keys()))
                col1, col2 = st.columns(2)
                nombre = col1.text_input("Nombre del equipo *",  placeholder="ej. Analizador Hematológico")
                marca  = col2.text_input("Marca / Fabricante *", placeholder="ej. Sysmex, Beckman Coulter, Roche")
                col3, col4 = st.columns(2)
                modelo = col3.text_input("Modelo", placeholder="ej. XN-1000")
                serie  = col4.text_input("N° de serie", placeholder="ej. SN-2024-001")
                submitted = st.form_submit_button("💾 Guardar Equipo", type="primary", use_container_width=True)
                if submitted:
                    if not nombre.strip():
                        st.error("El nombre del equipo es obligatorio.")
                    elif not marca.strip():
                        st.error("La marca / fabricante es obligatoria.")
                    else:
                        try:
                            crud.crear_equipo(db, area_opts[area_sel], nombre, marca, modelo, serie)
                            st.success(f"✅ Equipo **{nombre}** registrado correctamente.")
                            invalidate_all()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

        st.markdown("**Filtrar por área:**")
        area_filtro = st.selectbox("", ["Todas las áreas"] + list(area_opts.keys()),
                                   key="filtro_eq", label_visibility="collapsed")
        area_id_filtro = area_opts.get(area_filtro) if area_filtro != "Todas las áreas" else None
        equipos = crud.listar_equipos(db, area_id=area_id_filtro, solo_activos=False)

        if not equipos:
            _empty_state("No hay equipos registrados para esta área.")
            return

        st.markdown(f"**{len(equipos)} equipo(s) registrado(s)**")
        df = pd.DataFrame([{
            "ID": e.id,
            "Área": e.area.nombre,
            "Equipo": e.nombre,
            "Marca": e.marca or "—",
            "Modelo": e.modelo or "—",
            "N° Serie": e.numero_serie or "—",
            "Estado": "✅ Activo" if e.activo else "⛔ Inactivo",
        } for e in equipos])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        _section_title("✏️ Editar o Cambiar Estado")
        todos_equipos = crud.listar_equipos(db, solo_activos=False)
        eq_opts_all = {
            f"{'✅' if e.activo else '⛔'} {e.area.nombre} › {e.nombre} ({e.marca or '—'})": e.id
            for e in todos_equipos
        }
        sel_eq = st.selectbox("Seleccione el equipo:", list(eq_opts_all.keys()),
                              key="sel_eq_edit", label_visibility="collapsed")
        eq_id_sel = eq_opts_all[sel_eq]
        eq_obj = next(e for e in todos_equipos if e.id == eq_id_sel)

        with st.form("form_edit_equipo"):
            area_names = list(area_opts.keys())
            try:
                area_idx = list(area_opts.values()).index(eq_obj.area_id)
            except ValueError:
                area_idx = 0

            area_edit = st.selectbox("Área *", area_names, index=area_idx)
            col1, col2 = st.columns(2)
            nuevo_nombre = col1.text_input("Nombre del equipo *", value=eq_obj.nombre)
            nueva_marca  = col2.text_input("Marca / Fabricante",  value=eq_obj.marca or "")
            col3, col4 = st.columns(2)
            nuevo_modelo = col3.text_input("Modelo",    value=eq_obj.modelo or "")
            nueva_serie  = col4.text_input("N° Serie",  value=eq_obj.numero_serie or "")

            estado_label = "✅ Activar" if not eq_obj.activo else "⛔ Desactivar"
            col_s, col_t, col_d = st.columns([2, 1.3, 1])
            guardar  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
            toggling = col_t.form_submit_button(estado_label, use_container_width=True)
            del_btn  = col_d.form_submit_button("🗑️ Eliminar", use_container_width=True)

            if guardar:
                if not nuevo_nombre.strip():
                    st.error("El nombre del equipo es obligatorio.")
                else:
                    try:
                        crud.actualizar_equipo(
                            db, eq_id_sel, area_opts[area_edit],
                            nuevo_nombre, nueva_marca, nuevo_modelo, nueva_serie
                        )
                        st.success("✅ Equipo actualizado correctamente.")
                        invalidate_all()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if toggling:
                nuevo_estado = crud.toggle_activo_equipo(db, eq_id_sel)
                label = "activado ✅" if nuevo_estado else "desactivado ⛔"
                st.info(f"Equipo **{eq_obj.nombre}** {label}.")
                st.rerun()

            if del_btn:
                st.session_state["_confirm_del_eq"] = eq_id_sel

        if st.session_state.get("_confirm_del_eq") == eq_id_sel:
            st.warning(f"⚠️ ¿Eliminar permanentemente el equipo **{eq_obj.nombre}**? Esta acción no se puede deshacer.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Sí, eliminar definitivamente", key="btn_eq_del_yes", type="primary", use_container_width=True):
                ok, msg = crud.eliminar_equipo(db, eq_id_sel)
                st.session_state.pop("_confirm_del_eq", None)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            if c2.button("❌ Cancelar", key="btn_eq_del_no", use_container_width=True):
                st.session_state.pop("_confirm_del_eq", None)
                st.rerun()
    finally:
        db.close()


# ─── PERSONAL ────────────────────────────────────────────────────────────────

@st.fragment
def _tab_personal():
    db = get_session()
    try:
        _section_title("👤 Personal de Laboratorio",
                       "Registre bioquímicos, técnicos y auxiliares que ejecutan los controles.")

        with st.expander("➕ Registrar Personal", expanded=False):
            with st.form("form_personal"):
                col1, col2 = st.columns(2)
                nombre   = col1.text_input("Nombre(s) *",      placeholder="ej. Juan Carlos")
                apellido = col2.text_input("Apellido(s) *",    placeholder="ej. Cuadrado")
                codigo   = col1.text_input("Código / Matrícula", placeholder="ej. BQ-001")
                cargo    = col2.text_input("Cargo / Función",  placeholder="ej. Bioquímico Clínico")
                submitted = st.form_submit_button("💾 Guardar Personal", type="primary", use_container_width=True)
                if submitted:
                    if not nombre.strip() or not apellido.strip():
                        st.error("El nombre y el apellido son obligatorios.")
                    else:
                        try:
                            crud.crear_personal(db, nombre, apellido, codigo, cargo)
                            st.success(f"✅ **{apellido}, {nombre}** registrado correctamente.")
                            invalidate_all()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

        personal = crud.listar_personal(db, solo_activos=False)
        if not personal:
            _empty_state("No hay personal registrado.")
            return

        st.markdown(f"**{len(personal)} persona(s) registrada(s)**")
        df = pd.DataFrame([{
            "ID": p.id,
            "Apellido": p.apellido,
            "Nombre": p.nombre,
            "Código": p.codigo or "—",
            "Cargo": p.cargo or "—",
            "Estado": "✅ Activo" if p.activo else "⛔ Inactivo",
        } for p in personal])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        _section_title("✏️ Editar o Cambiar Estado")
        pers_opts_all = {
            f"{'✅' if p.activo else '⛔'} {p.apellido}, {p.nombre} — {p.cargo or 'sin cargo'}": p.id
            for p in personal
        }
        sel_p = st.selectbox("Seleccione el personal:", list(pers_opts_all.keys()),
                             key="sel_pers_edit", label_visibility="collapsed")
        pers_id_sel = pers_opts_all[sel_p]
        pers_obj = next(p for p in personal if p.id == pers_id_sel)

        with st.form("form_edit_personal"):
            col1, col2 = st.columns(2)
            nuevo_nombre   = col1.text_input("Nombre(s) *",        value=pers_obj.nombre)
            nuevo_apellido = col2.text_input("Apellido(s) *",      value=pers_obj.apellido)
            nuevo_codigo   = col1.text_input("Código / Matrícula", value=pers_obj.codigo or "")
            nuevo_cargo    = col2.text_input("Cargo / Función",    value=pers_obj.cargo or "")

            estado_label = "✅ Activar" if not pers_obj.activo else "⛔ Desactivar"
            col_s, col_t, col_d = st.columns([2, 1.3, 1])
            guardar  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
            toggling = col_t.form_submit_button(estado_label, use_container_width=True)
            del_btn  = col_d.form_submit_button("🗑️ Eliminar", use_container_width=True)

            if guardar:
                if not nuevo_nombre.strip() or not nuevo_apellido.strip():
                    st.error("El nombre y apellido son obligatorios.")
                else:
                    try:
                        crud.actualizar_personal(
                            db, pers_id_sel, nuevo_nombre, nuevo_apellido, nuevo_codigo, nuevo_cargo
                        )
                        st.success("✅ Personal actualizado correctamente.")
                        invalidate_all()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if toggling:
                nuevo_estado = crud.toggle_activo_personal(db, pers_id_sel)
                label = "activado ✅" if nuevo_estado else "desactivado ⛔"
                st.info(f"**{pers_obj.apellido}, {pers_obj.nombre}** {label}.")
                st.rerun()

            if del_btn:
                st.session_state["_confirm_del_pers"] = pers_id_sel

        if st.session_state.get("_confirm_del_pers") == pers_id_sel:
            st.warning(f"⚠️ ¿Eliminar permanentemente a **{pers_obj.apellido}, {pers_obj.nombre}**? Esta acción no se puede deshacer.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Sí, eliminar definitivamente", key="btn_pers_del_yes", type="primary", use_container_width=True):
                ok, msg = crud.eliminar_personal(db, pers_id_sel)
                st.session_state.pop("_confirm_del_pers", None)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            if c2.button("❌ Cancelar", key="btn_pers_del_no", use_container_width=True):
                st.session_state.pop("_confirm_del_pers", None)
                st.rerun()
    finally:
        db.close()


# ─── GRUPOS DE PRUEBAS ────────────────────────────────────────────────────────

@st.fragment
def _tab_grupos():
    db = get_session()
    try:
        _section_title("📋 Grupos de Pruebas (Paneles)",
                       "Agrupe analitos que se miden juntos: Hemograma, Gases Arteriales, Electrolitos, etc.")

        equipos = crud.listar_equipos(db)
        if not equipos:
            st.warning("⚠️ Primero debe registrar **Equipos**.")
            return
        eq_opts = {f"{e.area.nombre} › {e.nombre}": e.id for e in equipos}

        # ── Crear desde plantilla predefinida ─────────────────────────────────
        with st.expander("⚡ Crear Panel desde Plantilla", expanded=False):
            st.caption(
                "Seleccione la plantilla, ajuste nombre/equipo/proveedor y luego edite la tabla: "
                "desmarque ✓ para excluir, edite nombre o unidad, y use la última fila vacía para agregar parámetros extra."
            )

            col1, col2 = st.columns(2)
            plantilla_sel    = col1.selectbox("Plantilla base", list(PANELES_PREDEFINIDOS.keys()), key="plt_sel")
            eq_plantilla     = col2.selectbox("Equipo *", list(eq_opts.keys()), key="plt_eq")
            col3, col4       = st.columns(2)
            _nom_sug = " ".join(plantilla_sel.split(" ")[1:]).split("—")[-1].strip() if "—" in plantilla_sel \
                       else " ".join(plantilla_sel.split(" ")[1:])
            nombre_grupo_plt = col3.text_input("Nombre del grupo *", value=_nom_sug, key="plt_nombre")
            proveedor_plt    = col4.text_input("Proveedor material de control *",
                                               placeholder="ej. Bio-Rad, Roche, Sysmex", key="plt_prov")
            desc_plt = st.text_input("Descripción (opcional)", key="plt_desc")

            params_base  = PANELES_PREDEFINIDOS[plantilla_sel]
            df_template  = pd.DataFrame(
                [{"✓": True, "Parámetro": n, "Unidad": u} for n, u in params_base]
            )
            edited_tpl = st.data_editor(
                df_template,
                column_config={
                    "✓":         st.column_config.CheckboxColumn("✓",         default=True, width="small"),
                    "Parámetro": st.column_config.TextColumn("Parámetro",     width="large"),
                    "Unidad":    st.column_config.TextColumn("Unidad (editable)", width="medium"),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key=f"plt_editor_{plantilla_sel}",
            )

            params_finales = [
                (str(r["Parámetro"]).strip(), str(r["Unidad"]).strip())
                for _, r in edited_tpl.iterrows()
                if r["✓"] and str(r.get("Parámetro", "")).strip()
            ]

            col_info, col_btn = st.columns([3, 1])
            col_info.info(f"**{len(params_finales)} parámetros** listos para crear")
            if col_btn.button("🚀 Crear Panel", type="primary", key="btn_crear_plantilla", use_container_width=True):
                if not nombre_grupo_plt.strip():
                    st.error("El nombre del grupo es obligatorio.")
                elif not proveedor_plt.strip():
                    st.error("El proveedor es obligatorio.")
                elif not params_finales:
                    st.error("Marque al menos un parámetro.")
                else:
                    try:
                        grupo, mats = crud.crear_panel_desde_plantilla(
                            db, eq_opts[eq_plantilla],
                            nombre_grupo_plt, desc_plt, proveedor_plt, params_finales,
                        )
                        st.success(
                            f"✅ Panel **{grupo.nombre}** creado con **{len(mats)} parámetros**. "
                            "Vaya a **📦 Lotes** para registrar los valores objetivo."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # ── Crear grupo manualmente ───────────────────────────────────────────
        with st.expander("➕ Crear Grupo Manualmente", expanded=False):
            with st.form("form_grupo"):
                col1, col2 = st.columns([2, 3])
                eq_nuevo = col1.selectbox("Equipo *", list(eq_opts.keys()), key="grp_eq_new")
                nombre_g = col2.text_input("Nombre del grupo *", placeholder="ej. Panel Hepático")
                desc_g   = st.text_input("Descripción", placeholder="Descripción breve opcional")
                if st.form_submit_button("💾 Guardar Grupo", type="primary", use_container_width=True):
                    if not nombre_g.strip():
                        st.error("El nombre es obligatorio.")
                    else:
                        try:
                            crud.crear_grupo(db, eq_opts[eq_nuevo], nombre_g, desc_g)
                            st.success(f"✅ Grupo **{nombre_g}** creado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ── Lista de grupos ───────────────────────────────────────────────────
        grupos = crud.listar_grupos(db, solo_activos=False)
        if not grupos:
            _empty_state("No hay grupos de pruebas registrados. Use una plantilla o cree uno manualmente.")
            return

        st.markdown(f"**{len(grupos)} grupo(s) registrado(s)**")
        ids_con_lote = crud.material_ids_con_lote_activo(db)
        filas_g = []
        for g in grupos:
            mats_g = list(g.materiales)
            filas_g.append({
                "ID": g.id,
                "Equipo": g.equipo.nombre,
                "Área": g.equipo.area.nombre,
                "Grupo / Panel": g.nombre,
                "Descripción": g.descripcion or "—",
                "Analitos": len(mats_g),
                "Con lote ✅": sum(1 for m in mats_g if m.id in ids_con_lote),
                "Estado": "✅ Activo" if g.activo else "⛔ Inactivo",
            })
        st.dataframe(pd.DataFrame(filas_g), use_container_width=True, hide_index=True)

        # ── Detalle del grupo seleccionado ────────────────────────────────────
        st.markdown("---")
        grp_opts = {
            f"{'✅' if g.activo else '⛔'} {g.equipo.nombre} › {g.nombre}": g.id
            for g in grupos
        }
        sel_g = st.selectbox("Seleccione un grupo para gestionar:", list(grp_opts.keys()),
                             key="sel_grp_edit", label_visibility="collapsed")
        grp_id_sel = grp_opts[sel_g]
        grp_obj = next(g for g in grupos if g.id == grp_id_sel)

        mats_del_grupo = list(grp_obj.materiales)
        if mats_del_grupo:
            st.markdown(f"**Parámetros de «{grp_obj.nombre}»** — {len(mats_del_grupo)} analitos:")
            lotes_bulk = crud.get_lotes_activos_bulk(db, [m.id for m in mats_del_grupo])
            filas_m = []
            for m in mats_del_grupo:
                lote_a = lotes_bulk.get(m.id)
                filas_m.append({
                    "Analito": m.analito,
                    "Unidad": m.unidad or "—",
                    "Proveedor": m.proveedor,
                    "Lote activo": lote_a.numero_lote if lote_a else "⚠️ Sin lote",
                    "Vencimiento": lote_a.fecha_vencimiento if lote_a else "—",
                    "Estado": "✅" if m.activo else "⛔",
                })
            st.dataframe(pd.DataFrame(filas_m), use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Este grupo no tiene analitos aún. Cree analitos en la pestaña **🧪 Analitos** y asígnelos a este grupo.")

        # ── Editar / Estado / Eliminar ────────────────────────────────────────
        _section_title("✏️ Editar o Cambiar Estado")
        with st.form("form_edit_grupo"):
            area_names_g = list(eq_opts.keys())
            try:
                eq_idx_g = list(eq_opts.values()).index(grp_obj.equipo_id)
            except ValueError:
                eq_idx_g = 0
            eq_edit_g    = st.selectbox("Equipo *", area_names_g, index=eq_idx_g, key="grp_eq_edit")
            col1, col2  = st.columns([2, 3])
            nuevo_nom_g = col1.text_input("Nombre del grupo *", value=grp_obj.nombre)
            nueva_desc_g = col2.text_input("Descripción", value=grp_obj.descripcion or "")

            estado_g = "✅ Activar" if not grp_obj.activo else "⛔ Desactivar"
            col_s, col_t, col_d = st.columns([2, 1.3, 1])
            guardar_g  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
            toggling_g = col_t.form_submit_button(estado_g, use_container_width=True)
            del_btn_g  = col_d.form_submit_button("🗑️ Eliminar", use_container_width=True)

            if guardar_g:
                if not nuevo_nom_g.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    crud.actualizar_grupo(db, grp_id_sel, eq_opts[eq_edit_g], nuevo_nom_g, nueva_desc_g)
                    st.success("✅ Grupo actualizado.")
                    st.rerun()

            if toggling_g:
                nv = crud.toggle_activo_grupo(db, grp_id_sel)
                st.info(f"Grupo **{grp_obj.nombre}** {'activado ✅' if nv else 'desactivado ⛔'}.")
                st.rerun()

            if del_btn_g:
                st.session_state["_confirm_del_grp"] = grp_id_sel

        if st.session_state.get("_confirm_del_grp") == grp_id_sel:
            n_mats = len(mats_del_grupo)
            st.warning(
                f"⚠️ ¿Eliminar el grupo **{grp_obj.nombre}**? "
                f"Tiene **{n_mats} analito(s)** asociado(s). Elige qué hacer con ellos:"
            )
            also_del = st.checkbox(
                "🗑️ También eliminar los analitos del grupo (solo si no tienen historial de controles o lotes)",
                key="chk_del_analitos",
            )
            c1, c2 = st.columns(2)
            if c1.button("✅ Confirmar eliminación", key="btn_grp_del_yes", type="primary", use_container_width=True):
                ok, msg = crud.eliminar_grupo(db, grp_id_sel, eliminar_analitos=also_del)
                st.session_state.pop("_confirm_del_grp", None)
                st.success(msg) if ok else st.error(msg)
                st.rerun()
            if c2.button("❌ Cancelar", key="btn_grp_del_no", use_container_width=True):
                st.session_state.pop("_confirm_del_grp", None)
                st.rerun()
    finally:
        db.close()


# ─── ANALITOS / MATERIALES DE CONTROL ────────────────────────────────────────

@st.fragment
def _tab_analitos():
    db = get_session()
    try:
        _section_title("🧪 Analitos / Materiales de Control",
                       "Asocie cada analito al equipo y proveedor correspondiente.")

        equipos = crud.listar_equipos(db)
        if not equipos:
            st.warning("⚠️ Primero debe registrar **Equipos**.")
            return

        eq_opts = {f"{e.area.nombre} › {e.nombre} [{e.marca or '—'}]": e.id for e in equipos}

        with st.expander("➕ Registrar Nuevo Analito", expanded=False):
            with st.form("form_analito"):
                eq_sel = st.selectbox("Equipo / Analizador *", list(eq_opts.keys()))
                col1, col2 = st.columns(2)
                analito    = col1.text_input("Nombre del analito *",    placeholder="ej. Glucosa")
                proveedor  = col2.text_input("Proveedor / Marca *",     placeholder="ej. Roche, Mindray")
                unidad     = col1.text_input("Unidad de medida",        placeholder="ej. mg/dL, g/L, U/L")
                nombre_mat = col2.text_input("Nombre material control", placeholder="ej. Multiqual Level 1")
                todos_grupos_new = crud.listar_grupos(db, solo_activos=False)
                grp_opts_new = {"(Sin grupo — analito individual)": None}
                grp_opts_new.update({f"{g.equipo.nombre} › {g.nombre}": g.id for g in todos_grupos_new})
                grp_sel_new = st.selectbox("Grupo de pruebas (opcional)", list(grp_opts_new.keys()))
                submitted  = st.form_submit_button("💾 Guardar Analito", type="primary", use_container_width=True)
                if submitted:
                    if not analito.strip() or not proveedor.strip():
                        st.error("El nombre del analito y el proveedor son obligatorios.")
                    else:
                        try:
                            crud.crear_material(
                                db, eq_opts[eq_sel], analito, proveedor, unidad, nombre_mat,
                                grupo_id=grp_opts_new[grp_sel_new]
                            )
                            st.success(f"✅ Analito **{analito}** registrado correctamente.")
                            invalidate_all()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

        st.markdown("**Filtrar por equipo:**")
        eq_filtro = st.selectbox("", ["Todos los equipos"] + list(eq_opts.keys()),
                                 key="filtro_mat", label_visibility="collapsed")
        eq_id_filtro = eq_opts.get(eq_filtro) if eq_filtro != "Todos los equipos" else None
        materiales = crud.listar_materiales(db, equipo_id=eq_id_filtro, solo_activos=False)

        if not materiales:
            _empty_state("No hay analitos registrados.")
            return

        st.markdown(f"**{len(materiales)} analito(s) registrado(s)**")
        df = pd.DataFrame([{
            "ID": m.id,
            "Área": m.equipo.area.nombre,
            "Equipo": m.equipo.nombre,
            "Analito": m.analito,
            "Unidad": m.unidad or "—",
            "Proveedor": m.proveedor,
            "Grupo / Panel": m.grupo.nombre if m.grupo else "—",
            "Material control": m.nombre_material or "—",
            "Estado": "✅" if m.activo else "⛔",
        } for m in materiales])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Editar / Cambiar estado / Eliminar analito ──
        st.markdown("---")
        _section_title("✏️ Editar o Cambiar Estado")
        todos_materiales = crud.listar_materiales(db, solo_activos=False)
        mat_opts_all = {
            f"{'✅' if m.activo else '⛔'} {m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}": m.id
            for m in todos_materiales
        }
        sel_mat = st.selectbox("Seleccione el analito:", list(mat_opts_all.keys()),
                               key="sel_mat_edit", label_visibility="collapsed")
        mat_id_sel = mat_opts_all[sel_mat]
        mat_obj = next(m for m in todos_materiales if m.id == mat_id_sel)

        with st.form("form_edit_analito"):
            todos_equipos_mat = crud.listar_equipos(db, solo_activos=False)
            eq_opts_mat = {f"{e.area.nombre} › {e.nombre} [{e.marca or '—'}]": e.id for e in todos_equipos_mat}
            eq_names_mat = list(eq_opts_mat.keys())
            try:
                eq_idx_mat = list(eq_opts_mat.values()).index(mat_obj.equipo_id)
            except ValueError:
                eq_idx_mat = 0
            eq_edit_mat = st.selectbox("Equipo / Analizador *", eq_names_mat, index=eq_idx_mat)

            col1, col2 = st.columns(2)
            nuevo_analito   = col1.text_input("Nombre del analito *", value=mat_obj.analito)
            nuevo_proveedor = col2.text_input("Proveedor / Marca *",  value=mat_obj.proveedor)
            nueva_unidad    = col1.text_input("Unidad de medida",     value=mat_obj.unidad or "")
            nuevo_nom_mat   = col2.text_input("Nombre material control", value=mat_obj.nombre_material or "")

            todos_grupos_edit = crud.listar_grupos(db, solo_activos=False)
            grp_opts_edit = {"(Sin grupo — analito individual)": None}
            grp_opts_edit.update({f"{g.equipo.nombre} › {g.nombre}": g.id for g in todos_grupos_edit})
            grp_edit_keys = list(grp_opts_edit.keys())
            try:
                grp_edit_idx = list(grp_opts_edit.values()).index(mat_obj.grupo_id)
            except ValueError:
                grp_edit_idx = 0
            grp_sel_edit = st.selectbox("Grupo de pruebas (opcional)", grp_edit_keys, index=grp_edit_idx)

            estado_label_mat = "✅ Activar" if not mat_obj.activo else "⛔ Desactivar"
            col_s, col_t, col_d = st.columns([2, 1.3, 1])
            guardar_mat  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
            toggling_mat = col_t.form_submit_button(estado_label_mat, use_container_width=True)
            del_btn_mat  = col_d.form_submit_button("🗑️ Eliminar", use_container_width=True)

            if guardar_mat:
                if not nuevo_analito.strip() or not nuevo_proveedor.strip():
                    st.error("El nombre del analito y el proveedor son obligatorios.")
                else:
                    try:
                        crud.actualizar_material(
                            db, mat_id_sel, eq_opts_mat[eq_edit_mat],
                            nuevo_analito, nuevo_proveedor, nueva_unidad, nuevo_nom_mat,
                            grupo_id=grp_opts_edit[grp_sel_edit]
                        )
                        st.success("✅ Analito actualizado correctamente.")
                        invalidate_all()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if toggling_mat:
                nuevo_estado_mat = crud.toggle_activo_material(db, mat_id_sel)
                label = "activado ✅" if nuevo_estado_mat else "desactivado ⛔"
                st.info(f"Analito **{mat_obj.analito}** {label}.")
                st.rerun()

            if del_btn_mat:
                st.session_state["_confirm_del_mat"] = mat_id_sel

        if st.session_state.get("_confirm_del_mat") == mat_id_sel:
            st.warning(f"⚠️ ¿Eliminar permanentemente el analito **{mat_obj.analito}**? Esta acción no se puede deshacer.")
            c1, c2 = st.columns(2)
            if c1.button("✅ Sí, eliminar definitivamente", key="btn_mat_del_yes", type="primary", use_container_width=True):
                ok, msg = crud.eliminar_material(db, mat_id_sel)
                st.session_state.pop("_confirm_del_mat", None)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            if c2.button("❌ Cancelar", key="btn_mat_del_no", use_container_width=True):
                st.session_state.pop("_confirm_del_mat", None)
                st.rerun()
    finally:
        db.close()


# ─── LOTES ───────────────────────────────────────────────────────────────────

@st.fragment
def _tab_lotes():
    db = get_session()
    try:
        _section_title("📦 Lotes de Reactivo / Material de Control",
                       "Registre lotes con su fecha de vencimiento y los valores objetivo por nivel (media, DE, rango aceptable).")

        # ── Registrar lote para un grupo completo ─────────────────────────────
        grupos_con_mats = [g for g in crud.listar_grupos(db, solo_activos=False)
                           if any(m.activo for m in g.materiales)]
        if grupos_con_mats:
            with st.expander("🧩 Registrar Lote para un Panel / Grupo Completo", expanded=False):
                st.info("Ingrese el número de lote y los valores objetivo de **todos los parámetros del panel** de una sola vez.")
                grp_lote_opts = {f"{g.equipo.nombre} › {g.nombre}": g.id for g in grupos_con_mats}
                grp_lote_sel  = st.selectbox("Seleccione el panel / grupo *", list(grp_lote_opts.keys()), key="gl_grp")
                grp_lote_obj  = next(g for g in grupos_con_mats if g.id == grp_lote_opts[grp_lote_sel])
                mats_grp_activos = [m for m in grp_lote_obj.materiales if m.activo]

                col1, col2, col3 = st.columns(3)
                num_lote_g  = col1.text_input("Número de lote *", placeholder="ej. LOT-2025-001", key="gl_num")
                fecha_vto_g = col2.date_input("Fecha de vencimiento *", min_value=date.today(), key="gl_fecha")
                n_niveles_g = col3.selectbox("Niveles a registrar *", [1, 2, 3], key="gl_niv")

                st.caption(f"Complete los valores objetivo de los {len(mats_grp_activos)} parámetros de «{grp_lote_obj.nombre}»:")

                nivel_editors = {}
                _col_cfg = {
                    "Analito": st.column_config.TextColumn("Analito",  disabled=True, width="medium"),
                    "Unidad":  st.column_config.TextColumn("Unidad",   disabled=True, width="small"),
                    "X̄ (Media)":  st.column_config.NumberColumn("X̄ (Media)",  format="%.4f", width="small"),
                    "s (DE)":      st.column_config.NumberColumn("s (DE)",  min_value=0.0001, format="%.4f", width="small"),
                    "Mín":         st.column_config.NumberColumn("Mín",     format="%.4f", width="small"),
                    "Máx":         st.column_config.NumberColumn("Máx",     format="%.4f", width="small"),
                }
                nv_tabs = st.tabs([f"Nivel {n+1}" for n in range(n_niveles_g)])
                for nv_i in range(n_niveles_g):
                    with nv_tabs[nv_i]:
                        df_nv = pd.DataFrame([{
                            "Analito":   m.analito,
                            "Unidad":    m.unidad or "—",
                            "X̄ (Media)": 0.0,
                            "s (DE)":    0.0001,
                            "Mín":       0.0,
                            "Máx":       0.0,
                        } for m in mats_grp_activos])
                        nivel_editors[nv_i + 1] = st.data_editor(
                            df_nv,
                            column_config=_col_cfg,
                            use_container_width=True,
                            hide_index=True,
                            num_rows="fixed",
                            key=f"gl_ed_nv{nv_i}_{grp_lote_obj.id}",
                        )

                if st.button("💾 Guardar Lote para Todo el Panel", type="primary", key="btn_gl_save"):
                    if not num_lote_g.strip():
                        st.error("El número de lote es obligatorio.")
                    else:
                        targets_g: dict = {}
                        invalidos: list = []
                        for nv_i, mat in enumerate(mats_grp_activos, 0):
                            niveles_data_g = []
                            for nv_num, df_ed in nivel_editors.items():
                                row = df_ed.iloc[nv_i]
                                de_val = float(row["s (DE)"])
                                if de_val <= 0:
                                    invalidos.append(f"{mat.analito} Nivel {nv_num}: DE debe ser > 0")
                                niveles_data_g.append({
                                    "nivel": nv_num,
                                    "media": float(row["X̄ (Media)"]),
                                    "de":    de_val,
                                    "min":   float(row["Mín"]),
                                    "max":   float(row["Máx"]),
                                })
                            targets_g[mat.id] = niveles_data_g

                        if invalidos:
                            for err in invalidos:
                                st.error(err)
                        else:
                            creados_g, errores_g = crud.crear_lotes_grupo(
                                db, grp_lote_obj.id, num_lote_g, fecha_vto_g, targets_g
                            )
                            if errores_g:
                                for e in errores_g:
                                    st.error(e)
                            st.success(
                                f"✅ Lote **{num_lote_g}** registrado para {creados_g} analito(s) "
                                f"del panel «{grp_lote_obj.nombre}»."
                            )
                            st.rerun()

        # ── Registrar lote individual ─────────────────────────────────────────
        st.markdown("---")
        materiales = crud.listar_materiales(db)
        if not materiales:
            st.warning("⚠️ Primero debe registrar **Analitos**.")
            return

        mat_opts = {
            f"{m.equipo.area.nombre} › {m.analito} [{m.proveedor}]": m.id
            for m in materiales
        }

        with st.expander("➕ Registrar Nuevo Lote Individual", expanded=False):
            with st.form("form_lote"):
                mat_sel = st.selectbox("Analito *", list(mat_opts.keys()))
                col1, col2 = st.columns(2)
                num_lote  = col1.text_input("N° de lote *", placeholder="ej. LOT-2024-001")
                fecha_vto = col2.date_input("Fecha vencimiento *", min_value=date.today())

                st.markdown("**Niveles** — active los que correspondan:")
                nv_tabs_f = st.tabs(["Nivel 1", "Nivel 2", "Nivel 3"])
                niveles_data = []
                for nv, tab in enumerate(nv_tabs_f, 1):
                    with tab:
                        activo_nv = st.checkbox("Incluir", value=(nv == 1), key=f"nv_activo_{nv}")
                        if activo_nv:
                            c1, c2, c3, c4 = st.columns(4)
                            media = c1.number_input("X̄ (Media)", key=f"media_{nv}", format="%.4f")
                            de    = c2.number_input("s (DE)", min_value=0.0001, key=f"de_{nv}", format="%.4f")
                            vmin  = c3.number_input("Mín", key=f"vmin_{nv}", format="%.4f")
                            vmax  = c4.number_input("Máx", key=f"vmax_{nv}", format="%.4f")
                            niveles_data.append({"nivel": nv, "media": media, "de": de, "min": vmin, "max": vmax})

                if st.form_submit_button("💾 Guardar Lote", type="primary", use_container_width=True):
                    if not num_lote.strip():
                        st.error("El número de lote es obligatorio.")
                    elif not niveles_data:
                        st.error("Active al menos un nivel.")
                    elif any(nv["de"] <= 0 for nv in niveles_data):
                        st.error("La DE debe ser > 0 en todos los niveles activos.")
                    else:
                        try:
                            crud.crear_lote(db, mat_opts[mat_sel], num_lote, fecha_vto, niveles_data)
                            st.success(f"✅ Lote **{num_lote}** registrado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ── Gestión de lotes: ver, activar, desactivar, eliminar ─────────────
        st.markdown("---")
        _section_title("📋 Gestión de Lotes por Analito",
                       "Seleccione el analito y marque qué lote está en uso. Solo un lote puede estar activo a la vez.")

        mat_filtro = st.selectbox("Analito:", list(mat_opts.keys()), key="filtro_lote",
                                  label_visibility="collapsed")
        lotes = crud.listar_lotes(db, mat_opts[mat_filtro], solo_activos=False)

        if not lotes:
            _empty_state("No hay lotes registrados para este analito.")
            return

        hoy = date.today()
        for lote in lotes:
            dias = (lote.fecha_vencimiento - hoy).days
            es_vencido = dias < 0
            en_uso = lote.activo and not es_vencido

            # Badges de estado
            if en_uso:
                badge = "🟢 **En uso**"
            elif lote.activo and es_vencido:
                badge = "🔴 **Vencido** *(activo)*"
            else:
                badge = "⚫ *Inactivo*"

            if dias < 0:
                vto_str = f"⛔ Venció hace {abs(dias)} días"
            elif dias <= 30:
                vto_str = f"⚠️ Vence en {dias} días"
            else:
                vto_str = f"✅ Vence {lote.fecha_vencimiento.strftime('%d/%m/%Y')} ({dias}d)"

            c_nom, c_vto, c_niv, c_act, c_del = st.columns([2.5, 2.8, 0.8, 1.5, 0.6])
            c_nom.markdown(f"**{lote.numero_lote}**  {badge}")
            c_vto.caption(vto_str)
            c_niv.caption(f"{len(lote.niveles)} niv.")

            if lote.activo:
                if c_act.button("⏸ Desactivar", key=f"deact_{lote.id}", use_container_width=True):
                    crud.toggle_activo_lote(db, lote.id)
                    st.rerun()
            else:
                if c_act.button("▶ Activar", key=f"act_{lote.id}", type="primary", use_container_width=True):
                    crud.activar_lote(db, lote.id)
                    st.rerun()

            if c_del.button("🗑️", key=f"del_lote_{lote.id}", use_container_width=True,
                            help="Eliminar lote (solo si no tiene controles registrados)"):
                st.session_state[f"_confirm_lote_{lote.id}"] = True

            # Confirmación de eliminación
            if st.session_state.get(f"_confirm_lote_{lote.id}"):
                st.warning(f"¿Eliminar **{lote.numero_lote}**? Esta acción no se puede deshacer.")
                cc1, cc2 = st.columns(2)
                if cc1.button("✅ Sí, eliminar", key=f"yes_lote_{lote.id}", type="primary", use_container_width=True):
                    ok, msg = crud.eliminar_lote(db, lote.id)
                    st.session_state.pop(f"_confirm_lote_{lote.id}", None)
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
                if cc2.button("❌ Cancelar", key=f"no_lote_{lote.id}", use_container_width=True):
                    st.session_state.pop(f"_confirm_lote_{lote.id}", None)
                    st.rerun()

            # Detalle de niveles plegable
            if lote.niveles:
                with st.expander(f"📊 Estadísticos — {lote.numero_lote}", expanded=False):
                    filas_nv = []
                    for nv in sorted(lote.niveles, key=lambda x: x.nivel):
                        filas_nv.append({
                            "Nivel": nv.nivel,
                            "X̄ (Media)": round(nv.media, 4),
                            "s (DE)": round(nv.de, 4),
                            "CV%": round(nv.de / nv.media * 100, 2) if nv.media else "—",
                            "+2s": round(nv.media + 2 * nv.de, 4),
                            "-2s": round(nv.media - 2 * nv.de, 4),
                            "+3s": round(nv.media + 3 * nv.de, 4),
                            "-3s": round(nv.media - 3 * nv.de, 4),
                            "Mín": round(nv.valor_minimo, 4),
                            "Máx": round(nv.valor_maximo, 4),
                        })
                    st.dataframe(pd.DataFrame(filas_nv), use_container_width=True, hide_index=True)

            st.divider()
    finally:
        db.close()


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _section_title(title: str, subtitle: str = ""):
    st.html(
        f"<div style='margin-bottom:1.1rem;'>"
        f"<div style='font-size:1.05rem; font-weight:700; color:var(--txt-primary,#f1f5f9); margin-bottom:2px;'>{title}</div>"
        f"<div style='font-size:0.8rem; color:var(--txt-muted,#94a3b8);'>{subtitle}</div>"
        f"</div>"
    )


def _empty_state(msg: str):
    st.html(
        "<div style='text-align:center; padding:2.5rem 1rem;"
        " color:var(--txt-muted,#94a3b8); font-size:0.9rem;"
        " background:rgba(255,255,255,0.03);"
        " border-radius:12px; border:1px dashed rgba(255,255,255,0.10);"
        " margin-top:1rem;'>"
        f"<div style='font-size:2rem; margin-bottom:10px;'>📭</div>"
        f"{msg}</div>"
    )


if __name__ == "__main__":
    main()
