"""
Informe de Corrida de Controles:
  - Reporte formal por turno/fecha (requerido para acreditación ISO 15189 / CAP)
  - Decisión de aceptación/rechazo de la corrida completa
  - Exportación PDF imprimible
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict

from database.database import init_db, get_session
from database import crud
from database.models import TURNOS
from modules.page_utils import setup_page

st.set_page_config(page_title="Informe de Corrida", page_icon="📄", layout="wide")
init_db()
setup_page()


def main():
    st.title("📄 Informe de Corrida de Controles")
    st.markdown(
        "Reporte oficial por turno — requerido para acreditación **ISO 15189 / CAP / CLIA**. "
        "Documenta la aceptación o rechazo de cada corrida analítica."
    )

    db = get_session()
    try:
        tab_informe, tab_sigma = st.tabs(["📋 Informe de Corrida", "📐 Índice de Sigma"])
        with tab_informe:
            _tab_informe(db)
        with tab_sigma:
            _tab_sigma(db)
    finally:
        db.close()


# ─── INFORME DE CORRIDA ───────────────────────────────────────────────────────

def _tab_informe(db):
    st.subheader("Generar Informe de Corrida")

    col1, col2, col3 = st.columns(3)
    fecha_sel = col1.date_input("Fecha de la corrida", value=date.today(),
                                 max_value=date.today(), key="ic_fecha")
    turno_sel = col2.selectbox("Turno", ["TODOS"] + TURNOS, key="ic_turno")
    areas = crud.listar_areas(db)
    area_opts = {"Todas": None} | {a.nombre: a.id for a in areas}
    area_sel = col3.selectbox("Área", list(area_opts.keys()), key="ic_area")

    controles = crud.listar_controles_diarios(db, fecha_desde=fecha_sel, fecha_hasta=fecha_sel)

    if area_opts[area_sel]:
        controles = [c for c in controles if c.material.equipo.area_id == area_opts[area_sel]]
    if turno_sel != "TODOS":
        controles = [c for c in controles if c.turno == turno_sel]

    if not controles:
        st.info("No hay controles registrados para la fecha y filtros seleccionados.")
        return

    # ── Decisión global de la corrida ─────────────────────────────────────
    total = len(controles)
    rechazos = [c for c in controles if c.resultado == "RECHAZO"]
    advertencias = [c for c in controles if c.resultado == "ADVERTENCIA"]
    aceptados = [c for c in controles if c.resultado == "OK"]

    decision = "RECHAZADA" if rechazos else "ACEPTADA"
    col_dec_color = "#fee2e2" if rechazos else "#d1fae5"
    col_dec_border = "#dc2626" if rechazos else "#10b981"
    col_dec_text = "#7f1d1d" if rechazos else "#065f46"
    icono_dec = "🛑" if rechazos else "✅"

    st.markdown(f"""
    <div style="
        background:{col_dec_color}; border:2px solid {col_dec_border};
        border-radius:14px; padding:20px 28px; margin-bottom:20px;
        display:flex; align-items:center; gap:20px;
    ">
        <div style="font-size:3rem;">{icono_dec}</div>
        <div>
            <div style="font-size:1.4rem; font-weight:800; color:{col_dec_text}; letter-spacing:-0.02em;">
                CORRIDA {decision}
            </div>
            <div style="color:{col_dec_text}; font-size:0.88rem; margin-top:4px; opacity:0.8;">
                {fecha_sel.strftime('%d/%m/%Y')} · Turno: {turno_sel}
                · {total} controles · {len(rechazos)} rechazo(s) · {len(advertencias)} advertencia(s)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs de la corrida ────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total controles", total)
    c2.metric("✅ Aceptados", len(aceptados))
    c3.metric("⚠️ Advertencias", len(advertencias))
    c4.metric("❌ Rechazos", len(rechazos),
              delta=f"{len(rechazos)} rechazo(s)" if rechazos else None,
              delta_color="inverse")

    st.markdown("---")

    # ── Tabla detallada de la corrida ─────────────────────────────────────
    st.markdown("### Detalle de controles de la corrida")

    filas = []
    for c in controles:
        m = c.material
        nl = c.nivel_lote
        limite_inf = nl.media - 2 * nl.de
        limite_sup = nl.media + 2 * nl.de
        dentro = "Dentro" if nl.valor_minimo <= c.valor <= nl.valor_maximo else "Fuera"
        filas.append({
            "Hora": c.hora.strftime("%H:%M"),
            "Turno": c.turno or "—",
            "Área": m.equipo.area.nombre,
            "Equipo": m.equipo.nombre,
            "Analito": m.analito,
            "Nv.": c.nivel_lote.nivel,
            "Lote": c.lote.numero_lote,
            "X̄ ± 2s": f"{nl.media:.3f} ± {2*nl.de:.3f}",
            "Valor": c.valor,
            "z-score": round(c.zscore, 3) if c.zscore else "",
            "Rango": dentro,
            "Resultado": c.resultado,
            "Regla": c.regla_violada or "—",
            "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
        })

    df = pd.DataFrame(filas)

    def _estilo_resultado(val):
        return {
            "OK":          "background-color:#d1fae5; color:#065f46; font-weight:600",
            "ADVERTENCIA": "background-color:#fef3c7; color:#78350f; font-weight:600",
            "RECHAZO":     "background-color:#fee2e2; color:#7f1d1d; font-weight:700",
        }.get(val, "")

    def _estilo_rango(val):
        return "background-color:#fee2e2; color:#7f1d1d; font-weight:600" if val == "Fuera" else ""

    st.dataframe(
        df.style
          .applymap(_estilo_resultado, subset=["Resultado"])
          .applymap(_estilo_rango, subset=["Rango"]),
        use_container_width=True, hide_index=True
    )

    # ── Resumen por analito ───────────────────────────────────────────────
    st.markdown("### Resumen por analito")
    resumen = defaultdict(lambda: {"total": 0, "ok": 0, "adv": 0, "rej": 0})
    for c in controles:
        k = f"{c.material.analito} Nv{c.nivel_lote.nivel}"
        resumen[k]["total"] += 1
        resumen[k][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

    filas_res = []
    for analito, d in sorted(resumen.items()):
        estado = "✅ OK" if d["rej"] == 0 else "❌ RECHAZO"
        filas_res.append({
            "Analito / Nivel": analito,
            "N": d["total"],
            "✅ OK": d["ok"],
            "⚠️ Adv.": d["adv"],
            "❌ Rech.": d["rej"],
            "Estado corrida": estado,
        })
    df_res = pd.DataFrame(filas_res)

    def _estilo_estado(val):
        return ("background-color:#fee2e2; color:#7f1d1d; font-weight:700" if "RECHAZO" in str(val)
                else "background-color:#d1fae5; color:#065f46; font-weight:600")

    st.dataframe(df_res.style.applymap(_estilo_estado, subset=["Estado corrida"]),
                 use_container_width=True, hide_index=True)

    # ── Rechazos pendientes de AC ─────────────────────────────────────────
    rechazos_sin_ac = [c for c in rechazos if not c.accion_correctiva]
    if rechazos_sin_ac:
        st.error(f"⚠️ **{len(rechazos_sin_ac)} rechazo(s) sin acción correctiva.** "
                 "Registre la acción en 🔧 Acciones Correctivas antes de liberar resultados.")

    # ── Exportar PDF ──────────────────────────────────────────────────────
    st.markdown("---")
    col_pdf, _ = st.columns([1, 3])
    if col_pdf.button("📄 Exportar Informe PDF", type="primary", key="btn_pdf_corrida"):
        try:
            from modules.pdf_export import informe_corrida_pdf
            try:
                lab = st.secrets.get("laboratorio_nombre", "Laboratorio Clínico")
            except Exception:
                lab = "Laboratorio Clínico"
            pdf_bytes = informe_corrida_pdf(
                controles=controles,
                fecha=fecha_sel,
                turno=turno_sel,
                decision=decision,
                laboratorio=lab,
            )
            st.download_button(
                "⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"informe_corrida_{fecha_sel}_{turno_sel}.pdf",
                mime="application/pdf",
                key="dl_corrida_pdf",
            )
        except ImportError:
            st.error("Instale fpdf2: `pip install fpdf2`")
        except Exception as e:
            st.error(f"Error generando PDF: {e}")


# ─── ÍNDICE DE SIGMA ─────────────────────────────────────────────────────────

def _tab_sigma(db):
    st.subheader("Índice de Sigma — Planificación del Control de Calidad")
    st.info(
        "El **Índice de Sigma** cuantifica la calidad analítica del proceso. "
        "**Fórmula:** σ = (TEa − |Sesgo%|) / CV%  \n"
        "Donde **TEa** = Error Total Permitido (CLIA/RiliBÄK), "
        "**Sesgo%** = sesgo observado, **CV%** = imprecisión observada."
    )

    materiales = crud.listar_materiales(db)
    if not materiales:
        st.warning("No hay analitos configurados.")
        return

    from modules.sigma import calcular_sigma
    import plotly.graph_objects as go

    # ── Configuración de TEa ───────────────────────────────────────────
    st.markdown("#### 1. Configure el Error Total Permitido (TEa%) por analito")
    st.caption("Use valores CLIA, RiliBÄK o de su protocolo interno.")

    tea_defaults = {
        "Glucosa": 10.0, "Hemoglobina": 7.0, "Hematocrito": 6.0,
        "Sodio": 0.3, "Potasio": 0.5, "Calcio": 1.0,
        "Creatinina": 15.0, "Urea": 9.0, "Colesterol": 9.0,
        "Triglicéridos": 25.0, "ALT": 20.0, "AST": 20.0,
        "Bilirrubina": 20.0, "Proteínas": 10.0, "Albúmina": 10.0,
    }

    # Datos de CV% observado de controles del último mes
    from datetime import date
    from calendar import monthrange
    hoy = date.today()
    _, ult = monthrange(hoy.year, hoy.month)
    fecha_desde = date(hoy.year, hoy.month, 1)
    controles_mes = crud.listar_controles_diarios(db, fecha_desde=fecha_desde, fecha_hasta=hoy)

    # Calcular CV% y sesgo por analito+nivel
    import statistics
    stats_por_analito: dict = defaultdict(list)
    for c in controles_mes:
        k = (c.material.analito, c.nivel_lote.nivel, c.nivel_lote.media, c.nivel_lote.de)
        stats_por_analito[k].append(c.valor)

    resultados_sigma = []
    mat_procesados = set()

    with st.form("form_sigma"):
        st.markdown("**Ingrese TEa% para cada analito:**")
        tea_inputs = {}
        cols = st.columns(4)
        col_idx = 0
        for m in materiales:
            if m.analito in mat_procesados:
                continue
            mat_procesados.add(m.analito)
            default_tea = tea_defaults.get(m.analito, 10.0)
            with cols[col_idx % 4]:
                tea_inputs[m.analito] = st.number_input(
                    f"{m.analito} (%)",
                    min_value=0.1, max_value=100.0,
                    value=default_tea, step=0.5,
                    key=f"tea_{m.analito}"
                )
            col_idx += 1

        calcular = st.form_submit_button("📐 Calcular Índice de Sigma", type="primary")

    if calcular or stats_por_analito:
        for (analito, nivel, media, de), valores in stats_por_analito.items():
            if len(valores) < 2:
                continue
            tea = tea_inputs.get(analito, 10.0)
            media_obs = statistics.mean(valores)
            de_obs = statistics.stdev(valores)
            cv_pct = (de_obs / media_obs * 100) if media_obs else 0
            sesgo_pct = ((media_obs - media) / media * 100) if media else 0
            res = calcular_sigma(tea, sesgo_pct, cv_pct)
            resultados_sigma.append({
                "analito": analito,
                "nivel": nivel,
                "n": len(valores),
                "tea": tea,
                "cv_pct": round(cv_pct, 2),
                "sesgo_pct": round(sesgo_pct, 2),
                "resultado": res,
            })

        if not resultados_sigma:
            st.info("No hay suficientes datos del mes actual para calcular Sigma. "
                    "Se necesitan al menos 2 controles por analito.")
            return

        # ── Gráfico de Sigma ───────────────────────────────────────────
        st.markdown("#### 2. Gráfico de Índice de Sigma por Analito")

        etiquetas = [f"{r['analito']} Nv{r['nivel']}" for r in resultados_sigma]
        sigmas    = [r["resultado"].sigma for r in resultados_sigma]
        colores   = [r["resultado"].color for r in resultados_sigma]

        fig = go.Figure()

        # Zonas de referencia
        fig.add_hrect(y0=0,  y1=2,  fillcolor="rgba(220,38,38,0.08)",  line_width=0)
        fig.add_hrect(y0=2,  y1=3,  fillcolor="rgba(234,88,12,0.08)",  line_width=0)
        fig.add_hrect(y0=3,  y1=4,  fillcolor="rgba(202,138,4,0.08)",  line_width=0)
        fig.add_hrect(y0=4,  y1=6,  fillcolor="rgba(22,163,74,0.08)",  line_width=0)
        fig.add_hrect(y0=6,  y1=12, fillcolor="rgba(5,150,105,0.08)",  line_width=0)

        # Líneas de referencia
        for y, label, color in [(2,"Inaceptable","#dc2626"),(3,"Marginal","#ea580c"),
                                  (4,"Bueno","#ca8a04"),(6,"Clase mundial","#059669")]:
            fig.add_hline(y=y, line_color=color, line_dash="dash", line_width=1.5,
                          annotation_text=f"σ={y} — {label}",
                          annotation_position="right", annotation_font_size=9)

        fig.add_bar(
            x=etiquetas, y=sigmas,
            marker_color=colores,
            marker_line_width=0,
            text=[f"σ={s:.1f}" for s in sigmas],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>σ = %{y:.2f}<extra></extra>",
        )
        fig.update_layout(
            height=420,
            margin=dict(l=0, r=120, t=20, b=0),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(title="Índice σ", gridcolor="#f1f5f9", range=[0, max(sigmas)*1.3 if sigmas else 10]),
            xaxis=dict(gridcolor="#f1f5f9", tickangle=30),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Tabla de resultados ────────────────────────────────────────
        st.markdown("#### 3. Tabla de resultados y recomendaciones")
        filas_sigma = []
        for r in resultados_sigma:
            res = r["resultado"]
            filas_sigma.append({
                "Analito": r["analito"],
                "Nivel": r["nivel"],
                "N": r["n"],
                "TEa%": r["tea"],
                "CV%": r["cv_pct"],
                "Sesgo%": r["sesgo_pct"],
                "σ": res.sigma,
                "Clasificación": res.clasificacion,
                "Niveles QC": res.n_niveles_recomendado,
                "Reglas recomendadas": res.reglas_recomendadas,
            })

        df_s = pd.DataFrame(filas_sigma)

        def _color_sigma(val):
            try:
                v = float(val)
                if v >= 6:  return "background-color:#d1fae5; color:#065f46; font-weight:700"
                if v >= 4:  return "background-color:#dcfce7; color:#166534; font-weight:600"
                if v >= 3:  return "background-color:#fef3c7; color:#78350f; font-weight:600"
                if v >= 2:  return "background-color:#ffedd5; color:#7c2d12; font-weight:600"
                return "background-color:#fee2e2; color:#7f1d1d; font-weight:700"
            except Exception:
                return ""

        st.dataframe(df_s.style.applymap(_color_sigma, subset=["σ"]),
                     use_container_width=True, hide_index=True)

        # ── Alertas críticas ───────────────────────────────────────────
        criticos = [r for r in resultados_sigma if r["resultado"].sigma < 3]
        if criticos:
            st.error(f"🚨 **{len(criticos)} analito(s) con σ < 3** requieren acción inmediata:")
            for r in criticos:
                st.markdown(
                    f"&emsp;▸ **{r['analito']} Nv{r['nivel']}** — "
                    f"σ = {r['resultado'].sigma:.2f} ({r['resultado'].clasificacion}) — "
                    f"{r['resultado'].recomendacion_qc}"
                )


if __name__ == "__main__":
    main()
