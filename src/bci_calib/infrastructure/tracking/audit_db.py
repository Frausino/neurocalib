# infrastructure/tracking/audit_db.py
"""SQLite (Banco de Dados Estruturado, BDE) audit database for experiment traceability.

Schema
------
4 tables : experiment, run, metric, artifact
5 views  : v_run_experiment, v_latest_runs, v_run_metrics,
           v_failed_runs, v_experiment_stats

PRAGMA WAL (Write-Ahead Logging, Registro de Escrita Antecipada) is enabled
so concurrent readers are never blocked by an ongoing write. This is critical
when the calibration pipeline writes metrics while a separate monitoring
process queries the views. With WAL, readers see a consistent snapshot at
the last committed checkpoint without acquiring a write lock [1].

PRAGMA STRICT tables enforce column-level type checking (available since
SQLite 3.37, released November 2021) [2]. STRICT prevents silent type
coercion that could corrupt metric values (e.g. storing TEXT in a REAL column).

Design decisions
----------------
- ``sqlite3.Row`` as row_factory allows dict-like column access by name,
  simplifying view queries and test assertions without an ORM dependency.
- The ``connection()`` context manager commits on clean exit and rolls back
  on any exception, providing automatic transactional safety.
- ``INSERT OR IGNORE`` on experiment prevents duplicate-key errors when the
  same experiment name is registered across pipeline restarts.
- ``CHECK (status IN (...))`` on run.status is enforced at the DB layer,
  not only at the application layer, following the defence-in-depth principle
  from CIS Controls v8 [3].
- For ``:memory:`` databases, a single shared connection is kept alive for
  the object lifetime because each ``sqlite3.connect(":memory:")`` creates an
  independent, empty database. See ``__init__`` docstring for details.

References
----------
[1] SQLite WAL mode: https://www.sqlite.org/wal.html
[2] SQLite STRICT tables: https://www.sqlite.org/stricttables.html
[3] CIS Controls v8, Control 3 (Data Protection):
    https://www.cisecurity.org/controls/v8
[4] sqlite3 stdlib: https://docs.python.org/3.11/library/sqlite3.html
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

# ---------------------------------------------------------------------------
# DDL: Tables
# ---------------------------------------------------------------------------
_DDL_TABLES: str = """\
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- TABLE 1: experiment
CREATE TABLE IF NOT EXISTS experiment (
    experiment_id  TEXT    PRIMARY KEY,
    name           TEXT    NOT NULL UNIQUE,
    description    TEXT,
    created_at     TEXT    NOT NULL
                           DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;

-- TABLE 2: run
-- correlation_id links this row to structlog context and the MLflow tag
-- "bci.correlation_id", forming the three-plane traceability chain.
CREATE TABLE IF NOT EXISTS run (
    run_id         TEXT    PRIMARY KEY,
    experiment_id  TEXT    NOT NULL REFERENCES experiment(experiment_id),
    correlation_id TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'running'
                           CHECK (status IN ('running', 'finished', 'failed')),
    started_at     TEXT    NOT NULL
                           DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    finished_at    TEXT,
    git_hash       TEXT,
    python_env     TEXT
) STRICT;

-- TABLE 3: metric
-- Scalar metrics (kappa, accuracy, etc.) keyed by (run_id, key, step).
CREATE TABLE IF NOT EXISTS metric (
    metric_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL REFERENCES run(run_id),
    key         TEXT    NOT NULL,
    value       REAL    NOT NULL,
    step        INTEGER NOT NULL DEFAULT 0,
    logged_at   TEXT    NOT NULL
                        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;

-- TABLE 4: artifact
-- File paths for model checkpoints, figures, and reports produced by a run.
CREATE TABLE IF NOT EXISTS artifact (
    artifact_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT    NOT NULL REFERENCES run(run_id),
    name         TEXT    NOT NULL,
    path         TEXT    NOT NULL,
    mime_type    TEXT,
    logged_at    TEXT    NOT NULL
                         DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;
"""

# ---------------------------------------------------------------------------
# DDL: Views
# ---------------------------------------------------------------------------
_DDL_VIEWS: str = """\
-- VIEW 1: v_run_experiment
-- Flat join of run + experiment. Primary entry point for most queries.
CREATE VIEW IF NOT EXISTS v_run_experiment AS
SELECT
    r.run_id,
    r.correlation_id,
    r.status,
    r.started_at,
    r.finished_at,
    r.git_hash,
    r.python_env,
    e.experiment_id,
    e.name           AS experiment_name,
    e.description
FROM run         r
JOIN experiment  e USING (experiment_id);

-- VIEW 2: v_latest_runs
-- Most recent 50 runs across all experiments. Used by the weekly audit.
CREATE VIEW IF NOT EXISTS v_latest_runs AS
SELECT *
FROM   v_run_experiment
ORDER  BY started_at DESC
LIMIT  50;

-- VIEW 3: v_run_metrics
-- All scalar metrics joined with their parent run context.
CREATE VIEW IF NOT EXISTS v_run_metrics AS
SELECT
    m.run_id,
    m.key,
    m.value,
    m.step,
    m.logged_at,
    r.correlation_id,
    r.status,
    r.started_at
FROM metric  m
JOIN run     r USING (run_id);

-- VIEW 4: v_failed_runs
-- Subset of v_run_experiment where status = 'failed'.
CREATE VIEW IF NOT EXISTS v_failed_runs AS
SELECT *
FROM   v_run_experiment
WHERE  status = 'failed'
ORDER  BY started_at DESC;

-- VIEW 5: v_experiment_stats
-- Aggregate counts per experiment.
CREATE VIEW IF NOT EXISTS v_experiment_stats AS
SELECT
    e.experiment_id,
    e.name                           AS experiment_name,
    COUNT(r.run_id)                  AS total_runs,
    SUM(r.status = 'finished')       AS finished_runs,
    SUM(r.status = 'failed')         AS failed_runs,
    SUM(r.status = 'running')        AS running_runs,
    MIN(r.started_at)                AS first_run_at,
    MAX(r.started_at)                AS last_run_at
FROM experiment   e
LEFT JOIN run     r USING (experiment_id)
GROUP BY e.experiment_id, e.name;
"""


# ---------------------------------------------------------------------------
# AuditDB
# ---------------------------------------------------------------------------


class AuditDB:
    """Manages the SQLite audit database with WAL mode.

    Parameters
    ----------
    db_path:
        Filesystem path for the SQLite file. Defaults to ``audit.db`` in the
        current working directory. Pass ``":memory:"`` for in-process testing.

    Notes on ``:memory:``
    ---------------------
    Each call to ``sqlite3.connect(":memory:")`` creates an independent, empty
    database scoped to that connection object. The per-call connection pattern
    used for file databases would therefore open a different (empty) database
    on every ``connection()`` call, making tables created in ``initialise()``
    invisible to all subsequent calls. To prevent this, when
    ``db_path == ":memory:"`` the class keeps a single shared connection alive
    for the object lifetime. ``__del__`` closes it on garbage collection.

    Usage
    -----
    One-time initialisation (idempotent)::

        db = AuditDB("audit.db")
        db.initialise()

    Logging a calibration run::

        db.insert_experiment("exp-eegnet-s1", "EEGNet Sub-PIC 1")
        db.insert_run(run_id, "exp-eegnet-s1", correlation_id, git_hash="a1b2c3d")
        db.log_metric(run_id, "kappa", 0.82)
        db.log_artifact(
            run_id, "model", "models/eegnet_s1.pt", "application/octet-stream"
        )
        db.finish_run(run_id)

    Direct SQL access::

        with db.connection() as conn:
            rows = conn.execute("SELECT * FROM v_experiment_stats").fetchall()
    """

    def __init__(self, db_path: str | Path = "audit.db") -> None:
        self._is_memory: bool = str(db_path) == ":memory:"
        self._path: str | Path = db_path if self._is_memory else Path(db_path)
        self._memory_conn: sqlite3.Connection | None = None
        if self._is_memory:
            self._memory_conn = sqlite3.connect(
                ":memory:",
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            self._memory_conn.row_factory = sqlite3.Row

    def __del__(self) -> None:
        if self._memory_conn is not None:
            self._memory_conn.close()
            self._memory_conn = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialise(self) -> None:
        """Create tables and views if they do not exist. Idempotent."""
        with self.connection() as conn:
            conn.executescript(_DDL_TABLES)
            conn.executescript(_DDL_VIEWS)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a connection with ``sqlite3.Row`` factory.

        For file databases: opens a fresh WAL-enabled connection per call and
        closes on exit, committing on success and rolling back on exception.

        For ``:memory:`` databases: yields the single shared connection created
        in ``__init__``. Commit/rollback semantics are preserved; the
        connection is never closed here.

        Yields
        ------
        sqlite3.Connection
            Ready-to-use connection with ``row_factory = sqlite3.Row``.
        """
        if self._is_memory:
            assert self._memory_conn is not None
            try:
                yield self._memory_conn
                self._memory_conn.commit()
            except Exception:
                self._memory_conn.rollback()
                raise
            return

        conn = sqlite3.connect(
            self._path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def insert_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str | None = None,
    ) -> None:
        """Register an experiment. ``INSERT OR IGNORE`` on duplicate name."""
        with self.connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO experiment (experiment_id, name, description)"
                " VALUES (?, ?, ?)",
                (experiment_id, name, description),
            )

    def insert_run(
        self,
        run_id: str,
        experiment_id: str,
        correlation_id: str,
        git_hash: str | None = None,
        python_env: str | None = None,
    ) -> None:
        """Register a new run with status='running'."""
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO run"
                " (run_id, experiment_id, correlation_id, git_hash, python_env)"
                " VALUES (?, ?, ?, ?, ?)",
                (run_id, experiment_id, correlation_id, git_hash, python_env),
            )

    def finish_run(self, run_id: str, status: str = "finished") -> None:
        """Set run status and record finish timestamp."""
        with self.connection() as conn:
            conn.execute(
                "UPDATE run"
                " SET status = ?,"
                "     finished_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
                " WHERE run_id = ?",
                (status, run_id),
            )

    def log_metric(self, run_id: str, key: str, value: float, step: int = 0) -> None:
        """Append a scalar metric to the metric table."""
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO metric (run_id, key, value, step) VALUES (?, ?, ?, ?)",
                (run_id, key, value, step),
            )

    def log_artifact(
        self,
        run_id: str,
        name: str,
        path: str,
        mime_type: str | None = None,
    ) -> None:
        """Record an artifact path produced by a run."""
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO artifact (run_id, name, path, mime_type)"
                " VALUES (?, ?, ?, ?)",
                (run_id, name, path, mime_type),
            )

    # ------------------------------------------------------------------
    # Read helpers (used by tests and weekly audit)
    # ------------------------------------------------------------------

    def table_count(self) -> int:
        """Return the number of user tables. Expected: 4."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master"
                " WHERE type = 'table'"
                " AND name NOT LIKE 'sqlite_%'"
            ).fetchone()
        return int(row[0]) if row else 0

    def view_count(self) -> int:
        """Return the number of views. Expected: 5."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'view'"
            ).fetchone()
        return int(row[0]) if row else 0

    def journal_mode(self) -> str:
        """Return the active journal mode. Expected: 'wal'."""
        with self.connection() as conn:
            row = conn.execute("PRAGMA journal_mode").fetchone()
        return str(row[0]) if row else "unknown"
