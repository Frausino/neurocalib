# tests/unit/application/test_session_audit.py
"""Unit tests for bci_calib.application.session_audit."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from bci_calib.application.session_audit import (
    METRIC_DYNAMIC_EFFECT_DEGENERATE,
    METRIC_FUNCTIONAL_IDENTIFIABLE,
    METRIC_TAU_MAX_DEGENERATE,
    METRIC_VAR_R_T,
    SESSION_LOG_ARTIFACT_NAME,
    SessionLogEntry,
    build_session_log_entry,
    is_dynamic_effect_degenerate,
    is_tau_max_degenerate,
    record_session_audit,
)
from bci_calib.application.trial_rmssd_alignment import SessionIdentifiability
from bci_calib.domain.calibration import CalibrationParams


class RecordingSink:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, float, int]] = []
        self.artifacts: list[tuple[str, str, str, str | None]] = []

    def log_metric(self, run_id: str, key: str, value: float, step: int = 0) -> None:
        self.calls.append((run_id, key, value, step))

    def log_artifact(
        self, run_id: str, name: str, path: str, mime_type: str | None = None
    ) -> None:
        self.artifacts.append((run_id, name, path, mime_type))


LOG_PATH = Path("sessions/s1/session_log.json")


def _identifiability(variance: float, identifiable: bool) -> SessionIdentifiability:
    return SessionIdentifiability(
        session_id="s1", variance=variance, functionally_identifiable=identifiable
    )


class TestDegeneracyRules:
    @pytest.mark.parametrize(
        ("a", "expected"),
        [(0.0, True), (-0.05, True), (0.0999, True), (-0.1, False), (-3.0, False)],
    )
    def test_dynamic_effect_threshold_is_0_1(self, a: float, expected: bool) -> None:
        assert is_dynamic_effect_degenerate(a) is expected

    @pytest.mark.parametrize(
        ("tau_max", "expected"),
        [(1.0, True), (1.05, True), (1.0500001, False), (3.0, False)],
    )
    def test_tau_max_threshold_is_1_05(self, tau_max: float, expected: bool) -> None:
        assert is_tau_max_degenerate(tau_max) is expected

    @pytest.mark.parametrize("bad", [math.nan, math.inf])
    def test_non_finite_values_fail_closed(self, bad: float) -> None:
        with pytest.raises(ValueError, match="finite"):
            is_dynamic_effect_degenerate(bad)
        with pytest.raises(ValueError, match="finite"):
            is_tau_max_degenerate(bad)


class TestBuildSessionLogEntry:
    def test_before_fit_degeneracy_flags_are_unset(self) -> None:
        entry = build_session_log_entry(_identifiability(0.2, True))
        assert entry == SessionLogEntry("s1", 0.2, True, None, None)

    def test_after_fit_flags_follow_parameters(self) -> None:
        params = CalibrationParams(tau_max=1.02, a=-0.05)
        entry = build_session_log_entry(_identifiability(0.01, False), params)
        assert entry.dynamic_effect_degenerate is True
        assert entry.tau_max_degenerate is True
        assert entry.functional_identifiable is False

    def test_healthy_fit_has_no_degeneracy(self) -> None:
        params = CalibrationParams(tau_max=3.0, a=-2.0)
        entry = build_session_log_entry(_identifiability(0.3, True), params)
        assert entry.dynamic_effect_degenerate is False
        assert entry.tau_max_degenerate is False


class TestRecordSessionAudit:
    def test_before_fit_only_identifiability_is_recorded(self) -> None:
        sink = RecordingSink()
        record_session_audit(sink, "run-1", SessionLogEntry("s1", 0.2, True), LOG_PATH)
        assert sink.calls == [
            ("run-1", METRIC_VAR_R_T, 0.2, 0),
            ("run-1", METRIC_FUNCTIONAL_IDENTIFIABLE, 1.0, 0),
        ]

    def test_after_fit_all_four_metrics_are_recorded(self) -> None:
        sink = RecordingSink()
        entry = SessionLogEntry("s1", 0.01, False, True, False)
        record_session_audit(sink, "run-1", entry, LOG_PATH, step=3)
        assert sink.calls == [
            ("run-1", METRIC_VAR_R_T, 0.01, 3),
            ("run-1", METRIC_FUNCTIONAL_IDENTIFIABLE, 0.0, 3),
            ("run-1", METRIC_DYNAMIC_EFFECT_DEGENERATE, 1.0, 3),
            ("run-1", METRIC_TAU_MAX_DEGENERATE, 0.0, 3),
        ]

    def test_run_is_linked_to_the_session_log_once(self) -> None:
        sink = RecordingSink()
        record_session_audit(sink, "run-1", SessionLogEntry("s1", 0.2, True), LOG_PATH)
        assert sink.artifacts == [
            ("run-1", SESSION_LOG_ARTIFACT_NAME, str(LOG_PATH), "application/json")
        ]
