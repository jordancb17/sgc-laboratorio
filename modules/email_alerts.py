"""
Alertas por correo electrónico.
Configurar en .streamlit/secrets.toml:

  [email]
  habilitado   = true
  smtp_host    = "smtp.gmail.com"
  smtp_port    = 465
  remitente    = "sgc.laboratorio@gmail.com"
  password     = "xxxx xxxx xxxx xxxx"   # Contraseña de aplicación de Gmail
  destinatarios = "jefe@lab.com, calidad@lab.com"

Para Gmail: Cuenta → Seguridad → Verificación en 2 pasos → Contraseñas de aplicación
"""

import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, time


def _cfg() -> dict | None:
    try:
        cfg = dict(st.secrets["email"])
        return cfg if cfg.get("habilitado") else None
    except Exception:
        return None


def _enviar(asunto: str, cuerpo_html: str) -> tuple[bool, str]:
    cfg = _cfg()
    if not cfg:
        return False, "Alertas por email no habilitadas."
    destinatarios = [d.strip() for d in cfg.get("destinatarios", "").split(",") if d.strip()]
    if not destinatarios:
        return False, "No hay destinatarios configurados."
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = asunto
        msg["From"]    = cfg["remitente"]
        msg["To"]      = ", ".join(destinatarios)
        msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))
        with smtplib.SMTP_SSL(cfg.get("smtp_host", "smtp.gmail.com"),
                               int(cfg.get("smtp_port", 465))) as srv:
            srv.login(cfg["remitente"], cfg["password"])
            srv.sendmail(cfg["remitente"], destinatarios, msg.as_string())
        return True, f"Alerta enviada a: {', '.join(destinatarios)}"
    except Exception as e:
        return False, f"Error al enviar: {e}"


def _fila(label: str, valor: str, color: str = "") -> str:
    estilo = f"color:{color}; font-weight:bold;" if color else ""
    return f"<tr><td style='padding:6px 12px; background:#f8fafc; font-weight:600;'>{label}</td><td style='padding:6px 12px; {estilo}'>{valor}</td></tr>"


def alerta_rechazo(
    analito: str, area: str, equipo: str, nivel: int,
    valor: float, unidad: str, zscore: float, regla: str,
    personal: str, fecha: date, hora: time,
) -> tuple[bool, str]:
    asunto = f"🛑 RECHAZO QC — {analito} | {area} | {fecha}"
    cuerpo = f"""
<html><body style="font-family:Arial,sans-serif; color:#1e293b;">
<div style="max-width:600px; margin:auto; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;">
  <div style="background:linear-gradient(135deg,#dc2626,#b91c1c); padding:20px 24px;">
    <h2 style="color:white; margin:0;">🛑 Alerta de Rechazo — Control de Calidad</h2>
    <p style="color:#fecaca; margin:4px 0 0;">SGC Laboratorio Clínico</p>
  </div>
  <div style="padding:24px;">
    <table style="width:100%; border-collapse:collapse; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden;">
      {_fila("Fecha / Hora", f"{fecha} — {hora.strftime('%H:%M')}")}
      {_fila("Área", area)}
      {_fila("Equipo", equipo)}
      {_fila("Analito", analito)}
      {_fila("Nivel de control", str(nivel))}
      {_fila("Valor medido", f"{valor} {unidad}")}
      {_fila("z-score", f"{zscore:.3f}")}
      {_fila("Regla violada", regla, "#dc2626")}
      {_fila("Personal responsable", personal)}
    </table>
    <div style="margin-top:16px; padding:12px 16px; background:#fef2f2; border-left:4px solid #dc2626; border-radius:6px;">
      <strong>Acción requerida:</strong> No libere resultados de pacientes hasta resolver y registrar la acción correctiva.
    </div>
  </div>
  <div style="padding:12px 24px; background:#f8fafc; border-top:1px solid #e2e8f0; font-size:12px; color:#64748b;">
    Mensaje automático · SGC Laboratorio Clínico · Westgard Multi-Regla
  </div>
</div>
</body></html>"""
    return _enviar(asunto, cuerpo)


def alerta_lote_por_vencer(analito: str, area: str, lote: str,
                            vencimiento: date, dias_restantes: int) -> tuple[bool, str]:
    color = "#dc2626" if dias_restantes <= 7 else "#d97706"
    asunto = f"⚠️ Lote por vencer ({dias_restantes}d) — {analito} | {area}"
    cuerpo = f"""
<html><body style="font-family:Arial,sans-serif; color:#1e293b;">
<div style="max-width:580px; margin:auto; border:1px solid #e2e8f0; border-radius:12px; overflow:hidden;">
  <div style="background:{color}; padding:18px 24px;">
    <h2 style="color:white; margin:0;">⚠️ Lote próximo a vencer</h2>
  </div>
  <div style="padding:20px 24px;">
    <table style="width:100%; border-collapse:collapse;">
      {_fila("Área", area)}
      {_fila("Analito", analito)}
      {_fila("Número de lote", lote)}
      {_fila("Vencimiento", str(vencimiento))}
      {_fila("Días restantes", str(dias_restantes), color)}
    </table>
  </div>
</div></body></html>"""
    return _enviar(asunto, cuerpo)


def probar_conexion() -> tuple[bool, str]:
    """Envía un email de prueba para verificar la configuración."""
    asunto = "✅ Prueba de conexión — SGC Laboratorio Clínico"
    cuerpo = """
<html><body style="font-family:Arial,sans-serif;">
<div style="max-width:500px; margin:auto; padding:24px; border:1px solid #e2e8f0; border-radius:12px;">
  <h2 style="color:#16a34a;">✅ Conexión de email exitosa</h2>
  <p>El sistema de alertas del SGC Laboratorio Clínico está configurado correctamente.</p>
  <p style="color:#64748b; font-size:12px;">Mensaje de prueba automático.</p>
</div></body></html>"""
    return _enviar(asunto, cuerpo)
