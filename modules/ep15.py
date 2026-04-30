"""
Módulo EP15-A3 — Verificación de precisión y sesgo del método.

Protocolo CLSI EP15-A3:
  - n_dias  : número de días de medición (mín. 5)
  - n_reps  : replicados por día (mín. 3)
  - Total   : n_dias × n_reps mediciones

Estadísticos calculados
------------------------
  Repetibilidad (within-run):
    s²_r  = MS_within  (cuadrado medio dentro del día)
    CV%_r = (s_r / X̄) × 100

  Precisión intermedia (between-day + within-run):
    s²_ip = s²_r + max(0, (MS_between - s²_r) / n_reps)
    CV%_ip = (s_ip / X̄) × 100

  Sesgo:
    Sesgo absoluto = X̄ - valor_referencia
    Sesgo%         = (Sesgo_abs / valor_referencia) × 100

Verificación contra valores del fabricante (chi-cuadrado, un lado):
    H₀: σ²_obs ≤ σ²_fabricante  →  rechazar si χ² > χ²_crítico(df, 0.05)
"""

import math
from dataclasses import dataclass
from typing import Optional

try:
    from scipy import stats as sp_stats
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False


@dataclass
class ResultadoEP15:
    n_dias: int
    n_reps: int
    n_total: int
    grand_mean: float
    # Repetibilidad
    de_r: float
    cv_r: float
    # Precisión intermedia
    de_ip: float
    cv_ip: float
    # Sesgo
    sesgo_absoluto: Optional[float]
    sesgo_porcentual: Optional[float]
    # Verificación
    verificacion_precision_r: Optional[bool]    # True = cumple
    verificacion_precision_ip: Optional[bool]
    verificacion_sesgo: Optional[bool]
    # Detalles estadísticos
    ms_within: float
    ms_between: float
    df_within: int
    df_between: int
    chi2_r: Optional[float]
    chi2_r_critico: Optional[float]
    chi2_ip: Optional[float]
    chi2_ip_critico: Optional[float]
    t_sesgo: Optional[float]
    t_critico: Optional[float]
    medias_dias: list[float]
    de_dias: list[float]


def calcular_ep15(
    datos: list[list[float]],           # datos[dia][replicado], 0-indexado
    valor_referencia: Optional[float] = None,
    cv_r_fabricante: Optional[float] = None,   # CV% repetibilidad del fabricante
    cv_ip_fabricante: Optional[float] = None,  # CV% precisión intermedia del fabricante
    sesgo_permitido: Optional[float] = None,   # sesgo máximo permitido (%)
    alpha: float = 0.05,
) -> ResultadoEP15:
    """
    Calcula los estadísticos EP15-A3 a partir de la matriz de datos.

    Parameters
    ----------
    datos : list[list[float]]
        Matriz [n_dias][n_reps] con los valores medidos.
    valor_referencia : float, optional
        Valor de referencia para cálculo de sesgo.
    cv_r_fabricante : float, optional
        CV% de repetibilidad declarado por el fabricante.
    cv_ip_fabricante : float, optional
        CV% de precisión intermedia declarado por el fabricante.
    sesgo_permitido : float, optional
        Sesgo máximo permitido en %.
    alpha : float
        Nivel de significación (default 0.05).
    """
    n_dias = len(datos)
    n_reps = len(datos[0])
    n_total = n_dias * n_reps

    # Medias y DE por día
    medias_dias = [sum(d) / len(d) for d in datos]
    de_dias = [
        math.sqrt(sum((v - medias_dias[i]) ** 2 for v in datos[i]) / (n_reps - 1))
        if n_reps > 1 else 0.0
        for i in range(n_dias)
    ]

    grand_mean = sum(medias_dias) / n_dias

    # ── ANOVA ───────────────────────────────────────────────────────────────
    # SS_within (dentro del día)
    ss_within = sum(
        sum((v - medias_dias[i]) ** 2 for v in datos[i])
        for i in range(n_dias)
    )
    df_within = n_dias * (n_reps - 1)
    ms_within = ss_within / df_within if df_within > 0 else 0.0

    # SS_between (entre días)
    ss_between = n_reps * sum((m - grand_mean) ** 2 for m in medias_dias)
    df_between = n_dias - 1
    ms_between = ss_between / df_between if df_between > 0 else 0.0

    # ── Varianzas de precisión ───────────────────────────────────────────────
    s2_r = ms_within                                              # repetibilidad
    s2_b = max(0.0, (ms_between - ms_within) / n_reps)           # entre días
    s2_ip = s2_r + s2_b                                          # precisión intermedia

    de_r = math.sqrt(s2_r)
    de_ip = math.sqrt(s2_ip)
    cv_r = (de_r / grand_mean) * 100 if grand_mean != 0 else 0.0
    cv_ip = (de_ip / grand_mean) * 100 if grand_mean != 0 else 0.0

    # ── Sesgo ────────────────────────────────────────────────────────────────
    sesgo_abs = None
    sesgo_pct = None
    if valor_referencia is not None and valor_referencia != 0:
        sesgo_abs = grand_mean - valor_referencia
        sesgo_pct = (sesgo_abs / valor_referencia) * 100

    # ── Verificación de precisión (chi-cuadrado) ─────────────────────────────
    chi2_r = chi2_r_crit = None
    verif_r = None
    if cv_r_fabricante is not None and grand_mean != 0:
        sigma_r_fab = (cv_r_fabricante / 100) * grand_mean
        if sigma_r_fab > 0:
            chi2_r = (df_within * s2_r) / (sigma_r_fab ** 2)
            if SCIPY_OK:
                chi2_r_crit = sp_stats.chi2.ppf(1 - alpha, df_within)
            else:
                # Aproximación de Wilson-Hilferty para chi² crítico
                k = df_within
                z_alpha = 1.6449  # z₀.₀₅ una cola
                chi2_r_crit = k * (1 - 2 / (9 * k) + z_alpha * math.sqrt(2 / (9 * k))) ** 3
            verif_r = chi2_r <= chi2_r_crit

    chi2_ip = chi2_ip_crit = None
    verif_ip = None
    df_ip_approx = n_total - 1  # aproximación conservadora
    if cv_ip_fabricante is not None and grand_mean != 0:
        sigma_ip_fab = (cv_ip_fabricante / 100) * grand_mean
        if sigma_ip_fab > 0:
            chi2_ip = (df_ip_approx * s2_ip) / (sigma_ip_fab ** 2)
            if SCIPY_OK:
                chi2_ip_crit = sp_stats.chi2.ppf(1 - alpha, df_ip_approx)
            else:
                k = df_ip_approx
                z_alpha = 1.6449
                chi2_ip_crit = k * (1 - 2 / (9 * k) + z_alpha * math.sqrt(2 / (9 * k))) ** 3
            verif_ip = chi2_ip <= chi2_ip_crit

    # ── Verificación de sesgo (t de Student) ────────────────────────────────
    t_sesgo = t_crit = None
    verif_sesgo = None
    if sesgo_permitido is not None and valor_referencia is not None and valor_referencia != 0:
        # El sesgo permitido se compara directamente con el sesgo%
        if sesgo_abs is not None and sesgo_pct is not None:
            # Prueba t: H₀: μ = referencia
            se_mean = de_ip / math.sqrt(n_total)
            if se_mean > 0:
                t_sesgo = abs(sesgo_abs) / se_mean
                if SCIPY_OK:
                    t_crit = sp_stats.t.ppf(1 - alpha / 2, n_total - 1)
                else:
                    # Aproximación normal para df grandes
                    t_crit = 1.96
            verif_sesgo = abs(sesgo_pct) <= sesgo_permitido

    return ResultadoEP15(
        n_dias=n_dias,
        n_reps=n_reps,
        n_total=n_total,
        grand_mean=grand_mean,
        de_r=de_r,
        cv_r=cv_r,
        de_ip=de_ip,
        cv_ip=cv_ip,
        sesgo_absoluto=sesgo_abs,
        sesgo_porcentual=sesgo_pct,
        verificacion_precision_r=verif_r,
        verificacion_precision_ip=verif_ip,
        verificacion_sesgo=verif_sesgo,
        ms_within=ms_within,
        ms_between=ms_between,
        df_within=df_within,
        df_between=df_between,
        chi2_r=chi2_r,
        chi2_r_critico=chi2_r_crit,
        chi2_ip=chi2_ip,
        chi2_ip_critico=chi2_ip_crit,
        t_sesgo=t_sesgo,
        t_critico=t_crit,
        medias_dias=medias_dias,
        de_dias=de_dias,
    )
