"""
Generación de reportes en PDF usando fpdf2.
"""

import io
from datetime import date
from fpdf import FPDF, XPos, YPos


AZUL      = (30,  58, 138)
AZUL_CLAR = (219, 234, 254)
VERDE     = (21, 128,  61)
VERDE_CL  = (220, 252, 231)
ROJO      = (185,  28,  28)
ROJO_CL   = (254, 226, 226)
AMBAR     = (180, 83,   9)
AMBAR_CL  = (254, 243, 199)
GRIS      = (100, 116, 139)
GRIS_CL   = (248, 250, 252)
NEGRO     = (15,  23,  42)
BLANCO    = (255, 255, 255)


class ReportePDF(FPDF):
    def __init__(self, laboratorio: str = "Laboratorio Clínico"):
        super().__init__("P", "mm", "A4")
        self.laboratorio = laboratorio
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(16, 16, 16)

    def header(self):
        self.set_fill_color(*AZUL)
        self.rect(0, 0, 210, 22, "F")
        self.set_text_color(*BLANCO)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(16, 6)
        self.cell(0, 10, f"  SGC — {self.laboratorio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*NEGRO)
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 5, f"Sistema de Gestión de Calidad  ·  Página {self.page_no()}  ·  Generado: {date.today()}", align="C")

    def titulo_seccion(self, texto: str):
        self.set_fill_color(*AZUL_CLAR)
        self.set_text_color(*AZUL)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {texto}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*NEGRO)
        self.ln(2)

    def tabla_encabezado(self, columnas: list[tuple[str, float]], fill=True):
        """columnas: [(nombre, ancho_mm), ...]"""
        self.set_fill_color(*AZUL)
        self.set_text_color(*BLANCO)
        self.set_font("Helvetica", "B", 8)
        for nombre, ancho in columnas:
            self.cell(ancho, 7, nombre, border=0, fill=fill, align="C")
        self.ln()
        self.set_text_color(*NEGRO)

    def tabla_fila(self, datos: list[str], anchos: list[float],
                   resultado: str = "", par: bool = False):
        if resultado == "RECHAZO":
            self.set_fill_color(*ROJO_CL)
        elif resultado == "ADVERTENCIA":
            self.set_fill_color(*AMBAR_CL)
        elif resultado == "OK":
            self.set_fill_color(*VERDE_CL)
        elif par:
            self.set_fill_color(*GRIS_CL)
        else:
            self.set_fill_color(*BLANCO)

        self.set_font("Helvetica", "", 7.5)
        fill = resultado != "" or par
        for valor, ancho in zip(datos, anchos):
            self.cell(ancho, 6, str(valor)[:30], border=0, fill=fill, align="C")
        self.ln()

    def kpi_box(self, label: str, valor: str, color: tuple):
        x, y = self.get_x(), self.get_y()
        w, h = 42, 18
        self.set_fill_color(*color)
        self.rect(x, y, w, h, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*BLANCO)
        self.set_xy(x, y + 3)
        self.cell(w, 7, valor, align="C")
        self.set_font("Helvetica", "", 7)
        self.set_xy(x, y + 10)
        self.cell(w, 5, label, align="C")
        self.set_text_color(*NEGRO)
        self.set_xy(x + w + 4, y)


# ── Reporte mensual ───────────────────────────────────────────────────────────

def reporte_mensual_pdf(
    controles: list,
    mes: int,
    anio: int,
    laboratorio: str = "Laboratorio Clínico",
) -> bytes:
    from calendar import month_name
    nombre_mes = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"][mes]

    pdf = ReportePDF(laboratorio)
    pdf.add_page()

    # Título
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 10, f"Reporte Mensual de Control de Calidad", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 7, f"{nombre_mes} {anio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(*NEGRO)
    pdf.ln(4)

    # KPIs
    total = len(controles)
    rechazos = sum(1 for c in controles if c.resultado == "RECHAZO")
    advertencias = sum(1 for c in controles if c.resultado == "ADVERTENCIA")
    oks = total - rechazos - advertencias
    tasa_rej = rechazos / total * 100 if total else 0

    pdf.titulo_seccion("Resumen del período")
    pdf.ln(2)
    pdf.kpi_box("Total controles", str(total), AZUL)
    pdf.kpi_box("✓ OK", str(oks), VERDE)
    pdf.kpi_box("⚠ Advertencia", str(advertencias), AMBAR)
    pdf.kpi_box("✗ Rechazos", str(rechazos), ROJO)
    pdf.ln(22)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Tasa de rechazo del período: {tasa_rej:.1f}%   |   Tasa de aceptación: {(oks/total*100) if total else 0:.1f}%")
    pdf.ln(10)

    # Resumen por analito
    pdf.titulo_seccion("Resultados por Analito y Nivel")
    cols = [("Área", 30), ("Equipo", 30), ("Analito", 35), ("Nv", 10),
            ("N", 10), ("OK", 10), ("Adv.", 12), ("Rech.", 12), ("% Rec.", 18), ("CV% obs.", 21)]
    anchos = [c[1] for c in cols]
    pdf.tabla_encabezado(cols)

    resumen: dict[tuple, dict] = {}
    for c in controles:
        mat = c.material
        k = (mat.equipo.area.nombre, mat.equipo.nombre, mat.analito, c.nivel_lote.nivel)
        if k not in resumen:
            resumen[k] = {"total": 0, "ok": 0, "adv": 0, "rej": 0, "vals": []}
        resumen[k]["total"] += 1
        resumen[k]["vals"].append(c.valor)
        resumen[k][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

    import statistics
    for i, (k, d) in enumerate(sorted(resumen.items())):
        area, equipo, analito, nivel = k
        n = d["total"]
        cv = 0.0
        if len(d["vals"]) > 1:
            m = statistics.mean(d["vals"])
            cv = statistics.stdev(d["vals"]) / m * 100 if m else 0
        pdf.tabla_fila(
            [area, equipo, analito, str(nivel), str(n), str(d["ok"]),
             str(d["adv"]), str(d["rej"]), f"{d['rej']/n*100:.1f}%", f"{cv:.2f}%"],
            anchos, par=(i % 2 == 0)
        )
    pdf.ln(8)

    # Detalle de rechazos
    rechazados = [c for c in controles if c.resultado == "RECHAZO"]
    if rechazados:
        pdf.titulo_seccion(f"Detalle de Rechazos ({len(rechazados)})")
        cols_r = [("Fecha", 22), ("Hora", 16), ("Área", 28), ("Analito", 32),
                  ("Nv", 10), ("Valor", 20), ("z", 14), ("Regla", 18), ("Personal", 28)]
        anchos_r = [c[1] for c in cols_r]
        pdf.tabla_encabezado(cols_r)
        for c in rechazados:
            mat = c.material
            pdf.tabla_fila(
                [str(c.fecha), c.hora.strftime("%H:%M"), mat.equipo.area.nombre,
                 mat.analito, str(c.nivel_lote.nivel), str(c.valor),
                 f"{c.zscore:.2f}" if c.zscore else "", c.regla_violada or "—",
                 f"{c.personal.apellido[:10]}, {c.personal.nombre[:8]}"],
                anchos_r, resultado="RECHAZO"
            )

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── Reporte Levey-Jennings ────────────────────────────────────────────────────

def reporte_levey_jennings_pdf(
    controles: list,
    analito: str,
    nivel: int,
    laboratorio: str = "Laboratorio Clínico",
) -> bytes:
    pdf = ReportePDF(laboratorio)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 9, f"Registro Levey-Jennings — {analito} — Nivel {nivel}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(*NEGRO)
    pdf.ln(4)

    if not controles:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, "Sin datos en el período seleccionado.")
        buf = io.BytesIO(); pdf.output(buf); return buf.getvalue()

    import statistics
    primer = controles[0]
    media  = primer.nivel_lote.media
    de     = primer.nivel_lote.de
    unidad = primer.material.unidad or ""
    valores = [c.valor for c in controles]
    media_obs = statistics.mean(valores)
    de_obs    = statistics.stdev(valores) if len(valores) > 1 else 0
    cv_obs    = de_obs / media_obs * 100 if media_obs else 0

    # Parámetros del lote
    pdf.titulo_seccion("Parámetros del lote de control")
    params = [
        ("Media objetivo (X̄)", f"{media:.4f} {unidad}"),
        ("DE objetivo (s)", f"{de:.4f} {unidad}"),
        ("Límite +2s", f"{media + 2*de:.4f} {unidad}"),
        ("Límite -2s", f"{media - 2*de:.4f} {unidad}"),
        ("Límite +3s", f"{media + 3*de:.4f} {unidad}"),
        ("Límite -3s", f"{media - 3*de:.4f} {unidad}"),
    ]
    pdf.set_font("Helvetica", "", 9)
    for label, val in params:
        pdf.cell(60, 6, label, border=0)
        pdf.cell(50, 6, val, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Estadísticos observados
    pdf.titulo_seccion("Estadísticos observados en el período")
    obs = [
        ("N controles", str(len(controles))),
        ("Media observada", f"{media_obs:.4f} {unidad}"),
        ("DE observada", f"{de_obs:.4f} {unidad}"),
        ("CV% observado", f"{cv_obs:.2f}%"),
        ("Rechazos", str(sum(1 for c in controles if c.resultado == "RECHAZO"))),
        ("Advertencias", str(sum(1 for c in controles if c.resultado == "ADVERTENCIA"))),
    ]
    for label, val in obs:
        pdf.cell(60, 6, label, border=0)
        pdf.cell(50, 6, val, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # Tabla detallada
    pdf.titulo_seccion("Registro detallado de controles")
    cols = [("Fecha", 24), ("Hora", 16), ("Turno", 20), ("Valor", 22),
            ("z-score", 18), ("Resultado", 24), ("Regla", 18), ("Personal", 36)]
    anchos = [c[1] for c in cols]
    pdf.tabla_encabezado(cols)
    for i, c in enumerate(controles):
        pdf.tabla_fila(
            [str(c.fecha), c.hora.strftime("%H:%M"), c.turno or "—",
             str(c.valor), f"{c.zscore:.3f}" if c.zscore is not None else "—",
             c.resultado, c.regla_violada or "—",
             f"{c.personal.apellido[:12]}, {c.personal.nombre[:10]}"],
            anchos, resultado=c.resultado, par=(i % 2 == 0)
        )

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# ── Informe de Corrida ────────────────────────────────────────────────────────

def informe_corrida_pdf(
    controles: list,
    fecha,
    turno: str,
    decision: str,
    laboratorio: str = "Laboratorio Clínico",
) -> bytes:
    pdf = ReportePDF(laboratorio)
    pdf.add_page()

    dec_color = VERDE if decision == "ACEPTADA" else ROJO
    dec_bg    = VERDE_CL if decision == "ACEPTADA" else ROJO_CL

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 9, "Informe de Corrida de Controles", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GRIS)
    fecha_str = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
    pdf.cell(0, 6, f"{fecha_str}  -  Turno: {turno}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(4)

    pdf.set_fill_color(*dec_bg)
    pdf.set_text_color(*dec_color)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 14, f"  CORRIDA {decision}  -  {len(controles)} controles evaluados",
             fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(*NEGRO)
    pdf.ln(6)

    rechazos     = sum(1 for c in controles if c.resultado == "RECHAZO")
    advertencias = sum(1 for c in controles if c.resultado == "ADVERTENCIA")
    aceptados    = len(controles) - rechazos - advertencias

    pdf.titulo_seccion("Resumen de la corrida")
    pdf.ln(2)
    pdf.kpi_box("Total", str(len(controles)), AZUL)
    pdf.kpi_box("Aceptados", str(aceptados), VERDE)
    pdf.kpi_box("Advertencias", str(advertencias), AMBAR)
    pdf.kpi_box("Rechazos", str(rechazos), ROJO)
    pdf.ln(22)
    pdf.ln(4)

    pdf.titulo_seccion("Detalle de controles")
    cols = [("Hora", 14), ("Turno", 18), ("Area", 25), ("Equipo", 22),
            ("Analito", 26), ("Nv", 8), ("Lote", 18), ("Valor", 16),
            ("z-score", 14), ("Resultado", 22)]
    anchos = [c[1] for c in cols]
    pdf.tabla_encabezado(cols)
    for i, c in enumerate(controles):
        m = c.material
        pdf.tabla_fila(
            [c.hora.strftime("%H:%M"), c.turno or "-", m.equipo.area.nombre[:12],
             m.equipo.nombre[:10], m.analito[:13], str(c.nivel_lote.nivel),
             c.lote.numero_lote[:8], str(c.valor),
             f"{c.zscore:.2f}" if c.zscore is not None else "-",
             c.resultado],
            anchos, resultado=c.resultado, par=(i % 2 == 0)
        )
    pdf.ln(6)

    from collections import defaultdict
    resumen: dict = defaultdict(lambda: {"total": 0, "ok": 0, "adv": 0, "rej": 0})
    for c in controles:
        k = f"{c.material.analito} Nv{c.nivel_lote.nivel}"
        resumen[k]["total"] += 1
        resumen[k][{"OK": "ok", "ADVERTENCIA": "adv", "RECHAZO": "rej"}.get(c.resultado, "ok")] += 1

    pdf.titulo_seccion("Resumen por analito")
    cols2 = [("Analito / Nivel", 60), ("N", 16), ("OK", 16), ("Adv.", 18), ("Rech.", 20), ("Estado", 48)]
    anchos2 = [c[1] for c in cols2]
    pdf.tabla_encabezado(cols2)
    for i, (analito, d) in enumerate(sorted(resumen.items())):
        estado = "ACEPTADO" if d["rej"] == 0 else "RECHAZADO"
        pdf.tabla_fila(
            [analito, str(d["total"]), str(d["ok"]), str(d["adv"]), str(d["rej"]), estado],
            anchos2, resultado="RECHAZO" if d["rej"] else "", par=(i % 2 == 0)
        )
    pdf.ln(6)

    rej_list = [c for c in controles if c.resultado == "RECHAZO"]
    if rej_list:
        pdf.titulo_seccion(f"Rechazos con regla violada ({len(rej_list)})")
        cols3 = [("Hora", 16), ("Analito", 30), ("Nv", 8), ("Valor", 18),
                 ("z", 14), ("Regla violada", 30), ("Personal", 62)]
        anchos3 = [c[1] for c in cols3]
        pdf.tabla_encabezado(cols3)
        for c in rej_list:
            m = c.material
            pdf.tabla_fila(
                [c.hora.strftime("%H:%M"), m.analito[:15], str(c.nivel_lote.nivel),
                 str(c.valor), f"{c.zscore:.2f}" if c.zscore is not None else "-",
                 c.regla_violada or "-",
                 f"{c.personal.apellido[:14]}, {c.personal.nombre[:10]}"],
                anchos3, resultado="RECHAZO"
            )

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, f"Documento generado por SGC Laboratorio  -  Fecha de impresion: {date.today()}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
