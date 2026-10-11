# src/bci_calib/domain/calibration.py
"""Dynamic temperature scaling (Escalonamento de Temperatura, ET) τ(r_t).

Pre-registered model (OSF, PIC CEUB 2026/2027)
----------------------------------------------
    τ(r_t) = 1 + (τ_max − 1) · σ(a · r_t)

    P(y | X) = softmax(z / τ(r_t))

where σ is the logistic sigmoid and r_t is the RMSSD z-score computed
with training-fold statistics: r_t = (RMSSD_smooth_t − μ_train) / σ_train.

Frozen decisions (Guia Mestre, Seção 0.6)
-----------------------------------------
- τ_min is fixed at 1.0: the lower bound is the uncalibrated softmax.
- The sigmoid bias b is fixed at 0.0: r_t is already centred (μ_train = 0),
  so a free b would be redundant with the normalisation term.
- Only two parameters are free: θ = (τ_max, a). With n = 19 subjects the
  four-parameter form is not identifiable.

Changing either constant requires a formal OSF amendment and an entry in
docs/CHANGELOG_CIENTIFICO.md.

Architectural constraint
------------------------
Zero external dependencies beyond stdlib and Pydantic.
Any import of mne, numpy, torch, scipy or sklearn here is an
architectural error.

Scientific reference
--------------------
Guo et al. 2017 (arXiv:1706.04599): temperature scaling, ECE, NLL.
When a = 0, or when r_t is constant, τ(r_t) collapses to a static
temperature, which is ablation condition B.
"""

from __future__ import annotations

import math
from typing import Final

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

TAU_MIN: Final[float] = 1.0
SIGMOID_BIAS: Final[float] = 0.0


@dataclass(config=ConfigDict(frozen=True, allow_inf_nan=False))
class CalibrationParams:
    """Frozen free parameters θ = (τ_max, a) of the pre-registered τ(r_t).

    Fields
    ------
    tau_max :
        Upper bound of the temperature. Must be finite and >= TAU_MIN, so
        that τ(r_t) never sharpens the softmax below the uncalibrated
        baseline. τ_max == TAU_MIN makes τ(r_t) identically 1.
    a :
        Slope of the sigmoid in r_t. Must be finite. The sign sets the
        direction of the modulation: for a < 0, τ rises as RMSSD falls.
        Search bounds for a belong to the fitter (application layer).

    Examples
    --------
    >>> params = CalibrationParams(3.0, 1.0)
    >>> params.tau_max, params.a
    (3.0, 1.0)
    """

    tau_max: float = Field(ge=TAU_MIN)
    a: float = 1.0


def _stable_sigmoid(x: float) -> float:
    """Numerically stable logistic sigmoid σ(x) = 1 / (1 + e^{−x}).

    The two branches keep the argument of math.exp non-positive, so it never
    overflows. The naive formula raises OverflowError for x << 0.
    σ(0) is exactly 0.5 in IEEE 754.
    """
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    exp_x = math.exp(x)
    return exp_x / (1.0 + exp_x)


def compute_tau(r_t: float, params: CalibrationParams) -> float:
    """Compute the calibration temperature τ(r_t) = 1 + (τ_max − 1) · σ(a · r_t).

    The result lies in [TAU_MIN, τ_max] for every finite r_t.

    GO/NO-GO identity (exact in IEEE 754)
    -------------------------------------
    compute_tau(0.0, CalibrationParams(3.0, 1.0)):
      σ(0) = 0.5 → τ = 1.0 + (3.0 − 1.0) × 0.5 = 2.0 exactly.

    Examples
    --------
    >>> compute_tau(0.0, CalibrationParams(3.0, 1.0))
    2.0
    """
    temperature_range = params.tau_max - TAU_MIN
    sigmoid_input = params.a * r_t + SIGMOID_BIAS
    return TAU_MIN + temperature_range * _stable_sigmoid(sigmoid_input)
