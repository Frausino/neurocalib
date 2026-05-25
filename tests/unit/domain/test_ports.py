# tests/unit/domain/test_ports.py
"""Unit tests for bci_calib.domain.ports.

Test strategy for @runtime_checkable protocols
-----------------------------------------------
``isinstance(obj, Protocol)`` checks only for method name presence,
not signatures. Tests therefore:
  1. Define minimal stub classes that implement all required methods.
  2. Assert ``isinstance(stub, Protocol)`` is True.
  3. Define incomplete stubs missing one method each.
  4. Assert ``isinstance(incomplete, Protocol)`` is False.
  5. Verify each protocol exposes the correct method names via inspection.

This pattern catches regressions where a method is accidentally removed
or renamed in the protocol definition.
"""

from __future__ import annotations

from typing import Sequence

import pytest

from bci_calib.domain.calibration import CalibrationParams
from bci_calib.domain.entities import Epoch, RRInterval, SessionMetadata
from bci_calib.domain.ports import Calibrator, EEGSource, HRVSource, MIClassifier
from bci_calib.domain.value_objects import AblationCondition

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture  # type: ignore[misc]
def sample_session() -> SessionMetadata:
    return SessionMetadata(
        session_id="sess-001",
        participant_id="S1",
        recording_date="2026-08-20",
        ablation_condition=AblationCondition.D,
        functionally_identifiable=True,
        n_epochs=288,
        n_channels=22,
        sampling_rate_hz=250.0,
    )


@pytest.fixture  # type: ignore[misc]
def sample_epoch() -> Epoch:
    return Epoch(
        participant_id="S1",
        trial_index=0,
        label=1,
        n_channels=22,
        n_samples=375,
        sampling_rate_hz=250.0,
        onset_s=3.5,
    )


@pytest.fixture  # type: ignore[misc]
def sample_params() -> CalibrationParams:
    return CalibrationParams(tau_min=1.0, tau_max=3.0, a=1.0, b=0.0)


# ---------------------------------------------------------------------------
# Stub implementations
# ---------------------------------------------------------------------------


class _FullEEGSource:
    def load_epochs(self, session: SessionMetadata) -> Sequence[Epoch]:
        return []


class _FullHRVSource:
    def load_rr_intervals(self, session: SessionMetadata) -> Sequence[RRInterval]:
        return []


class _FullMIClassifier:
    def fit(self, session: SessionMetadata) -> None:
        pass

    def predict_proba(self, epoch: Epoch) -> Sequence[float]:
        return [0.5, 0.5]

    def predict(self, epoch: Epoch) -> int:
        return 0


class _FullCalibrator:
    def compute_temperature(self, r_t: float, params: CalibrationParams) -> float:
        return params.tau_min

    def fit_params(
        self,
        arousal_indices: Sequence[float],
        labels: Sequence[int],
    ) -> CalibrationParams:
        return CalibrationParams(tau_min=1.0, tau_max=3.0)


# ---------------------------------------------------------------------------
# Incomplete stubs — missing one method each
# ---------------------------------------------------------------------------


class _EEGSourceMissingLoadEpochs:
    pass


class _HRVSourceMissingLoadRRIntervals:
    pass


class _MIClassifierMissingFit:
    def predict_proba(self, epoch: Epoch) -> Sequence[float]:
        return []

    def predict(self, epoch: Epoch) -> int:
        return 0


class _MIClassifierMissingPredict:
    def fit(self, session: SessionMetadata) -> None:
        pass

    def predict_proba(self, epoch: Epoch) -> Sequence[float]:
        return []


class _CalibratorMissingFitParams:
    def compute_temperature(self, r_t: float, params: CalibrationParams) -> float:
        return 1.0


class _CalibratorMissingComputeTemperature:
    def fit_params(
        self, arousal_indices: Sequence[float], labels: Sequence[int]
    ) -> CalibrationParams:
        return CalibrationParams(tau_min=1.0, tau_max=3.0)


# ---------------------------------------------------------------------------
# TestEEGSource
# ---------------------------------------------------------------------------


class TestEEGSource:
    def test_full_implementation_is_instance(self) -> None:
        assert isinstance(_FullEEGSource(), EEGSource)

    def test_missing_load_epochs_is_not_instance(self) -> None:
        assert not isinstance(_EEGSourceMissingLoadEpochs(), EEGSource)

    def test_protocol_has_load_epochs_method(self) -> None:
        assert hasattr(EEGSource, "load_epochs")

    def test_stub_load_epochs_returns_sequence(
        self, sample_session: SessionMetadata
    ) -> None:
        source = _FullEEGSource()
        result = source.load_epochs(sample_session)
        assert isinstance(result, Sequence)


# ---------------------------------------------------------------------------
# TestHRVSource
# ---------------------------------------------------------------------------


class TestHRVSource:
    def test_full_implementation_is_instance(self) -> None:
        assert isinstance(_FullHRVSource(), HRVSource)

    def test_missing_load_rr_intervals_is_not_instance(self) -> None:
        assert not isinstance(_HRVSourceMissingLoadRRIntervals(), HRVSource)

    def test_protocol_has_load_rr_intervals_method(self) -> None:
        assert hasattr(HRVSource, "load_rr_intervals")

    def test_stub_load_rr_intervals_returns_sequence(
        self, sample_session: SessionMetadata
    ) -> None:
        source = _FullHRVSource()
        result = source.load_rr_intervals(sample_session)
        assert isinstance(result, Sequence)


# ---------------------------------------------------------------------------
# TestMIClassifier
# ---------------------------------------------------------------------------


class TestMIClassifier:
    def test_full_implementation_is_instance(self) -> None:
        assert isinstance(_FullMIClassifier(), MIClassifier)

    def test_missing_fit_is_not_instance(self) -> None:
        assert not isinstance(_MIClassifierMissingFit(), MIClassifier)

    def test_missing_predict_is_not_instance(self) -> None:
        assert not isinstance(_MIClassifierMissingPredict(), MIClassifier)

    def test_protocol_has_all_three_methods(self) -> None:
        assert hasattr(MIClassifier, "fit")
        assert hasattr(MIClassifier, "predict_proba")
        assert hasattr(MIClassifier, "predict")

    def test_stub_predict_proba_returns_sequence(self, sample_epoch: Epoch) -> None:
        clf = _FullMIClassifier()
        result = clf.predict_proba(sample_epoch)
        assert isinstance(result, Sequence)

    def test_stub_predict_returns_int(self, sample_epoch: Epoch) -> None:
        clf = _FullMIClassifier()
        assert isinstance(clf.predict(sample_epoch), int)


# ---------------------------------------------------------------------------
# TestCalibrator
# ---------------------------------------------------------------------------


class TestCalibrator:
    def test_full_implementation_is_instance(self) -> None:
        assert isinstance(_FullCalibrator(), Calibrator)

    def test_missing_fit_params_is_not_instance(self) -> None:
        assert not isinstance(_CalibratorMissingFitParams(), Calibrator)

    def test_missing_compute_temperature_is_not_instance(self) -> None:
        assert not isinstance(_CalibratorMissingComputeTemperature(), Calibrator)

    def test_protocol_has_both_methods(self) -> None:
        assert hasattr(Calibrator, "compute_temperature")
        assert hasattr(Calibrator, "fit_params")

    def test_stub_compute_temperature_returns_float(
        self, sample_params: CalibrationParams
    ) -> None:
        cal = _FullCalibrator()
        result = cal.compute_temperature(0.0, sample_params)
        assert isinstance(result, float)

    def test_stub_fit_params_returns_calibration_params(self) -> None:
        cal = _FullCalibrator()
        result = cal.fit_params([0.1, 0.2, 0.3], [0, 1, 0])
        assert isinstance(result, CalibrationParams)


# ---------------------------------------------------------------------------
# Cross-protocol: zero external imports in domain/ports.py
# ---------------------------------------------------------------------------


class TestZeroExternalDependencies:
    def test_no_forbidden_imports(self) -> None:
        """domain/ports.py must not import mne, numpy, torch, scipy."""
        import ast
        import pathlib

        source = pathlib.Path("src/bci_calib/domain/ports.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for forbidden in ("mne", "numpy", "torch", "scipy", "sklearn"):
                    assert (
                        forbidden not in node.module
                    ), f"Forbidden dependency in domain/ports.py: {node.module}"
