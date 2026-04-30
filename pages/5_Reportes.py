"""
Página de Reportes:
  - Gráfico de Levey-Jennings anotado (reglas violadas)
  - Reporte mensual con comparativa mes anterior
  - Actividad de personal
  - Exportación PDF y Excel
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
from calendar import monthrange

from database.database import init_db, get_session
from database import crud
from modules.westgard import RESULTADO_OK, RESULTADO_ADVERTENCIA, RESULTADO_RECHAZO

st.set_page_config(page_title="Reportes", page_icon="📊", layout="wide")
init_db()
from modules.page_utils import setup_page, page_header
setup_page()


def main():
    page_header(
        icon="📊",
        title="Reportes de Calidad",
        subtitle="Levey-Jennings anotado, reporte mensual comparativo y actividad de personal",
        badge="Reportes y Tendencias",
    )
    tab_lj, tab_mensual, tab_personal = st.tabs(
        ["📈 Levey-Jennings", "📅 Reporte Mensual", "👤 Actividad de Personal"]
    )
    db = get_session()
    try:
        with tab_lj:
            _tab_levey_jennings(db)
        with tab_mensual:
            _tab_mensual(db)
        with tab_personal:
            _tab_personal(db)
    finally:
        db.close()


# ─── LEVEY-JENNINGS ──────────────────────────────────────────────────────────

def _tab_levey_jennings(db):
    st.subheader("Gráfico de Levey-Jennings")

    materiales = crud.listar_materiales(db)
    if not materiales:
        st.info("No hay analitos configurados.")
        return

    mat_opts = {f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}": m.id for m in materiales}

    col1, col2 = st.columns([3, 1])
    mat_sel = col1.selectbox("Analito", list(mat_opts.keys()), key="lj_mat")
    nivel = col2.selectbox("Nivel", [1, 2, 3], key="lj_nivel")

    col1, col2 = st.columns(2)
    fecha_desde = col1.date_input("Desde", value=date.today() - timedelta(days=30), key="lj_desde")
    fecha_hasta = col2.date_input("Hasta", value=date.today(), key="lj_hasta")

    material_id = mat_opts[mat_sel]
    controles = crud.listar_controles_diarios(
        db, material_id=material_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, nivel=nivel
    )

    if not controles:
        st.info("No hay controles para ese período y nivel.")
        return

    primer = controles[0]
    media = primer.nivel_lote.media
    de = primer.nivel_lote.de
    unidad = primer.material.unidad or ""

    fechas   = [f"{c.fecha} {c.hora.strftime('%H:%M')}" for c in controles]
    valores  = [c.valor for c in controles]
    zscores  = [c.zscore for c in controles]
    resultados = [c.resultado for c in controles]
    reglas   = [c.regla_violada or "" for c in controles]

    col_map = {RESULTADO_OK: "#16a34a", RESULTADO_ADVERTENCIA: "#d97706", RESULTADO_RECHAZO: "#dc2626"}
    col_puntos = [col_map.get(r, "#94a3b8") for r in resultados]

    fig = go.Figure()

    # Bandas de fondo ±1s / ±2s / ±3s
    xs_band = [fechas[0], fechas[-1]] if len(fechas) >= 2 else fechas * 2
    for upper, lower, fill_color in [
        (media + 3*de, media + 2*de, "rgba(220,38,38,0.06)"),
        (media - 2*de, media - 3*de, "rgba(220,38,38,0.06)"),
        (media + 2*de, media + de,   "rgba(217,119,6,0.06)"),
        (media - de,   media - 2*de, "rgba(217,119,6,0.06)"),
        (media + de,   media - de,   "rgba(22,163,74,0.06)"),
    ]:
        fig.add_trace(go.Scatter(
            x=xs_band + xs_band[::-1],
            y=[upper]*2 + [lower]*2,
            fill="toself", fillcolor=fill_color,
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))

    # Líneas de referencia
    lineas = [
        (media + 3*de, "#dc2626", "dot",    f"+3s = {media+3*de:.4f}"),
        (media + 2*de, "#d97706", "dash",   f"+2s = {media+2*de:.4f}"),
        (media + de,   "#16a34a", "dashdot",f"+1s = {media+de:.4f}"),
        (media,        "#2563eb", "solid",  f"X̄ = {media:.4f}"),
        (media - de,   "#16a34a", "dashdot",f"-1s = {media-de:.4f}"),
        (media - 2*de, "#d97706", "dash",   f"-2s = {media-2*de:.4f}"),
        (media - 3*de, "#dc2626", "dot",    f"-3s = {media-3*de:.4f}"),
    ]
    for y_val, color, dash, label in lineas:
        fig.add_hline(
            y=y_val, line_color=color, line_dash=dash, line_width=1.5,
            annotation_text=label, annotation_position="right",
            annotation_font_size=9,
        )

    # Línea de datos
    fig.add_trace(go.Scatter(
        x=fechas, y=valores,
        mode="lines+markers",
        marker=dict(color=col_puntos, size=9, line=dict(width=1.5, color="white")),
        line=dict(color="#64748b", width=1.5),
        text=[f"z={z:.3f} | {r}" + (f" | Regla: {rg}" if rg else "")
              for z, r, rg in zip(zscores, resultados, reglas)],
        hovertemplate="%{x}<br>Valor: %{y:.4f} " + unidad + "<br>%{text}<extra></extra>",
        name="Control",
    ))

    # Anotaciones de reglas violadas sobre cada punto de advertencia/rechazo
    for i, (r, rg) in enumerate(zip(resultados, reglas)):
        if r in (RESULTADO_RECHAZO, RESULTADO_ADVERTENCIA) and rg:
            fig.add_annotation(
                x=fechas[i], y=valores[i],
                text=rg,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=1.5,
                arrowcolor=col_map.get(r, "#94a3b8"),
                ax=0, ay=-32,
                font=dict(size=9, color=col_map.get(r, "#94a3b8")),
                bgcolor="white",
                bordercolor=col_map.get(r, "#94a3b8"),
                borderwidth=1,
                borderpad=2,
            )

    # X marcando rechazos
    rechazos_x = [fechas[i] for i, r in enumerate(resultados) if r == RESULTADO_RECHAZO]
    rechazos_y = [valores[i] for i, r in enumerate(resultados) if r == RESULTADO_RECHAZO]
    if rechazos_x:
        fig.add_trace(go.Scatter(
            x=rechazos_x, y=rechazos_y,
            mode="markers",
            marker=dict(symbol="x", size=16, color="#dc2626", line=dict(width=2.5)),
            name="Rechazo",
        ))

    fig.update_layout(
        title=dict(
            text=f"Levey-Jennings — {primer.material.analito} — Nivel {nivel}",
            font=dict(size=15, color="#1e3a8a"),
        ),
        xaxis_title="Fecha / Hora",
        yaxis_title=f"Valor ({unidad})",
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#f1f5f9", tickangle=45),
        yaxis=dict(gridcolor="#f1f5f9"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Estadísticos del período
    import statistics
    if len(valores) > 1:
        media_obs = statistics.mean(valores)
        de_obs    = statistics.stdev(valores)
        cv_obs    = (de_obs / media_obs) * 100 if media_obs else 0
        rej_n = sum(1 for r in resultados if r == RESULTADO_RECHAZO)
        adv_n = sum(1 for r in resultados if r == RESULTADO_ADVERTENCIA)
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("N controles", len(valores))
        col2.metric("Media obs.", f"{media_obs:.4f}")
        col3.metric("DE obs.", f"{de_obs:.4f}")
        col4.metric("CV%", f"{cv_obs:.2f}%")
        col5.metric("❌ Rechazos", rej_n)
        col6.metric("⚠️ Advertencias", adv_n)

    # Exportar PDF Levey-Jennings
    st.markdown("---")
    try:
        laboratorio = st.secrets.get("laboratorio", "Laboratorio Clínico")
    except Exception:
        laboratorio = "Laboratorio Clínico"

    if st.button("📄 Exportar PDF Levey-Jennings", key="pdf_lj"):
        try:
            from modules.pdf_export import reporte_levey_jennings_pdf
            pdf_bytes = reporte_levey_jennings_pdf(
                controles=controles,
                analito=primer.material.analito,
                nivel=nivel,
                laboratorio=laboratorio,
            )
            st.download_button(
                "⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"levey_jennings_{primer.material.analito}_nv{nivel}.pdf",
                mime="application/pdf",
                key="dl_pdf_lj",
            )
        except ImportError:
            st.error("Instale fpdf2: `pip install fpdf2`")
        except Exception as e:
            st.error(f"Error generando PDF: {e}")


# ─── REPORTE MENSUAL ─────────────────────────────────────────────────────────

def _tab_mensual(db):
    st.subheader("Reporte Mensual de Control de Calidad")

    hoy = date.today()
    col1, col2 = st.columns(2)
    anio = col1.number_input("Año", min_value=2020, max_value=hoy.year + 1, value=hoy.year, step=1)
    mes = col2.selectbox(
        "Mes",
        list(range(1, 13)),
        index=hoy.month - 1,
        format_func=lambda m: ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][m - 1],
    )

    _, ultimo_dia = monthrange(int(anio), int(mes))
    fecha_desde = date(int(anio), int(mes), 1)
    fecha_hasta = date(int(anio), int(mes), ultimo_dia)

    # Mes anterior para comparativa
    mes_ant = int(mes) - 1 if int(mes) > 1 else 12
    anio_ant = int(anio) if int(mes) > 1 else int(anio) - 1
    _, ult_dia_ant = monthrange(anio_ant, mes_ant)
    fecha_desde_ant = date(anio_ant, mes_ant, 1)
    fecha_hasta_ant = date(anio_ant, mes_ant, ult_dia_ant)

    controles     = crud.listar_controles_diarios(db, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    controles_ant = crud.listar_controles_diarios(db, fecha_desde=fecha_desde_ant, fecha_hasta=fecha_hasta_ant)

    if not controles:
        st.info("No hay controles registrados en ese mes.")
        return

    # ── KPIs con delta vs mes anterior ───────────────────────────────────────
    total     = len(controles)
    rechazos  = sum(1 for c in controles if c.resultado == RESULTADO_RECHAZO)
    advert    = sum(1 for c in controles if c.resultado == RESULTADO_ADVERTENCIA)
    oks       = total - rechazos - advert
    tasa_rej  = rechazos / total * 100 if total else 0

    total_ant    = len(controles_ant)
    rechazos_ant = sum(1 for c in controles_ant if c.resultado == RESULTADO_RECHAZO)
    tasa_rej_ant = rechazos_ant / total_ant * 100 if total_ant else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total controles", total,
                delta=f"{total - total_ant:+d} vs mes ant." if total_ant else None)
    col2.metric("✅ OK", oks)
    col3.metric("❌ Rechazos", rechazos,
                delta=f"{rechazos - rechazos_ant:+d} vs mes ant." if total_ant else None,
                delta_color="inverse")
    col4.metric("Tasa rechazo", f"{tasa_rej:.1f}%",
                delta=f"{tasa_rej - tasa_rej_ant:+.1f}pp vs mes ant." if total_ant else None,
                delta_color="inverse")

    st.markdown("---")

    # ── Gráfico comparativa rechazos por semana ───────────────────────────────
    from collections import defaultdict
    import plotly.graph_objects as go

    semanas_mes: dict = defaultdict(lambda: {"OK": 0, "ADVERTENCIA": 0, "RECHAZO": 0})
    for c in controles:
        sem = f"Sem {c.fecha.isocalendar()[1]}"
        semanas_mes[sem][c.resultado] = semanas_mes[sem].get(c.resultado, 0) + 1

    if semanas_mes:
        sems = sorted(semanas_mes.keys())
        fig_sem = go.Figure(data=[
            go.Bar(name="✅ OK",          x=sems, y=[semanas_mes[s].get("OK", 0) for s in sems],          marker_color="#16a34a"),
            go.Bar(name="⚠️ Advertencia", x=sems, y=[semanas_mes[s].get("ADVERTENCIA", 0) for s in sems], marker_color="#d97706"),
            go.Bar(name="❌ Rechazo",     x=sems, y=[semanas_mes[s].get("RECHAZO", 0) for s in sems],     marker_color="#dc2626"),
        ])
        fig_sem.update_layout(
            barmode="stack", height=260,
            margin=dict(l=0, r=0, t=30, b=0),
            title="Controles por semana del mes",
            title_font=dict(size=13),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#f1f5f9", title="N° controles"),
        )
        fig_sem.update_traces(marker_line_width=0)
        st.plotly_chart(fig_sem, use_container_width=True)

    # ── Tabla resumen por analito + nivel ────────────────────────────────────
    st.markdown("### Resultados por Analito y Nivel")
    resumen: dict[tuple, dict] = {}
    for c in controles:
        mat = c.material
        clave = (mat.equipo.area.nombre, mat.equipo.nombre, mat.analito, c.nivel_lote.nivel)
        if clave not in resumen:
            resumen[clave] = {"total": 0, "ok": 0, "adv": 0, "rej": 0, "valores": []}
        resumen[clave]["total"] += 1
        resumen[clave]["valores"].append(c.valor)
        resumen[clave][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

    import statistics
    filas = []
    for (area, equipo, analito, nivel), data in sorted(resumen.items()):
        n    = data["total"]
        vals = data["valores"]
        media_obs = statistics.mean(vals) if vals else 0
        de_obs    = statistics.stdev(vals) if len(vals) > 1 else 0
        cv_obs    = (de_obs / media_obs * 100) if media_obs else 0
        filas.append({
            "Área": area,
            "Equipo": equipo,
            "Analito": analito,
            "Nivel": nivel,
            "N": n,
            "✅ OK": data["ok"],
            "⚠️ Adv.": data["adv"],
            "❌ Rech.": data["rej"],
            "% OK": f"{data['ok']/n*100:.1f}%",
            "% Rech.": f"{data['rej']/n*100:.1f}%",
            "Media obs.": round(media_obs, 4),
            "CV%": f"{cv_obs:.2f}%",
        })

    df = pd.DataFrame(filas)

    def _color_rej(val):
        try:
            p = float(str(val).replace("%", ""))
            if p >= 10:  return "background-color:#fee2e2; color:#7f1d1d; font-weight:bold"
            if p >= 5:   return "background-color:#fff3cd; color:#78350f"
        except Exception:
            pass
        return ""

    st.dataframe(df.style.applymap(_color_rej, subset=["% Rech."]),
                 use_container_width=True, hide_index=True)

    # ── Exportación ──────────────────────────────────────────────────────────
    st.markdown("---")
    col_xl, col_pdf = st.columns(2)

    try:
        import io
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        col_xl.download_button(
            "⬇️ Descargar Excel",
            buf.getvalue(),
            f"reporte_qc_{anio}_{mes:02d}.xlsx",
            key="dl_xls_mensual",
        )
    except Exception:
        pass

    if col_pdf.button("📄 Exportar PDF mensual", key="pdf_mensual"):
        try:
            from modules.pdf_export import reporte_mensual_pdf
            try:
                lab = st.secrets.get("laboratorio", "Laboratorio Clínico")
            except Exception:
                lab = "Laboratorio Clínico"
            pdf_bytes = reporte_mensual_pdf(controles, int(mes), int(anio), lab)
            st.download_button(
                "⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"reporte_mensual_{anio}_{mes:02d}.pdf",
                mime="application/pdf",
                key="dl_pdf_mensual",
            )
        except ImportError:
            st.error("Instale fpdf2: `pip install fpdf2`")
        except Exception as e:
            st.error(f"Error generando PDF: {e}")


# ─── ACTIVIDAD DE PERSONAL ────────────────────────────────────────────────────

def _tab_personal(db):
    st.subheader("Actividad de Personal")

    col1, col2 = st.columns(2)
    fecha_desde = col1.date_input("Desde", value=date.today() - timedelta(days=30), key="per_desde")
    fecha_hasta = col2.date_input("Hasta", value=date.today(), key="per_hasta")

    controles = crud.listar_controles_diarios(db, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    if not controles:
        st.info("No hay controles en ese período.")
        return

    from collections import defaultdict
    actividad: dict = defaultdict(lambda: {"total": 0, "rechazos": 0, "advertencias": 0, "fechas": set()})
    for c in controles:
        nombre = f"{c.personal.apellido}, {c.personal.nombre}"
        actividad[nombre]["total"] += 1
        actividad[nombre]["fechas"].add(c.fecha)
        if c.resultado == RESULTADO_RECHAZO:
            actividad[nombre]["rechazos"] += 1
        elif c.resultado == RESULTADO_ADVERTENCIA:
            actividad[nombre]["advertencias"] += 1

    filas = [
        {
            "Personal": nombre,
            "N° controles": datos["total"],
            "Días activos": len(datos["fechas"]),
            "❌ Rechazos": datos["rechazos"],
            "⚠️ Advertencias": datos["advertencias"],
            "% Rechazo": f"{datos['rechazos']/datos['total']*100:.1f}%",
        }
        for nombre, datos in sorted(actividad.items())
    ]
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

    st.markdown("---")
    pers_list = list(actividad.keys())
    pers_sel = st.selectbox("Ver detalle de:", pers_list, key="per_det")

    controles_pers = crud.listar_controles_diarios(
        db,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        personal_id=next(
            c.personal_id for c in controles
            if f"{c.personal.apellido}, {c.personal.nombre}" == pers_sel
        ),
    )
    filas_det = [
        {
            "Fecha": c.fecha,
            "Hora": c.hora.strftime("%H:%M"),
            "Turno": c.turno or "—",
            "Área": c.material.equipo.area.nombre,
            "Equipo": c.material.equipo.nombre,
            "Analito": c.material.analito,
            "Nivel": c.nivel_lote.nivel,
            "Valor": c.valor,
            "Resultado": c.resultado,
            "Regla": c.regla_violada or "—",
        }
        for c in controles_pers
    ]
    if filas_det:
        df_det = pd.DataFrame(filas_det)

        def _estilo(val):
            return {
                "OK": "background-color:#d4edda",
                "ADVERTENCIA": "background-color:#fff3cd",
                "RECHAZO": "background-color:#f8d7da",
            }.get(val, "")

        st.dataframe(df_det.style.applymap(_estilo, subset=["Resultado"]),
                     use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
