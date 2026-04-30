"""
Página de Configuración:
  - Áreas
  - Equipos
  - Personal
  - Analitos / Materiales de control
  - Lotes y niveles (con media, DE, rango)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
from database.database import init_db, get_session
from database import crud

st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")
init_db()
from modules.page_utils import setup_page
setup_page()


def main():
    st.title("⚙️ Configuración del Sistema")
    tab_areas, tab_equipos, tab_personal, tab_analitos, tab_lotes = st.tabs(
        ["🏥 Áreas", "🔧 Equipos", "👤 Personal", "🧪 Analitos", "📦 Lotes"]
    )
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
    st.subheader("Áreas de Laboratorio")
    with st.expander("➕ Nueva Área", expanded=False):
        with st.form("form_area"):
            nombre = st.text_input("Nombre del área *")
            desc = st.text_area("Descripción", height=60)
            if st.form_submit_button("Guardar"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    try:
                        crud.crear_area(db, nombre, desc)
                        st.success(f"Área '{nombre}' creada correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    areas = crud.listar_areas(db, solo_activos=False)
    if areas:
        import pandas as pd
        df = pd.DataFrame([
            {"ID": a.id, "Nombre": a.nombre, "Descripción": a.descripcion or "", "Activo": "✅" if a.activo else "❌"}
            for a in areas
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("**Desactivar área:**")
        area_opts = {f"{a.nombre} (ID {a.id})": a.id for a in areas if a.activo}
        if area_opts:
            sel = st.selectbox("Seleccione área", list(area_opts.keys()), key="del_area")
            if st.button("Desactivar área seleccionada", key="btn_del_area"):
                crud.desactivar_area(db, area_opts[sel])
                st.success("Área desactivada.")
                st.rerun()
    else:
        st.info("No hay áreas registradas.")


# ─── EQUIPOS ─────────────────────────────────────────────────────────────────

def _tab_equipos(db):
    st.subheader("Equipos / Analizadores")
    areas = crud.listar_areas(db)
    if not areas:
        st.warning("Primero debe registrar áreas.")
        return

    area_opts = {a.nombre: a.id for a in areas}

    with st.expander("➕ Nuevo Equipo", expanded=False):
        with st.form("form_equipo"):
            area_sel = st.selectbox("Área *", list(area_opts.keys()))
            nombre = st.text_input("Nombre del equipo *")
            modelo = st.text_input("Modelo")
            serie = st.text_input("N° de serie")
            if st.form_submit_button("Guardar"):
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    try:
                        crud.crear_equipo(db, area_opts[area_sel], nombre, modelo, serie)
                        st.success(f"Equipo '{nombre}' creado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # Filtro por área
    area_filtro = st.selectbox("Filtrar por área", ["Todas"] + list(area_opts.keys()), key="filtro_eq")
    area_id_filtro = area_opts.get(area_filtro) if area_filtro != "Todas" else None
    equipos = crud.listar_equipos(db, area_id=area_id_filtro, solo_activos=False)
    if equipos:
        import pandas as pd
        df = pd.DataFrame([
            {
                "ID": e.id,
                "Área": e.area.nombre,
                "Equipo": e.nombre,
                "Modelo": e.modelo or "",
                "Serie": e.numero_serie or "",
                "Activo": "✅" if e.activo else "❌",
            }
            for e in equipos
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        eq_opts = {f"{e.area.nombre} › {e.nombre} (ID {e.id})": e.id for e in equipos if e.activo}
        if eq_opts:
            sel = st.selectbox("Desactivar equipo:", list(eq_opts.keys()), key="del_eq")
            if st.button("Desactivar equipo seleccionado", key="btn_del_eq"):
                crud.desactivar_equipo(db, eq_opts[sel])
                st.success("Equipo desactivado.")
                st.rerun()
    else:
        st.info("No hay equipos registrados.")


# ─── PERSONAL ────────────────────────────────────────────────────────────────

def _tab_personal(db):
    st.subheader("Personal de Laboratorio")
    with st.expander("➕ Nuevo Personal", expanded=False):
        with st.form("form_personal"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre *")
            apellido = col2.text_input("Apellido *")
            codigo = col1.text_input("Código / Matrícula")
            cargo = col2.text_input("Cargo")
            if st.form_submit_button("Guardar"):
                if not nombre.strip() or not apellido.strip():
                    st.error("Nombre y apellido son obligatorios.")
                else:
                    try:
                        crud.crear_personal(db, nombre, apellido, codigo, cargo)
                        st.success("Personal registrado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    personal = crud.listar_personal(db, solo_activos=False)
    if personal:
        import pandas as pd
        df = pd.DataFrame([
            {
                "ID": p.id,
                "Apellido": p.apellido,
                "Nombre": p.nombre,
                "Código": p.codigo or "",
                "Cargo": p.cargo or "",
                "Activo": "✅" if p.activo else "❌",
            }
            for p in personal
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        pers_opts = {f"{p.apellido}, {p.nombre} (ID {p.id})": p.id for p in personal if p.activo}
        if pers_opts:
            sel = st.selectbox("Desactivar personal:", list(pers_opts.keys()), key="del_pers")
            if st.button("Desactivar personal seleccionado", key="btn_del_pers"):
                crud.desactivar_personal(db, pers_opts[sel])
                st.success("Personal desactivado.")
                st.rerun()
    else:
        st.info("No hay personal registrado.")


# ─── ANALITOS ────────────────────────────────────────────────────────────────

def _tab_analitos(db):
    st.subheader("Analitos / Materiales de Control")
    equipos = crud.listar_equipos(db)
    if not equipos:
        st.warning("Primero debe registrar equipos.")
        return

    eq_opts = {f"{e.area.nombre} › {e.nombre}": e.id for e in equipos}

    with st.expander("➕ Nuevo Analito", expanded=False):
        with st.form("form_analito"):
            eq_sel = st.selectbox("Equipo *", list(eq_opts.keys()))
            col1, col2 = st.columns(2)
            analito = col1.text_input("Nombre del analito *")
            proveedor = col2.text_input("Proveedor / Marca *")
            unidad = col1.text_input("Unidad de medida (ej: mg/dL)")
            nombre_mat = col2.text_input("Nombre del material de control")
            if st.form_submit_button("Guardar"):
                if not analito.strip() or not proveedor.strip():
                    st.error("Analito y proveedor son obligatorios.")
                else:
                    try:
                        crud.crear_material(db, eq_opts[eq_sel], analito, proveedor, unidad, nombre_mat)
                        st.success(f"Analito '{analito}' registrado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    eq_filtro = st.selectbox("Filtrar por equipo:", ["Todos"] + list(eq_opts.keys()), key="filtro_mat")
    eq_id_filtro = eq_opts.get(eq_filtro) if eq_filtro != "Todos" else None
    materiales = crud.listar_materiales(db, equipo_id=eq_id_filtro, solo_activos=False)

    if materiales:
        import pandas as pd
        df = pd.DataFrame([
            {
                "ID": m.id,
                "Área": m.equipo.area.nombre,
                "Equipo": m.equipo.nombre,
                "Analito": m.analito,
                "Proveedor": m.proveedor,
                "Unidad": m.unidad or "",
                "Material": m.nombre_material or "",
                "Activo": "✅" if m.activo else "❌",
            }
            for m in materiales
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay analitos registrados.")


# ─── LOTES ───────────────────────────────────────────────────────────────────

def _tab_lotes(db):
    st.subheader("Lotes de Reactivo / Control")
    materiales = crud.listar_materiales(db)
    if not materiales:
        st.warning("Primero debe registrar analitos.")
        return

    mat_opts = {f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito} [{m.proveedor}]": m.id for m in materiales}

    with st.expander("➕ Nuevo Lote", expanded=True):
        with st.form("form_lote"):
            mat_sel = st.selectbox("Analito / Material *", list(mat_opts.keys()))
            col1, col2 = st.columns(2)
            num_lote = col1.text_input("Número de lote *")
            fecha_vto = col2.date_input("Fecha de vencimiento *", min_value=date.today())

            st.markdown("**Niveles del lote** (complete los niveles que apliquen):")
            niveles_data = []
            for nv in [1, 2, 3]:
                with st.expander(f"Nivel {nv}", expanded=(nv == 1)):
                    activo_nv = st.checkbox(f"Incluir Nivel {nv}", value=(nv == 1), key=f"nv_activo_{nv}")
                    if activo_nv:
                        c1, c2, c3, c4 = st.columns(4)
                        media = c1.number_input(f"Media objetivo (X̄)", key=f"media_{nv}", format="%.4f")
                        de = c2.number_input(f"DE objetivo (s)", min_value=0.0, key=f"de_{nv}", format="%.4f")
                        vmin = c3.number_input(f"Valor mínimo", key=f"vmin_{nv}", format="%.4f")
                        vmax = c4.number_input(f"Valor máximo", key=f"vmax_{nv}", format="%.4f")
                        niveles_data.append({"nivel": nv, "media": media, "de": de, "min": vmin, "max": vmax})

            if st.form_submit_button("Guardar Lote"):
                if not num_lote.strip():
                    st.error("El número de lote es obligatorio.")
                elif not niveles_data:
                    st.error("Debe incluir al menos un nivel.")
                else:
                    invalidos = [nv for nv in niveles_data if nv["de"] <= 0]
                    if invalidos:
                        st.error(f"La DE debe ser mayor a 0 en todos los niveles.")
                    else:
                        try:
                            crud.crear_lote(db, mat_opts[mat_sel], num_lote, fecha_vto, niveles_data)
                            st.success(f"Lote '{num_lote}' creado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    st.markdown("---")
    st.subheader("Lotes registrados")
    mat_filtro = st.selectbox("Ver lotes de:", list(mat_opts.keys()), key="filtro_lote")
    lotes = crud.listar_lotes(db, mat_opts[mat_filtro], solo_activos=False)

    if lotes:
        import pandas as pd
        filas = []
        for lote in lotes:
            vencido = lote.fecha_vencimiento < date.today()
            for nv in lote.niveles:
                filas.append({
                    "Lote": lote.numero_lote,
                    "Vence": lote.fecha_vencimiento,
                    "Estado": "VENCIDO" if vencido else ("Activo" if lote.activo else "Inactivo"),
                    "Nivel": nv.nivel,
                    "Media": nv.media,
                    "DE": nv.de,
                    "Mín": nv.valor_minimo,
                    "Máx": nv.valor_maximo,
                    "+2s": round(nv.media + 2 * nv.de, 4),
                    "-2s": round(nv.media - 2 * nv.de, 4),
                    "+3s": round(nv.media + 3 * nv.de, 4),
                    "-3s": round(nv.media - 3 * nv.de, 4),
                })
        df = pd.DataFrame(filas)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay lotes registrados para este analito.")


if __name__ == "__main__":
    main()
