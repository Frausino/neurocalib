# src/bci_calib/domain/value_objects.py
"""Domain value objects (Objetos de Valor, OV).

Value objects are immutable, identity-free descriptors of domain concepts.
Equality is determined by field values, not by object identity.

Architectural constraint
------------------------
Zero external dependencies beyond stdlib and Pydantic.
Any import of mne, numpy, torch, or scipy here is an architectural error.
"""

from __future__ import annotations

from enum import Enum


class AblationCondition(str, Enum):
    """Ablation study condition for the calibration pipeline.

    Each member represents one configuration in the ablation study,
    allowing isolation of each component's contribution to the final
    calibration quality.

    Members
    -------
    A : Baseline — no temperature scaling, no HRV modulation.
    B : + Temperature scaling via fixed τ (no autonomic adaptation).
    C : + RMSSD-derived arousal index r_t (no τ modulation).
    D : + τ(r_t) modulation (full autonomic-dependent scaling).
    E : + Nested cross-validation with subject-specific calibration.
    F : Platt scaling — sigmoid fit on held-out calibration set.
    G : Isotonic regression — non-parametric monotone fit.

    GO/NO-GO
    --------
    This enum must have exactly 7 members (A through G) as specified
    in bci-calib v3 sprint card. Conditions F and G are added in v3
    to benchmark against classical post-hoc calibration methods.

    Examples
    --------
    >>> AblationCondition.F
    <AblationCondition.F: 'F'>
    >>> AblationCondition.F.value
    'F'
    >>> len(AblationCondition)
    7
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"  # Platt scaling
    G = "G"  # Isotonic regression
