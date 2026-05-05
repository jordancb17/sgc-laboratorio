"""
Configuración del sistema: Áreas, Equipos (con Marca), Personal, Analitos y Lotes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date

from database.database import init_db, get_session
from database import crud
from modules.page_utils import setup_page, page_header

st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="⚙️",
        title="Configuración del Sistema",
        subtitle="Gestione áreas, equipos, personal, analitos y lotes de control",
        badge="Administración",
    )

    tab_areas, tab_equipos, tab_personal, tab_analitos, tab_lotes = st.tabs([
        "🏥 Áreas", "🔬 Equipos", "👤 Personal", "🧪 Analitos / Materiales", "📦 Lotes",
    ])
    db = get_session()
    try:
        with tab_areas:
            _tab_areas(db)
        with tab_equipos:
            _tab_equipos(db)
        with tab_personal:
            _tab_personal(db)
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
        col_s, col_t = st.columns(2)
        guardar  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
        toggling = col_t.form_submit_button(estado_label, use_container_width=True)

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
        col_s, col_t = st.columns(2)
        guardar  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
        toggling = col_t.form_submit_button(estado_label, use_container_width=True)

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
        col_s, col_t = st.columns(2)
        guardar  = col_s.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
        toggling = col_t.form_submit_button(estado_label, use_container_width=True)

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
            submitted  = st.form_submit_button("💾 Guardar Analito", type="primary", use_container_width=True)
            if submitted:
                if not analito.strip() or not proveedor.strip():
                    st.error("El nombre del analito y el proveedor son obligatorios.")
                else:
                    try:
                        crud.crear_material(db, eq_opts[eq_sel], analito, proveedor, unidad, nombre_mat)
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

    # ── Activar / Desactivar analito ──
    if materiales:
        st.markdown("---")
        _section_title("🔄 Cambiar Estado de Analito")
        mat_opts_all = {
            f"{'✅' if m.activo else '⛔'} {m.equipo.nombre} › {m.analito}": m.id
            for m in crud.listar_materiales(db, solo_activos=False)
        }
        sel_mat = st.selectbox("Seleccione el analito:", list(mat_opts_all.keys()),
                               key="sel_mat_toggle", label_visibility="collapsed")
        mat_id_sel = mat_opts_all[sel_mat]
        mat_obj = next(m for m in crud.listar_materiales(db, solo_activos=False) if m.id == mat_id_sel)
        estado_label = "✅ Activar" if not mat_obj.activo else "⛔ Desactivar"
        if st.button(estado_label, key="btn_toggle_mat"):
            mat_obj.activo = not mat_obj.activo
            db.commit()
            label = "activado ✅" if mat_obj.activo else "desactivado ⛔"
            st.info(f"Analito **{mat_obj.analito}** {label}.")
            st.rerun()


# ─── LOTES ───────────────────────────────────────────────────────────────────

def _tab_lotes(db):
    _section_title("📦 Lotes de Reactivo / Material de Control",
                   "Registre lotes con su fecha de vencimiento y los valores objetivo por nivel (media, DE, rango aceptable).")

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
