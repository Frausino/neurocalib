# src/bci_calib/application/session_audit.py
"""Per-session identifiability and degeneracy flags, ready for audit storage.

Three flags are pre-registered (OSF_PREREG.md, Section 6.3):

functional_identifiable
    ``Var(r_t) >= 0.05`` in the session. Known after the session, before any fit.
dynamic_effect_degenerate
    ``|a| < 0.1`` in the fitted model. Known only after the fit, so it is
    ``None`` until fitted parameters exist.
tau_max_degenerate
    ``tau_max <= 1.05`` in the fitted model. Also ``None`` until fitted.

The key ``functional_identifiable`` follows the session_log.json contract of the
Guia Mestre. The domain entity spells it ``functionally_identifiable``.

Run and session
    Each audit ``run_id`` represents exactly one session. Metrics are keyed by
    ``(run_id, key, step)`` and carry no session column, so the link to the
    session is an artifact named ``session_log`` on the same run, pointing at
    the ``session_log.json`` that holds the ``session_id``.

``AuditSink`` is satisfied structurally by ``AuditDB``, so this module needs no
import from the infrastructure layer.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Final, Protocol

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from bci_calib.application.trial_rmssd_alignment import SessionIdentifiability
from bci_calib.domain.calibration import CalibrationParams

DYNAMIC_EFFECT_MIN_ABS_A: Final[float] = 0.1
TAU_MAX_DEGENERATE_UPPER_BOUND: Final[float] = 1.05

SESSION_LOG_ARTIFACT_NAME: Final[str] = "session_log"
SESSION_LOG_MIME_TYPE: Final[str] = "application/json"

METRIC_VAR_R_T: Final[str] = "var_r_t"
METRIC_FUNCTIONAL_IDENTIFIABLE: Final[str] = "functional_identifiable"
METRIC_DYNAMIC_EFFECT_DEGENERATE: Final[str] = "dynamic_effect_degenerate"
METRIC_TAU_MAX_DEGENERATE: Final[str] = "tau_max_degenerate"


class AuditSink(Protocol):
    """Destination for scalar metrics and artifact links, keyed by run."""

    def log_metric(
        self, run_id: str, key: str, value: float, step: int = 0
    ) -> None: ...

    def log_artifact(
        self,
        run_id: str,
        name: str,
        path: str,
        mime_type: str | None = None,
    ) -> None: ...


@dataclass(config=ConfigDict(frozen=True, allow_inf_nan=False))
class SessionLogEntry:
    """Content of session_log.json for the flags implemented so far."""

    session_id: str
    var_r_t: float
    functional_identifiable: bool
    dynamic_effect_degenerate: bool | None = None
    tau_max_degenerate: bool | None = None


def is_dynamic_effect_degenerate(a: float) -> bool:
    """True when the fitted slope is too small to count as a dynamic effect."""
    _require_finite(a, "a")
    return abs(a) < DYNAMIC_EFFECT_MIN_ABS_A


def is_tau_max_degenerate(tau_max: float) -> bool:
    """True when the fitted ceiling is indistinguishable from no calibration."""
    _require_finite(tau_max, "tau_max")
    return tau_max <= TAU_MAX_DEGENERATE_UPPER_BOUND


def build_session_log_entry(
    identifiability: SessionIdentifiability,
    fitted_params: CalibrationParams | None = None,
) -> SessionLogEntry:
    """Combine the identifiability result with fit degeneracy, when a fit exists."""
    dynamic_flag = None
    tau_flag = None
    if fitted_params is not None:
        dynamic_flag = is_dynamic_effect_degenerate(fitted_params.a)
        tau_flag = is_tau_max_degenerate(fitted_params.tau_max)
    return SessionLogEntry(
        session_id=identifiability.session_id,
        var_r_t=identifiability.variance,
        functional_identifiable=identifiability.functionally_identifiable,
        dynamic_effect_degenerate=dynamic_flag,
        tau_max_degenerate=tau_flag,
    )


def record_session_audit(
    sink: AuditSink,
    run_id: str,
    entry: SessionLogEntry,
    session_log_path: Path,
    step: int = 0,
) -> None:
    """Link the run to its session log, then write the flags as metrics.

    The link comes first so that a partial failure never leaves metrics without
    a traceable session. Unfitted flags are not written.
    """
    sink.log_artifact(
        run_id,
        SESSION_LOG_ARTIFACT_NAME,
        str(session_log_path),
        SESSION_LOG_MIME_TYPE,
    )
    sink.log_metric(run_id, METRIC_VAR_R_T, entry.var_r_t, step)
    sink.log_metric(
        run_id,
        METRIC_FUNCTIONAL_IDENTIFIABLE,
        _as_metric(entry.functional_identifiable),
        step,
    )
    if entry.dynamic_effect_degenerate is not None:
        sink.log_metric(
            run_id,
            METRIC_DYNAMIC_EFFECT_DEGENERATE,
            _as_metric(entry.dynamic_effect_degenerate),
            step,
        )
    if entry.tau_max_degenerate is not None:
        sink.log_metric(
            run_id,
            METRIC_TAU_MAX_DEGENERATE,
            _as_metric(entry.tau_max_degenerate),
            step,
        )


def _as_metric(flag: bool) -> float:
    return 1.0 if flag else 0.0


def _require_finite(value: float, name: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}")
