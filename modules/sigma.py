"""
Índice de Sigma (Six Sigma) para planificación del control de calidad.
Sigma = (TEa - |Bias%|) / CV%

Interpretación:
  >= 6  : Clase mundial — 1 nivel, regla 1:3s
  4-6   : Excelente — 2 niveles, regla 1:3s/2:2s/R:4s
  3-4   : Bueno — 2 niveles, reglas múltiples
  2-3   : Marginal — 3 niveles, reglas múltiples reforzadas
  < 2   : Inaceptable — revisión del proceso
"""
from dataclasses import dataclass


@dataclass
class ResultadoSigma:
    sigma: float
    tea: float
    bias_pct: float
    cv_pct: float
    clasificacion: str
    color: str
    recomendacion_qc: str
    n_niveles_recomendado: int
    reglas_recomendadas: str


def calcular_sigma(tea: float, bias_pct: float, cv_pct: float) -> ResultadoSigma:
    """
    tea       : Error Total Permitido en % (ej. 10.0 para 10%)
    bias_pct  : Sesgo porcentual observado (puede ser negativo)
    cv_pct    : CV% observado (imprecisión)
    """
    if cv_pct <= 0:
        return ResultadoSigma(0, tea, bias_pct, cv_pct, "Sin datos", "#94a3b8",
                              "No calculable — CV% debe ser > 0", 2, "—")

    sigma = (tea - abs(bias_pct)) / cv_pct

    if sigma >= 6:
        cls = "Clase Mundial"
        color = "#059669"
        rec = "Control óptimo — mínima carga analítica"
        n = 1
        reglas = "1:3s — 1 nivel"
    elif sigma >= 4:
        cls = "Excelente"
        color = "#16a34a"
        rec = "Proceso bajo control, bajo riesgo"
        n = 2
        reglas = "1:3s / 2:2s / R:4s — 2 niveles"
    elif sigma >= 3:
        cls = "Bueno"
        color = "#ca8a04"
        rec = "Monitoreo frecuente recomendado"
        n = 2
        reglas = "1:3s / 2:2s / R:4s / 4:1s — 2 niveles"
    elif sigma >= 2:
        cls = "Marginal"
        color = "#d97706"
        rec = "Reforzar controles — evaluar causas de sesgo/imprecisión"
        n = 3
        reglas = "1:2s / 1:3s / 2:2s / R:4s / 4:1s / 10x — 3 niveles"
    else:
        cls = "Inaceptable"
        color = "#dc2626"
        rec = "ACCIÓN INMEDIATA — proceso no apto para uso clínico"
        n = 3
        reglas = "Revisión completa del proceso antes de continuar"

    return ResultadoSigma(
        sigma=round(sigma, 2),
        tea=tea,
        bias_pct=bias_pct,
        cv_pct=cv_pct,
        clasificacion=cls,
        color=color,
        recomendacion_qc=rec,
        n_niveles_recomendado=n,
        reglas_recomendadas=reglas,
    )
