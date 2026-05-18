-- logs/schema.sql
-- Versioned DDL (Data Definition Language, Linguagem de Definicao de Dados)
-- for the bci-calib audit database.
--
-- PURPOSE: This file is committed to Git so that schema evolution is tracked
-- alongside code. The binary file audit.db is listed in .gitignore and is
-- NEVER committed. Reviewers and CI pipelines inspect this SQL instead.
--
-- AUTHORITY: This file is the canonical schema definition.
--            AuditDB.initialise() in infrastructure/tracking/audit_db.py
--            embeds an identical copy as a Python string constant.
--            Both must be kept in sync. Version: bci-calib v0.2.0 / S2.
--
-- Manual usage (PowerShell):
--   Remove-Item audit.db -ErrorAction Ignore
--   sqlite3 audit.db ".read logs/schema.sql"
--   sqlite3 audit.db ".tables"   -- should show 4 tables
--   sqlite3 audit.db ".schema"   -- shows tables + views

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ════════════════════════════════════════════════════════════════════════════
-- TABLES (4)
-- ════════════════════════════════════════════════════════════════════════════

-- ── TABLE 1: experiment ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS experiment (
    experiment_id  TEXT    PRIMARY KEY,
    name           TEXT    NOT NULL UNIQUE,
    description    TEXT,
    created_at     TEXT    NOT NULL
                           DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;

-- ── TABLE 2: run ──────────────────────────────────────────────────────────
-- correlation_id format: exp_{gitHash}_{ts}_{uid4}
-- Appears identically in structlog output, this table, and the MLflow UI.
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

-- ── TABLE 3: metric ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metric (
    metric_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL REFERENCES run(run_id),
    key         TEXT    NOT NULL,
    value       REAL    NOT NULL,
    step        INTEGER NOT NULL DEFAULT 0,
    logged_at   TEXT    NOT NULL
                        DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;

-- ── TABLE 4: artifact ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS artifact (
    artifact_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT    NOT NULL REFERENCES run(run_id),
    name         TEXT    NOT NULL,
    path         TEXT    NOT NULL,
    mime_type    TEXT,
    logged_at    TEXT    NOT NULL
                         DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;

-- ════════════════════════════════════════════════════════════════════════════
-- VIEWS (5)
-- ════════════════════════════════════════════════════════════════════════════

-- ── VIEW 1: v_run_experiment ─────────────────────────────────────────────
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

-- ── VIEW 2: v_latest_runs ────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_latest_runs AS
SELECT *
FROM   v_run_experiment
ORDER  BY started_at DESC
LIMIT  50;

-- ── VIEW 3: v_run_metrics ────────────────────────────────────────────────
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

-- ── VIEW 4: v_failed_runs ────────────────────────────────────────────────
CREATE VIEW IF NOT EXISTS v_failed_runs AS
SELECT *
FROM   v_run_experiment
WHERE  status = 'failed'
ORDER  BY started_at DESC;

-- ── VIEW 5: v_experiment_stats ───────────────────────────────────────────
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

-- ════════════════════════════════════════════════════════════════════════════
-- VERIFICATION (run after applying schema)
-- ════════════════════════════════════════════════════════════════════════════
-- Expected output of: sqlite3 audit.db "SELECT type, name FROM sqlite_master ORDER BY type, name;"
--
--   table | artifact
--   table | experiment
--   table | metric
--   table | run
--   view  | v_experiment_stats
--   view  | v_failed_runs
--   view  | v_latest_runs
--   view  | v_run_experiment
--   view  | v_run_metrics
