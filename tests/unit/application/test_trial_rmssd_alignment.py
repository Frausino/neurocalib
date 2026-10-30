# tests/unit/application/test_trial_rmssd_alignment.py
"""Tests for bci_calib.application.trial_rmssd_alignment.

The two Guia Mestre S4 gates live here: ``test_causal_alignment`` and
``test_no_lookahead``. A failing ``test_no_lookahead`` blocks the whole phase.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from bci_calib.application.trial_rmssd_alignment import (
    FUNCTIONAL_IDENTIFIABILITY_MIN_VARIANCE,
    RmssdAlignmentError,
    assign_rmssd_to_trials,
    compute_r_t,
    compute_r_t_variance_per_session,
    compute_rmssd_indices,
)

DELTA_T_S = 6.07
NO_LAG_S = 0.0
SAFETY_LAG_S = 2.0
RMSSD_SERIES = (10.0, 20.0, 30.0, 40.0, 50.0)


def _align(onsets: list[float], lag: float = NO_LAG_S) -> tuple[float, ...]:
    return assign_rmssd_to_trials(
        onsets, RMSSD_SERIES, delta_t_s=DELTA_T_S, safety_lag_s=lag
    )


class TestCausalAlignment:
    def test_causal_alignment(self) -> None:
        onsets = [0.0, 6.06, 6.07, 12.0, 18.5, 24.5]
        assert _align(onsets) == (10.0, 10.0, 20.0, 20.0, 40.0, 50.0)

    def test_safety_lag_moves_reference_time_back(self) -> None:
        assert _align([8.0], lag=NO_LAG_S) == (20.0,)
        assert _align([8.0], lag=SAFETY_LAG_S) == (10.0,)

    def test_onset_order_does_not_matter(self) -> None:
        assert _align([18.5, 0.0, 6.07]) == (40.0, 10.0, 20.0)

    def test_empty_trial_list_gives_empty_result(self) -> None:
        assert _align([]) == ()


class TestNoLookahead:
    def test_no_lookahead_where_round_would_leak(self) -> None:
        onset_closer_to_next_sample = 0.6 * DELTA_T_S
        assert round(onset_closer_to_next_sample / DELTA_T_S) == 1
        assert _align([onset_closer_to_next_sample]) == (RMSSD_SERIES[0],)

    @given(
        onset=st.floats(min_value=0.0, max_value=30.0, allow_nan=False),
        lag=st.floats(min_value=0.0, max_value=2.0, allow_nan=False),
    )
    def test_used_sample_is_never_later_than_reference_time(
        self, onset: float, lag: float
    ) -> None:
        reference_time = onset - lag
        if reference_time < 0.0:
            return
        index = compute_rmssd_indices(
            [onset], series_length=10, delta_t_s=DELTA_T_S, safety_lag_s=lag
        )[0]
        assert index * DELTA_T_S <= reference_time + 1e-9
        assert reference_time - index * DELTA_T_S < DELTA_T_S + 1e-9

    @given(
        onsets=st.lists(
            st.floats(min_value=0.0, max_value=30.0, allow_nan=False),
            min_size=2,
            max_size=20,
        )
    )
    def test_indices_are_monotone_in_onset(self, onsets: list[float]) -> None:
        ordered = sorted(onsets)
        indices = compute_rmssd_indices(
            ordered, series_length=10, delta_t_s=DELTA_T_S, safety_lag_s=NO_LAG_S
        )
        assert list(indices) == sorted(indices)


class TestFutureSamplesCannotChangePast:
    @given(
        series=st.lists(
            st.floats(min_value=1.0, max_value=200.0, allow_nan=False),
            min_size=8,
            max_size=8,
        ),
        onsets=st.lists(
            st.floats(min_value=0.0, max_value=40.0, allow_nan=False),
            min_size=1,
            max_size=15,
        ),
        cutoff_s=st.floats(min_value=0.0, max_value=40.0, allow_nan=False),
    )
    def test_corrupting_samples_after_cutoff_keeps_earlier_trials_identical(
        self, series: list[float], onsets: list[float], cutoff_s: float
    ) -> None:
        tolerance_s = 1e-9
        corrupted = [
            1e9 if index * DELTA_T_S > cutoff_s + tolerance_s else value
            for index, value in enumerate(series)
        ]
        original = assign_rmssd_to_trials(
            onsets, series, delta_t_s=DELTA_T_S, safety_lag_s=NO_LAG_S
        )
        altered = assign_rmssd_to_trials(
            onsets, corrupted, delta_t_s=DELTA_T_S, safety_lag_s=NO_LAG_S
        )
        for onset, before, after in zip(onsets, original, altered, strict=True):
            if onset <= cutoff_s:
                assert before == after

    def test_explicit_future_corruption_example(self) -> None:
        corrupted = (10.0, 20.0, 9999.0, 9999.0, 9999.0)
        aligned = assign_rmssd_to_trials(
            [0.0, 6.5], corrupted, delta_t_s=DELTA_T_S, safety_lag_s=NO_LAG_S
        )
        assert aligned == (10.0, 20.0)


class TestAlignmentErrors:
    def test_reference_time_before_first_sample_raises(self) -> None:
        with pytest.raises(RmssdAlignmentError, match="precedes"):
            _align([1.0], lag=SAFETY_LAG_S)

    def test_trial_after_end_of_series_raises(self) -> None:
        with pytest.raises(RmssdAlignmentError, match="needs index"):
            _align([31.0])

    @pytest.mark.parametrize("delta_t", [0.0, -1.0, math.inf, math.nan])
    def test_invalid_delta_t_raises(self, delta_t: float) -> None:
        with pytest.raises(ValueError, match="delta_t_s"):
            assign_rmssd_to_trials(
                [1.0], RMSSD_SERIES, delta_t_s=delta_t, safety_lag_s=NO_LAG_S
            )

    @pytest.mark.parametrize("lag", [-0.1, math.inf, math.nan])
    def test_invalid_safety_lag_raises(self, lag: float) -> None:
        with pytest.raises(ValueError, match="safety_lag_s"):
            assign_rmssd_to_trials(
                [1.0], RMSSD_SERIES, delta_t_s=DELTA_T_S, safety_lag_s=lag
            )

    def test_non_finite_onset_raises(self) -> None:
        with pytest.raises(RmssdAlignmentError):
            _align([math.nan])


class TestNonFiniteInputsFailClosed:
    @pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
    def test_non_finite_rmssd_sample_raises(self, bad: float) -> None:
        with pytest.raises(ValueError, match=r"rmssd_smooth\[1\]"):
            assign_rmssd_to_trials(
                [0.0],
                (10.0, bad, 30.0),
                delta_t_s=DELTA_T_S,
                safety_lag_s=NO_LAG_S,
            )

    @pytest.mark.parametrize("bad", [math.nan, math.inf])
    def test_non_finite_train_mean_raises(self, bad: float) -> None:
        with pytest.raises(ValueError, match="train_mean"):
            compute_r_t([1.0], train_mean=bad, train_std=1.0)

    def test_non_finite_rmssd_value_raises(self) -> None:
        with pytest.raises(ValueError, match="rmssd_values"):
            compute_r_t([1.0, math.nan], train_mean=0.0, train_std=1.0)

    def test_overflowing_r_t_raises(self) -> None:
        with pytest.raises(ValueError, match="r_t"):
            compute_r_t([1e308], train_mean=-1e308, train_std=1e-300)

    def test_non_finite_r_t_in_session_raises(self) -> None:
        with pytest.raises(ValueError, match="session 's1'"):
            compute_r_t_variance_per_session({"s1": [0.1, math.nan]})


class TestArousalIndex:
    def test_r_t_is_z_score_against_training_statistics(self) -> None:
        r_t = compute_r_t([30.0, 40.0, 20.0], train_mean=30.0, train_std=10.0)
        assert r_t == (0.0, 1.0, -1.0)

    @pytest.mark.parametrize("train_std", [0.0, -1.0, math.nan])
    def test_invalid_training_std_raises(self, train_std: float) -> None:
        with pytest.raises(ValueError, match="train_std"):
            compute_r_t([1.0], train_mean=0.0, train_std=train_std)


class TestSessionIdentifiability:
    @staticmethod
    def _two_values_with_variance(variance: float) -> list[float]:
        return [0.0, math.sqrt(2.0 * variance)]

    def test_constant_r_t_is_not_identifiable(self) -> None:
        result = compute_r_t_variance_per_session({"s1": [0.3, 0.3, 0.3]})["s1"]
        assert result.variance == 0.0
        assert result.functionally_identifiable is False

    def test_variance_is_sample_variance(self) -> None:
        result = compute_r_t_variance_per_session({"s1": [1.0, 2.0, 3.0, 4.0]})["s1"]
        assert result.variance == pytest.approx(5.0 / 3.0)

    def test_threshold_separates_sessions(self) -> None:
        below = self._two_values_with_variance(
            FUNCTIONAL_IDENTIFIABILITY_MIN_VARIANCE - 0.001
        )
        above = self._two_values_with_variance(
            FUNCTIONAL_IDENTIFIABILITY_MIN_VARIANCE + 0.001
        )
        results = compute_r_t_variance_per_session({"low": below, "high": above})
        assert results["low"].functionally_identifiable is False
        assert results["high"].functionally_identifiable is True

    def test_each_session_is_reported_under_its_id(self) -> None:
        results = compute_r_t_variance_per_session({"a": [0.0, 1.0], "b": [0.0, 2.0]})
        assert {key: value.session_id for key, value in results.items()} == {
            "a": "a",
            "b": "b",
        }

    def test_session_with_one_value_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            compute_r_t_variance_per_session({"s1": [0.5]})

    def test_no_sessions_gives_empty_result(self) -> None:
        assert compute_r_t_variance_per_session({}) == {}
