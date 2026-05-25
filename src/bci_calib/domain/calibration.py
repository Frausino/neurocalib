# src/bci_calib/domain/calibration.py
"""Temperature scaling (Escalonamento de Temperatura, ET) function τ(r_t).

Formula
-------
    τ(r_t) = τ_min + (τ_max − τ_min) · σ(a · r_t + b)

where σ is the logistic sigmoid and r_t is the autonomic arousal index
derived from HRV (RMSSD normalizado).

Architectural constraint
------------------------
This module has ZERO external dependencies beyond stdlib and Pydantic.
Any import of mne, numpy, torch, or scipy here is an architectural error.

Scientific reference
--------------------
Guo et al. 2017 (arXiv:1706.04599) — ECE formal, temperature scaling
como parâmetro, NLL como objetivo. A função τ(r_t) estende o trabalho
ao modular a temperatura pelo estado autonômico do participante.
"""

from __future__ import annotations

import math

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(frozen=True))
class CalibrationParams:
    """Frozen parameter set for the temperature scaling function τ(r_t).

    <<<<<<< HEAD
            Implemented as a Pydantic dataclass so that:
            - Positional construction works: ``CalibrationParams(3.0, 1.0)``.
            - All fields are type-validated by Pydantic at construction time.
            - ``frozen=True`` makes every field immutable after construction;
              any mutation attempt raises ``pydantic_core.ValidationError``.

            Fields
            ------
        tau_min :
            Lower bound of the temperature range.
            When a > 0, τ(r_t) → tau_min as r_t → −∞.
        tau_max :
            Upper bound of the temperature range.
            When a > 0, τ(r_t) → tau_max as r_t → +∞.
            a :
                Slope controlling sensitivity to autonomic arousal. Default 1.0.
            b :
                Bias shifting the sigmoid inflection point. Default 0.0.
                When b = 0, τ(0) equals the arithmetic mean of tau_min and tau_max
                exactly in IEEE 754, because σ(0) = 0.5 exactly.

            Examples
            --------
            >>> p = CalibrationParams(3.0, 1.0)
            >>> p.tau_min, p.tau_max, p.a, p.b
            (3.0, 1.0, 1.0, 0.0)
    =======
        Implemented as a Pydantic dataclass so that:
        - Positional construction works: ``CalibrationParams(3.0, 1.0)``.
        - All fields are type-validated by Pydantic at construction time.
        - ``frozen=True`` makes every field immutable after construction;
          any mutation attempt raises ``pydantic_core.ValidationError``.

        Fields
        ------
        tau_min :
            Lower bound of the temperature range.
            When a > 0, τ(r_t) → tau_min as r_t → +∞.
        tau_max :
            Upper bound of the temperature range.
            When a > 0, τ(r_t) → tau_max as r_t → −∞.
        a :
            Slope controlling sensitivity to autonomic arousal. Default 1.0.
        b :
            Bias shifting the sigmoid inflection point. Default 0.0.
            When b = 0, τ(0) equals the arithmetic mean of tau_min and tau_max
            exactly in IEEE 754, because σ(0) = 0.5 exactly.

        Examples
        --------
        >>> p = CalibrationParams(3.0, 1.0)
        >>> p.tau_min, p.tau_max, p.a, p.b
        (3.0, 1.0, 1.0, 0.0)
    >>>>>>> origin/dev
    """

    tau_min: float
    tau_max: float
    a: float = 1.0
    b: float = 0.0


def _stable_sigmoid(x: float) -> float:
    """Numerically stable sigmoid σ(x) = 1 / (1 + e^{−x}).

    Uses two branches to avoid floating-point overflow in math.exp:

    - x ≥ 0: computes 1 / (1 + e^{−x}).
      e^{−x} ≤ 1, so math.exp(−x) never overflows.
    - x < 0: computes e^x / (1 + e^x).
      e^x < 1, so math.exp(x) never overflows.

    The naive formula 1 / (1 + math.exp(−x)) raises OverflowError for
    x ≪ 0 because math.exp(large_positive) exceeds sys.float_info.max.

    At x = 0, returns 0.5 EXACTLY in IEEE 754:
      math.exp(0) == 1.0 exactly → 1 / (1 + 1) == 0.5 exactly.

    Parameters
    ----------
    x :
        Input value. Accepts the full range of finite IEEE 754 doubles.

    Returns
    -------
    float
        σ(x) ∈ (0.0, 1.0). Equals 0.5 exactly when x == 0.0.
    """
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    exp_x = math.exp(x)
    return exp_x / (1.0 + exp_x)


def compute_tau(r_t: float, params: CalibrationParams) -> float:
    """Compute calibration temperature τ(r_t).

    Formula: τ(r_t) = τ_min + (τ_max − τ_min) · σ(a · r_t + b)

    The result lies strictly within the open interval
    (min(τ_min, τ_max), max(τ_min, τ_max)) for all finite r_t,
    because σ maps ℝ onto (0, 1) exclusively.

    GO/NO-GO identity (exact IEEE 754)
    ------------------------------------
    With tau_min=3.0, tau_max=1.0, a=1.0, b=0.0 and r_t=0.0:
      σ(0) = 0.5 exactly
      τ = 3.0 + (1.0 − 3.0) × 0.5 = 3.0 − 1.0 = 2.0 exactly.
    All intermediate values are representable as IEEE 754 binary fractions.

    Parameters
    ----------
    r_t :
        Autonomic arousal index derived from HRV (RMSSD normalizado).
    params :
        Frozen parameter set for the scaling function.

    Returns
    -------
    float
        Temperature τ(r_t).

    Examples
    --------
    >>> compute_tau(0.0, CalibrationParams(3.0, 1.0))
    2.0
    """
    sigmoid_input = params.a * r_t + params.b
    return params.tau_min + (params.tau_max - params.tau_min) * _stable_sigmoid(
        sigmoid_input
    )
