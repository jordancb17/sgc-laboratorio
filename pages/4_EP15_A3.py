"""
Página EP15-A3 — Verificación de precisión y sesgo del método.

Flujo:
  1. Nueva sesión: seleccionar analito, configurar parámetros
  2. Ingreso de datos: matriz días × replicados
  3. Calcular y ver resultados estadísticos
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

from database.database import init_db, get_session
from database import crud
from modules.ep15 import calcular_ep15

st.set_page_config(page_title="EP15-A3", page_icon="📐", layout="wide")
init_db()
from modules.page_utils import setup_page, page_header
setup_page()


def main():
    page_header(
        icon="📐",
        title="Verificación de Método — EP15-A3",
        subtitle="Verificación de precisión (repetibilidad e intermedia) y sesgo conforme a CLSI EP15-A3",
        badge="Verificación Analítica",
    )
    tab_nueva, tab_datos, tab_resultados = st.tabs(
        ["🆕 Nueva Sesión", "📊 Ingresar / Editar Datos", "📈 Resultados"]
    )
    db = get_session()
    try:
        with tab_nueva:
            _tab_nueva(db)
        with tab_datos:
            _tab_datos(db)
        with tab_resultados:
            _tab_resultados(db)
    finally:
        db.close()


# ─── NUEVA SESIÓN ─────────────────────────────────────────────────────────────

def _tab_nueva(db):
    st.subheader("Crear Nueva Sesión de Verificación EP15-A3")

    materiales = crud.listar_materiales(db)
    if not materiales:
        st.warning("No hay analitos configurados.")
        return

    mat_opts = {f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}": m.id for m in materiales}

    with st.form("form_ep15_nueva"):
        mat_sel = st.selectbox("Analito a verificar *", list(mat_opts.keys()))
        nombre_sesion = st.text_input("Nombre / descripción de la sesión *", placeholder="Ej: Verificación Glucosa — Equipo A — 2024")

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        nivel = col1.selectbox("Nivel de control a verificar", [1, 2, 3])
        n_dias = col2.number_input("Número de días (mín. 5)", min_value=3, max_value=20, value=5, step=1)
        n_reps = col3.number_input("Replicados por día (mín. 3)", min_value=2, max_value=10, value=3, step=1)

        st.markdown("**Valores del fabricante (para verificación):**")
        col1, col2, col3, col4 = st.columns(4)
        cv_r_fab = col1.number_input("CV% Repetibilidad (fabricante)", min_value=0.0, format="%.2f")
        cv_ip_fab = col2.number_input("CV% Precisión intermedia (fabricante)", min_value=0.0, format="%.2f")
        sesgo_perm = col3.number_input("Sesgo máximo permitido (%)", min_value=0.0, format="%.2f")
        val_ref = col4.number_input("Valor de referencia (para sesgo)", format="%.4f", value=0.0)

        if st.form_submit_button("✅ Crear Sesión", type="primary"):
            if not nombre_sesion.strip():
                st.error("El nombre de la sesión es obligatorio.")
            else:
                sesion = crud.crear_sesion_ep15(
                    db=db,
                    material_id=mat_opts[mat_sel],
                    nombre_sesion=nombre_sesion,
                    nivel=nivel,
                    n_dias=int(n_dias),
                    n_replicados=int(n_reps),
                    cv_r_fabricante=cv_r_fab if cv_r_fab > 0 else None,
                    cv_ip_fabricante=cv_ip_fab if cv_ip_fab > 0 else None,
                    sesgo_permitido=sesgo_perm if sesgo_perm > 0 else None,
                    valor_referencia=val_ref if val_ref != 0 else None,
                )
                st.success(f"Sesión creada (ID {sesion.id}). Vaya a 'Ingresar / Editar Datos'.")

    # Listar sesiones existentes
    st.markdown("---")
    st.subheader("Sesiones registradas")
    sesiones = crud.listar_sesiones_ep15(db)
    if sesiones:
        filas = []
        for s in sesiones:
            filas.append({
                "ID": s.id,
                "Sesión": s.nombre_sesion,
                "Analito": s.material.analito,
                "Equipo": s.material.equipo.nombre,
                "Nivel": s.nivel,
                "Días": s.n_dias,
                "Reps": s.n_replicados,
                "Completada": "✅" if s.completada else "🔄",
                "Fecha": s.registrado_en.date(),
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)


# ─── INGRESO DE DATOS ─────────────────────────────────────────────────────────

def _tab_datos(db):
    st.subheader("Ingresar / Editar Mediciones")

    sesiones = crud.listar_sesiones_ep15(db)
    if not sesiones:
        st.info("No hay sesiones creadas.")
        return

    ses_opts = {f"[ID {s.id}] {s.nombre_sesion} ({s.material.analito})": s.id for s in sesiones}
    ses_sel_key = st.selectbox("Sesión *", list(ses_opts.keys()), key="ep15_ses_datos")
    sesion_id = ses_opts[ses_sel_key]
    sesion = next(s for s in sesiones if s.id == sesion_id)

    st.info(
        f"**{sesion.nombre_sesion}** — Analito: {sesion.material.analito} — "
        f"Nivel {sesion.nivel} — {sesion.n_dias} días × {sesion.n_replicados} replicados"
    )

    # Cargar mediciones existentes
    from database.models import MedicionEP15
    db_ses = get_session()
    mediciones_existentes: dict[tuple, float] = {}
    try:
        meds = db_ses.query(MedicionEP15).filter(MedicionEP15.sesion_id == sesion_id).all()
        for m in meds:
            mediciones_existentes[(m.dia, m.replicado)] = m.valor
    finally:
        db_ses.close()

    st.markdown(f"**Ingrese los {sesion.n_dias * sesion.n_replicados} valores** (días en filas, replicados en columnas):")

    # Formulario dinámico: tabla días × replicados
    with st.form(f"form_ep15_datos_{sesion_id}"):
        valores: dict[tuple, float] = {}
        cols_header = st.columns([1] + [1] * sesion.n_replicados)
        cols_header[0].markdown("**Día**")
        for r in range(1, sesion.n_replicados + 1):
            cols_header[r].markdown(f"**Rep. {r}**")

        for d in range(1, sesion.n_dias + 1):
            cols_row = st.columns([1] + [1] * sesion.n_replicados)
            cols_row[0].markdown(f"Día {d}")
            for r in range(1, sesion.n_replicados + 1):
                default_val = mediciones_existentes.get((d, r), 0.0)
                v = cols_row[r].number_input(
                    f"D{d}R{r}",
                    value=float(default_val),
                    format="%.4f",
                    label_visibility="collapsed",
                    key=f"ep15_v_{sesion_id}_{d}_{r}",
                )
                valores[(d, r)] = v

        col1, col2 = st.columns(2)
        guardar = col1.form_submit_button("💾 Guardar Datos", type="primary")
        calcular = col2.form_submit_button("📐 Guardar y Calcular EP15-A3")

    if guardar or calcular:
        db2 = get_session()
        try:
            errores = []
            for (d, r), v in valores.items():
                _, err = crud.agregar_medicion_ep15(db2, sesion_id, d, r, v)
                if err:
                    errores.append(err)
            if errores:
                for e in errores:
                    st.error(e)
            else:
                st.success("Datos guardados correctamente.")
                if calcular:
                    sesion_calc, err_calc = crud.calcular_y_guardar_ep15(db2, sesion_id)
                    if err_calc:
                        st.error(f"Error al calcular: {err_calc}")
                    else:
                        st.success("Cálculo EP15-A3 completado. Vea los resultados en la pestaña 📈 Resultados.")
        finally:
            db2.close()

    # Vista previa de datos ingresados
    if mediciones_existentes:
        st.markdown("---")
        st.subheader("Vista previa — Datos actuales")
        filas_prev = []
        for d in range(1, sesion.n_dias + 1):
            fila = {"Día": f"Día {d}"}
            for r in range(1, sesion.n_replicados + 1):
                fila[f"Rep. {r}"] = mediciones_existentes.get((d, r), "—")
            filas_prev.append(fila)
        st.dataframe(pd.DataFrame(filas_prev), use_container_width=True, hide_index=True)


# ─── RESULTADOS ───────────────────────────────────────────────────────────────

def _tab_resultados(db):
    st.subheader("Resultados EP15-A3")

    sesiones = [s for s in crud.listar_sesiones_ep15(db) if s.completada]
    if not sesiones:
        st.info("No hay sesiones completadas. Ingrese los datos y calcule en la pestaña anterior.")
        return

    ses_opts = {f"[ID {s.id}] {s.nombre_sesion} ({s.material.analito})": s.id for s in sesiones}
    ses_sel = st.selectbox("Sesión completada", list(ses_opts.keys()), key="ep15_res_sel")
    sesion = next(s for s in sesiones if s.id == ses_opts[ses_sel])

    mat = sesion.material

    st.markdown(f"### {sesion.nombre_sesion}")
    st.markdown(
        f"**Analito:** {mat.analito} &nbsp;|&nbsp; "
        f"**Equipo:** {mat.equipo.nombre} &nbsp;|&nbsp; "
        f"**Nivel:** {sesion.nivel} &nbsp;|&nbsp; "
        f"**Diseño:** {sesion.n_dias} días × {sesion.n_replicados} replicados "
        f"(n = {sesion.n_dias * sesion.n_replicados})"
    )

    st.markdown("---")

    # ── Métricas principales ─────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Media calculada (X̄)", f"{sesion.grand_mean:.4f}" if sesion.grand_mean else "—")
    col2.metric("DE Repetibilidad", f"{sesion.de_r:.4f}" if sesion.de_r else "—")
    col3.metric("DE Prec. Intermedia", f"{sesion.de_ip:.4f}" if sesion.de_ip else "—")
    col4.metric(
        "Sesgo",
        f"{sesion.sesgo_porcentual:.2f}%" if sesion.sesgo_porcentual is not None else "N/A",
    )

    col1, col2, col3 = st.columns(3)

    # CV% Repetibilidad
    cv_r_val = f"{sesion.cv_r:.3f}%" if sesion.cv_r is not None else "—"
    cv_r_fab_val = f"{sesion.cv_r_fabricante:.3f}%" if sesion.cv_r_fabricante else "N/A"
    verif_r = sesion.verificacion_precision_r
    if verif_r is True:
        col1.success(f"✅ Repetibilidad\nCV%: {cv_r_val}\nFabricante: {cv_r_fab_val}\n→ **VERIFICADA**")
    elif verif_r is False:
        col1.error(f"❌ Repetibilidad\nCV%: {cv_r_val}\nFabricante: {cv_r_fab_val}\n→ **NO VERIFICADA**")
    else:
        col1.info(f"ℹ️ Repetibilidad\nCV%: {cv_r_val}\n(Sin valor de fabricante)")

    # CV% Precisión Intermedia
    cv_ip_val = f"{sesion.cv_ip:.3f}%" if sesion.cv_ip is not None else "—"
    cv_ip_fab_val = f"{sesion.cv_ip_fabricante:.3f}%" if sesion.cv_ip_fabricante else "N/A"
    verif_ip = sesion.verificacion_precision_ip
    if verif_ip is True:
        col2.success(f"✅ Prec. Intermedia\nCV%: {cv_ip_val}\nFabricante: {cv_ip_fab_val}\n→ **VERIFICADA**")
    elif verif_ip is False:
        col2.error(f"❌ Prec. Intermedia\nCV%: {cv_ip_val}\nFabricante: {cv_ip_fab_val}\n→ **NO VERIFICADA**")
    else:
        col2.info(f"ℹ️ Prec. Intermedia\nCV%: {cv_ip_val}\n(Sin valor de fabricante)")

    # Sesgo
    verif_sesgo = sesion.verificacion_sesgo
    sesgo_val = f"{sesion.sesgo_porcentual:.3f}%" if sesion.sesgo_porcentual is not None else "N/A"
    sesgo_perm_val = f"{sesion.sesgo_permitido:.2f}%" if sesion.sesgo_permitido else "N/A"
    if verif_sesgo is True:
        col3.success(f"✅ Sesgo\nObtenido: {sesgo_val}\nPermitido: ±{sesgo_perm_val}\n→ **VERIFICADO**")
    elif verif_sesgo is False:
        col3.error(f"❌ Sesgo\nObtenido: {sesgo_val}\nPermitido: ±{sesgo_perm_val}\n→ **NO VERIFICADO**")
    else:
        col3.info(f"ℹ️ Sesgo\nObtenido: {sesgo_val}\n(Sin criterio definido)")

    # ── Tabla de datos y medias por día ─────────────────────────────────────
    st.markdown("---")
    st.subheader("Datos detallados")

    from database.models import MedicionEP15
    db2 = get_session()
    try:
        meds = db2.query(MedicionEP15).filter(MedicionEP15.sesion_id == sesion.id).order_by(MedicionEP15.dia, MedicionEP15.replicado).all()
    finally:
        db2.close()

    if meds:
        datos: dict[int, list[float]] = {}
        for m in meds:
            datos.setdefault(m.dia, []).append(m.valor)

        # Recalcular para gráficos
        import math
        grand_mean = sesion.grand_mean
        de_r = sesion.de_r

        filas_det = []
        for d, vals in sorted(datos.items()):
            media_d = sum(vals) / len(vals)
            de_d = math.sqrt(sum((v - media_d) ** 2 for v in vals) / (len(vals) - 1)) if len(vals) > 1 else 0
            row = {"Día": f"Día {d}"}
            for i, v in enumerate(vals, 1):
                row[f"Rep. {i}"] = v
            row["Media día"] = round(media_d, 4)
            row["DE día"] = round(de_d, 4)
            filas_det.append(row)

        st.dataframe(pd.DataFrame(filas_det), use_container_width=True, hide_index=True)

        # ── Gráfico de medias por día ──────────────────────────────────────
        st.subheader("Medias por día vs Media general")
        medias_dias = [r["Media día"] for r in filas_det]
        dias_labels = [r["Día"] for r in filas_det]

        fig = go.Figure()
        fig.add_hline(y=grand_mean, line_color="blue", line_width=2, annotation_text=f"X̄={grand_mean:.4f}")
        if de_r:
            fig.add_hline(y=grand_mean + 2 * de_r, line_color="orange", line_dash="dash", annotation_text="+2s_r")
            fig.add_hline(y=grand_mean - 2 * de_r, line_color="orange", line_dash="dash", annotation_text="-2s_r")
        fig.add_trace(go.Scatter(
            x=dias_labels,
            y=medias_dias,
            mode="lines+markers",
            marker=dict(size=10, color="steelblue"),
            name="Media del día",
        ))
        fig.update_layout(title="Media por día", xaxis_title="Día", yaxis_title="Valor", height=350)
        st.plotly_chart(fig, use_container_width=True)

        # ── Box plot por día ───────────────────────────────────────────────
        st.subheader("Dispersión de valores por día")
        filas_box = []
        for d, vals in sorted(datos.items()):
            for v in vals:
                filas_box.append({"Día": f"Día {d}", "Valor": v})
        fig2 = px.box(pd.DataFrame(filas_box), x="Día", y="Valor", title="Box Plot por día", height=350)
        fig2.add_hline(y=grand_mean, line_color="blue", line_dash="dash", annotation_text="X̄")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Resumen estadístico para impresión ───────────────────────────────────
    st.markdown("---")
    st.subheader("Informe EP15-A3")
    resumen = f"""
**Sesión:** {sesion.nombre_sesion}
**Analito:** {mat.analito} | **Equipo:** {mat.equipo.nombre} | **Área:** {mat.equipo.area.nombre}
**Nivel:** {sesion.nivel} | **Diseño:** {sesion.n_dias} días × {sesion.n_replicados} replicados | **n total:** {sesion.n_dias * sesion.n_replicados}

| Parámetro | Obtenido | Fabricante | Verificado |
|---|---|---|---|
| Media (X̄) | {sesion.grand_mean:.4f if sesion.grand_mean else '—'} | — | — |
| DE Repetibilidad | {sesion.de_r:.4f if sesion.de_r else '—'} | — | — |
| CV% Repetibilidad | {sesion.cv_r:.3f if sesion.cv_r else '—'}% | {sesion.cv_r_fabricante or 'N/A'}% | {'✅' if verif_r is True else '❌' if verif_r is False else 'N/A'} |
| DE Prec. Intermedia | {sesion.de_ip:.4f if sesion.de_ip else '—'} | — | — |
| CV% Prec. Intermedia | {sesion.cv_ip:.3f if sesion.cv_ip else '—'}% | {sesion.cv_ip_fabricante or 'N/A'}% | {'✅' if verif_ip is True else '❌' if verif_ip is False else 'N/A'} |
| Sesgo (absoluto) | {sesion.sesgo_absoluto:.4f if sesion.sesgo_absoluto is not None else 'N/A'} | — | — |
| Sesgo (%) | {sesion.sesgo_porcentual:.3f if sesion.sesgo_porcentual is not None else 'N/A'}% | ≤ {sesion.sesgo_permitido or 'N/A'}% | {'✅' if verif_sesgo is True else '❌' if verif_sesgo is False else 'N/A'} |
"""
    st.markdown(resumen)

    # Descargar
    try:
        import io
        buf = io.BytesIO()
        pd.DataFrame(filas_det).to_excel(buf, index=False) if meds else None
        st.download_button("⬇️ Descargar datos Excel", buf.getvalue(), f"ep15_{sesion.id}.xlsx")
    except Exception:
        pass


if __name__ == "__main__":
    main()
