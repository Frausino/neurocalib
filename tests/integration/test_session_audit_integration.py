# tests/integration/test_session_audit_integration.py
"""AuditDB and session_log.json receive what the pre-registration promises."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bci_calib.application.session_audit import (
    SESSION_LOG_ARTIFACT_NAME,
    SessionLogEntry,
    build_session_log_entry,
    record_session_audit,
)
from bci_calib.application.trial_rmssd_alignment import (
    compute_r_t,
    compute_r_t_variance_per_session,
)
from bci_calib.domain.calibration import CalibrationParams
from bci_calib.infrastructure.tracking.audit_db import AuditDB
from bci_calib.infrastructure.tracking.session_log import (
    SESSION_LOG_FILENAME,
    read_session_log,
    write_session_log,
)

RUN_ID = "run-s4"


@pytest.fixture
def audit_db() -> AuditDB:
    database = AuditDB(":memory:")
    database.initialise()
    database.insert_experiment("exp-1", "s4-session-audit")
    database.insert_run(RUN_ID, "exp-1", "exp_abc1234_20261011T210000_a1b2")
    return database


def _stored_metrics(database: AuditDB) -> dict[str, float]:
    with database.connection() as connection:
        rows = connection.execute(
            "SELECT key, value FROM metric WHERE run_id = ?", (RUN_ID,)
        ).fetchall()
    return {key: value for key, value in rows}


def test_flat_session_is_flagged_and_stored(audit_db: AuditDB, tmp_path: Path) -> None:
    r_t = compute_r_t([40.0, 40.0, 40.1, 40.0], train_mean=40.0, train_std=10.0)
    result = compute_r_t_variance_per_session({"s-flat": r_t})["s-flat"]
    entry = build_session_log_entry(result)
    log_path = write_session_log(entry, tmp_path)
    record_session_audit(audit_db, RUN_ID, entry, log_path)
    stored = _stored_metrics(audit_db)
    assert stored["functional_identifiable"] == 0.0
    assert stored["var_r_t"] == pytest.approx(result.variance)


def test_varied_session_with_fit_stores_all_flags(
    audit_db: AuditDB, tmp_path: Path
) -> None:
    r_t = compute_r_t([20.0, 60.0, 30.0, 70.0], train_mean=45.0, train_std=20.0)
    result = compute_r_t_variance_per_session({"s-vary": r_t})["s-vary"]
    entry = build_session_log_entry(result, CalibrationParams(tau_max=2.5, a=-1.5))
    record_session_audit(audit_db, RUN_ID, entry, write_session_log(entry, tmp_path))
    assert _stored_metrics(audit_db) == {
        "var_r_t": pytest.approx(result.variance),
        "functional_identifiable": 1.0,
        "dynamic_effect_degenerate": 0.0,
        "tau_max_degenerate": 0.0,
    }


def test_metrics_for_unknown_run_are_rejected(
    audit_db: AuditDB, tmp_path: Path
) -> None:
    entry = SessionLogEntry("s1", 0.2, True)
    with pytest.raises(Exception, match="FOREIGN KEY"):
        record_session_audit(
            audit_db, "run-missing", entry, write_session_log(entry, tmp_path)
        )


def test_run_resolves_to_exactly_one_session(audit_db: AuditDB, tmp_path: Path) -> None:
    entry = SessionLogEntry("sub-01_ses-02", 0.2, True)
    record_session_audit(audit_db, RUN_ID, entry, write_session_log(entry, tmp_path))
    with audit_db.connection() as connection:
        rows = connection.execute(
            "SELECT path FROM artifact WHERE run_id = ? AND name = ?",
            (RUN_ID, SESSION_LOG_ARTIFACT_NAME),
        ).fetchall()
    assert len(rows) == 1
    session_directory = Path(rows[0][0]).parent
    assert read_session_log(session_directory).session_id == "sub-01_ses-02"


def test_session_log_round_trip(tmp_path: Path) -> None:
    entry = SessionLogEntry("s1", 0.12, True, False, True)
    path = write_session_log(entry, tmp_path)
    assert path == tmp_path / SESSION_LOG_FILENAME
    assert read_session_log(tmp_path) == entry
    assert json.loads(path.read_text(encoding="utf-8"))["functional_identifiable"]


def test_session_log_has_no_leftover_temporary_file(tmp_path: Path) -> None:
    write_session_log(SessionLogEntry("s1", 0.12, True), tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == [SESSION_LOG_FILENAME]


def test_missing_directory_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        write_session_log(SessionLogEntry("s1", 0.1, True), tmp_path / "absent")


def test_corrupted_log_is_rejected(tmp_path: Path) -> None:
    (tmp_path / SESSION_LOG_FILENAME).write_text('{"session_id": "s1"}', "utf-8")
    with pytest.raises(ValidationError):
        read_session_log(tmp_path)
