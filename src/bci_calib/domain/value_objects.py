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
    """Ablation condition of the calibration study.

    A to E follow the pre-registered ablation of the PIC (OSF). F and G add
    the canonical post-hoc calibrators requested by the Guia Mestre.

    Members
    -------
    A : Pure EEG, τ = 1, no calibration (baseline).
    B : Static global temperature scaling (Guo et al. 2017).
    C : Dynamic τ(r_t) modulated by RMSSD (proposed model).
    D : Internal epistemic uncertainty (MC Dropout or Bootstrap).
    E : RMSSD as a discriminant feature, without τ modulation.
    F : Platt scaling.
    G : Isotonic regression.

    Interpretive contrasts
    ----------------------
    C vs A isolates the total gain of autonomic calibration.
    C vs B isolates the dynamic contribution of r_t.
    C vs D compares exogenous (HRV) with internal epistemic calibration.
    C vs E answers why τ is modulated instead of adding RMSSD as a feature.

    Examples
    --------
    >>> AblationCondition.C.description
    'Dynamic tau(r_t) modulated by RMSSD (proposed model)'
    >>> len(AblationCondition)
    7
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"

    @property
    def description(self) -> str:
        """Human-readable meaning of the condition, stable for MLflow tags."""
        return _CONDITION_DESCRIPTIONS[self]


_CONDITION_DESCRIPTIONS: dict[AblationCondition, str] = {
    AblationCondition.A: "Pure EEG, tau = 1, no calibration (baseline)",
    AblationCondition.B: "Static global temperature scaling",
    AblationCondition.C: "Dynamic tau(r_t) modulated by RMSSD (proposed model)",
    AblationCondition.D: "Internal epistemic uncertainty (MC Dropout or Bootstrap)",
    AblationCondition.E: "RMSSD as discriminant feature, no tau modulation",
    AblationCondition.F: "Platt scaling",
    AblationCondition.G: "Isotonic regression",
}
