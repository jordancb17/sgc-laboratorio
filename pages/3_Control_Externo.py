"""
Página de Control Externo (PEEC / EQA):
  - Registro de resultados de evaluación externa
  - Cálculo automático de z-score
  - Clasificación: ACEPTABLE / ADVERTENCIA / INACEPTABLE
  - Tendencia por período
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from database.database import init_db, get_session
from database import crud

st.set_page_config(page_title="Control Externo", page_icon="🌐", layout="wide")
init_db()
from modules.page_utils import setup_page
setup_page()


def main():
    st.title("🌐 Control Externo de Calidad (PEEC / EQA)")
    tab_reg, tab_ver = st.tabs(["📝 Registrar Resultado", "📊 Ver Resultados y Tendencia"])
    db = get_session()
    try:
        with tab_reg:
            _tab_registrar(db)
        with tab_ver:
            _tab_ver(db)
    finally:
        db.close()


def _tab_registrar(db):
    st.subheader("Registrar Resultado de Control Externo")

    materiales = crud.listar_materiales(db)
    if not materiales:
        st.warning("No hay analitos configurados. Vaya a ⚙️ Configuración.")
        return

    personal = crud.listar_personal(db)
    if not personal:
        st.warning("No hay personal configurado.")
        return

    mat_opts = {f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}": m.id for m in materiales}
    pers_opts = {f"{p.apellido}, {p.nombre}": p.id for p in personal}

    with st.form("form_ce"):
        col1, col2 = st.columns(2)
        mat_sel = col1.selectbox("Analito *", list(mat_opts.keys()))
        pers_sel = col2.selectbox("Personal que ingresa *", list(pers_opts.keys()))

        col1, col2, col3 = st.columns(3)
        proveedor = col1.text_input("Proveedor externo *", placeholder="Ej: RIQAS, EQAS, CAP")
        periodo = col2.text_input("Período *", placeholder="Ej: 2024-01, 2024-S1")
        nivel = col3.selectbox("Nivel", [1, 2, 3])

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        valor_obtenido = col1.number_input("Valor obtenido por el laboratorio *", format="%.4f")
        valor_diana = col2.number_input("Valor diana / Media del grupo", format="%.4f", value=0.0)
        de_grupo = col3.number_input("DE del grupo de pares", min_value=0.0, format="%.4f", value=0.0)

        col1, col2 = st.columns(2)
        n_part = col1.number_input("N° de participantes", min_value=0, step=1)
        percentil = col2.number_input("Percentil obtenido (%)", min_value=0.0, max_value=100.0, value=0.0)

        comentario = st.text_area("Comentario", height=60)

        # Preview z-score
        if valor_diana != 0.0 and de_grupo > 0:
            z = (valor_obtenido - valor_diana) / de_grupo
            az = abs(z)
            if az <= 2.0:
                clasif = "✅ ACEPTABLE"
            elif az <= 3.0:
                clasif = "⚠️ ADVERTENCIA"
            else:
                clasif = "❌ INACEPTABLE"
            st.info(f"**z-score calculado:** `{z:.3f}` → **{clasif}**")

        if st.form_submit_button("💾 Guardar Resultado", type="primary"):
            if not proveedor.strip() or not periodo.strip():
                st.error("Proveedor y período son obligatorios.")
            elif valor_obtenido == 0.0:
                st.error("Ingrese el valor obtenido.")
            else:
                ce, err = crud.registrar_control_externo(
                    db=db,
                    material_id=mat_opts[mat_sel],
                    personal_id=pers_opts[pers_sel],
                    proveedor_externo=proveedor,
                    periodo=periodo,
                    nivel=nivel,
                    valor_obtenido=valor_obtenido,
                    valor_diana=valor_diana if valor_diana != 0 else None,
                    de_grupo=de_grupo if de_grupo > 0 else None,
                    n_participantes=int(n_part) if n_part > 0 else None,
                    percentil=percentil if percentil > 0 else None,
                    comentario=comentario,
                )
                if err:
                    st.error(f"Error: {err}")
                else:
                    st.success(f"Resultado registrado. Estado: **{ce.resultado}**")
                    if ce.zscore is not None:
                        st.metric("z-score", f"{ce.zscore:.3f}")


def _tab_ver(db):
    st.subheader("Resultados y Tendencia de Control Externo")

    materiales = crud.listar_materiales(db)
    if not materiales:
        st.info("No hay analitos configurados.")
        return

    mat_opts = {f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}": m.id for m in materiales}
    mat_sel = st.selectbox("Analito", list(mat_opts.keys()), key="ce_mat")

    controles = crud.listar_controles_externos(db, material_id=mat_opts[mat_sel])
    if not controles:
        st.info("No hay resultados de control externo para este analito.")
        return

    filas = []
    for ce in controles:
        mat = ce.material
        filas.append({
            "ID": ce.id,
            "Proveedor": ce.proveedor_externo,
            "Período": ce.periodo,
            "Nivel": ce.nivel,
            "Valor obtenido": ce.valor_obtenido,
            "Valor diana": ce.valor_diana,
            "DE grupo": ce.de_grupo,
            "z-score": round(ce.zscore, 3) if ce.zscore is not None else "N/D",
            "N° participantes": ce.n_participantes,
            "Percentil": ce.percentil,
            "Resultado": ce.resultado,
            "Personal": f"{ce.personal.apellido}, {ce.personal.nombre}" if ce.personal else "",
            "Comentario": ce.comentario or "",
        })

    df = pd.DataFrame(filas)

    def _estilo_ce(val):
        mapa = {"ACEPTABLE": "background-color:#d4edda", "ADVERTENCIA": "background-color:#fff3cd", "INACEPTABLE": "background-color:#f8d7da"}
        return mapa.get(val, "")

    st.dataframe(df.style.applymap(_estilo_ce, subset=["Resultado"]), use_container_width=True, hide_index=True)

    # ── Gráfico de z-scores por período ──────────────────────────────────────
    ce_con_z = [ce for ce in controles if ce.zscore is not None]
    if ce_con_z:
        st.subheader("Gráfico de z-scores por período")
        niveles_uniq = sorted({ce.nivel for ce in ce_con_z})
        nivel_graf = st.selectbox("Nivel a graficar", niveles_uniq, key="ce_niv_graf")

        datos_graf = [(ce.periodo, ce.zscore) for ce in ce_con_z if ce.nivel == nivel_graf]
        datos_graf.sort(key=lambda x: x[0])

        if datos_graf:
            periodos = [d[0] for d in datos_graf]
            zscores = [d[1] for d in datos_graf]

            fig = go.Figure()
            fig.add_hline(y=0, line_color="gray", line_dash="solid", line_width=1)
            fig.add_hline(y=2, line_color="orange", line_dash="dash", line_width=1, annotation_text="+2s")
            fig.add_hline(y=-2, line_color="orange", line_dash="dash", line_width=1, annotation_text="-2s")
            fig.add_hline(y=3, line_color="red", line_dash="dot", line_width=1, annotation_text="+3s")
            fig.add_hline(y=-3, line_color="red", line_dash="dot", line_width=1, annotation_text="-3s")

            colores_puntos = []
            for z in zscores:
                if abs(z) > 3:
                    colores_puntos.append("red")
                elif abs(z) > 2:
                    colores_puntos.append("orange")
                else:
                    colores_puntos.append("green")

            fig.add_trace(go.Scatter(
                x=periodos,
                y=zscores,
                mode="lines+markers",
                marker=dict(color=colores_puntos, size=10),
                line=dict(color="steelblue"),
                name="z-score",
            ))

            fig.update_layout(
                title=f"z-scores Control Externo — Nivel {nivel_graf}",
                xaxis_title="Período",
                yaxis_title="z-score",
                yaxis=dict(range=[-4.5, 4.5]),
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    # Descargar
    try:
        import io
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        st.download_button("⬇️ Descargar Excel", buf.getvalue(), "control_externo.xlsx")
    except Exception:
        pass


if __name__ == "__main__":
    main()
