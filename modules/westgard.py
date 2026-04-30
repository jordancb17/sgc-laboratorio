"""
Motor de Reglas de Westgard (multi-regla).

Reglas implementadas
--------------------
1-2s   Advertencia  : 1 valor fuera de media ± 2s
1-3s   Rechazo      : 1 valor fuera de media ± 3s  (error aleatorio)
2-2s   Rechazo      : 2 consecutivos al mismo lado de ± 2s  (error sistemático)
R-4s   Rechazo      : rango entre 2 consecutivos ≥ 4s  (error aleatorio)
4-1s   Rechazo      : 4 consecutivos al mismo lado de ± 1s  (error sistemático)
10x    Rechazo      : 10 consecutivos al mismo lado de la media  (error sistemático)
"""

from dataclasses import dataclass
from typing import Optional


RESULTADO_OK = "OK"
RESULTADO_ADVERTENCIA = "ADVERTENCIA"
RESULTADO_RECHAZO = "RECHAZO"


@dataclass
class ResultadoWestgard:
    resultado: str                   # OK / ADVERTENCIA / RECHAZO
    regla_violada: Optional[str]     # ej: "1-3s", "2-2s"
    zscore: float
    descripcion: str


def calcular_zscore(valor: float, media: float, de: float) -> float:
    if de == 0:
        return 0.0
    return (valor - media) / de


def evaluar_westgard(
    valor_nuevo: float,
    media: float,
    de: float,
    historial_zscores: list[float],   # zscores previos del MISMO nivel, más reciente primero
    historial_zscores_otros_niveles: list[float] | None = None,  # zscores del mismo run, otros niveles
) -> ResultadoWestgard:
    """
    Evalúa el valor nuevo aplicando las reglas de Westgard multi-regla.

    Parameters
    ----------
    valor_nuevo : float
        Valor medido del control.
    media : float
        Media objetivo del nivel.
    de : float
        Desviación estándar objetivo del nivel.
    historial_zscores : list[float]
        Lista de z-scores previos del mismo nivel (más reciente primero),
        excluyendo el valor actual. Se usan hasta los últimos 9.
    historial_zscores_otros_niveles : list[float] | None
        Z-scores de otros niveles en la MISMA corrida para R-4s inter-nivel.
    """
    z = calcular_zscore(valor_nuevo, media, de)
    # Construir lista completa: [z_actual, z_prev1, z_prev2, ...]
    zs = [z] + list(historial_zscores[:9])

    # ── 1-3s : rechazo inmediato ────────────────────────────────────────────
    if abs(z) > 3.0:
        return ResultadoWestgard(
            resultado=RESULTADO_RECHAZO,
            regla_violada="1-3s",
            zscore=z,
            descripcion=f"Valor fuera de media ± 3s (z={z:.2f}). Error aleatorio.",
        )

    # ── 2-2s : dos consecutivos al mismo lado de ± 2s ──────────────────────
    if len(zs) >= 2:
        if zs[0] > 2.0 and zs[1] > 2.0:
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="2-2s",
                zscore=z,
                descripcion="Dos valores consecutivos por encima de +2s. Error sistemático.",
            )
        if zs[0] < -2.0 and zs[1] < -2.0:
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="2-2s",
                zscore=z,
                descripcion="Dos valores consecutivos por debajo de -2s. Error sistemático.",
            )

    # ── R-4s : rango ≥ 4s entre dos consecutivos (mismo nivel) ────────────
    if len(zs) >= 2:
        rango = abs(zs[0] - zs[1])
        if rango >= 4.0 and (
            (zs[0] > 2.0 and zs[1] < -2.0) or (zs[0] < -2.0 and zs[1] > 2.0)
        ):
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="R-4s",
                zscore=z,
                descripcion=f"Rango de {rango:.2f}s entre dos consecutivos. Error aleatorio.",
            )

    # ── R-4s inter-nivel (mismo run) ────────────────────────────────────────
    if historial_zscores_otros_niveles:
        for z_otro in historial_zscores_otros_niveles:
            rango = abs(z - z_otro)
            if rango >= 4.0 and (
                (z > 2.0 and z_otro < -2.0) or (z < -2.0 and z_otro > 2.0)
            ):
                return ResultadoWestgard(
                    resultado=RESULTADO_RECHAZO,
                    regla_violada="R-4s",
                    zscore=z,
                    descripcion=f"Rango de {rango:.2f}s entre niveles en la misma corrida. Error aleatorio.",
                )

    # ── 4-1s : cuatro consecutivos al mismo lado de ± 1s ──────────────────
    if len(zs) >= 4:
        ultimos4 = zs[:4]
        if all(v > 1.0 for v in ultimos4):
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="4-1s",
                zscore=z,
                descripcion="Cuatro valores consecutivos por encima de +1s. Error sistemático.",
            )
        if all(v < -1.0 for v in ultimos4):
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="4-1s",
                zscore=z,
                descripcion="Cuatro valores consecutivos por debajo de -1s. Error sistemático.",
            )

    # ── 10x : diez consecutivos al mismo lado de la media ──────────────────
    if len(zs) >= 10:
        ultimos10 = zs[:10]
        if all(v > 0 for v in ultimos10):
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="10x",
                zscore=z,
                descripcion="Diez valores consecutivos por encima de la media. Error sistemático.",
            )
        if all(v < 0 for v in ultimos10):
            return ResultadoWestgard(
                resultado=RESULTADO_RECHAZO,
                regla_violada="10x",
                zscore=z,
                descripcion="Diez valores consecutivos por debajo de la media. Error sistemático.",
            )

    # ── 1-2s : advertencia ─────────────────────────────────────────────────
    if abs(z) > 2.0:
        return ResultadoWestgard(
            resultado=RESULTADO_ADVERTENCIA,
            regla_violada="1-2s",
            zscore=z,
            descripcion=f"Valor fuera de media ± 2s (z={z:.2f}). Advertencia.",
        )

    return ResultadoWestgard(
        resultado=RESULTADO_OK,
        regla_violada=None,
        zscore=z,
        descripcion="Control dentro de límites aceptables.",
    )


def color_resultado(resultado: str) -> str:
    """Devuelve el color HTML para cada resultado."""
    colores = {
        RESULTADO_OK: "#28a745",
        RESULTADO_ADVERTENCIA: "#ffc107",
        RESULTADO_RECHAZO: "#dc3545",
    }
    return colores.get(resultado, "#6c757d")


def emoji_resultado(resultado: str) -> str:
    emojis = {
        RESULTADO_OK: "✅",
        RESULTADO_ADVERTENCIA: "⚠️",
        RESULTADO_RECHAZO: "❌",
    }
    return emojis.get(resultado, "❓")
