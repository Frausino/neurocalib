# tests/unit/domain/test_calibration.py
"""Unit tests for bci_calib.domain.calibration.

Structure
---------
TestStableSigmoid     : deterministic + Hypothesis (500 exemplos)
TestComputeTau        : GO/NO-GO, assintótica, monotonia, valor em 0
TestCalibrationParams : frozen, defaults, Hypothesis (500 exemplos)

Floating-point saturation
--------------------------
For |a·r_t + b| >> 1, _stable_sigmoid saturates to 0.0 or 1.0 exactly.
Tests that assert strict bounds use a moderate range where saturation
does not occur. Tests that check asymptotic behavior use large |r_t|
and assert approximate equality to the boundary value.

Monotonia (a > 0, tau_min < tau_max)
--------------------------------------
τ(r_t) = tau_min + (tau_max − tau_min) · σ(a · r_t + b)
       = tau_min + positive_range · increasing_sigmoid
→ τ is STRICTLY INCREASING in r_t when a > 0 and tau_min < tau_max.

Coverage target: 100% de domain/calibration.py.
"""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from bci_calib.domain.calibration import (
    CalibrationParams,
    _stable_sigmoid,
    compute_tau,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_finite_floats = st.floats(allow_nan=False, allow_infinity=False)
_moderate_floats = st.floats(
    min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False
)
_nonzero_moderate = _moderate_floats.filter(lambda x: x != 0.0)

# Bounded r_t AND b to prevent sigmoid saturation in bound tests:
# ensures |a·r_t + b| < 10 for the strict (lower, upper) assertion.
_bounded_rt = st.floats(
    min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False
)
_small_b = st.floats(
    min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False
)
_safe_a = st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False)


def _safe_params_strategy() -> st.SearchStrategy[CalibrationParams]:
    """Params where |a·r_t + b| stays away from saturation for |r_t| <= 5."""
    return st.builds(
        CalibrationParams,
        tau_min=_moderate_floats,
        tau_max=_moderate_floats,
        a=_safe_a,
        b=_small_b,
    )


def _any_params_strategy() -> st.SearchStrategy[CalibrationParams]:
    return st.builds(
        CalibrationParams,
        tau_min=_moderate_floats,
        tau_max=_moderate_floats,
        a=_nonzero_moderate,
        b=_moderate_floats,
    )


# ---------------------------------------------------------------------------
# TestStableSigmoid
# ---------------------------------------------------------------------------


class TestStableSigmoid:
    def test_at_zero_is_exactly_half(self) -> None:
        """σ(0) must be 0.5 exactly in IEEE 754.

        math.exp(0) == 1.0 exactly; 1/(1+1) == 0.5 exactly because
        0.5 is representable as the binary fraction 2^{-1}.
        """
        assert _stable_sigmoid(0.0) == 0.5

    def test_positive_branch_executes(self) -> None:
        """x > 0 takes the branch 1/(1+exp(-x))."""
        result = _stable_sigmoid(1.0)
        assert result == 1.0 / (1.0 + math.exp(-1.0))

    def test_negative_branch_executes(self) -> None:
        """x < 0 takes the branch exp(x)/(1+exp(x))."""
        exp_neg = math.exp(-1.0)
        assert _stable_sigmoid(-1.0) == exp_neg / (1.0 + exp_neg)

    def test_large_positive_saturates_to_one_without_overflow(self) -> None:
        """σ(710) returns 1.0 by IEEE 754 saturation — no OverflowError."""
        result = _stable_sigmoid(710.0)
        assert result == 1.0
        assert not math.isnan(result)

    def test_large_negative_saturates_near_zero_without_overflow(self) -> None:
        """σ(-710) returns a subnormal near zero — no OverflowError."""
        result = _stable_sigmoid(-710.0)
        assert result < 1e-200
        assert not math.isnan(result)

    def test_moderate_range_strictly_between_zero_and_one(self) -> None:
        """For |x| <= 10, σ(x) ∈ (0, 1) strictly — no saturation."""
        for x in [-10.0, -1.0, 0.0, 1.0, 10.0]:
            assert 0.0 < _stable_sigmoid(x) < 1.0

    def test_symmetry(self) -> None:
        """σ(x) + σ(−x) = 1.0 (logistic symmetry)."""
        for x in [0.5, 1.0, 3.0, 10.0]:
            total = _stable_sigmoid(x) + _stable_sigmoid(-x)
            assert total == pytest.approx(1.0, abs=1e-14)

    @settings(max_examples=500)
    @given(_finite_floats)
    def test_output_finite_and_in_unit_interval_hypothesis(self, x: float) -> None:
        """For any finite x, σ(x) ∈ [0, 1] and is finite. 500 exemplos."""
        result = _stable_sigmoid(x)
        assert not math.isnan(result)
        assert not math.isinf(result)
        assert 0.0 <= result <= 1.0

    @settings(max_examples=500)
    @given(
        st.floats(
            min_value=-500.0, max_value=500.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_monotone_hypothesis(self, x: float) -> None:
        """σ is non-decreasing: σ(x) <= σ(x+ε). 500 exemplos.

        Uses <= (not <) because for |x| >> 1 both σ(x) and σ(x+ε)
        saturate to the same float value (0.0 or 1.0).
        """
        assert _stable_sigmoid(x) <= _stable_sigmoid(x + 1e-6)


# ---------------------------------------------------------------------------
# TestComputeTau
# ---------------------------------------------------------------------------


class TestComputeTau:
    def test_go_no_go_exact(self) -> None:
        """GO/NO-GO: compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0 exatamente.

        Exact IEEE 754 equality (==), not approximate.
        Chain: σ(0)=0.5 → (1.0−3.0)×0.5=−1.0 → 3.0+(−1.0)=2.0.
        All intermediate values are exact binary fractions.
        """
        assert compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0

    def test_at_zero_rt_with_zero_b_is_arithmetic_mean(self) -> None:
        """When b=0 and r_t=0: τ = tau_min + (tau_max−tau_min)·0.5."""
        params = CalibrationParams(tau_min=1.0, tau_max=5.0)
        assert compute_tau(0.0, params) == pytest.approx(3.0)

    def test_large_positive_rt_approaches_tau_max_when_a_positive(self) -> None:
        """When a > 0 and r_t → +∞: σ → 1, τ → tau_min + (tau_max−tau_min) = tau_max."""
        params = CalibrationParams(tau_min=1.0, tau_max=5.0)
        assert compute_tau(1000.0, params) == pytest.approx(params.tau_max, abs=1e-6)

    def test_large_negative_rt_approaches_tau_min_when_a_positive(self) -> None:
        """When a > 0 and r_t → −∞: σ → 0, τ → tau_min."""
        params = CalibrationParams(tau_min=1.0, tau_max=5.0)
        assert compute_tau(-1000.0, params) == pytest.approx(params.tau_min, abs=1e-6)

    def test_moderate_rt_strictly_between_bounds(self) -> None:
        """For |r_t| <= 5 and default a=1, b=0: τ strictly inside (tau_min, tau_max)."""
        params = CalibrationParams(tau_min=1.0, tau_max=5.0)
        for r_t in [-5.0, -1.0, 0.0, 1.0, 5.0]:
            result = compute_tau(r_t, params)
            assert 1.0 < result < 5.0

    def test_strictly_increasing_when_tau_min_less_than_tau_max_and_a_positive(
        self,
    ) -> None:
        """τ is STRICTLY INCREASING in r_t when a > 0 and tau_min < tau_max."""
        params = CalibrationParams(tau_min=1.0, tau_max=5.0, a=1.0)
        r_values = [-2.0, -1.0, 0.0, 1.0, 2.0]
        taus = [compute_tau(r, params) for r in r_values]
        for i in range(len(taus) - 1):
            assert taus[i] < taus[i + 1]

    def test_bias_shifts_inflection_point(self) -> None:
        """compute_tau(0, params_b0) == compute_tau(-b/a, params_b) at inflection."""
        params_no_bias = CalibrationParams(tau_min=1.0, tau_max=5.0, b=0.0)
        params_biased = CalibrationParams(tau_min=1.0, tau_max=5.0, b=2.0)
        assert compute_tau(0.0, params_no_bias) == pytest.approx(
            compute_tau(-2.0, params_biased), rel=1e-10
        )

    @settings(max_examples=500)
    @given(_safe_params_strategy(), _bounded_rt)
    def test_output_within_bounds_hypothesis(
        self, params: CalibrationParams, r_t: float
    ) -> None:
        """τ stays within [tau_min, tau_max] bounds. 500 exemplos."""
        result = compute_tau(r_t, params)
        lower = min(params.tau_min, params.tau_max)
        upper = max(params.tau_min, params.tau_max)
        if params.tau_min != params.tau_max:
            assert lower <= result <= upper
        else:
            assert result == pytest.approx(params.tau_min)

    @settings(max_examples=500)
    @given(
        tau_min=_moderate_floats,
        tau_max=_moderate_floats,
    )
    def test_arithmetic_mean_at_zero_rt_zero_b_hypothesis(
        self, tau_min: float, tau_max: float
    ) -> None:
        """τ(0, b=0) == tau_min + (tau_max − tau_min) · 0.5 para qualquer par.

        Proof: σ(0) = 0.5 exactamente em IEEE 754. 500 exemplos.
        """
        params = CalibrationParams(tau_min=tau_min, tau_max=tau_max, b=0.0)
        result = compute_tau(0.0, params)
        expected = tau_min + (tau_max - tau_min) * 0.5
        assert result == pytest.approx(expected, rel=1e-10, abs=1e-10)

    @settings(max_examples=500)
    @given(
        params=_safe_params_strategy(),
        r_t=_bounded_rt,
    )
    def test_monotone_direction_matches_sign_of_range_times_a_hypothesis(
        self, params: CalibrationParams, r_t: float
    ) -> None:
        """Monotonia: sinal da variação = sign(tau_max − tau_min). 500 exemplos.

        _safe_params_strategy constrains a ∈ [0.1, 2.0] (always positive).
        range > 0 → τ increasing. range < 0 → τ decreasing. range == 0 → constant.
        Uses <= (not <) to tolerate floating-point saturation at boundaries.
        """
        eps = 1e-4
        tau_range = params.tau_max - params.tau_min
        tau_at_r = compute_tau(r_t, params)
        tau_at_r_plus_eps = compute_tau(r_t + eps, params)

        if tau_range > 0.0:
            assert tau_at_r <= tau_at_r_plus_eps
        elif tau_range < 0.0:
            assert tau_at_r >= tau_at_r_plus_eps


# ---------------------------------------------------------------------------
# TestCalibrationParams
# ---------------------------------------------------------------------------


class TestCalibrationParams:
    def test_positional_construction(self) -> None:
        """CalibrationParams(3.0, 1.0) maps to tau_min=3.0, tau_max=1.0."""
        params = CalibrationParams(3.0, 1.0)
        assert params.tau_min == 3.0
        assert params.tau_max == 1.0

    def test_default_a_is_one(self) -> None:
        assert CalibrationParams(tau_min=1.0, tau_max=3.0).a == 1.0

    def test_default_b_is_zero(self) -> None:
        assert CalibrationParams(tau_min=1.0, tau_max=3.0).b == 0.0

    def test_frozen_raises_on_tau_min_mutation(self) -> None:
        params = CalibrationParams(tau_min=1.0, tau_max=3.0)
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            params.tau_min = 99.0

    def test_frozen_raises_on_a_mutation(self) -> None:
        params = CalibrationParams(tau_min=1.0, tau_max=3.0)
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            params.a = 0.0

    def test_keyword_construction(self) -> None:
        params = CalibrationParams(tau_min=0.5, tau_max=2.0, a=3.0, b=-1.0)
        assert params.tau_min == 0.5
        assert params.tau_max == 2.0
        assert params.a == 3.0
        assert params.b == -1.0

    @settings(max_examples=500)
    @given(
        tau_min=_moderate_floats,
        tau_max=_moderate_floats,
        a=_nonzero_moderate,
        b=_moderate_floats,
    )
    def test_construction_always_succeeds_hypothesis(
        self, tau_min: float, tau_max: float, a: float, b: float
    ) -> None:
        """Any finite float combination constructs CalibrationParams. 500 exemplos."""
        params = CalibrationParams(tau_min=tau_min, tau_max=tau_max, a=a, b=b)
        assert params.tau_min == tau_min
        assert params.tau_max == tau_max
