"""
Página de Reportes — v3 profesional.

Novedades v3:
  - Canvas de firma digital del Responsable de Área (streamlit-drawable-canvas)
  - Gráfico Levey-Jennings embebido en el PDF (requiere kaleido)
  - Vista previa del reporte integrada en pantalla (st.components.v1.html)
  - Selector de rango temporal con presets
  - Levey-Jennings multi-nivel simultáneo

Westgard multi-regla (1-2s / 1-3s / 2-2s / R-4s / 4-1s / 10x) aplicado en
tiempo real durante el registro (ver 2_Controles_Diarios.py). Los resultados
se muestran anotados en el gráfico y detallados en todos los reportes.
"""

import sys, io, base64, statistics
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from database.database import init_db, get_session
from database import crud
from database.models import TURNOS
from modules.westgard import RESULTADO_OK, RESULTADO_ADVERTENCIA, RESULTADO_RECHAZO
from modules.page_utils import setup_page, page_header

st.set_page_config(page_title="Reportes", page_icon="📊", layout="wide")
init_db()
setup_page()

# ── Paleta ────────────────────────────────────────────────────────────────────
COL_OK  = "#16a34a"
COL_ADV = "#d97706"
COL_REJ = "#dc2626"
COL_PTS = {RESULTADO_OK: COL_OK, RESULTADO_ADVERTENCIA: COL_ADV, RESULTADO_RECHAZO: COL_REJ}

RANGOS = ["Hoy", "Última semana", "Último mes", "Últimos 3 meses", "Último año", "Personalizado"]


# ── Helpers globales ──────────────────────────────────────────────────────────

def _rango_fechas(rango: str, def_desde: date, def_hasta: date) -> tuple[date, date]:
    hoy = date.today()
    match rango:
        case "Hoy":             return hoy, hoy
        case "Última semana":   return hoy - timedelta(days=7),  hoy
        case "Último mes":      return hoy - timedelta(days=30), hoy
        case "Últimos 3 meses": return hoy - timedelta(days=90), hoy
        case "Último año":      return hoy - timedelta(days=365), hoy
        case _:                 return def_desde, def_hasta


def _get_lab() -> str:
    try:
        return st.secrets.get("laboratorio_nombre", "Laboratorio Clínico")
    except Exception:
        return "Laboratorio Clínico"


def _firma_dict(pers_obj, sig_bytes) -> dict | None:
    """Construye el dict de firma para los PDFs."""
    if pers_obj is None:
        return None
    return {
        "nombre":  f"{pers_obj.apellido}, {pers_obj.nombre}",
        "cargo":   pers_obj.cargo or "Profesional de Laboratorio",
        "codigo":  pers_obj.codigo or "—",
        "fecha":   date.today(),
        "imagen":  sig_bytes,
    }


# ── Widget de firma digital ───────────────────────────────────────────────────

def _bloque_firma(db, key_prefix: str) -> tuple:
    """
    Muestra el selector de Responsable de Área y el canvas de firma.
    Retorna (personal_obj | None, sig_bytes | None).
    """
    personal = crud.listar_personal(db)
    if not personal:
        st.caption("ℹ️ Configure personal en ⚙️ Configuración para habilitar la firma.")
        return None, None

    pers_opts = {f"{p.apellido}, {p.nombre}": p for p in personal}

    col_p, col_c = st.columns([1, 2])

    with col_p:
        pers_sel = st.selectbox(
            "Responsable de Área",
            list(pers_opts.keys()),
            key=f"{key_prefix}_firma_pers",
        )
        pers_obj = pers_opts[pers_sel]

        with st.container(border=True):
            st.markdown(f"**{pers_obj.apellido}, {pers_obj.nombre}**")
            st.caption(f"Cargo: {pers_obj.cargo or '—'}")
            st.caption(f"Código: {pers_obj.codigo or '—'}")

        if st.button("🗑️ Limpiar firma", key=f"{key_prefix}_clear_sig",
                     help="Borrar el trazo del lienzo"):
            st.session_state[f"{key_prefix}_sig_gen"] = (
                st.session_state.get(f"{key_prefix}_sig_gen", 0) + 1
            )
            st.rerun()

    with col_c:
        st.caption("✍️ Trace la firma en el recuadro:")
        try:
            from streamlit_drawable_canvas import st_canvas

            sig_gen = st.session_state.get(f"{key_prefix}_sig_gen", 0)
            canvas_result = st_canvas(
                fill_color="rgba(255,255,255,1)",
                stroke_width=2,
                stroke_color="#000000",
                background_color="#FFFFFF",
                update_streamlit=True,
                height=115,
                drawing_mode="freedraw",
                key=f"{key_prefix}_canvas_{sig_gen}",
            )

            sig_bytes = None
            data = canvas_result.image_data
            if data is not None and int(data.sum()) > 0:
                try:
                    from PIL import Image
                    import numpy as np
                    arr = data.astype("uint8")
                    img_pil = Image.fromarray(arr, "RGBA")
                    bg = Image.new("RGB", img_pil.size, (255, 255, 255))
                    bg.paste(img_pil, mask=img_pil.split()[3])
                    buf = io.BytesIO()
                    bg.save(buf, format="PNG")
                    sig_bytes = buf.getvalue()
                except Exception:
                    sig_bytes = None

            return pers_obj, sig_bytes

        except ImportError:
            st.info(
                "Instale las dependencias para habilitar la firma digital:\n"
                "`pip install streamlit-drawable-canvas pillow`"
            )
            return pers_obj, None


# ── HTML imprimible — Levey-Jennings ──────────────────────────────────────────

def _html_lj(controles, material, niveles, stats, desde, hasta, lab, firma_info=None) -> str:
    filas_stats = ""
    for nv, s in sorted(stats.items()):
        color_rej = "#dc2626" if s["rej_n"] > 0 else "#16a34a"
        filas_stats += (
            f"<tr><td><b>Nivel {nv}</b></td>"
            f"<td>{s['N']}</td>"
            f"<td>{s['media_ref']:.4f}</td><td>{s['de_ref']:.4f}</td>"
            f"<td>{s['media_obs']:.4f}</td><td>{s['de_obs']:.4f}</td>"
            f"<td>{s['cv_obs']:.2f}%</td>"
            f"<td style='color:{color_rej};font-weight:700;'>"
            f"{s['rej_n']} ({s['tasa_rej']:.1f}%)</td>"
            f"<td>{s['adv_n']}</td></tr>"
        )

    filas_ctrl = ""
    for c in controles:
        bg = {"OK": "#d1fae5", "ADVERTENCIA": "#fef3c7", "RECHAZO": "#fee2e2"}.get(c.resultado, "#fff")
        fg = {"OK": "#065f46", "ADVERTENCIA": "#78350f", "RECHAZO": "#7f1d1d"}.get(c.resultado, "#000")
        zsco = f"{c.zscore:.3f}" if c.zscore is not None else "—"
        filas_ctrl += (
            f"<tr style='background:{bg};'>"
            f"<td>{c.fecha}</td><td>{c.hora.strftime('%H:%M')}</td>"
            f"<td>{c.turno or '—'}</td><td>{c.nivel_lote.nivel}</td>"
            f"<td><b>{c.valor}</b></td><td>{zsco}</td>"
            f"<td style='color:{fg};font-weight:700;'>{c.resultado}</td>"
            f"<td>{c.regla_violada or '—'}</td>"
            f"<td>{c.personal.apellido}, {c.personal.nombre}</td></tr>"
        )

    firma_html = ""
    if firma_info:
        firma_html = f"""
        <div style="border:1px solid #bfdbfe;border-radius:8px;padding:14px 18px;
                    margin-top:18px;background:#f0f7ff;">
          <h2 style="font-size:12px;color:#1e3a8a;border-bottom:1.5px solid #bfdbfe;
                     padding-bottom:3px;margin-bottom:8px;">
            Validación — Responsable de Área
          </h2>
          <table style="font-size:10px;width:auto;">
            <tr><td style="font-weight:700;padding-right:16px;">Responsable de Área:</td>
                <td>{firma_info.get('nombre','—')}</td></tr>
            <tr><td style="font-weight:700;padding-right:16px;">Cargo:</td>
                <td>{firma_info.get('cargo','—')}</td></tr>
            <tr><td style="font-weight:700;padding-right:16px;">Código:</td>
                <td>{firma_info.get('codigo','—')}</td></tr>
            <tr><td style="font-weight:700;padding-right:16px;">Fecha de revisión:</td>
                <td>{date.today().strftime('%d/%m/%Y')}</td></tr>
          </table>
          {_firma_img_html(firma_info)}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Levey-Jennings — {material.analito}</title>
<style>
  @page {{ size: A4 landscape; margin: 12mm 15mm; }}
  @media print {{ .no-print {{ display:none !important; }} }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:Arial,sans-serif; color:#1e293b; font-size:10px; padding:16px; }}
  .header {{ background:#1e3a8a; color:white; padding:12px 16px; border-radius:8px; margin-bottom:10px; }}
  .header h1 {{ font-size:15px; margin-bottom:3px; }}
  .header .meta {{ font-size:9px; opacity:.82; }}
  .wg-badges {{ margin-bottom:10px; }}
  .badge {{ display:inline-block;background:#eff6ff;color:#1e40af;border:1px solid #bfdbfe;
            border-radius:4px;padding:2px 7px;font-size:8.5px;margin:2px; }}
  h2 {{ font-size:11px;color:#1e3a8a;border-bottom:1.5px solid #bfdbfe;
        padding-bottom:3px;margin:12px 0 5px; }}
  table {{ width:100%;border-collapse:collapse;font-size:9px;margin-bottom:8px; }}
  th {{ background:#1e3a8a;color:white;padding:4px 6px;text-align:left; }}
  td {{ padding:3px 6px;border-bottom:1px solid #e2e8f0; }}
  .print-btn {{ background:#1e3a8a;color:white;border:none;padding:9px 20px;
                border-radius:7px;cursor:pointer;font-size:13px;font-weight:600;
                margin-bottom:14px;display:block; }}
  .footer {{ color:#94a3b8;font-size:8px;text-align:center;
             margin-top:16px;border-top:1px solid #e2e8f0;padding-top:6px; }}
</style>
</head>
<body>
  <button class="print-btn no-print" onclick="window.print()">
    🖨️ Imprimir / Guardar como PDF
  </button>

  <div class="header">
    <h1>Registro Levey-Jennings — {material.analito}</h1>
    <div class="meta">
      {lab} &nbsp;·&nbsp; {desde.strftime('%d/%m/%Y')} → {hasta.strftime('%d/%m/%Y')}
      &nbsp;·&nbsp; Niveles: {', '.join(str(n) for n in sorted(niveles))}
      &nbsp;·&nbsp; Generado: {date.today().strftime('%d/%m/%Y')}
    </div>
  </div>

  <div class="wg-badges">
    <b style="font-size:9px;">Reglas Westgard aplicadas:</b>
    <span class="badge">1-2s Advertencia</span>
    <span class="badge">1-3s Rechazo</span>
    <span class="badge">2-2s Rechazo</span>
    <span class="badge">R-4s Rechazo</span>
    <span class="badge">4-1s Rechazo</span>
    <span class="badge">10x Rechazo</span>
    <span class="badge">R-4s Inter-nivel</span>
  </div>

  <h2>Estadísticos por Nivel de Control</h2>
  <table>
    <thead>
      <tr><th>Nivel</th><th>N</th><th>X̄ objetivo</th><th>s objetivo</th>
          <th>X̄ obs.</th><th>s obs.</th><th>CV% obs.</th>
          <th>Rechazos (N / %)</th><th>Advertencias</th></tr>
    </thead>
    <tbody>{filas_stats}</tbody>
  </table>

  <h2>Detalle de Controles</h2>
  <table>
    <thead>
      <tr><th>Fecha</th><th>Hora</th><th>Turno</th><th>Nivel</th>
          <th>Valor ({material.unidad or ''})</th><th>z-score</th>
          <th>Resultado</th><th>Regla Westgard</th><th>Personal</th></tr>
    </thead>
    <tbody>{filas_ctrl}</tbody>
  </table>

  {firma_html}

  <p class="footer">
    SGC Laboratorio Clínico · Control de Calidad Interno · ISO 15189 / CLSI C24-A3 ·
    Westgard Multi-Regla
  </p>
</body>
</html>"""


def _firma_img_html(firma_info: dict) -> str:
    """Retorna HTML de la imagen de firma si existe, o línea vacía."""
    img_b = firma_info.get("imagen_b64")
    if img_b:
        return (
            f"<div style='margin-top:8px;'>"
            f"<div style='font-weight:700;margin-bottom:3px;'>Firma:</div>"
            f"<img src='data:image/png;base64,{img_b}' "
            f"style='height:50px;border:1px solid #bfdbfe;border-radius:4px;'></div>"
        )
    return (
        "<div style='margin-top:18px;border-bottom:1px solid #94a3b8;"
        "width:180px;'></div>"
        "<div style='font-size:8px;color:#94a3b8;margin-top:3px;'>"
        "Firma del Responsable de Área</div>"
    )


# ── HTML imprimible — Informe de Corrida ──────────────────────────────────────

def _html_corrida(controles, fecha, turno, decision, lab, firma_info=None) -> str:
    ic = "🛑 RECHAZADA" if decision == "RECHAZADA" else "✅ ACEPTADA"
    bg = "#fee2e2" if decision == "RECHAZADA" else "#d1fae5"
    fg = "#7f1d1d" if decision == "RECHAZADA" else "#065f46"

    filas_ana: dict = defaultdict(lambda: {"total": 0, "ok": 0, "adv": 0, "rej": 0})
    for c in controles:
        k = f"{c.material.analito}  Nv{c.nivel_lote.nivel}"
        filas_ana[k]["total"] += 1
        filas_ana[k][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

    res_html = ""
    for analito, d in sorted(filas_ana.items()):
        bg_e = "#fee2e2" if d["rej"] else "#d1fae5"
        fg_e = "#7f1d1d" if d["rej"] else "#065f46"
        res_html += (
            f"<tr><td>{analito}</td><td>{d['total']}</td><td>{d['ok']}</td>"
            f"<td>{d['adv']}</td><td>{d['rej']}</td>"
            f"<td style='background:{bg_e};color:{fg_e};font-weight:700;'>"
            f"{'RECHAZO' if d['rej'] else 'OK'}</td></tr>"
        )

    det_html = ""
    for c in controles:
        m = c.material
        row_bg = {"OK": "#d1fae5", "ADVERTENCIA": "#fef3c7", "RECHAZO": "#fee2e2"}.get(c.resultado, "#fff")
        row_fg = {"OK": "#065f46", "ADVERTENCIA": "#78350f", "RECHAZO": "#7f1d1d"}.get(c.resultado, "#000")
        den = "Fuera" if not (c.nivel_lote.valor_minimo <= c.valor <= c.nivel_lote.valor_maximo) else "Dentro"
        det_html += (
            f"<tr style='background:{row_bg};'>"
            f"<td>{c.hora.strftime('%H:%M')}</td><td>{c.turno or '—'}</td>"
            f"<td>{m.equipo.area.nombre}</td><td>{m.equipo.nombre}</td>"
            f"<td>{m.analito}</td><td>{c.nivel_lote.nivel}</td>"
            f"<td>{c.valor}</td><td>{c.zscore:.3f if c.zscore else '—'}</td>"
            f"<td>{den}</td>"
            f"<td style='color:{row_fg};font-weight:700;'>{c.resultado}</td>"
            f"<td>{c.regla_violada or '—'}</td>"
            f"<td>{c.personal.apellido}, {c.personal.nombre}</td></tr>"
        )

    firma_html = ""
    if firma_info:
        firma_html = f"""
        <div style="border:1px solid #bfdbfe;border-radius:8px;padding:14px 18px;
                    margin-top:18px;background:#f0f7ff;">
          <h2 style="font-size:12px;color:#1e3a8a;margin-bottom:8px;">
            Validación — Responsable de Área
          </h2>
          <table style="font-size:10px;width:auto;">
            <tr><td style="font-weight:700;padding-right:16px;">Responsable:</td>
                <td>{firma_info.get('nombre','—')}</td></tr>
            <tr><td style="font-weight:700;padding-right:16px;">Cargo:</td>
                <td>{firma_info.get('cargo','—')}</td></tr>
            <tr><td style="font-weight:700;padding-right:16px;">Fecha revisión:</td>
                <td>{date.today().strftime('%d/%m/%Y')}</td></tr>
          </table>
          {_firma_img_html(firma_info)}
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><title>Informe Corrida — {fecha}</title>
<style>
  @page {{ size: A4 landscape; margin: 12mm 15mm; }}
  @media print {{ .no-print {{ display:none !important; }} }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:Arial,sans-serif;color:#1e293b;font-size:9.5px;padding:14px; }}
  .header {{ background:#1e3a8a;color:white;padding:10px 16px;border-radius:8px;margin-bottom:8px; }}
  .header h1 {{ font-size:14px; }}
  .decision {{ background:{bg};color:{fg};border-radius:7px;padding:9px 16px;
               font-size:13px;font-weight:800;margin-bottom:10px; }}
  h2 {{ font-size:11px;color:#1e3a8a;border-bottom:1.5px solid #bfdbfe;
        padding-bottom:3px;margin:10px 0 5px; }}
  table {{ width:100%;border-collapse:collapse;font-size:9px;margin-bottom:8px; }}
  th {{ background:#1e3a8a;color:white;padding:4px 6px;text-align:left; }}
  td {{ padding:3px 6px;border-bottom:1px solid #e2e8f0; }}
  .print-btn {{ background:#1e3a8a;color:white;border:none;padding:8px 18px;
                border-radius:7px;cursor:pointer;font-size:12px;font-weight:600;
                margin-bottom:12px;display:block; }}
  .footer {{ color:#94a3b8;font-size:8px;text-align:center;
             margin-top:14px;border-top:1px solid #e2e8f0;padding-top:6px; }}
</style>
</head>
<body>
  <button class="print-btn no-print" onclick="window.print()">
    🖨️ Imprimir / Guardar como PDF
  </button>
  <div class="header">
    <h1>Informe de Corrida — {lab}</h1>
    <div style="font-size:9px;opacity:.85;">
      {fecha.strftime('%d/%m/%Y')} · Turno: {turno} · Generado: {date.today().strftime('%d/%m/%Y')}
    </div>
  </div>
  <div class="decision">CORRIDA {ic}</div>

  <h2>Resumen por Analito y Nivel</h2>
  <table>
    <thead><tr><th>Analito / Nivel</th><th>N</th><th>✅ OK</th>
        <th>⚠️ Adv.</th><th>❌ Rech.</th><th>Estado</th></tr></thead>
    <tbody>{res_html}</tbody>
  </table>

  <h2>Detalle de Controles</h2>
  <table>
    <thead><tr><th>Hora</th><th>Turno</th><th>Área</th><th>Equipo</th><th>Analito</th>
        <th>Nv</th><th>Valor</th><th>z</th><th>Rango</th>
        <th>Resultado</th><th>Regla</th><th>Personal</th></tr></thead>
    <tbody>{det_html}</tbody>
  </table>

  {firma_html}

  <p class="footer">
    SGC Laboratorio Clínico · ISO 15189 / CAP · Westgard Multi-Regla
  </p>
</body>
</html>"""


# ── Figura Plotly LJ multi-nivel ──────────────────────────────────────────────

def _lj_figura(controles: list, material, niveles: list[int]) -> go.Figure:
    n_niv  = len(niveles)
    altura = max(400 * n_niv, 440)

    fig = make_subplots(
        rows=n_niv, cols=1,
        subplot_titles=[f"Nivel {n}" for n in niveles],
        shared_xaxes=False,
        vertical_spacing=max(0.10 / n_niv, 0.03) if n_niv > 1 else 0.0,
    )

    for row_idx, nivel_num in enumerate(niveles, start=1):
        cs = [c for c in controles if c.nivel_lote.nivel == nivel_num]
        if not cs:
            continue

        nl  = cs[0].nivel_lote
        med = nl.media
        de  = nl.de
        uni = material.unidad or ""

        fechas   = [f"{c.fecha} {c.hora.strftime('%H:%M')}" for c in cs]
        valores  = [c.valor for c in cs]
        zscores  = [c.zscore or 0.0 for c in cs]
        res      = [c.resultado for c in cs]
        reglas   = [c.regla_violada or "" for c in cs]
        pts_col  = [COL_PTS.get(r, "#94a3b8") for r in res]

        # Bandas de fondo
        if len(fechas) >= 2:
            xs2 = [fechas[0], fechas[-1]]
            for upper, lower, fc in [
                (med + 3*de, med + 2*de, "rgba(220,38,38,0.07)"),
                (med - 2*de, med - 3*de, "rgba(220,38,38,0.07)"),
                (med + 2*de, med + de,   "rgba(217,119,6,0.07)"),
                (med - de,   med - 2*de, "rgba(217,119,6,0.07)"),
                (med + de,   med - de,   "rgba(22,163,74,0.06)"),
            ]:
                fig.add_trace(go.Scatter(
                    x=xs2 + xs2[::-1], y=[upper, upper, lower, lower],
                    fill="toself", fillcolor=fc,
                    line=dict(width=0), showlegend=False, hoverinfo="skip",
                ), row=row_idx, col=1)

        # Línea de datos
        fig.add_trace(go.Scatter(
            x=fechas, y=valores,
            mode="lines+markers",
            marker=dict(color=pts_col, size=8, line=dict(width=1.5, color="white")),
            line=dict(color="rgba(100,116,139,0.6)", width=1.5),
            text=[
                f"z = {z:.3f}  |  {r}" + (f"  |  Regla: {rg}" if rg else "")
                for z, r, rg in zip(zscores, res, reglas)
            ],
            hovertemplate="%{x}<br>Valor: <b>%{y:.4f}</b> " + uni + "<br>%{text}<extra></extra>",
            name=f"Nivel {nivel_num}", showlegend=(n_niv > 1),
        ), row=row_idx, col=1)

        # Líneas de referencia
        for y_val, color, dash, label in [
            (med + 3*de, COL_REJ,   "dot",     f"+3s = {med+3*de:.3f}"),
            (med + 2*de, COL_ADV,   "dash",    f"+2s = {med+2*de:.3f}"),
            (med + de,   COL_OK,    "dashdot", "+1s"),
            (med,        "#2563eb", "solid",   f"X̄ = {med:.3f}"),
            (med - de,   COL_OK,    "dashdot", "−1s"),
            (med - 2*de, COL_ADV,   "dash",    f"−2s = {med-2*de:.3f}"),
            (med - 3*de, COL_REJ,   "dot",     f"−3s = {med-3*de:.3f}"),
        ]:
            fig.add_hline(
                y=y_val, line_color=color, line_dash=dash, line_width=1.2,
                annotation_text=label, annotation_position="right",
                annotation_font_size=8,
                row=row_idx, col=1,
            )

        # × para rechazos
        rej_x = [fechas[i] for i, r in enumerate(res) if r == RESULTADO_RECHAZO]
        rej_y = [valores[i] for i, r in enumerate(res) if r == RESULTADO_RECHAZO]
        if rej_x:
            fig.add_trace(go.Scatter(
                x=rej_x, y=rej_y, mode="markers",
                marker=dict(symbol="x", size=14, color=COL_REJ, line=dict(width=2.5)),
                name="Rechazo", showlegend=False,
            ), row=row_idx, col=1)

        # Anotaciones de reglas (solo cuando hay pocos puntos)
        if len(cs) <= 60:
            for i, (r, rg) in enumerate(zip(res, reglas)):
                if r in (RESULTADO_RECHAZO, RESULTADO_ADVERTENCIA) and rg:
                    xref = "x" if row_idx == 1 else f"x{row_idx}"
                    yref = "y" if row_idx == 1 else f"y{row_idx}"
                    fig.add_annotation(
                        x=fechas[i], y=valores[i], xref=xref, yref=yref,
                        text=rg, showarrow=True,
                        arrowhead=2, arrowsize=0.8, arrowwidth=1.5,
                        arrowcolor=COL_PTS.get(r, "#94a3b8"),
                        ax=0, ay=-26,
                        font=dict(size=8, color=COL_PTS.get(r, "#94a3b8")),
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor=COL_PTS.get(r, "#94a3b8"),
                        borderwidth=1, borderpad=2,
                    )

    fig.update_layout(
        height=altura,
        margin=dict(l=0, r=130, t=40, b=10),
        hovermode="closest",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
    )
    fig.update_xaxes(gridcolor="rgba(128,128,128,0.12)", tickangle=35)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.12)")
    return fig, altura


# ── PÁGINA PRINCIPAL ──────────────────────────────────────────────────────────

def main():
    page_header(
        icon="📊",
        title="Reportes de Calidad",
        subtitle=(
            "Levey-Jennings multi-nivel · Reporte periódico · Informe de corrida · "
            "Westgard 1-3s / 2-2s / R-4s / 4-1s / 10x aplicado en tiempo real"
        ),
        badge="Reportes y Tendencias",
    )
    tab_lj, tab_per, tab_cor, tab_prs = st.tabs([
        "📈 Levey-Jennings",
        "📅 Reporte Periódico",
        "📄 Informe de Corrida",
        "👤 Personal",
    ])
    with tab_lj:  _tab_lj()
    with tab_per: _tab_periodico()
    with tab_cor: _tab_corrida()
    with tab_prs: _tab_personal()


# ── TAB 1: LEVEY-JENNINGS ─────────────────────────────────────────────────────

@st.fragment
def _tab_lj():
    db = get_session()
    try:
        materiales = crud.listar_materiales(db)
        if not materiales:
            st.info("No hay analitos configurados.")
            return

        # ── Filtros ──────────────────────────────────────────────────────────
        col_mat, col_rng = st.columns([4, 2])
        mat_opts = {
            f"{m.equipo.area.nombre} › {m.equipo.nombre} › {m.analito}": m.id
            for m in materiales
        }
        mat_sel = col_mat.selectbox("Analito", list(mat_opts.keys()), key="lj_mat")
        rango   = col_rng.selectbox("Período", RANGOS, index=2, key="lj_rng")

        hoy = date.today()
        if rango == "Personalizado":
            c1, c2 = st.columns(2)
            desde = c1.date_input("Desde", value=hoy - timedelta(days=30), key="lj_desde")
            hasta = c2.date_input("Hasta", value=hoy, key="lj_hasta")
        else:
            desde, hasta = _rango_fechas(rango, hoy - timedelta(days=30), hoy)
            st.caption(f"📅 {desde.strftime('%d/%m/%Y')} → {hasta.strftime('%d/%m/%Y')}")

        material_id = mat_opts[mat_sel]
        material    = next(m for m in materiales if m.id == material_id)

        controles = crud.listar_controles_diarios(
            db, material_id=material_id, fecha_desde=desde, fecha_hasta=hasta
        )
        if not controles:
            st.info("No hay controles para ese analito y período.")
            return

        niveles = sorted({c.nivel_lote.nivel for c in controles})
        fig, altura_px = _lj_figura(controles, material, niveles)
        st.plotly_chart(fig, use_container_width=True)

        # ── Estadísticos por nivel ────────────────────────────────────────────
        stats: dict[int, dict] = {}
        for nivel_num in niveles:
            cs  = [c for c in controles if c.nivel_lote.nivel == nivel_num]
            nl  = cs[0].nivel_lote
            vals = [c.valor for c in cs]
            rej_n = sum(1 for c in cs if c.resultado == RESULTADO_RECHAZO)
            adv_n = sum(1 for c in cs if c.resultado == RESULTADO_ADVERTENCIA)
            m_obs = statistics.mean(vals)
            d_obs = statistics.stdev(vals) if len(vals) > 1 else 0.0
            cv    = d_obs / m_obs * 100 if m_obs else 0.0
            stats[nivel_num] = {
                "N": len(vals), "media_obs": m_obs, "de_obs": d_obs, "cv_obs": cv,
                "rej_n": rej_n, "adv_n": adv_n,
                "media_ref": nl.media, "de_ref": nl.de,
                "tasa_rej": rej_n / len(vals) * 100,
                "unidad": material.unidad or "",
            }

        st.markdown("### Estadísticos del período")
        cols_st = st.columns(len(niveles))
        for col_idx, nivel_num in enumerate(sorted(niveles)):
            s = stats[nivel_num]
            with cols_st[col_idx]:
                st.markdown(f"#### Nivel {nivel_num}")
                with st.container(border=True):
                    a, b = st.columns(2)
                    a.metric("N controles",    s["N"])
                    b.metric("❌ Rechazos",    s["rej_n"],
                             delta=f"{s['tasa_rej']:.1f}%" if s["rej_n"] else None,
                             delta_color="inverse")
                    a.metric("X̄ obs.",         f"{s['media_obs']:.4f}")
                    b.metric("⚠️ Advertencias", s["adv_n"])
                    a.metric("DE obs.",         f"{s['de_obs']:.4f}")
                    b.metric("CV%",             f"{s['cv_obs']:.2f}%")
                    st.caption(
                        f"Referencia: X̄={s['media_ref']:.4f}  s={s['de_ref']:.4f} {s['unidad']}"
                    )

        # ── Firma del Responsable de Área ─────────────────────────────────────
        st.markdown("---")
        with st.expander("✍️ Firma del Responsable de Área (opcional para el reporte)", expanded=False):
            firma_pers, firma_sig = _bloque_firma(db, "lj")
        # Guardar en session_state para uso posterior en la misma ejecución del fragment
        if "lj_firma_pers" not in st.session_state:
            firma_pers = None; firma_sig = None

        # ── Exportación ───────────────────────────────────────────────────────
        st.markdown("#### 🗂️ Exportar / Compartir reporte")
        col_pdf, col_mail, col_prev = st.columns(3)

        lab = _get_lab()

        # ── PDF con gráfico embebido ──────────────────────────────────────────
        with col_pdf:
            if st.button("📥 Preparar PDF", key="lj_pdf_btn", use_container_width=True):
                with st.spinner("Generando PDF con gráfico…"):
                    # Intentar exportar el gráfico como PNG (requiere kaleido)
                    chart_png = None
                    try:
                        chart_png = fig.to_image(
                            format="png",
                            width=1400,
                            height=int(altura_px * 1.1),
                            scale=1.5,
                        )
                    except Exception:
                        pass  # kaleido no disponible — PDF sin imagen del gráfico

                    # Recuperar firma del expander
                    try:
                        pers_k = f"lj_firma_pers"
                        pers_obj = next(
                            (p for p in crud.listar_personal(db)
                             if f"{p.apellido}, {p.nombre}" == st.session_state.get(pers_k, "")),
                            None,
                        )
                    except Exception:
                        pers_obj = None

                    firma = _firma_dict(pers_obj, st.session_state.get("lj_sig_bytes"))

                    try:
                        from modules.pdf_export import reporte_levey_jennings_pdf
                        pdfs = {}
                        for nv in niveles:
                            cs_nv = [c for c in controles if c.nivel_lote.nivel == nv]
                            pdfs[nv] = reporte_levey_jennings_pdf(
                                cs_nv, material.analito, nv, lab,
                                chart_png=chart_png,
                                firma=firma,
                            )
                        st.session_state["lj_pdfs"] = pdfs
                        if chart_png:
                            st.success("✅ PDF listo — incluye gráfico y firma.")
                        else:
                            st.info(
                                "⚠️ PDF listo sin imagen del gráfico. "
                                "Instale kaleido para incluirlo: `pip install kaleido`"
                            )
                    except ImportError:
                        st.warning("Instale fpdf2: `pip install fpdf2`")
                    except Exception as e:
                        st.error(f"Error generando PDF: {e}")

            for nv, pdf_b in st.session_state.get("lj_pdfs", {}).items():
                st.download_button(
                    f"⬇️ Descargar PDF — Nivel {nv}",
                    data=pdf_b,
                    file_name=f"LJ_{material.analito}_Nv{nv}_{desde}_{hasta}.pdf",
                    mime="application/pdf",
                    key=f"lj_dl_nv{nv}",
                    use_container_width=True,
                )

        # ── Email ──────────────────────────────────────────────────────────────
        with col_mail:
            if st.button("📧 Enviar por email", key="lj_email_btn", use_container_width=True):
                try:
                    from modules.email_alerts import enviar_reporte_pdf
                    from modules.pdf_export import reporte_levey_jennings_pdf

                    nv_env = niveles[0]
                    cs_env = [c for c in controles if c.nivel_lote.nivel == nv_env]
                    pdf_env = reporte_levey_jennings_pdf(
                        cs_env, material.analito, nv_env, lab
                    )
                    s_e   = stats[nv_env]
                    asunto = (
                        f"Levey-Jennings — {material.analito} Nv{nv_env} "
                        f"({desde.strftime('%d/%m/%Y')} – {hasta.strftime('%d/%m/%Y')})"
                    )
                    cuerpo = f"""
<div style='font-family:Arial,sans-serif;color:#1e293b;max-width:600px;'>
  <div style='background:#1e3a8a;color:white;padding:14px 18px;border-radius:8px 8px 0 0;'>
    <h2 style='margin:0;font-size:15px;'>📈 Reporte Levey-Jennings</h2>
    <p style='margin:3px 0 0;font-size:11px;opacity:.85;'>{lab}</p>
  </div>
  <div style='border:1px solid #e2e8f0;border-top:none;padding:18px;border-radius:0 0 8px 8px;'>
    <table style='width:100%;border-collapse:collapse;font-size:12px;'>
      <tr><td style='padding:4px 10px;font-weight:600;background:#f8fafc;'>Analito</td>
          <td style='padding:4px 10px;'>{material.analito} — Nivel {nv_env}</td></tr>
      <tr><td style='padding:4px 10px;font-weight:600;background:#f8fafc;'>Período</td>
          <td style='padding:4px 10px;'>{desde.strftime('%d/%m/%Y')} → {hasta.strftime('%d/%m/%Y')}</td></tr>
      <tr><td style='padding:4px 10px;font-weight:600;background:#f8fafc;'>N controles</td>
          <td style='padding:4px 10px;'>{s_e['N']}</td></tr>
      <tr><td style='padding:4px 10px;font-weight:600;background:#f8fafc;'>CV% observado</td>
          <td style='padding:4px 10px;'>{s_e['cv_obs']:.2f}%</td></tr>
      <tr><td style='padding:4px 10px;font-weight:600;background:#f8fafc;color:#dc2626;'>Rechazos</td>
          <td style='padding:4px 10px;color:#dc2626;font-weight:700;'>
          {s_e['rej_n']} ({s_e['tasa_rej']:.1f}%)</td></tr>
    </table>
    <p style='margin-top:12px;font-size:10px;color:#64748b;'>
      Reglas Westgard: 1-2s / 1-3s / 2-2s / R-4s / 4-1s / 10x · PDF adjunto
    </p>
  </div>
</div>"""
                    ok, msg = enviar_reporte_pdf(
                        asunto, cuerpo, pdf_env,
                        f"LJ_{material.analito}_Nv{nv_env}.pdf",
                    )
                    st.success(f"✅ {msg}") if ok else st.warning(f"⚠️ {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

        # ── Vista previa integrada + imprimir ─────────────────────────────────
        with col_prev:
            if st.button("🔍 Vista previa / Imprimir", key="lj_prev_btn",
                         use_container_width=True):
                st.session_state["lj_show_prev"] = not st.session_state.get("lj_show_prev", False)

        if st.session_state.get("lj_show_prev", False):
            # Construir firma_info para HTML (con imagen en base64 si hay firma)
            firma_info_html = None
            sig_b = st.session_state.get("lj_sig_bytes")
            pers_k = "lj_firma_pers"
            if st.session_state.get(pers_k):
                pers_n = st.session_state[pers_k]
                pers_o = next(
                    (p for p in crud.listar_personal(db)
                     if f"{p.apellido}, {p.nombre}" == pers_n),
                    None,
                )
                firma_info_html = {
                    "nombre": pers_n,
                    "cargo":  pers_o.cargo if pers_o else "—",
                    "codigo": pers_o.codigo if pers_o else "—",
                    "imagen_b64": base64.b64encode(sig_b).decode() if sig_b else None,
                }

            html_prev = _html_lj(
                controles, material, niveles, stats, desde, hasta, lab, firma_info_html
            )
            st.markdown("##### 🔍 Vista previa del reporte (desplácese para ver / Imprimir desde aquí)")
            st.components.v1.html(html_prev, height=750, scrolling=True)

    finally:
        db.close()


# ── TAB 2: REPORTE PERIÓDICO ──────────────────────────────────────────────────

@st.fragment
def _tab_periodico():
    db = get_session()
    try:
        st.subheader("📅 Reporte Periódico de Control de Calidad")

        col1, col2, col3 = st.columns([2, 2, 2])
        rango = col1.selectbox("Período", RANGOS, index=2, key="per_rng")
        hoy   = date.today()

        if rango == "Personalizado":
            c1, c2 = st.columns(2)
            desde = c1.date_input("Desde", value=hoy - timedelta(days=30), key="per_desde")
            hasta = c2.date_input("Hasta", value=hoy, key="per_hasta")
        else:
            desde, hasta = _rango_fechas(rango, hoy - timedelta(days=30), hoy)
            col1.caption(f"📅 {desde.strftime('%d/%m/%Y')} → {hasta.strftime('%d/%m/%Y')}")

        areas    = crud.listar_areas(db)
        area_opts = {"Todas": None} | {a.nombre: a.id for a in areas}
        area_f   = col2.selectbox("Área", list(area_opts.keys()), key="per_area")
        eq_opts  = {"Todos": None} | {e.nombre: e.id for e in crud.listar_equipos(db, area_id=area_opts[area_f])}
        eq_f     = col3.selectbox("Equipo", list(eq_opts.keys()), key="per_eq")

        controles = crud.listar_controles_diarios(db, fecha_desde=desde, fecha_hasta=hasta)
        if area_opts[area_f]:
            controles = [c for c in controles if c.material.equipo.area_id == area_opts[area_f]]
        if eq_opts[eq_f]:
            controles = [c for c in controles if c.material.equipo_id == eq_opts[eq_f]]

        if not controles:
            st.info("No hay controles en ese período con los filtros seleccionados.")
            return

        total    = len(controles)
        rechazos = sum(1 for c in controles if c.resultado == RESULTADO_RECHAZO)
        advert   = sum(1 for c in controles if c.resultado == RESULTADO_ADVERTENCIA)
        oks      = total - rechazos - advert
        tasa_rej = rechazos / total * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total controles", total)
        c2.metric("✅ OK", oks)
        c3.metric("❌ Rechazos", rechazos,
                  delta=f"{tasa_rej:.1f}% tasa" if rechazos else None, delta_color="inverse")
        c4.metric("⚠️ Advertencias", advert)
        st.markdown("---")

        # ── Gráfico de tendencia ──────────────────────────────────────────────
        agrup = st.radio("Agrupar por", ["Día", "Semana", "Mes"], horizontal=True, key="per_agrup")
        bucket: dict = defaultdict(lambda: {"OK": 0, "ADVERTENCIA": 0, "RECHAZO": 0})
        for c in controles:
            if agrup == "Día":
                k = c.fecha.strftime("%d/%m/%y")
            elif agrup == "Semana":
                iso = c.fecha.isocalendar()
                k = f"Sem {iso[1]}/{iso[0]}"
            else:
                k = c.fecha.strftime("%b %Y")
            bucket[k][c.resultado] = bucket[k].get(c.resultado, 0) + 1

        if bucket:
            ks = list(bucket.keys())
            fig_t = go.Figure(data=[
                go.Bar(name="✅ OK",          x=ks, y=[bucket[k].get("OK", 0)          for k in ks], marker_color=COL_OK),
                go.Bar(name="⚠️ Advertencia", x=ks, y=[bucket[k].get("ADVERTENCIA", 0) for k in ks], marker_color=COL_ADV),
                go.Bar(name="❌ Rechazo",     x=ks, y=[bucket[k].get("RECHAZO", 0)     for k in ks], marker_color=COL_REJ),
            ])
            fig_t.update_layout(
                barmode="stack", height=240,
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="rgba(128,128,128,0.12)", title="N° controles"),
            )
            fig_t.update_traces(marker_line_width=0)
            st.plotly_chart(fig_t, use_container_width=True)

        # ── Tabla por analito + nivel ─────────────────────────────────────────
        st.markdown("### Resultados por Analito y Nivel")
        resumen: dict = {}
        for c in controles:
            k = (c.material.equipo.area.nombre, c.material.equipo.nombre,
                 c.material.analito, c.nivel_lote.nivel)
            if k not in resumen:
                resumen[k] = {"total": 0, "ok": 0, "adv": 0, "rej": 0, "vals": []}
            resumen[k]["total"] += 1
            resumen[k]["vals"].append(c.valor)
            resumen[k][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

        filas = []
        for (area, equipo, analito, nivel), d in sorted(resumen.items()):
            n   = d["total"]
            vals = d["vals"]
            m_o = statistics.mean(vals)
            d_o = statistics.stdev(vals) if len(vals) > 1 else 0
            cv  = d_o / m_o * 100 if m_o else 0
            filas.append({
                "Área": area, "Equipo": equipo, "Analito": analito, "Nivel": nivel,
                "N": n, "✅ OK": d["ok"], "⚠️ Adv.": d["adv"], "❌ Rech.": d["rej"],
                "% OK": f"{d['ok']/n*100:.1f}%", "% Rech.": f"{d['rej']/n*100:.1f}%",
                "X̄ obs.": round(m_o, 4), "CV%": f"{cv:.2f}%",
            })

        df = pd.DataFrame(filas)

        def _col_rej(v):
            try:
                p = float(str(v).replace("%", ""))
                if p >= 10: return "background-color:#fee2e2;color:#7f1d1d;font-weight:700"
                if p >= 5:  return "background-color:#fef3c7;color:#78350f"
            except Exception: pass
            return ""

        st.dataframe(df.style.applymap(_col_rej, subset=["% Rech."]),
                     use_container_width=True, hide_index=True)

        sin_ac = [c for c in controles if c.resultado == RESULTADO_RECHAZO and not c.accion_correctiva]
        if sin_ac:
            st.error(f"⚠️ **{len(sin_ac)} rechazo(s) sin acción correctiva** — registre en 🔧 Acciones Correctivas.")

        # ── Firma ─────────────────────────────────────────────────────────────
        st.markdown("---")
        with st.expander("✍️ Firma del Responsable de Área (opcional para el reporte)", expanded=False):
            per_firma, sig_firma = _bloque_firma(db, "per")

        # ── Exportación ───────────────────────────────────────────────────────
        st.markdown("#### 🗂️ Exportar / Compartir")
        cl, cm, cr, cprev = st.columns(4)
        lab = _get_lab()

        try:
            buf = io.BytesIO()
            df.to_excel(buf, index=False)
            cl.download_button("⬇️ Excel", buf.getvalue(),
                               f"reporte_qc_{desde}_{hasta}.xlsx", key="per_xl",
                               use_container_width=True)
        except Exception: pass

        if cm.button("📥 Preparar PDF", key="per_pdf_btn", use_container_width=True):
            try:
                from modules.pdf_export import reporte_mensual_pdf
                firma = _firma_dict(per_firma, sig_firma)
                pdf_b = reporte_mensual_pdf(controles, desde.month, desde.year, lab, firma=firma)
                st.session_state["per_pdf"] = pdf_b
                st.success("✅ PDF listo.")
            except Exception as e:
                st.error(f"Error PDF: {e}")

        if "per_pdf" in st.session_state:
            cm.download_button("⬇️ Descargar PDF", st.session_state["per_pdf"],
                               f"reporte_{desde}_{hasta}.pdf", mime="application/pdf",
                               key="per_dl_pdf", use_container_width=True)

        if cr.button("📧 Email", key="per_email_btn", use_container_width=True):
            try:
                from modules.email_alerts import enviar_reporte_pdf
                from modules.pdf_export import reporte_mensual_pdf
                firma = _firma_dict(per_firma, sig_firma)
                pdf_b = reporte_mensual_pdf(controles, desde.month, desde.year, lab, firma=firma)
                asunto = f"Reporte Periódico QC — {lab} — {desde} a {hasta}"
                cuerpo = (
                    f"<div style='font-family:Arial;'>"
                    f"<h2 style='color:#1e3a8a;'>Reporte Periódico QC</h2>"
                    f"<p>Período: <b>{desde}</b> → <b>{hasta}</b></p>"
                    f"<p>Total: {total} · ✅ {oks} · ❌ {rechazos} ({tasa_rej:.1f}%)</p>"
                    f"<p>PDF adjunto.</p></div>"
                )
                ok, msg = enviar_reporte_pdf(asunto, cuerpo, pdf_b,
                                              f"reporte_{desde}_{hasta}.pdf")
                st.success(f"✅ {msg}") if ok else st.warning(f"⚠️ {msg}")
            except Exception as e:
                st.error(f"Error: {e}")

        if cprev.button("🔍 Vista previa", key="per_prev_btn", use_container_width=True):
            st.session_state["per_show_prev"] = not st.session_state.get("per_show_prev", False)

        if st.session_state.get("per_show_prev", False):
            # HTML simple para reporte periódico
            filas_html = "".join(
                f"<tr><td>{f['Área']}</td><td>{f['Equipo']}</td><td>{f['Analito']}</td>"
                f"<td>{f['Nivel']}</td><td>{f['N']}</td><td>{f['✅ OK']}</td>"
                f"<td>{f['⚠️ Adv.']}</td><td>{f['❌ Rech.']}</td>"
                f"<td style='color:{'#dc2626' if float(f['% Rech.'].replace('%',''))>=5 else '#16a34a'};font-weight:700;'>{f['% Rech.']}</td>"
                f"<td>{f['CV%']}</td></tr>"
                for f in filas
            )
            firma_blq = ""
            if per_firma:
                firma_blq = (
                    f"<div style='border:1px solid #bfdbfe;border-radius:8px;padding:12px 16px;"
                    f"margin-top:16px;background:#f0f7ff;'>"
                    f"<b>Responsable de Área:</b> {per_firma.apellido}, {per_firma.nombre}<br>"
                    f"<b>Cargo:</b> {per_firma.cargo or '—'} &nbsp; "
                    f"<b>Fecha:</b> {date.today().strftime('%d/%m/%Y')}"
                    f"{'<br>' + _firma_img_html({'imagen_b64': base64.b64encode(sig_firma).decode()}) if sig_firma else ''}"
                    f"</div>"
                )
            html_per = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<title>Reporte Periódico</title>
<style>
  @page {{size:A4 portrait;margin:15mm;}} @media print {{.no-print{{display:none!important;}}}}
  *{{box-sizing:border-box;margin:0;padding:0;}} body{{font-family:Arial;font-size:10px;padding:14px;}}
  .header{{background:#1e3a8a;color:white;padding:10px 14px;border-radius:8px;margin-bottom:10px;}}
  h2{{font-size:11px;color:#1e3a8a;border-bottom:1.5px solid #bfdbfe;padding-bottom:3px;margin:10px 0 5px;}}
  table{{width:100%;border-collapse:collapse;font-size:9px;margin-bottom:8px;}}
  th{{background:#1e3a8a;color:white;padding:4px 6px;text-align:left;}}
  td{{padding:3px 6px;border-bottom:1px solid #e2e8f0;}}
  .btn{{background:#1e3a8a;color:white;border:none;padding:8px 16px;border-radius:6px;
        cursor:pointer;font-size:12px;font-weight:600;margin-bottom:12px;display:block;}}
  .footer{{color:#94a3b8;font-size:8px;text-align:center;margin-top:14px;border-top:1px solid #e2e8f0;padding-top:5px;}}
</style></head><body>
<button class="btn no-print" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
<div class="header">
  <h1 style="font-size:14px;">Reporte Periódico de Control de Calidad</h1>
  <div style="font-size:9px;opacity:.85;">{lab} · {desde.strftime('%d/%m/%Y')} → {hasta.strftime('%d/%m/%Y')} · Generado: {date.today().strftime('%d/%m/%Y')}</div>
</div>
<p style="margin-bottom:8px;font-size:10px;">Total: <b>{total}</b> · ✅ {oks} · ⚠️ {advert} · ❌ {rechazos} ({tasa_rej:.1f}% rechazo)</p>
<h2>Resultados por Analito y Nivel</h2>
<table>
  <thead><tr><th>Área</th><th>Equipo</th><th>Analito</th><th>Nivel</th>
    <th>N</th><th>✅ OK</th><th>⚠️ Adv.</th><th>❌ Rech.</th><th>% Rech.</th><th>CV%</th></tr></thead>
  <tbody>{filas_html}</tbody>
</table>
{firma_blq}
<p class="footer">SGC Laboratorio Clínico · Westgard Multi-Regla · ISO 15189</p>
</body></html>"""
            st.markdown("##### 🔍 Vista previa del reporte periódico")
            st.components.v1.html(html_per, height=700, scrolling=True)

    finally:
        db.close()


# ── TAB 3: INFORME DE CORRIDA ─────────────────────────────────────────────────

@st.fragment
def _tab_corrida():
    db = get_session()
    try:
        st.subheader("📄 Informe de Corrida — Decisión formal aceptación / rechazo")
        st.caption("Documento requerido por **ISO 15189 / CAP / CLIA** para acreditación.")

        col1, col2, col3 = st.columns(3)
        fecha_sel = col1.date_input("Fecha de corrida", value=date.today(),
                                    max_value=date.today(), key="ic_fecha")
        turno_sel = col2.selectbox("Turno", ["TODOS"] + TURNOS, key="ic_turno")
        areas     = crud.listar_areas(db)
        area_opts = {"Todas": None} | {a.nombre: a.id for a in areas}
        area_sel  = col3.selectbox("Área", list(area_opts.keys()), key="ic_area")

        controles = crud.listar_controles_diarios(db, fecha_desde=fecha_sel, fecha_hasta=fecha_sel)
        if area_opts[area_sel]:
            controles = [c for c in controles if c.material.equipo.area_id == area_opts[area_sel]]
        if turno_sel != "TODOS":
            controles = [c for c in controles if c.turno == turno_sel]

        if not controles:
            st.info("No hay controles registrados para esa fecha y filtros.")
            return

        total        = len(controles)
        rechazos     = [c for c in controles if c.resultado == "RECHAZO"]
        advertencias = [c for c in controles if c.resultado == "ADVERTENCIA"]
        aceptados    = [c for c in controles if c.resultado == "OK"]
        decision     = "RECHAZADA" if rechazos else "ACEPTADA"

        bg_dec = "#fee2e2" if rechazos else "#d1fae5"
        bd_dec = "#dc2626" if rechazos else "#10b981"
        fg_dec = "#7f1d1d" if rechazos else "#065f46"
        ic_dec = "🛑" if rechazos else "✅"

        st.html(
            f"<div style='background:{bg_dec};border:2px solid {bd_dec};"
            f"border-radius:14px;padding:18px 24px;margin-bottom:16px;"
            f"display:flex;align-items:center;gap:18px;'>"
            f"<div style='font-size:2.8rem;'>{ic_dec}</div>"
            f"<div>"
            f"<div style='font-size:1.3rem;font-weight:800;color:{fg_dec};'>"
            f"CORRIDA {decision}</div>"
            f"<div style='color:{fg_dec};font-size:0.85rem;margin-top:3px;opacity:.85;'>"
            f"{fecha_sel.strftime('%d/%m/%Y')} · Turno: {turno_sel} "
            f"· {total} controles · {len(rechazos)} rechazo(s) · {len(advertencias)} advertencia(s)"
            f"</div></div></div>"
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", total)
        c2.metric("✅ Aceptados", len(aceptados))
        c3.metric("⚠️ Advertencias", len(advertencias))
        c4.metric("❌ Rechazos", len(rechazos),
                  delta=f"{len(rechazos)} rechazo(s)" if rechazos else None,
                  delta_color="inverse")
        st.markdown("---")

        # Tabla detallada
        st.markdown("### Detalle de la corrida")
        filas = []
        for c in controles:
            m = c.material; nl = c.nivel_lote
            dentro = "Dentro" if nl.valor_minimo <= c.valor <= nl.valor_maximo else "Fuera"
            filas.append({
                "Hora": c.hora.strftime("%H:%M"), "Turno": c.turno or "—",
                "Área": m.equipo.area.nombre, "Equipo": m.equipo.nombre,
                "Analito": m.analito, "Nv.": nl.nivel,
                "Lote": c.lote.numero_lote,
                "X̄ ± 2s": f"{nl.media:.3f} ± {2*nl.de:.3f}",
                "Valor": c.valor,
                "z-score": round(c.zscore, 3) if c.zscore else "—",
                "Rango": dentro, "Resultado": c.resultado,
                "Regla": c.regla_violada or "—",
                "Personal": f"{c.personal.apellido}, {c.personal.nombre}",
            })

        df = pd.DataFrame(filas)

        def _est_r(v):
            return {"OK": "background-color:#d1fae5;color:#065f46;font-weight:600",
                    "ADVERTENCIA": "background-color:#fef3c7;color:#78350f;font-weight:600",
                    "RECHAZO": "background-color:#fee2e2;color:#7f1d1d;font-weight:700"}.get(v, "")

        def _est_rng(v):
            return "background-color:#fee2e2;color:#7f1d1d;font-weight:600" if v == "Fuera" else ""

        st.dataframe(df.style.applymap(_est_r, subset=["Resultado"]).applymap(_est_rng, subset=["Rango"]),
                     use_container_width=True, hide_index=True)

        # Resumen por analito
        st.markdown("### Resumen por analito y nivel")
        res_ana: dict = defaultdict(lambda: {"total": 0, "ok": 0, "adv": 0, "rej": 0})
        for c in controles:
            k = f"{c.material.analito}  Nv{c.nivel_lote.nivel}"
            res_ana[k]["total"] += 1
            res_ana[k][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

        filas_r = [{"Analito / Nivel": a, "N": d["total"], "✅ OK": d["ok"],
                    "⚠️ Adv.": d["adv"], "❌ Rech.": d["rej"],
                    "Estado corrida": "✅ OK" if d["rej"] == 0 else "❌ RECHAZO"}
                   for a, d in sorted(res_ana.items())]

        def _est_est(v):
            return ("background-color:#fee2e2;color:#7f1d1d;font-weight:700" if "RECHAZO" in str(v)
                    else "background-color:#d1fae5;color:#065f46;font-weight:600")

        st.dataframe(pd.DataFrame(filas_r).style.applymap(_est_est, subset=["Estado corrida"]),
                     use_container_width=True, hide_index=True)

        sin_ac = [c for c in rechazos if not c.accion_correctiva]
        if sin_ac:
            st.error(f"⚠️ **{len(sin_ac)} rechazo(s) sin acción correctiva** pendiente(s). "
                     "Registre la acción en 🔧 Acciones Correctivas.")

        # ── Firma del Responsable de Área ─────────────────────────────────────
        st.markdown("---")
        with st.expander("✍️ Firma del Responsable de Área", expanded=True):
            ic_firma_pers, ic_firma_sig = _bloque_firma(db, "ic")

        # ── Exportación ───────────────────────────────────────────────────────
        st.markdown("#### 🗂️ Exportar / Compartir")
        cl, cm, cr, cprev = st.columns(4)
        lab = _get_lab()

        if cl.button("📥 Preparar PDF", key="ic_pdf_btn", use_container_width=True, type="primary"):
            try:
                from modules.pdf_export import informe_corrida_pdf
                firma = _firma_dict(ic_firma_pers, ic_firma_sig)
                pdf_b = informe_corrida_pdf(controles, fecha_sel, turno_sel, decision, lab, firma=firma)
                st.session_state["ic_pdf"] = pdf_b
                st.success("✅ PDF listo con firma incluida." if firma else "✅ PDF listo.")
            except Exception as e:
                st.error(f"Error PDF: {e}")

        if "ic_pdf" in st.session_state:
            cl.download_button("⬇️ Descargar PDF", st.session_state["ic_pdf"],
                               f"corrida_{fecha_sel}_{turno_sel}.pdf",
                               mime="application/pdf", key="ic_dl",
                               use_container_width=True)

        if cm.button("📧 Enviar email", key="ic_email_btn", use_container_width=True):
            try:
                from modules.email_alerts import enviar_reporte_pdf
                from modules.pdf_export import informe_corrida_pdf
                firma = _firma_dict(ic_firma_pers, ic_firma_sig)
                pdf_b = informe_corrida_pdf(controles, fecha_sel, turno_sel, decision, lab, firma=firma)
                asunto = f"Informe Corrida {decision} — {lab} — {fecha_sel} T:{turno_sel}"
                color_c = "#dc2626" if rechazos else "#16a34a"
                cuerpo = (
                    f"<div style='font-family:Arial;'>"
                    f"<h2 style='color:{color_c};'>Corrida {decision} {ic_dec}</h2>"
                    f"<p><b>Fecha:</b> {fecha_sel.strftime('%d/%m/%Y')} · <b>Turno:</b> {turno_sel}</p>"
                    f"<p>Total: {total} · ✅ {len(aceptados)} · ⚠️ {len(advertencias)} · ❌ {len(rechazos)}</p>"
                    f"<p>PDF adjunto.</p></div>"
                )
                ok, msg = enviar_reporte_pdf(asunto, cuerpo, pdf_b,
                                              f"corrida_{fecha_sel}_{turno_sel}.pdf")
                st.success(f"✅ {msg}") if ok else st.warning(f"⚠️ {msg}")
            except Exception as e:
                st.error(f"Error: {e}")

        if cr.button("🔍 Vista previa", key="ic_prev_btn", use_container_width=True):
            st.session_state["ic_show_prev"] = not st.session_state.get("ic_show_prev", False)

        if st.session_state.get("ic_show_prev", False):
            sig_b64 = base64.b64encode(ic_firma_sig).decode() if ic_firma_sig else None
            firma_html_info = None
            if ic_firma_pers:
                firma_html_info = {
                    "nombre": f"{ic_firma_pers.apellido}, {ic_firma_pers.nombre}",
                    "cargo":  ic_firma_pers.cargo or "—",
                    "imagen_b64": sig_b64,
                }
            html_cor = _html_corrida(controles, fecha_sel, turno_sel, decision, lab, firma_html_info)
            st.markdown("##### 🔍 Vista previa del informe de corrida")
            st.components.v1.html(html_cor, height=750, scrolling=True)

    finally:
        db.close()


# ── TAB 4: PERSONAL ───────────────────────────────────────────────────────────

@st.fragment
def _tab_personal():
    db = get_session()
    try:
        st.subheader("👤 Actividad de Personal")

        col1, col2 = st.columns([2, 2])
        rango = col1.selectbox("Período", RANGOS, index=2, key="prs_rng")
        hoy   = date.today()
        if rango == "Personalizado":
            c1, c2 = st.columns(2)
            desde = c1.date_input("Desde", value=hoy - timedelta(days=30), key="prs_desde")
            hasta = c2.date_input("Hasta", value=hoy, key="prs_hasta")
        else:
            desde, hasta = _rango_fechas(rango, hoy - timedelta(days=30), hoy)
            col2.caption(f"📅 {desde.strftime('%d/%m/%Y')} → {hasta.strftime('%d/%m/%Y')}")

        controles = crud.listar_controles_diarios(db, fecha_desde=desde, fecha_hasta=hasta)
        if not controles:
            st.info("No hay controles en ese período.")
            return

        actividad: dict = defaultdict(
            lambda: {"total": 0, "rechazos": 0, "advertencias": 0, "fechas": set()}
        )
        for c in controles:
            nombre = f"{c.personal.apellido}, {c.personal.nombre}"
            actividad[nombre]["total"] += 1
            actividad[nombre]["fechas"].add(c.fecha)
            if c.resultado == RESULTADO_RECHAZO:      actividad[nombre]["rechazos"] += 1
            elif c.resultado == RESULTADO_ADVERTENCIA: actividad[nombre]["advertencias"] += 1

        filas = [{
            "Personal": nombre, "N° controles": d["total"],
            "Días activos": len(d["fechas"]),
            "❌ Rechazos": d["rechazos"], "⚠️ Advertencias": d["advertencias"],
            "% Rechazo": f"{d['rechazos']/d['total']*100:.1f}%",
        } for nombre, d in sorted(actividad.items())]

        def _col_rej(v):
            try:
                p = float(str(v).replace("%", ""))
                if p >= 10: return "background-color:#fee2e2;color:#7f1d1d;font-weight:700"
                if p >= 5:  return "background-color:#fef3c7;color:#78350f"
            except Exception: pass
            return ""

        st.dataframe(pd.DataFrame(filas).style.applymap(_col_rej, subset=["% Rechazo"]),
                     use_container_width=True, hide_index=True)

        st.markdown("---")
        pers_sel = st.selectbox("Ver detalle de:", sorted(actividad.keys()), key="prs_det")
        pers_id  = next(c.personal_id for c in controles
                        if f"{c.personal.apellido}, {c.personal.nombre}" == pers_sel)
        cs_pers  = crud.listar_controles_diarios(db, fecha_desde=desde,
                                                  fecha_hasta=hasta, personal_id=pers_id)
        if cs_pers:
            filas_d = [{
                "Fecha": c.fecha, "Hora": c.hora.strftime("%H:%M"), "Turno": c.turno or "—",
                "Área": c.material.equipo.area.nombre, "Equipo": c.material.equipo.nombre,
                "Analito": c.material.analito, "Nivel": c.nivel_lote.nivel,
                "Valor": c.valor, "z-score": round(c.zscore, 3) if c.zscore else "—",
                "Resultado": c.resultado, "Regla": c.regla_violada or "—",
            } for c in cs_pers]

            def _est(v):
                return {"OK": "background-color:#d1fae5", "ADVERTENCIA": "background-color:#fef3c7",
                        "RECHAZO": "background-color:#fee2e2"}.get(v, "")

            st.dataframe(pd.DataFrame(filas_d).style.applymap(_est, subset=["Resultado"]),
                         use_container_width=True, hide_index=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
