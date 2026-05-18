# tests/tracking/test_audit_db.py
"""Unit tests for bci_calib.infrastructure.tracking.audit_db.

Fixture strategy
----------------
``db`` (scope=function): in-memory AuditDB for fast CRUD and view tests.
``file_db`` (scope=function): file-based AuditDB via tmp_path, required for
  WAL journal mode assertions because SQLite only supports WAL on disk.
  Each ``sqlite3.connect(":memory:")`` creates a database that uses 'memory'
  journal mode regardless of any PRAGMA setting.

Coverage
--------
Schema  : 4 user tables, 5 views, WAL journal mode (file), FK enforcement.
CRUD    : insert_experiment, insert_run, finish_run, log_metric, log_artifact.
Views   : v_run_experiment, v_run_metrics, v_failed_runs,
          v_experiment_stats, v_latest_runs (explicit timestamps).
Safety  : Invalid status value rejected by CHECK constraint.
          Duplicate experiment_id silently ignored (INSERT OR IGNORE).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from bci_calib.infrastructure.tracking.audit_db import AuditDB

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture  # type: ignore[misc]
def db() -> AuditDB:
    _db = AuditDB(":memory:")
    _db.initialise()
    return _db


@pytest.fixture  # type: ignore[misc]
def file_db(tmp_path: Path) -> AuditDB:
    _db = AuditDB(tmp_path / "audit_test.db")
    _db.initialise()
    return _db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXP_ID = "exp-eegnet-001"
_EXP_NAME = "EEGNet Pilot"
_RUN_ID = "run-00000001"
_CID = "exp_a1b2c3d_20260810T143022_f4e2"


def _seed_experiment(db: AuditDB) -> None:
    db.insert_experiment(_EXP_ID, _EXP_NAME, description="S2 unit test seed")


def _seed_run(db: AuditDB) -> None:
    _seed_experiment(db)
    db.insert_run(_RUN_ID, _EXP_ID, _CID, git_hash="a1b2c3d")


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestSchema:
    def test_four_user_tables(self, db: AuditDB) -> None:
        """sqlite_sequence (created by AUTOINCREMENT) must be excluded."""
        assert db.table_count() == 4, f"Expected 4 tables, got {db.table_count()}"

    def test_five_views(self, db: AuditDB) -> None:
        assert db.view_count() == 5, f"Expected 5 views, got {db.view_count()}"

    def test_wal_journal_mode_on_file(self, file_db: AuditDB) -> None:
        """WAL mode is only available for file-based databases.
        In-memory databases use 'memory' mode regardless of PRAGMA."""
        assert file_db.journal_mode() == "wal"

    def test_foreign_keys_enabled(self, db: AuditDB) -> None:
        with db.connection() as conn:
            row = conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1, "PRAGMA foreign_keys must be ON"

    def test_expected_table_names(self, db: AuditDB) -> None:
        with db.connection() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master"
                " WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                " ORDER BY name"
            ).fetchall()
        names = {r["name"] for r in rows}
        assert names == {"experiment", "run", "metric", "artifact"}

    def test_expected_view_names(self, db: AuditDB) -> None:
        with db.connection() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
            ).fetchall()
        names = {r["name"] for r in rows}
        assert names == {
            "v_run_experiment",
            "v_latest_runs",
            "v_run_metrics",
            "v_failed_runs",
            "v_experiment_stats",
        }


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------


class TestCRUD:
    def test_insert_experiment(self, db: AuditDB) -> None:
        _seed_experiment(db)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT name FROM experiment WHERE experiment_id = ?", (_EXP_ID,)
            ).fetchone()
        assert row["name"] == _EXP_NAME

    def test_duplicate_experiment_is_ignored(self, db: AuditDB) -> None:
        """INSERT OR IGNORE must not raise on duplicate experiment_id."""
        _seed_experiment(db)
        _seed_experiment(db)
        with db.connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM experiment").fetchone()[0]
        assert count == 1

    def test_insert_run_default_status_is_running(self, db: AuditDB) -> None:
        _seed_run(db)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT status FROM run WHERE run_id = ?", (_RUN_ID,)
            ).fetchone()
        assert row["status"] == "running"

    def test_insert_run_stores_correlation_id(self, db: AuditDB) -> None:
        _seed_run(db)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT correlation_id FROM run WHERE run_id = ?", (_RUN_ID,)
            ).fetchone()
        assert row["correlation_id"] == _CID

    def test_finish_run_sets_finished(self, db: AuditDB) -> None:
        _seed_run(db)
        db.finish_run(_RUN_ID)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT status FROM run WHERE run_id = ?", (_RUN_ID,)
            ).fetchone()
        assert row["status"] == "finished"

    def test_finish_run_failed_status(self, db: AuditDB) -> None:
        _seed_run(db)
        db.finish_run(_RUN_ID, status="failed")
        with db.connection() as conn:
            row = conn.execute(
                "SELECT status FROM run WHERE run_id = ?", (_RUN_ID,)
            ).fetchone()
        assert row["status"] == "failed"

    def test_invalid_status_raises_integrity_error(self, db: AuditDB) -> None:
        """CHECK constraint must reject status values outside the allowed set."""
        _seed_run(db)
        with pytest.raises(sqlite3.IntegrityError):
            with db.connection() as conn:
                conn.execute(
                    "UPDATE run SET status = 'invalid' WHERE run_id = ?",
                    (_RUN_ID,),
                )

    def test_log_metric_stores_value(self, db: AuditDB) -> None:
        _seed_run(db)
        db.log_metric(_RUN_ID, "kappa", 0.82)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT value FROM metric WHERE run_id = ? AND key = 'kappa'",
                (_RUN_ID,),
            ).fetchone()
        assert abs(row["value"] - 0.82) < 1e-9

    def test_log_metric_multiple_steps(self, db: AuditDB) -> None:
        _seed_run(db)
        for step, val in enumerate([0.70, 0.75, 0.82]):
            db.log_metric(_RUN_ID, "kappa", val, step=step)
        with db.connection() as conn:
            rows = conn.execute(
                "SELECT step, value FROM metric WHERE run_id = ? ORDER BY step",
                (_RUN_ID,),
            ).fetchall()
        assert len(rows) == 3
        assert abs(rows[-1]["value"] - 0.82) < 1e-9

    def test_log_artifact(self, db: AuditDB) -> None:
        _seed_run(db)
        db.log_artifact(
            _RUN_ID,
            "model",
            "models/eegnet_s1.pt",
            "application/octet-stream",
        )
        with db.connection() as conn:
            row = conn.execute(
                "SELECT path, mime_type FROM artifact WHERE run_id = ?",
                (_RUN_ID,),
            ).fetchone()
        assert row["path"] == "models/eegnet_s1.pt"
        assert row["mime_type"] == "application/octet-stream"


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------


class TestViews:
    def test_v_failed_runs_contains_failed_run(self, db: AuditDB) -> None:
        _seed_run(db)
        db.finish_run(_RUN_ID, status="failed")
        with db.connection() as conn:
            rows = conn.execute("SELECT run_id FROM v_failed_runs").fetchall()
        assert any(r["run_id"] == _RUN_ID for r in rows)

    def test_v_failed_runs_excludes_finished_run(self, db: AuditDB) -> None:
        _seed_run(db)
        db.finish_run(_RUN_ID, status="finished")
        with db.connection() as conn:
            rows = conn.execute("SELECT run_id FROM v_failed_runs").fetchall()
        assert not any(r["run_id"] == _RUN_ID for r in rows)

    def test_v_run_metrics_joins_correctly(self, db: AuditDB) -> None:
        _seed_run(db)
        db.log_metric(_RUN_ID, "accuracy", 0.91)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT correlation_id, value FROM v_run_metrics"
                " WHERE run_id = ? AND key = 'accuracy'",
                (_RUN_ID,),
            ).fetchone()
        assert row["correlation_id"] == _CID
        assert abs(row["value"] - 0.91) < 1e-9

    def test_v_experiment_stats_counts(self, db: AuditDB) -> None:
        _seed_run(db)
        db.finish_run(_RUN_ID)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT total_runs, finished_runs FROM v_experiment_stats"
                " WHERE experiment_id = ?",
                (_EXP_ID,),
            ).fetchone()
        assert row["total_runs"] == 1
        assert row["finished_runs"] == 1

    def test_v_latest_runs_ordering(self, db: AuditDB) -> None:
        """Timestamps are injected explicitly to avoid second-precision ties.

        SQLite DEFAULT (strftime('now')) has 1-second resolution. Three fast
        inserts within the same second produce identical timestamps, making
        ORDER BY started_at DESC non-deterministic for the tie cases.
        Using explicit ISO-8601 strings guarantees a deterministic ordering.
        """
        _seed_experiment(db)
        timestamps = [
            "2026-08-10T14:00:00Z",
            "2026-08-10T15:00:00Z",
            "2026-08-10T16:00:00Z",
        ]
        for i, ts in enumerate(timestamps):
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO run"
                    " (run_id, experiment_id, correlation_id, started_at)"
                    " VALUES (?, ?, ?, ?)",
                    (
                        f"run-{i:08d}",
                        _EXP_ID,
                        f"exp_a1b2c3d_2026081{i}T140000_00{i:02x}",
                        ts,
                    ),
                )
        with db.connection() as conn:
            rows = conn.execute("SELECT run_id FROM v_latest_runs").fetchall()
        # DESC by started_at: run-2 (16:00) must be first.
        assert rows[0]["run_id"] == "run-00000002"

    def test_v_run_experiment_join(self, db: AuditDB) -> None:
        _seed_run(db)
        with db.connection() as conn:
            row = conn.execute(
                "SELECT experiment_name FROM v_run_experiment WHERE run_id = ?",
                (_RUN_ID,),
            ).fetchone()
        assert row["experiment_name"] == _EXP_NAME
