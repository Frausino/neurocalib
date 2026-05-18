# tests/tracking/test_mlflow_tracker.py
"""Unit tests for infrastructure.tracking.mlflow_tracker.

MLflowTracker integration tests (start_run / end_run) are NOT included here
because they require a live MLflow tracking server. They belong in a separate
integration test suite triggered only in environments with MLFLOW_TRACKING_URI
set. See tests/integration/test_mlflow_tracker_integration.py (S3+).

Coverage targets (pure unit tests, no network)
----------------
generate_correlation_id : format regex, uniqueness, prefix, ts/uid4 ranges.
_git_short_hash         : return type, length constraint.
"""

from __future__ import annotations

import re

import pytest

from bci_calib.infrastructure.tracking.mlflow_tracker import (
    _git_short_hash,
    generate_correlation_id,
)

# ---------------------------------------------------------------------------
# Regex pattern for the expected correlation ID format:
#   exp_{gitHash}_{ts}_{uid4}
#   gitHash : 7-char hex string OR literal "nogit"
#   ts      : 15-char UTC timestamp YYYYMMDDTHHMMSS
#   uid4    : 4-char hex string
# ---------------------------------------------------------------------------
_CID_PATTERN: re.Pattern[str] = re.compile(
    r"^exp_([0-9a-f]{7}|nogit)_\d{8}T\d{6}_[0-9a-f]{4}$"
)


class TestGenerateCorrelationId:
    def test_format_matches_pattern(self) -> None:
        cid = generate_correlation_id()
        assert _CID_PATTERN.match(cid), (
            f"Correlation ID {cid!r} does not match expected pattern "
            f"{_CID_PATTERN.pattern!r}"
        )

    def test_prefix_is_exp(self) -> None:
        assert generate_correlation_id().startswith("exp_")

    def test_has_exactly_three_underscored_segments_after_exp(self) -> None:
        # Split on "exp_" then count remaining underscore segments
        cid = generate_correlation_id()
        suffix = cid[len("exp_") :]
        parts = suffix.split("_")
        assert (
            len(parts) == 3
        ), f"Expected 3 segments after 'exp_', got {len(parts)}: {parts}"

    def test_uniqueness_over_ten_consecutive_calls(self) -> None:
        """P(collision) < 1/65536 per pair; 10 calls should always be unique."""
        ids = [generate_correlation_id() for _ in range(10)]
        assert len(set(ids)) == len(
            ids
        ), f"Collision detected among {len(ids)} consecutive IDs"

    def test_uid4_segment_is_four_hex_chars(self) -> None:
        uid4 = generate_correlation_id().split("_")[-1]
        assert len(uid4) == 4
        assert all(c in "0123456789abcdef" for c in uid4)

    def test_ts_segment_is_valid_timestamp(self) -> None:
        from datetime import datetime, timezone

        ts_str = generate_correlation_id().split("_")[2]
        # Must parse without exception as %Y%m%dT%H%M%S
        dt = datetime.strptime(ts_str, "%Y%m%dT%H%M%S")
        # Timestamp must be recent (within 60 s of call)
        now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        delta = abs((now - dt).total_seconds())
        assert delta < 60, f"Timestamp {ts_str!r} is {delta:.1f}s away from now"


class TestGitShortHash:
    def test_returns_string(self) -> None:
        assert isinstance(_git_short_hash(), str)

    def test_is_seven_hex_chars_or_nogit(self) -> None:
        h = _git_short_hash()
        if h == "nogit":
            return
        assert len(h) == 7, f"Expected 7-char hash, got {len(h)}: {h!r}"
        assert all(
            c in "0123456789abcdef" for c in h
        ), f"Hash {h!r} contains non-hex characters"

    def test_nogit_fallback_is_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Simulate subprocess failure to verify 'nogit' fallback."""
        import subprocess  # nosec B404

        def _raise(*_: object, **__: object) -> None:
            raise subprocess.CalledProcessError(128, "git")

        monkeypatch.setattr(subprocess, "run", _raise)
        assert _git_short_hash() == "nogit"
