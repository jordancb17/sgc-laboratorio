"""
Carga Masiva de Controles — ingreso rápido de múltiples valores históricos.
Permite registrar semanas o meses de controles en una sola operación
usando una cuadrícula similar a una hoja de cálculo.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date, time, timedelta, datetime

from database.database import init_db, get_session
from database import crud
from database.models import TURNOS
from modules.page_utils import setup_page, page_header
from modules.westgard import evaluar_westgard

st.set_page_config(page_title="Carga Masiva", page_icon="📥", layout="wide")
init_db()
setup_page()


def main():
    page_header(
        icon="📥",
        title="Carga Masiva de Controles",
        subtitle="Ingrese múltiples valores históricos de forma rápida — días, semanas o meses en una sola operación",
        badge="Regularización Masiva",
    )

    st.info(
        "**¿Cuándo usar esta herramienta?** Cuando tiene controles atrasados de varios días o meses "
        "y registrarlos uno a uno sería muy lento. Complete la cuadrícula, revise la vista previa "
        "y confirme la carga en lote.",
        icon="💡",
    )

    db = get_session()
    try:
        _carga_masiva(db)
    finally:
        db.close()


def _carga_masiva(db):
    # ── PASO 1: Selección de analito ─────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem;">
        <div style="background:linear-gradient(135deg,#0a1f42,#1a3a8f);color:white;
            border-radius:50%;width:32px;height:32px;display:flex;align-items:center;
            justify-content:center;font-weight:800;font-size:0.9rem;flex-shrink:0;">1</div>
        <div style="font-size:1rem;font-weight:700;color:var(--txt-primary,#0a1628);">
            Seleccione el analito y lote
        </div>
    </div>
    """, unsafe_allow_html=True)

    areas = crud.listar_areas(db)
    if not areas:
        st.warning("No hay áreas configuradas.")
        return

    col1, col2, col3 = st.columns(3)
    area_opts = {a.nombre: a.id for a in areas}
    area_sel  = col1.selectbox("Área", list(area_opts.keys()), key="cm_area")

    equipos = crud.listar_equipos(db, area_id=area_opts[area_sel])
    if not equipos:
        col2.warning("Sin equipos en esta área.")
        return
    eq_opts = {f"{e.nombre} [{e.marca or '—'}]": e.id for e in equipos}
    eq_sel  = col2.selectbox("Equipo", list(eq_opts.keys()), key="cm_equipo")

    materiales = crud.listar_materiales(db, equipo_id=eq_opts[eq_sel])
    if not materiales:
        col3.warning("Sin analitos en este equipo.")
        return
    mat_opts = {m.analito: m.id for m in materiales}
    mat_sel  = col3.selectbox("Analito", list(mat_opts.keys()), key="cm_analito")

    material_id = mat_opts[mat_sel]
    material    = next(m for m in materiales if m.id == material_id)

    # ── Selección de lote y niveles ──────────────────────────────────────────
    lotes = crud.listar_lotes(db, material_id, solo_activos=True)
    if not lotes:
        st.warning("No hay lotes activos para este analito. Regístrelos en ⚙️ Configuración.")
        return

    col_l, col_p, col_t = st.columns(3)
    lote_opts = {f"{l.numero_lote} (vence {l.fecha_vencimiento})": l.id for l in lotes}
    lote_sel  = col_l.selectbox("Lote de control", list(lote_opts.keys()), key="cm_lote")
    lote_id   = lote_opts[lote_sel]
    lote      = next(l for l in lotes if l.id == lote_id)

    personal   = crud.listar_personal(db)
    pers_opts  = {f"{p.apellido}, {p.nombre}": p.id for p in personal}
    pers_sel   = col_p.selectbox("Responsable", list(pers_opts.keys()), key="cm_pers")
    turno_def  = col_t.selectbox("Turno por defecto", TURNOS, key="cm_turno")

    niveles_disponibles = sorted([nv.nivel for nv in lote.niveles])
    nivel_map = {nv.nivel: nv for nv in lote.niveles}

    st.markdown("---")

    # ── PASO 2: Rango de fechas ──────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem;">
        <div style="background:linear-gradient(135deg,#0a1f42,#1a3a8f);color:white;
            border-radius:50%;width:32px;height:32px;display:flex;align-items:center;
            justify-content:center;font-weight:800;font-size:0.9rem;flex-shrink:0;">2</div>
        <div style="font-size:1rem;font-weight:700;color:var(--txt-primary,#0a1628);">
            Defina el período a cargar
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_d1, col_d2, col_freq, col_hora = st.columns(4)
    fecha_desde = col_d1.date_input("Desde", value=date.today() - timedelta(days=30), key="cm_desde")
    fecha_hasta = col_d2.date_input("Hasta", value=date.today(), key="cm_hasta", max_value=date.today())
    frecuencia  = col_freq.selectbox("Frecuencia", ["Diario", "Días de semana (L-V)", "Personalizado"], key="cm_freq")
    hora_def    = col_hora.time_input("Hora por defecto", value=time(8, 0), key="cm_hora")

    # Generar lista de fechas
    if frecuencia == "Diario":
        fechas = [fecha_desde + timedelta(days=i)
                  for i in range((fecha_hasta - fecha_desde).days + 1)]
    elif frecuencia == "Días de semana (L-V)":
        fechas = [fecha_desde + timedelta(days=i)
                  for i in range((fecha_hasta - fecha_desde).days + 1)
                  if (fecha_desde + timedelta(days=i)).weekday() < 5]
    else:
        fechas = [fecha_desde + timedelta(days=i)
                  for i in range((fecha_hasta - fecha_desde).days + 1)]

    if len(fechas) > 120:
        st.warning(f"El rango genera {len(fechas)} filas. Se limitará a los primeros 120 días.")
        fechas = fechas[:120]

    st.caption(f"Se generarán **{len(fechas)} filas** — una por fecha, con {len(niveles_disponibles)} nivel(es).")

    st.markdown("---")

    # ── PASO 3: Cuadrícula de datos ──────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem;">
        <div style="background:linear-gradient(135deg,#0a1f42,#1a3a8f);color:white;
            border-radius:50%;width:32px;height:32px;display:flex;align-items:center;
            justify-content:center;font-weight:800;font-size:0.9rem;flex-shrink:0;">3</div>
        <div style="font-size:1rem;font-weight:700;color:var(--txt-primary,#0a1628);">
            Complete la cuadrícula de valores
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar referencia de valores objetivo
    with st.expander("📋 Valores objetivo del lote (referencia)", expanded=False):
        ref_filas = []
        for nv in sorted(lote.niveles, key=lambda x: x.nivel):
            ref_filas.append({
                "Nivel": nv.nivel,
                "Media (X̄)": round(nv.media, 4),
                "DE (s)": round(nv.de, 4),
                "CV%": round(nv.de / nv.media * 100, 2) if nv.media else "—",
                "-3s": round(nv.media - 3*nv.de, 4),
                "-2s": round(nv.media - 2*nv.de, 4),
                "+2s": round(nv.media + 2*nv.de, 4),
                "+3s": round(nv.media + 3*nv.de, 4),
                "Unidad": material.unidad or "—",
            })
        st.dataframe(pd.DataFrame(ref_filas), use_container_width=True, hide_index=True)

    # Construir DataFrame inicial para el editor
    col_defs = {}
    filas_init = []
    for f in fechas:
        fila: dict = {
            "Fecha": f,
            "Hora": hora_def.strftime("%H:%M"),
            "Turno": turno_def,
            "Incluir": True,
            "Observación": "",
        }
        for nv in niveles_disponibles:
            fila[f"Nivel {nv}"] = None
        filas_init.append(fila)

    df_init = pd.DataFrame(filas_init)

    # Configuración de columnas para data_editor
    column_config = {
        "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", required=True),
        "Hora": st.column_config.TextColumn("Hora", help="Formato HH:MM, ej: 08:30"),
        "Turno": st.column_config.SelectboxColumn("Turno", options=TURNOS),
        "Incluir": st.column_config.CheckboxColumn("✓", help="Desmarque para excluir esta fila"),
        "Observación": st.column_config.TextColumn("Obs.", help="Observación opcional"),
    }
    for nv in niveles_disponibles:
        nl = nivel_map[nv]
        column_config[f"Nivel {nv}"] = st.column_config.NumberColumn(
            f"Nivel {nv}",
            help=f"X̄={nl.media:.4f} ± 2s [{nl.media-2*nl.de:.4f} – {nl.media+2*nl.de:.4f}]",
            format="%.4f",
            min_value=0.0,
        )

    df_edited = st.data_editor(
        df_init,
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic",
        key="cm_grid",
        hide_index=True,
    )

    st.markdown("---")

    # ── PASO 4: Vista previa y confirmación ──────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem;">
        <div style="background:linear-gradient(135deg,#0a1f42,#1a3a8f);color:white;
            border-radius:50%;width:32px;height:32px;display:flex;align-items:center;
            justify-content:center;font-weight:800;font-size:0.9rem;flex-shrink:0;">4</div>
        <div style="font-size:1rem;font-weight:700;color:var(--txt-primary,#0a1628);">
            Vista previa y confirmación
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_prev, col_conf = st.columns([1, 1])

    if col_prev.button("🔍 Vista previa — Evaluar Westgard", use_container_width=True):
        _mostrar_preview(df_edited, nivel_map, niveles_disponibles, material)

    if col_conf.button("✅ Confirmar e insertar todos los registros", type="primary", use_container_width=True):
        _insertar_masivo(db, df_edited, material_id, lote_id, nivel_map,
                         niveles_disponibles, pers_opts[pers_sel], turno_def)


def _mostrar_preview(df, nivel_map, niveles, material):
    """Muestra evaluación Westgard de los valores ingresados antes de insertar."""
    filas_prev = []
    for _, row in df.iterrows():
        if not row.get("Incluir", True):
            continue
        for nv in niveles:
            val = row.get(f"Nivel {nv}")
            if val is None or (isinstance(val, float) and pd.isna(val)):
                continue
            nl = nivel_map[nv]
            res = evaluar_westgard(float(val), nl.media, nl.de, [], None)
            emoji = {"OK": "✅", "ADVERTENCIA": "⚠️", "RECHAZO": "❌"}.get(res.resultado, "")
            filas_prev.append({
                "Fecha": str(row["Fecha"]),
                "Hora": row["Hora"],
                "Nivel": nv,
                "Valor": round(float(val), 4),
                "z-score": round(res.zscore, 3),
                f"X̄ ± 2s": f"{nl.media:.4f} ± {2*nl.de:.4f}",
                "Resultado": f"{emoji} {res.resultado}",
                "Regla": res.regla_violada or "—",
            })

    if not filas_prev:
        st.warning("No hay valores ingresados para previsualizar.")
        return

    df_prev = pd.DataFrame(filas_prev)

    def _col_res(val):
        if "RECHAZO"     in str(val): return "background-color:#fee2e2;color:#7f1d1d;font-weight:700"
        if "ADVERTENCIA" in str(val): return "background-color:#fef3c7;color:#78350f;font-weight:600"
        if "OK"          in str(val): return "background-color:#d1fae5;color:#065f46;font-weight:600"
        return ""

    st.markdown(f"**Vista previa — {len(filas_prev)} registros a insertar:**")
    total  = len(filas_prev)
    ok_n   = sum(1 for f in filas_prev if "OK" in f["Resultado"])
    adv_n  = sum(1 for f in filas_prev if "ADVERTENCIA" in f["Resultado"])
    rej_n  = sum(1 for f in filas_prev if "RECHAZO" in f["Resultado"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("✅ OK", ok_n)
    c3.metric("⚠️ Advertencias", adv_n)
    c4.metric("❌ Rechazos", rej_n)

    st.dataframe(df_prev.style.applymap(_col_res, subset=["Resultado"]),
                 use_container_width=True, hide_index=True)

    if rej_n:
        st.warning(f"⚠️ {rej_n} rechazo(s) detectados. Después de la carga, regístreles acción correctiva en 🔧 Acciones Correctivas.")


def _insertar_masivo(db, df, material_id, lote_id, nivel_map, niveles, personal_id, turno_def):
    """Construye la lista de registros y llama a crud.insertar_controles_masivo."""
    registros = []

    for _, row in df.iterrows():
        if not row.get("Incluir", True):
            continue

        # Parsear fecha
        f = row["Fecha"]
        if isinstance(f, str):
            try:
                f = date.fromisoformat(f)
            except Exception:
                continue

        # Parsear hora
        h_str = str(row.get("Hora", "08:00")).strip()
        try:
            h = datetime.strptime(h_str, "%H:%M").time()
        except Exception:
            h = time(8, 0)

        turno = row.get("Turno", turno_def) or turno_def
        obs   = str(row.get("Observación", "") or "")

        for nv in niveles:
            val = row.get(f"Nivel {nv}")
            if val is None or (isinstance(val, float) and pd.isna(val)):
                continue
            try:
                valor = float(val)
            except Exception:
                continue

            registros.append({
                "material_id":   material_id,
                "lote_id":       lote_id,
                "nivel_lote_id": nivel_map[nv].id,
                "personal_id":   personal_id,
                "fecha":         f,
                "hora":          h,
                "turno":         turno,
                "valor":         valor,
                "comentario":    obs,
                "es_retroactivo": True,
            })

    if not registros:
        st.error("No se encontraron valores válidos para insertar. Complete al menos una celda de valor.")
        return

    with st.spinner(f"Insertando {len(registros)} registros..."):
        ins, omit, errs = crud.insertar_controles_masivo(db, registros)

    if ins:
        st.success(f"✅ **{ins} registro(s) insertados correctamente.**")
    if omit:
        st.info(f"ℹ️ {omit} registro(s) omitidos (ya existían en la base de datos).")
    if errs:
        st.error(f"❌ {len(errs)} error(es):")
        for e in errs[:10]:
            st.markdown(f"&emsp;▸ {e}")
    if ins:
        st.balloons()


if __name__ == "__main__":
    main()
