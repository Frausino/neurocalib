# src/bci_calib/application/trial_rmssd_alignment.py
"""Causal alignment of smoothed RMSSD to trials, and session identifiability.

Rule selected for pre-registration (Guia Mestre 0.6, immutable):

    k_t = floor(T_t / delta_t)

``T_t`` is the reference time of trial ``t``: its motor imagery onset minus the
safety lag. Sample ``k`` of the smoothed RMSSD series is stamped ``k * delta_t``
seconds after the start of the RMSSD stream and summarises only data up to that
instant. ``floor`` therefore selects the latest sample that is not later than
``T_t``. ``round`` would select a later sample for half of all trials and leak
future information into trial ``t``.

``delta_t`` and ``safety_lag`` are required arguments on purpose. Their values
are frozen decisions owned by the HRV extraction module and by the OSF
pre-registration, and a default here would be a second copy of them.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping, Sequence
from typing import Final

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

FUNCTIONAL_IDENTIFIABILITY_MIN_VARIANCE: Final[float] = 0.05


class RmssdAlignmentError(ValueError):
    """A trial cannot be aligned to the RMSSD series without breaking causality."""


@dataclass(config=ConfigDict(frozen=True, allow_inf_nan=False))
class SessionIdentifiability:
    """Variance of r_t in one session and the resulting identifiability flag."""

    session_id: str
    variance: float
    functionally_identifiable: bool


def assign_rmssd_to_trials(
    trial_onsets_s: Sequence[float],
    rmssd_smooth: Sequence[float],
    *,
    delta_t_s: float,
    safety_lag_s: float,
) -> tuple[float, ...]:
    """Smoothed RMSSD value that is causally available for each trial."""
    _require_all_finite(rmssd_smooth, "rmssd_smooth")
    indices = compute_rmssd_indices(
        trial_onsets_s,
        series_length=len(rmssd_smooth),
        delta_t_s=delta_t_s,
        safety_lag_s=safety_lag_s,
    )
    return tuple(rmssd_smooth[index] for index in indices)


def compute_rmssd_indices(
    trial_onsets_s: Sequence[float],
    *,
    series_length: int,
    delta_t_s: float,
    safety_lag_s: float,
) -> tuple[int, ...]:
    """Index k_t = floor(T_t / delta_t) of the RMSSD sample for each trial."""
    _require_positive_finite(delta_t_s, "delta_t_s")
    _require_non_negative_finite(safety_lag_s, "safety_lag_s")
    return tuple(
        _index_for_trial(onset_s, series_length, delta_t_s, safety_lag_s)
        for onset_s in trial_onsets_s
    )


def compute_r_t(
    rmssd_values: Sequence[float], *, train_mean: float, train_std: float
) -> tuple[float, ...]:
    """Autonomic arousal index r_t = (RMSSD - mu_train) / sigma_train."""
    _require_positive_finite(train_std, "train_std")
    _require_finite(train_mean, "train_mean")
    _require_all_finite(rmssd_values, "rmssd_values")
    r_t = tuple((value - train_mean) / train_std for value in rmssd_values)
    _require_all_finite(r_t, "r_t")
    return r_t


def compute_r_t_variance_per_session(
    r_t_by_session: Mapping[str, Sequence[float]],
) -> dict[str, SessionIdentifiability]:
    """Sample variance of r_t per session and the Var(r_t) >= 0.05 flag.

    Sessions below the threshold are not excluded. The pre-registration
    analyses them as a separate subgroup.
    """
    return {
        session_id: _identifiability_of(session_id, r_t_values)
        for session_id, r_t_values in r_t_by_session.items()
    }


def _index_for_trial(
    onset_s: float, series_length: int, delta_t_s: float, safety_lag_s: float
) -> int:
    reference_time_s = onset_s - safety_lag_s
    if not math.isfinite(reference_time_s) or reference_time_s < 0.0:
        raise RmssdAlignmentError(
            f"onset {onset_s} s minus lag {safety_lag_s} s "
            "precedes the first RMSSD sample"
        )
    index = math.floor(reference_time_s / delta_t_s)
    if index >= series_length:
        raise RmssdAlignmentError(
            f"RMSSD series has {series_length} samples but trial needs index {index}"
        )
    return index


def _identifiability_of(
    session_id: str, r_t_values: Sequence[float]
) -> SessionIdentifiability:
    if len(r_t_values) < 2:
        raise ValueError(f"session {session_id!r} needs at least 2 r_t values")
    _require_all_finite(r_t_values, f"r_t of session {session_id!r}")
    variance = statistics.variance(r_t_values)
    return SessionIdentifiability(
        session_id=session_id,
        variance=variance,
        functionally_identifiable=variance >= FUNCTIONAL_IDENTIFIABILITY_MIN_VARIANCE,
    )


def _require_finite(value: float, name: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value}")


def _require_all_finite(values: Sequence[float], name: str) -> None:
    for position, value in enumerate(values):
        if not math.isfinite(value):
            raise ValueError(f"{name}[{position}] must be finite, got {value}")


def _require_positive_finite(value: float, name: str) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be positive and finite, got {value}")


def _require_non_negative_finite(value: float, name: str) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be non-negative and finite, got {value}")
