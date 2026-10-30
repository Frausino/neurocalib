# src/bci_calib/infrastructure/tracking/session_log.py
"""Atomic writer for session_log.json.

The file is written to a temporary sibling and then renamed, so a crash never
leaves a half-written log. A missing directory is an error: the caller owns the
session folder layout, and silently creating it would hide a wrong path.
"""

from __future__ import annotations

import dataclasses
import json
import os
from pathlib import Path
from typing import Final

from bci_calib.application.session_audit import SessionLogEntry

SESSION_LOG_FILENAME: Final[str] = "session_log.json"


def write_session_log(entry: SessionLogEntry, session_directory: Path) -> Path:
    """Write ``session_log.json`` inside ``session_directory`` and return its path."""
    if not session_directory.is_dir():
        raise FileNotFoundError(f"session directory not found: {session_directory}")
    destination = session_directory / SESSION_LOG_FILENAME
    temporary = destination.with_suffix(".json.tmp")
    payload = json.dumps(dataclasses.asdict(entry), indent=2, sort_keys=True)
    temporary.write_text(payload + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    return destination


def read_session_log(session_directory: Path) -> SessionLogEntry:
    """Load and validate ``session_log.json``. Invalid content raises."""
    raw = (session_directory / SESSION_LOG_FILENAME).read_text(encoding="utf-8")
    return SessionLogEntry(**json.loads(raw))
