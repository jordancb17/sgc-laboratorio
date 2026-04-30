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

    activas = [a for a in areas if a.activo]
    if activas:
        st.markdown("---")
        st.markdown("**Desactivar área:**")
        area_opts = {f"{a.nombre}": a.id for a in activas}
        col1, col2 = st.columns([3, 1])
        sel = col1.selectbox("Seleccione el área a desactivar", list(area_opts.keys()), key="del_area", label_visibility="collapsed")
        if col2.button("⛔ Desactivar", key="btn_del_area", use_container_width=True):
            crud.desactivar_area(db, area_opts[sel])
            st.warning(f"Área **{sel}** desactivada.")
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

    activos = [e for e in equipos if e.activo]
    if activos:
        st.markdown("---")
        eq_opts = {f"{e.area.nombre} › {e.nombre} ({e.marca or '—'})": e.id for e in activos}
        col1, col2 = st.columns([3, 1])
        sel = col1.selectbox("Equipo a desactivar:", list(eq_opts.keys()), key="del_eq", label_visibility="collapsed")
        if col2.button("⛔ Desactivar", key="btn_del_eq", use_container_width=True):
            crud.desactivar_equipo(db, eq_opts[sel])
            st.warning(f"Equipo desactivado.")
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

    activos = [p for p in personal if p.activo]
    if activos:
        st.markdown("---")
        pers_opts = {f"{p.apellido}, {p.nombre} — {p.cargo or 'sin cargo'}": p.id for p in activos}
        col1, col2 = st.columns([3, 1])
        sel = col1.selectbox("Personal a desactivar:", list(pers_opts.keys()), key="del_pers", label_visibility="collapsed")
        if col2.button("⛔ Desactivar", key="btn_del_pers", use_container_width=True):
            crud.desactivar_personal(db, pers_opts[sel])
            st.warning("Personal desactivado.")
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
    st.markdown(f"""
    <div style="margin-bottom:1.1rem;">
        <div style="font-size:1.05rem; font-weight:700; color:var(--txt-primary,#0a1628); margin-bottom:2px;">
            {title}
        </div>
        <div style="font-size:0.8rem; color:var(--txt-muted,#94a3b8);">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def _empty_state(msg: str):
    st.markdown(f"""
    <div style="
        text-align:center; padding:2.5rem 1rem;
        color:var(--txt-muted,#94a3b8); font-size:0.9rem;
        background:var(--surface-2,#f8fafc);
        border-radius:12px; border:1px dashed var(--border,#e2e8f0);
        margin-top:1rem;
    ">
        <div style="font-size:2rem; margin-bottom:10px;">📭</div>
        {msg}
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
