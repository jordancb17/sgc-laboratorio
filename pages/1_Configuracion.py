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
    db = get_session()
    try:
        with tab_areas:
            _tab_areas(db)
        with tab_equipos:
            _tab_equipos(db)
        with tab_personal:
            _tab_personal(db)
        with tab_grupos:
            _tab_grupos(db)
        with tab_analitos:
            _tab_analitos(db)
        with tab_lotes:
            _tab_lotes(db)
    finally:
        db.close()


# ─── ÁREAS ───────────────────────────────────────────────────────────────────

def _tab_areas(db):
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

    # ── Editar / Cambiar estado ──
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
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        if toggling:
            nuevo_estado = crud.toggle_activo_area(db, area_id_sel)
            label = "activada ✅" if nuevo_estado else "desactivada ⛔"
            st.info(f"Área **{area_obj.nombre}** {label}.")
            st.rerun()

        if del_btn:
            st.session_state["_confirm_del_area"] = area_id_sel

    # Confirmación de eliminación (fuera del form)
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


# ─── EQUIPOS ─────────────────────────────────────────────────────────────────

def _tab_equipos(db):
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    # ── Lista de equipos ──
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

    # ── Editar / Cambiar estado ──
    st.markdown("---")
    _section_title("✏️ Editar o Cambiar Estado")

    # Cargar todos los equipos sin filtro para la gestión
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
        # Encontrar el índice del área actual en area_opts
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

    # Confirmación de eliminación (fuera del form)
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


# ─── PERSONAL ────────────────────────────────────────────────────────────────

def _tab_personal(db):
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

    # ── Editar / Cambiar estado ──
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

    # Confirmación de eliminación (fuera del form)
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


# ─── GRUPOS DE PRUEBAS ────────────────────────────────────────────────────────

def _tab_grupos(db):
    _section_title("📋 Grupos de Pruebas (Paneles)",
                   "Agrupe analitos que se miden juntos: Hemograma, Gases Arteriales, Electrolitos, etc.")

    equipos = crud.listar_equipos(db)
    if not equipos:
        st.warning("⚠️ Primero debe registrar **Equipos**.")
        return
    eq_opts = {f"{e.area.nombre} › {e.nombre}": e.id for e in equipos}

    # ── Crear desde plantilla predefinida ──────────────────────────────────────
    with st.expander("⚡ Crear Panel desde Plantilla", expanded=False):
        st.info(
            "Seleccione una plantilla, **marque solo los parámetros** que mide su equipo, "
            "edite los nombres o unidades si su equipo los llama diferente, "
            "y agregue los que no estén en la lista."
        )

        # ── Selectores superiores ────────────────────────────────────────────
        col1, col2 = st.columns(2)
        plantilla_sel = col1.selectbox("Plantilla base", list(PANELES_PREDEFINIDOS.keys()), key="plt_sel")
        eq_plantilla  = col2.selectbox("Equipo *", list(eq_opts.keys()), key="plt_eq")
        col3, col4 = st.columns(2)
        # Nombre sugerido = texto de la plantilla sin el emoji
        _nom_sug = " ".join(plantilla_sel.split(" ")[1:]).split("—")[-1].strip() if "—" in plantilla_sel else " ".join(plantilla_sel.split(" ")[1:])
        nombre_grupo_plt = col3.text_input("Nombre del grupo *", value=_nom_sug, key="plt_nombre")
        proveedor_plt    = col4.text_input("Proveedor material de control *",
                                           placeholder="ej. Bio-Rad, Roche, Sysmex", key="plt_prov")
        desc_plt = st.text_input("Descripción (opcional)", key="plt_desc")

        # Resetear parámetros personalizados al cambiar de plantilla
        if st.session_state.get("_plt_last") != plantilla_sel:
            st.session_state["_plt_last"]   = plantilla_sel
            st.session_state["_plt_custom"] = []

        params_base = PANELES_PREDEFINIDOS[plantilla_sel]

        # ── Tabla editable de parámetros de la plantilla ─────────────────────
        st.markdown(f"**Parámetros de la plantilla** — marque los que aplican a su equipo ({len(params_base)} en total):")

        h0, h1, h2 = st.columns([0.5, 4, 2])
        h0.caption("✓")
        h1.caption("Nombre del analito (editable)")
        h2.caption("Unidad (editable)")

        params_seleccionados = []
        for i, (nom_def, uni_def) in enumerate(params_base):
            c0, c1, c2 = st.columns([0.5, 4, 2])
            incluido = c0.checkbox("", value=True, key=f"plt_chk_{i}", label_visibility="collapsed")
            nom_edit = c1.text_input("n", value=nom_def, key=f"plt_nom_{i}", label_visibility="collapsed",
                                     disabled=not incluido)
            uni_edit = c2.text_input("u", value=uni_def, key=f"plt_uni_{i}", label_visibility="collapsed",
                                     disabled=not incluido)
            if incluido:
                params_seleccionados.append((nom_edit.strip(), uni_edit.strip()))

        # ── Parámetros personalizados (los que no están en la plantilla) ──────
        st.markdown("---")
        st.markdown("**Agregar parámetros que no están en la plantilla** (ej. parámetros exclusivos de su equipo):")

        custom_params = st.session_state.get("_plt_custom", [])

        # Listar los ya agregados
        if custom_params:
            for j, (cn, cu) in enumerate(custom_params):
                cj0, cj1, cj2, cj3 = st.columns([0.5, 4, 2, 0.5])
                cj0.markdown("✅")
                cj1.markdown(f"**{cn}**")
                cj2.markdown(f"`{cu or '—'}`")
                if cj3.button("🗑️", key=f"plt_del_cp_{j}", help="Quitar"):
                    custom_params.pop(j)
                    st.session_state["_plt_custom"] = custom_params
                    st.rerun()

        # Input para nuevo parámetro
        na0, na1, na2, na3 = st.columns([0.5, 4, 2, 0.5])
        nuevo_nom_p = na1.text_input("Nombre", key="plt_cp_nom",
                                     placeholder="ej. Granulocitos Inmaduros #",
                                     label_visibility="collapsed")
        nuevo_uni_p = na2.text_input("Unidad", key="plt_cp_uni",
                                     placeholder="ej. ×10³/µL",
                                     label_visibility="collapsed")
        if na3.button("➕", key="plt_btn_add_cp", help="Agregar parámetro"):
            if nuevo_nom_p.strip():
                custom_params.append((nuevo_nom_p.strip(), nuevo_uni_p.strip()))
                st.session_state["_plt_custom"] = custom_params
                st.rerun()
            else:
                st.warning("Escriba el nombre del parámetro antes de agregar.")

        # ── Resumen y botón crear ─────────────────────────────────────────────
        todos_params = params_seleccionados + custom_params
        st.markdown("---")
        col_res, col_btn = st.columns([3, 1])
        col_res.info(
            f"✅ **{len(params_seleccionados)}** de la plantilla   +   "
            f"➕ **{len(custom_params)}** personalizados   =   "
            f"**{len(todos_params)} parámetros** en total"
        )
        if col_btn.button("🚀 Crear Panel", type="primary", key="btn_crear_plantilla", use_container_width=True):
            if not nombre_grupo_plt.strip():
                st.error("El nombre del grupo es obligatorio.")
            elif not proveedor_plt.strip():
                st.error("El proveedor del material de control es obligatorio.")
            elif not todos_params:
                st.error("Seleccione al menos un parámetro.")
            else:
                try:
                    grupo, mats = crud.crear_panel_desde_plantilla(
                        db, eq_opts[eq_plantilla],
                        nombre_grupo_plt, desc_plt, proveedor_plt, todos_params,
                    )
                    st.session_state["_plt_custom"] = []
                    st.success(
                        f"✅ Panel **{grupo.nombre}** creado con **{len(mats)} parámetros**. "
                        f"Vaya a **📦 Lotes** para registrar los valores objetivo."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Crear grupo manualmente ────────────────────────────────────────────────
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

    # ── Lista de grupos ────────────────────────────────────────────────────────
    grupos = crud.listar_grupos(db, solo_activos=False)
    if not grupos:
        _empty_state("No hay grupos de pruebas registrados. Use una plantilla o cree uno manualmente.")
        return

    st.markdown(f"**{len(grupos)} grupo(s) registrado(s)**")
    filas_g = []
    for g in grupos:
        mats_g = [m for m in g.materiales]
        filas_g.append({
            "ID": g.id,
            "Equipo": g.equipo.nombre,
            "Área": g.equipo.area.nombre,
            "Grupo / Panel": g.nombre,
            "Descripción": g.descripcion or "—",
            "Analitos": len(mats_g),
            "Con lote": sum(1 for m in mats_g if crud.get_lote_activo(db, m.id)),
            "Estado": "✅ Activo" if g.activo else "⛔ Inactivo",
        })
    st.dataframe(pd.DataFrame(filas_g), use_container_width=True, hide_index=True)

    # ── Detalle del grupo seleccionado ────────────────────────────────────────
    st.markdown("---")
    grp_opts = {
        f"{'✅' if g.activo else '⛔'} {g.equipo.nombre} › {g.nombre}": g.id
        for g in grupos
    }
    sel_g = st.selectbox("Seleccione un grupo para gestionar:", list(grp_opts.keys()),
                         key="sel_grp_edit", label_visibility="collapsed")
    grp_id_sel = grp_opts[sel_g]
    grp_obj = next(g for g in grupos if g.id == grp_id_sel)

    # Analitos del grupo
    mats_del_grupo = [m for m in grp_obj.materiales]
    if mats_del_grupo:
        st.markdown(f"**Parámetros de «{grp_obj.nombre}»** — {len(mats_del_grupo)} analitos:")
        filas_m = []
        for m in mats_del_grupo:
            lote_a = crud.get_lote_activo(db, m.id)
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

    # ── Editar / Estado / Eliminar ─────────────────────────────────────────────
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
        st.warning(f"⚠️ ¿Eliminar el grupo **{grp_obj.nombre}**? Los analitos NO se borran, solo se desvinculan del grupo.")
        c1, c2 = st.columns(2)
        if c1.button("✅ Sí, eliminar grupo", key="btn_grp_del_yes", type="primary", use_container_width=True):
            ok, msg = crud.eliminar_grupo(db, grp_id_sel)
            st.session_state.pop("_confirm_del_grp", None)
            st.success(msg) if ok else st.error(msg)
            st.rerun()
        if c2.button("❌ Cancelar", key="btn_grp_del_no", use_container_width=True):
            st.session_state.pop("_confirm_del_grp", None)
            st.rerun()


# ─── ANALITOS / MATERIALES DE CONTROL ────────────────────────────────────────

def _tab_analitos(db):
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
            # Selector de grupo (opcional)
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
        "Marca equipo": m.equipo.marca or "—",
        "Analito": m.analito,
        "Proveedor": m.proveedor,
        "Unidad": m.unidad or "—",
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
        # Selector de equipo
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

        # Selector de grupo
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

    # Confirmación de eliminación (fuera del form)
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


# ─── LOTES ───────────────────────────────────────────────────────────────────

def _tab_lotes(db):
    _section_title("📦 Lotes de Reactivo / Material de Control",
                   "Registre lotes con su fecha de vencimiento y los valores objetivo por nivel (media, DE, rango aceptable).")

    # ── Registrar lote para un grupo completo ─────────────────────────────────
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
            num_lote_g   = col1.text_input("Número de lote *", placeholder="ej. LOT-2025-001", key="gl_num")
            fecha_vto_g  = col2.date_input("Fecha de vencimiento *", min_value=date.today(), key="gl_fecha")
            n_niveles_g  = col3.selectbox("Niveles a registrar *", [1, 2, 3], key="gl_niv")

            st.markdown(f"**Complete los valores objetivo para cada parámetro de «{grp_lote_obj.nombre}»:**")

            # Cabecera de columnas
            header_cols = st.columns([2] + [1, 1, 1, 1] * n_niveles_g)
            header_cols[0].markdown("**Analito (unidad)**")
            for nv_i in range(n_niveles_g):
                base = 1 + nv_i * 4
                header_cols[base].markdown(f"**L{nv_i+1} — X̄**")
                header_cols[base+1].markdown(f"**L{nv_i+1} — s**")
                header_cols[base+2].markdown(f"**L{nv_i+1} — Mín**")
                header_cols[base+3].markdown(f"**L{nv_i+1} — Máx**")

            targets_g = {}
            for m in mats_grp_activos:
                row_cols = st.columns([2] + [1, 1, 1, 1] * n_niveles_g)
                row_cols[0].markdown(f"**{m.analito}** ({m.unidad or '—'})")
                niveles_data_g = []
                for nv_i in range(n_niveles_g):
                    base = 1 + nv_i * 4
                    media_v = row_cols[base].number_input("X̄", format="%.4f",
                                                          key=f"gl_m{m.id}_nv{nv_i+1}_media",
                                                          label_visibility="collapsed")
                    de_v    = row_cols[base+1].number_input("s", min_value=0.0001, format="%.4f",
                                                            key=f"gl_m{m.id}_nv{nv_i+1}_de",
                                                            label_visibility="collapsed")
                    vmin_v  = row_cols[base+2].number_input("Mín", format="%.4f",
                                                             key=f"gl_m{m.id}_nv{nv_i+1}_min",
                                                             label_visibility="collapsed")
                    vmax_v  = row_cols[base+3].number_input("Máx", format="%.4f",
                                                             key=f"gl_m{m.id}_nv{nv_i+1}_max",
                                                             label_visibility="collapsed")
                    niveles_data_g.append({"nivel": nv_i+1, "media": media_v, "de": de_v,
                                           "min": vmin_v, "max": vmax_v})
                targets_g[m.id] = niveles_data_g

            if st.button("💾 Guardar Lote para Todo el Panel", type="primary", key="btn_gl_save"):
                if not num_lote_g.strip():
                    st.error("El número de lote es obligatorio.")
                else:
                    invalidos = []
                    for mat_id_g, nivs in targets_g.items():
                        for nv in nivs:
                            if nv["de"] <= 0:
                                mat_name = next(m.analito for m in mats_grp_activos if m.id == mat_id_g)
                                invalidos.append(f"{mat_name} Nivel {nv['nivel']}: DE debe ser > 0")
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
                            f"✅ Lote **{num_lote_g}** registrado para {creados_g} analito(s) del panel «{grp_lote_obj.nombre}»."
                        )
                        st.rerun()

    st.markdown("---")
    materiales = crud.listar_materiales(db)
    if not materiales:
        st.warning("⚠️ Primero debe registrar **Analitos**.")
        return

    mat_opts = {
        f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito} [{m.proveedor}]": m.id
        for m in materiales
    }

    with st.expander("➕ Registrar Nuevo Lote", expanded=True):
        with st.form("form_lote"):
            mat_sel = st.selectbox("Analito / Material de control *", list(mat_opts.keys()))
            col1, col2 = st.columns(2)
            num_lote   = col1.text_input("Número de lote *", placeholder="ej. LOT-2024-001")
            fecha_vto  = col2.date_input("Fecha de vencimiento *", min_value=date.today())

            st.markdown("---")
            st.markdown("**Niveles del lote** — complete los que correspondan:")

            niveles_data = []
            for nv in [1, 2, 3]:
                with st.expander(f"Nivel {nv}", expanded=(nv == 1)):
                    activo_nv = st.checkbox(f"Incluir Nivel {nv}", value=(nv == 1), key=f"nv_activo_{nv}")
                    if activo_nv:
                        c1, c2, c3, c4 = st.columns(4)
                        media = c1.number_input("Media objetivo (X̄)", key=f"media_{nv}", format="%.4f",
                                                help="Valor central de referencia del fabricante")
                        de    = c2.number_input("DE objetivo (s)", min_value=0.0001, key=f"de_{nv}", format="%.4f",
                                                help="Desviación estándar de referencia del fabricante")
                        vmin  = c3.number_input("Valor mínimo", key=f"vmin_{nv}", format="%.4f",
                                                help="Límite inferior aceptable (suele ser X̄ − 3s)")
                        vmax  = c4.number_input("Valor máximo", key=f"vmax_{nv}", format="%.4f",
                                                help="Límite superior aceptable (suele ser X̄ + 3s)")
                        niveles_data.append({"nivel": nv, "media": media, "de": de, "min": vmin, "max": vmax})

            submitted = st.form_submit_button("💾 Guardar Lote", type="primary", use_container_width=True)
            if submitted:
                if not num_lote.strip():
                    st.error("El número de lote es obligatorio.")
                elif not niveles_data:
                    st.error("Debe incluir al menos un nivel.")
                else:
                    invalidos = [nv for nv in niveles_data if nv["de"] <= 0]
                    if invalidos:
                        st.error("La DE debe ser mayor a 0 en todos los niveles.")
                    else:
                        try:
                            crud.crear_lote(db, mat_opts[mat_sel], num_lote, fecha_vto, niveles_data)
                            st.success(f"✅ Lote **{num_lote}** registrado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")

    st.markdown("---")
    _section_title("📋 Lotes Registrados", "Consulte los lotes y sus parámetros estadísticos por nivel.")
    mat_filtro = st.selectbox("Ver lotes de:", list(mat_opts.keys()), key="filtro_lote")
    lotes = crud.listar_lotes(db, mat_opts[mat_filtro], solo_activos=False)

    if not lotes:
        _empty_state("No hay lotes registrados para este analito.")
        return

    filas = []
    hoy = date.today()
    for lote in lotes:
        dias_vto = (lote.fecha_vencimiento - hoy).days
        if dias_vto < 0:
            estado_vto = "⛔ Vencido"
        elif dias_vto <= 30:
            estado_vto = f"⚠️ Vence en {dias_vto}d"
        else:
            estado_vto = f"✅ Vigente ({dias_vto}d)"

        for nv in lote.niveles:
            filas.append({
                "Lote": lote.numero_lote,
                "Vencimiento": lote.fecha_vencimiento.strftime("%d/%m/%Y"),
                "Estado": estado_vto,
                "Nivel": nv.nivel,
                "Media (X̄)": round(nv.media, 4),
                "DE (s)": round(nv.de, 4),
                "CV%": round(nv.de / nv.media * 100, 2) if nv.media else "—",
                "Mín": round(nv.valor_minimo, 4),
                "Máx": round(nv.valor_maximo, 4),
                "+2s": round(nv.media + 2 * nv.de, 4),
                "-2s": round(nv.media - 2 * nv.de, 4),
                "+3s": round(nv.media + 3 * nv.de, 4),
                "-3s": round(nv.media - 3 * nv.de, 4),
            })
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


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
