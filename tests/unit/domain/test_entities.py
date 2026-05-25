# tests/unit/domain/test_entities.py
"""Unit tests for bci_calib.domain.entities.

Coverage targets
----------------
RRInterval       : construction, positive constraint, frozen.
Epoch            : construction, field constraints, frozen.
Participant      : construction, handedness, pathology optional, frozen.
SessionMetadata  : construction, functionally_identifiable field,
                   ablation_condition integration, date pattern, frozen.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bci_calib.domain.entities import Epoch, Participant, RRInterval, SessionMetadata
from bci_calib.domain.value_objects import AblationCondition

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_session(**overrides: object) -> SessionMetadata:
    defaults: dict[str, object] = dict(
        session_id="sess-001",
        participant_id="S1",
        recording_date="2026-08-17",
        ablation_condition=AblationCondition.D,
        functionally_identifiable=True,
        n_epochs=288,
        n_channels=22,
        sampling_rate_hz=250.0,
    )
    defaults.update(overrides)
    return SessionMetadata(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestRRInterval
# ---------------------------------------------------------------------------


class TestRRInterval:
    def test_valid_construction(self) -> None:
        rr = RRInterval(value_ms=800.0, timestamp_s=12.5)
        assert rr.value_ms == 800.0
        assert rr.timestamp_s == 12.5

    def test_zero_value_ms_raises(self) -> None:
        with pytest.raises(ValidationError):
            RRInterval(value_ms=0.0, timestamp_s=0.0)

    def test_negative_value_ms_raises(self) -> None:
        with pytest.raises(ValidationError):
            RRInterval(value_ms=-100.0, timestamp_s=0.0)

    def test_negative_timestamp_raises(self) -> None:
        with pytest.raises(ValidationError):
            RRInterval(value_ms=800.0, timestamp_s=-1.0)

    def test_frozen(self) -> None:
        rr = RRInterval(value_ms=800.0, timestamp_s=0.0)
        with pytest.raises((ValidationError, TypeError)):
            rr.value_ms = 900.0


# ---------------------------------------------------------------------------
# TestEpoch
# ---------------------------------------------------------------------------


class TestEpoch:
    def test_valid_construction(self) -> None:
        epoch = Epoch(
            participant_id="S1",
            trial_index=0,
            label=1,
            n_channels=22,
            n_samples=375,
            sampling_rate_hz=250.0,
            onset_s=3.5,
        )
        assert epoch.participant_id == "S1"
        assert epoch.label == 1
        assert epoch.n_samples == 375

    def test_negative_trial_index_raises(self) -> None:
        with pytest.raises(ValidationError):
            Epoch(
                participant_id="S1",
                trial_index=-1,
                label=0,
                n_channels=22,
                n_samples=375,
                sampling_rate_hz=250.0,
                onset_s=0.0,
            )

    def test_zero_n_channels_raises(self) -> None:
        with pytest.raises(ValidationError):
            Epoch(
                participant_id="S1",
                trial_index=0,
                label=0,
                n_channels=0,
                n_samples=375,
                sampling_rate_hz=250.0,
                onset_s=0.0,
            )

    def test_zero_n_samples_raises(self) -> None:
        with pytest.raises(ValidationError):
            Epoch(
                participant_id="S1",
                trial_index=0,
                label=0,
                n_channels=22,
                n_samples=0,
                sampling_rate_hz=250.0,
                onset_s=0.0,
            )

    def test_zero_sampling_rate_raises(self) -> None:
        with pytest.raises(ValidationError):
            Epoch(
                participant_id="S1",
                trial_index=0,
                label=0,
                n_channels=22,
                n_samples=375,
                sampling_rate_hz=0.0,
                onset_s=0.0,
            )

    def test_frozen(self) -> None:
        epoch = Epoch(
            participant_id="S1",
            trial_index=0,
            label=0,
            n_channels=22,
            n_samples=375,
            sampling_rate_hz=250.0,
            onset_s=0.0,
        )
        with pytest.raises((ValidationError, TypeError)):
            epoch.label = 99


# ---------------------------------------------------------------------------
# TestParticipant
# ---------------------------------------------------------------------------


class TestParticipant:
    def test_valid_right_handed(self) -> None:
        p = Participant(participant_id="S1", age=28, handedness="R")
        assert p.handedness == "R"
        assert p.pathology is None

    def test_valid_left_handed_with_pathology(self) -> None:
        p = Participant(participant_id="S2", age=35, handedness="L", pathology="ALS")
        assert p.pathology == "ALS"

    def test_empty_participant_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            Participant(participant_id="", age=28, handedness="R")

    def test_invalid_handedness_raises(self) -> None:
        with pytest.raises(ValidationError):
            Participant(participant_id="S1", age=28, handedness="X")  # type: ignore[arg-type]

    def test_age_zero_raises(self) -> None:
        with pytest.raises(ValidationError):
            Participant(participant_id="S1", age=0, handedness="R")

    def test_age_above_limit_raises(self) -> None:
        with pytest.raises(ValidationError):
            Participant(participant_id="S1", age=121, handedness="R")

    def test_frozen(self) -> None:
        p = Participant(participant_id="S1", age=28, handedness="R")
        with pytest.raises((ValidationError, TypeError)):
            p.age = 99


# ---------------------------------------------------------------------------
# TestSessionMetadata
# ---------------------------------------------------------------------------


class TestSessionMetadata:
    def test_valid_construction(self) -> None:
        session = _valid_session()
        assert session.session_id == "sess-001"
        assert session.ablation_condition == AblationCondition.D
        assert session.functionally_identifiable is True

    def test_functionally_identifiable_field_exists(self) -> None:
        """GO/NO-GO: functionally_identifiable must be a field of SessionMetadata."""
        fields = SessionMetadata.model_fields
        assert "functionally_identifiable" in fields

    def test_functionally_identifiable_true(self) -> None:
        session = _valid_session(functionally_identifiable=True)
        assert session.functionally_identifiable is True

    def test_functionally_identifiable_false(self) -> None:
        session = _valid_session(functionally_identifiable=False)
        assert session.functionally_identifiable is False

    def test_ablation_condition_f_platt(self) -> None:
        session = _valid_session(ablation_condition=AblationCondition.F)
        assert session.ablation_condition == AblationCondition.F

    def test_ablation_condition_g_isotonic(self) -> None:
        session = _valid_session(ablation_condition=AblationCondition.G)
        assert session.ablation_condition == AblationCondition.G

    def test_invalid_date_format_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_session(recording_date="17/08/2026")

    def test_invalid_date_format_no_dashes_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_session(recording_date="20260817")

    def test_empty_session_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_session(session_id="")

    def test_zero_n_epochs_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_session(n_epochs=0)

    def test_zero_sampling_rate_raises(self) -> None:
        with pytest.raises(ValidationError):
            _valid_session(sampling_rate_hz=0.0)

    def test_frozen(self) -> None:
        session = _valid_session()
        with pytest.raises((ValidationError, TypeError)):
            session.functionally_identifiable = False

    def test_all_ablation_conditions_accepted(self) -> None:
        """All 7 AblationCondition values must be valid for SessionMetadata."""
        for condition in AblationCondition:
            session = _valid_session(ablation_condition=condition)
            assert session.ablation_condition == condition
