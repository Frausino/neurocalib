# src/bci_calib/domain/ports.py
"""Domain ports (Portas de Domínio, PD) — abstract service interfaces.

Ports are the boundary between the domain layer and the outside world.
They define WHAT the domain needs from infrastructure, not HOW it is done.
Concrete implementations live in the infrastructure layer and are injected
at runtime, keeping domain logic free of I/O and framework dependencies.

All protocols use ``@runtime_checkable`` so that ``isinstance()`` checks
work in tests and in dependency injection validation at startup.

``@runtime_checkable`` caveat
------------------------------
``isinstance(obj, Protocol)`` only verifies that the object has the required
method names. It does NOT check signatures or return types. Full type safety
requires mypy with ``--strict``, which is enforced in CI.

Architectural constraint
------------------------
Zero external dependencies beyond stdlib and Pydantic.
Any import of mne, numpy, torch, or scipy here is an architectural error.

On array data at domain boundaries
------------------------------------
``MIClassifier`` and ``EEGSource`` work with ``Epoch`` (metadata only).
Raw signal arrays are opaque to the domain. Concrete implementations
in the infrastructure layer resolve epoch metadata to numpy arrays
internally. This keeps the domain pure while allowing infrastructure
adapters to use any array library.

References
----------
Martin, R. C. — Clean Architecture, Chapter 18 (Boundary Anatomy).
van Vliet, B. — Ports and Adapters (Hexagonal Architecture), 2005.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from bci_calib.domain.calibration import CalibrationParams
from bci_calib.domain.entities import Epoch, RRInterval, SessionMetadata


@runtime_checkable
class EEGSource(Protocol):
    """Provider of EEG epoch metadata for a recording session.

    Concrete implementations adapt external sources (MOABB, MNE raw files,
    synthetic generators) to the domain's ``Epoch`` type. Raw signal arrays
    are not part of the protocol; they are an infrastructure concern.

    Methods
    -------
    load_epochs :
        Return all valid ``Epoch`` instances for the given session.
        The returned sequence preserves trial order as recorded.
    """

    def load_epochs(self, session: SessionMetadata) -> Sequence[Epoch]:
        """Load epoch metadata for all valid trials in ``session``.

        Parameters
        ----------
        session :
            Session descriptor identifying the participant, date, and
            ablation condition.

        Returns
        -------
        Sequence[Epoch]
            Ordered sequence of epoch metadata. Empty if no valid trials.
        """
        ...


@runtime_checkable
class HRVSource(Protocol):
    """Provider of RR interval sequences for a recording session.

    Concrete implementations read RR intervals from ECG/PPG hardware logs,
    WFDB files, or synthetic HRV generators.

    Methods
    -------
    load_rr_intervals :
        Return all RR intervals for the given session in temporal order.
    """

    def load_rr_intervals(self, session: SessionMetadata) -> Sequence[RRInterval]:
        """Load RR intervals for all cardiac beats in ``session``.

        Parameters
        ----------
        session :
            Session descriptor. Used to locate the HRV data file or stream.

        Returns
        -------
        Sequence[RRInterval]
            Temporally ordered sequence of RR intervals. Empty if no
            cardiac data is available for the session.
        """
        ...


@runtime_checkable
class MIClassifier(Protocol):
    """Motor imagery (Imagética Motora, IM) classifier interface.

    A classifier learns to distinguish motor imagery classes from EEG
    epochs. The training data source (numpy arrays, MOABB datasets) is
    resolved by the concrete implementation using the session metadata
    as a key into the infrastructure layer.

    Methods
    -------
    fit :
        Train the classifier on all epochs from the given session.
    predict_proba :
        Return per-class probability vector for a single epoch.
    predict :
        Return the most probable class label for a single epoch.
    """

    def fit(self, session: SessionMetadata) -> None:
        """Train the classifier using all epochs from ``session``.

        Parameters
        ----------
        session :
            Session descriptor. The concrete implementation uses this
            to locate and load the raw EEG signal arrays.
        """
        ...

    def predict_proba(self, epoch: Epoch) -> Sequence[float]:
        """Return class probability vector for a single ``epoch``.

        Parameters
        ----------
        epoch :
            Epoch metadata identifying the trial. The implementation
            resolves the raw signal data from the epoch descriptor.

        Returns
        -------
        Sequence[float]
            Probability vector of length ``n_classes``. Values sum to 1.0.
            Index corresponds to class label (0-based).
        """
        ...

    def predict(self, epoch: Epoch) -> int:
        """Return the predicted class label for a single ``epoch``.

        Parameters
        ----------
        epoch :
            Epoch metadata identifying the trial.

        Returns
        -------
        int
            Predicted class label (0-based). Equivalent to
            ``argmax(predict_proba(epoch))``.
        """
        ...


@runtime_checkable
class Calibrator(Protocol):
    """Temperature scaling calibrator interface.

    A calibrator maps the autonomic arousal index r_t to a calibration
    temperature τ, and fits the parameters of that mapping from empirical
    data. The core computation is ``compute_tau`` from
    ``bci_calib.domain.calibration``.

    Methods
    -------
    compute_temperature :
        Evaluate τ(r_t) for a given arousal level and parameter set.
    fit_params :
        Estimate ``CalibrationParams`` from observed arousal indices
        and ground-truth labels.
    """

    def compute_temperature(self, r_t: float, params: CalibrationParams) -> float:
        """Compute calibration temperature τ(r_t).

        Parameters
        ----------
        r_t :
            Autonomic arousal index derived from HRV (RMSSD normalizado).
        params :
            Frozen parameter set for the scaling function.

        Returns
        -------
        float
            Temperature τ(r_t) = tau_min + (tau_max − tau_min) · σ(a·r_t+b).
        """
        ...

    def fit_params(
        self,
        arousal_indices: Sequence[float],
        labels: Sequence[int],
    ) -> CalibrationParams:
        """Estimate ``CalibrationParams`` from empirical observations.

        Parameters
        ----------
        arousal_indices :
            Sequence of r_t values observed during a calibration session.
            Must be non-empty and have the same length as ``labels``.
        labels :
            Ground-truth class labels aligned with ``arousal_indices``.

        Returns
        -------
        CalibrationParams
            Fitted frozen parameter set minimising the NLL objective
            as in Guo et al. 2017 (arXiv:1706.04599).
        """
        ...
