# src/bci_calib/domain/entities.py
"""Domain entities (Entidades de Domínio, ED).

Entities represent concepts with domain identity and lifecycle.
All entities here are immutable (frozen Pydantic BaseModel) because
calibration data is read-only once acquired — mutations produce new
entities, they do not modify existing ones.

Raw EEG arrays are NOT stored in domain entities. Array data belongs
to the infrastructure layer (loaders, MOABB adapters). Domain entities
hold only the metadata needed for business rule evaluation.

Architectural constraint
------------------------
Zero external dependencies beyond stdlib and Pydantic.
Any import of mne, numpy, torch, or scipy here is an architectural error.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from bci_calib.domain.value_objects import AblationCondition


class RRInterval(BaseModel):
    """A single RR interval measurement from a cardiac signal.

    RR intervals are the time distances between consecutive R-peaks
    in an ECG/PPG signal. They are the raw material for HRV metrics
    such as RMSSD, which drives the autonomic arousal index r_t.

    Fields
    ------
    value_ms :
        Interval duration in milliseconds. Must be strictly positive.
        Physiologically valid range is roughly 300–2000 ms (30–200 bpm),
        but the model does not enforce physiological bounds to remain
        applicable to synthetic and edge-case test data.
    timestamp_s :
        Onset of the R-peak in seconds from session start. Non-negative.
    """

    model_config = ConfigDict(frozen=True)

    value_ms: float = Field(gt=0.0, description="RR interval in milliseconds.")
    timestamp_s: float = Field(ge=0.0, description="R-peak onset from session start.")


class Epoch(BaseModel):
    """Metadata descriptor for a single EEG trial epoch.

    An epoch is a time-locked segment of EEG data around a motor imagery
    cue. Raw sample data (numpy arrays) are handled by the infrastructure
    layer; this entity stores the metadata needed for calibration logic.

    Fields
    ------
    participant_id :
        Unique participant identifier (e.g., ``"S1"`` for BCI Competition
        IV Dataset 2a subject 1).
    trial_index :
        Zero-based index of this trial within the session.
    label :
        Motor imagery class label. For BCI Competition IV 2a:
        0=left hand, 1=right hand, 2=feet, 3=tongue.
    n_channels :
        Number of EEG channels. Must be strictly positive.
    n_samples :
        Number of time samples per channel. Must be strictly positive.
    sampling_rate_hz :
        Acquisition sampling rate in Hz. Must be strictly positive.
    onset_s :
        Epoch onset in seconds from session start. Non-negative.
    """

    model_config = ConfigDict(frozen=True)

    participant_id: str
    trial_index: int = Field(ge=0)
    label: int = Field(ge=0)
    n_channels: int = Field(gt=0)
    n_samples: int = Field(gt=0)
    sampling_rate_hz: float = Field(gt=0.0)
    onset_s: float = Field(ge=0.0)


class Participant(BaseModel):
    """A study participant with demographic metadata.

    Fields
    ------
    participant_id :
        Unique identifier (e.g., ``"S1"``). Must be non-empty.
    age :
        Age in years. Constrained to [1, 120] to catch data entry errors
        while remaining permissive for edge cases.
    handedness :
        Dominant hand: ``"R"`` (right) or ``"L"`` (left).
        Used to stratify lateralised motor imagery tasks.
    pathology :
        Clinical condition relevant to BCI performance, if any.
        ``None`` for healthy controls.
    """

    model_config = ConfigDict(frozen=True)

    participant_id: str = Field(min_length=1)
    age: int = Field(ge=1, le=120)
    handedness: Literal["R", "L"]
    pathology: str | None = None


class SessionMetadata(BaseModel):
    """Recording session descriptor with calibration context.

    A session groups all trials and HRV measurements collected in a
    single continuous recording block for one participant under one
    ablation condition.

    Fields
    ------
    session_id :
        Unique session identifier. Must be non-empty.
    participant_id :
        Participant this session belongs to.
    recording_date :
        ISO 8601 date string (``YYYY-MM-DD``). Stored as str to avoid
        datetime dependency in the domain layer.
    ablation_condition :
        Which ablation configuration was active during this session.
    functionally_identifiable :
        ``True`` when ``Var(r_t) >= 0.05`` across the session, indicating
        that the autonomic arousal index has sufficient variability for
        the temperature scaling function τ(r_t) to be meaningfully fitted.
        ``False`` sessions are excluded from hypothesis H1 evaluation but
        retained in the dataset for reproducibility.
    n_epochs :
        Total number of valid EEG epochs in the session. Must be positive.
    n_channels :
        Number of EEG channels recorded. Must be positive.
    sampling_rate_hz :
        EEG acquisition rate in Hz. Must be positive.
    """

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(min_length=1)
    participant_id: str = Field(min_length=1)
    recording_date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="ISO 8601 date, format YYYY-MM-DD.",
    )
    ablation_condition: AblationCondition
    functionally_identifiable: bool
    n_epochs: int = Field(gt=0)
    n_channels: int = Field(gt=0)
    sampling_rate_hz: float = Field(gt=0.0)
