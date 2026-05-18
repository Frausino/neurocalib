# infrastructure/tracking/mlflow_tracker.py
"""MLflow (Fluxo de Aprendizado de Máquina, MLflow) integration layer
with correlation ID (Identificador de Correlacao, CID) generation.

The correlation ID is the single thread connecting three traceability planes:

  Plane 1 — structlog contextvars: every log line emitted during a run
            automatically carries ``correlation_id`` via ``merge_contextvars``.
  Plane 2 — SQLite AuditDB: the ``run`` table is indexed by ``correlation_id``.
  Plane 3 — MLflow run tag ``bci.correlation_id``.

Correlation ID format
---------------------
    exp_{gitHash}_{ts}_{uid4}

    Field    Width  Source
    -------  -----  ---------------------------------------------------
    gitHash  7      ``git rev-parse --short=7 HEAD`` or ``"nogit"``
    ts       15     UTC timestamp, format ``YYYYMMDDTHHMMSS``
    uid4     4      First 4 hex chars of a random UUID4

Example: ``exp_a1b2c3d_20260810T143022_f4e2``

This format satisfies four requirements from the sprint spec:
- Appears identically in structlog output, audit.db, and the MLflow UI.
- Encodes the git commit, preventing version ambiguity across reruns.
- Is human-readable in log files and Git history without decoding.
- Is unique with overwhelming probability: P(collision) < 1 per 65 536
  IDs generated at the same UTC second from the same git HEAD.

References
----------
MLflow tracking API:
    https://mlflow.org/docs/latest/tracking.html
structlog contextvars:
    https://www.structlog.org/en/stable/contextvars.html
UUID4 (RFC 4122, Section 4.4):
    https://www.rfc-editor.org/rfc/rfc4122#section-4.4
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import uuid
from datetime import datetime, timezone

import mlflow
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _git_short_hash() -> str:
    """Return the 7-char short hash of HEAD, or 'nogit' on failure."""
    git_exec = shutil.which("git")
    if git_exec is None:
        return "nogit"
    try:
        # Safe: executable resolved via shutil.which(), shell=False, static args only.
        result = subprocess.run(  # noqa: S603  # nosec B603
            [git_exec, "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return "nogit"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_correlation_id() -> str:
    """Generate a unique, human-readable correlation ID.

    The function is intentionally stateless (no side effects on structlog
    context or MLflow) so it can be called freely in unit tests and utility
    scripts without requiring an active MLflow run.

    Returns
    -------
    str
        Format: ``exp_{gitHash}_{ts}_{uid4}``

    Examples
    --------
    >>> cid = generate_correlation_id()
    >>> cid.startswith("exp_")
    True
    >>> import re
    >>> bool(re.match(r"exp_([0-9a-f]{7}|nogit)_\\d{8}T\\d{6}_[0-9a-f]{4}$", cid))
    True
    """
    git_hash: str = _git_short_hash()
    ts: str = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    uid4: str = uuid.uuid4().hex[:4]
    return f"exp_{git_hash}_{ts}_{uid4}"


class MLflowTracker:
    """Thin wrapper around MLflow that propagates correlation IDs.

    Responsibilities
    ----------------
    1. Set the MLflow experiment on construction.
    2. On ``start_run()``: generate or accept a CID, bind it to structlog
       contextvars, tag the MLflow run with ``bci.correlation_id``.
    3. Expose ``log_metric()``, ``log_params()``, and ``set_tag()`` as
       thin delegates that avoid scattering ``mlflow.*`` calls across the
       codebase.
    4. On ``end_run()``: clear structlog contextvars so subsequent log lines
       from the same thread do not carry a stale CID.

    Parameters
    ----------
    experiment_name:
        MLflow experiment name. Created automatically if it does not exist.
    tracking_uri:
        Optional MLflow tracking URI. When ``None``, MLflow uses the
        ``MLFLOW_TRACKING_URI`` env var or ``./mlruns`` as the local
        file-system backend.

    Usage
    -----
    ::

        from infrastructure.tracking import configure_logging, MLflowTracker

        configure_logging()
        tracker = MLflowTracker("bci-calibration")
        run_id, cid = tracker.start_run(run_name="eegnet-pilot")
        try:
            tracker.log_params({"subject": "S1", "n_epochs": 288})
            tracker.log_metric("kappa", 0.82)
            tracker.log_metric("accuracy", 0.91)
            tracker.end_run()
        except Exception:
            tracker.end_run(status="FAILED")
            raise
    """

    def __init__(
        self,
        experiment_name: str,
        tracking_uri: str | None = None,
    ) -> None:
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self._experiment_name = experiment_name
        self._log = structlog.get_logger(__name__).bind(experiment=experiment_name)

    def start_run(
        self,
        run_name: str | None = None,
        correlation_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> tuple[str, str]:
        """Start an MLflow run and bind the CID to structlog.

        Parameters
        ----------
        run_name:
            Human-readable name shown in the MLflow UI. Optional.
        correlation_id:
            Pre-generated CID. When ``None``, ``generate_correlation_id()``
            is called. Passing an explicit CID is useful when the AuditDB
            ``run_id`` must be created before the MLflow run starts.
        tags:
            Additional key-value tags merged with the CID tag.

        Returns
        -------
        tuple[str, str]
            ``(mlflow_run_id, correlation_id)``

        Side Effects
        ------------
        - Clears any pre-existing structlog context with
          ``clear_contextvars()``.
        - Calls ``bind_contextvars(correlation_id=cid)`` so all subsequent
          log calls on this thread carry the CID automatically.
        - Sets the MLflow tag ``bci.correlation_id``.
        """
        cid: str = correlation_id or generate_correlation_id()

        # Reset then bind so no stale keys from a previous run leak through.
        clear_contextvars()
        bind_contextvars(correlation_id=cid)

        all_tags: dict[str, str] = {"bci.correlation_id": cid}
        if tags:
            all_tags.update(tags)

        active = mlflow.start_run(run_name=run_name, tags=all_tags)
        run_id: str = active.info.run_id

        self._log.info(
            "mlflow_run_started",
            run_id=run_id,
            correlation_id=cid,
        )
        return run_id, cid

    def end_run(self, status: str = "FINISHED") -> None:
        """End the active MLflow run and clear structlog context.

        Parameters
        ----------
        status:
            MLflow terminal status. Accepted values: ``"FINISHED"``,
            ``"FAILED"``, ``"KILLED"``.
        """
        mlflow.end_run(status=status)
        self._log.info("mlflow_run_ended", status=status)
        clear_contextvars()

    def log_metric(self, key: str, value: float, step: int = 0) -> None:
        """Log a scalar metric to the active MLflow run."""
        mlflow.log_metric(key, value, step=step)

    def log_params(self, params: dict[str, object]) -> None:
        """Log a parameter dictionary to the active MLflow run.

        All values are cast to ``str`` because MLflow param values are stored
        as strings internally; explicit casting prevents silent truncation of
        large integers or floats.
        """
        mlflow.log_params({k: str(v) for k, v in params.items()})

    def set_tag(self, key: str, value: str) -> None:
        """Set a single arbitrary tag on the active MLflow run."""
        mlflow.set_tag(key, value)
