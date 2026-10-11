# tests/unit/domain/test_calibration.py
"""Unit tests for bci_calib.domain.calibration.

Pre-registered model: τ(r_t) = 1 + (τ_max − 1) · σ(a · r_t).

Structure
---------
TestStableSigmoid     : deterministic + Hypothesis (500 examples)
TestComputeTau        : GO/NO-GO, bounds, asymptotes, monotonicity
TestCalibrationParams : frozen, positional order, validation
TestFrozenDecisions   : τ_min = 1 and b = 0 are module constants

Floating-point saturation
-------------------------
For |a · r_t| >> 1 the sigmoid saturates to 0.0 or 1.0 exactly, so strict
inequalities are only asserted on a moderate range of a · r_t.
"""

from __future__ import annotations

import ast
import math
import pathlib

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from bci_calib.domain.calibration import (
    SIGMOID_BIAS,
    TAU_MIN,
    CalibrationParams,
    _stable_sigmoid,
    compute_tau,
)

_finite_floats = st.floats(allow_nan=False, allow_infinity=False)
_valid_tau_max = st.floats(
    min_value=TAU_MIN, max_value=1e6, allow_nan=False, allow_infinity=False
)
_tau_max_above_floor = st.floats(
    min_value=1.01, max_value=10.0, allow_nan=False, allow_infinity=False
)
_moderate_slope = st.floats(
    min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False
)
_bounded_rt = st.floats(
    min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False
)


def _valid_params_strategy() -> st.SearchStrategy[CalibrationParams]:
    return st.builds(CalibrationParams, tau_max=_valid_tau_max, a=_finite_floats)


class TestStableSigmoid:
    def test_at_zero_is_exactly_half(self) -> None:
        assert _stable_sigmoid(0.0) == 0.5

    def test_positive_branch_matches_closed_form(self) -> None:
        assert _stable_sigmoid(1.0) == 1.0 / (1.0 + math.exp(-1.0))

    def test_negative_branch_matches_closed_form(self) -> None:
        exp_neg = math.exp(-1.0)
        assert _stable_sigmoid(-1.0) == exp_neg / (1.0 + exp_neg)

    def test_large_positive_saturates_to_one_without_overflow(self) -> None:
        assert _stable_sigmoid(710.0) == 1.0

    def test_large_negative_saturates_near_zero_without_overflow(self) -> None:
        assert _stable_sigmoid(-800.0) < 1e-200

    def test_logistic_symmetry(self) -> None:
        for x in [0.5, 1.0, 3.0, 10.0]:
            total = _stable_sigmoid(x) + _stable_sigmoid(-x)
            assert total == pytest.approx(1.0, abs=1e-14)

    @settings(max_examples=500)
    @given(_finite_floats)
    def test_output_is_finite_and_in_unit_interval(self, x: float) -> None:
        result = _stable_sigmoid(x)
        assert math.isfinite(result)
        assert 0.0 <= result <= 1.0

    @settings(max_examples=500)
    @given(st.floats(min_value=-500.0, max_value=500.0))
    def test_is_non_decreasing(self, x: float) -> None:
        assert _stable_sigmoid(x) <= _stable_sigmoid(x + 1e-6)


class TestComputeTau:
    def test_go_no_go_exact(self) -> None:
        """GO/NO-GO: 1 + (3 − 1) × σ(0) == 2.0 exactly in IEEE 754."""
        assert compute_tau(0.0, CalibrationParams(3.0, 1.0)) == 2.0

    def test_at_zero_rt_is_midpoint_between_one_and_tau_max(self) -> None:
        assert compute_tau(0.0, CalibrationParams(tau_max=5.0)) == 3.0

    def test_tau_max_equal_to_floor_gives_uncalibrated_softmax(self) -> None:
        params = CalibrationParams(tau_max=TAU_MIN, a=-4.0)
        for r_t in [-3.0, 0.0, 3.0]:
            assert compute_tau(r_t, params) == TAU_MIN

    def test_zero_slope_collapses_to_static_temperature(self) -> None:
        """a = 0 reduces τ(r_t) to a constant, i.e. ablation condition B."""
        params = CalibrationParams(tau_max=4.0, a=0.0)
        taus = {compute_tau(r_t, params) for r_t in [-3.0, 0.0, 3.0]}
        assert taus == {2.5}

    def test_negative_slope_raises_tau_when_rmssd_falls(self) -> None:
        """Pre-registered direction: a < 0 → low r_t (low RMSSD) → higher τ."""
        params = CalibrationParams(tau_max=3.0, a=-1.0)
        assert compute_tau(-2.0, params) > compute_tau(2.0, params)

    def test_negative_slope_asymptotes(self) -> None:
        params = CalibrationParams(tau_max=3.0, a=-1.0)
        assert compute_tau(-1000.0, params) == pytest.approx(3.0, abs=1e-9)
        assert compute_tau(1000.0, params) == pytest.approx(TAU_MIN, abs=1e-9)

    def test_positive_slope_asymptotes(self) -> None:
        params = CalibrationParams(tau_max=3.0, a=1.0)
        assert compute_tau(1000.0, params) == pytest.approx(3.0, abs=1e-9)
        assert compute_tau(-1000.0, params) == pytest.approx(TAU_MIN, abs=1e-9)

    @settings(max_examples=500)
    @given(_valid_params_strategy(), _finite_floats)
    def test_never_leaves_closed_interval_one_to_tau_max(
        self, params: CalibrationParams, r_t: float
    ) -> None:
        tau = compute_tau(r_t, params)
        one_ulp_tolerance = params.tau_max * 1e-15
        assert TAU_MIN <= tau <= params.tau_max + one_ulp_tolerance

    @settings(max_examples=500)
    @given(_tau_max_above_floor, _moderate_slope, _bounded_rt)
    def test_direction_of_change_follows_sign_of_slope(
        self, tau_max: float, a: float, r_t: float
    ) -> None:
        params = CalibrationParams(tau_max=tau_max, a=a)
        tau_here = compute_tau(r_t, params)
        tau_ahead = compute_tau(r_t + 1e-3, params)
        if a > 0.0:
            assert tau_here <= tau_ahead
        elif a < 0.0:
            assert tau_here >= tau_ahead
        else:
            assert tau_here == tau_ahead


class TestCalibrationParams:
    def test_positional_order_is_tau_max_then_slope(self) -> None:
        params = CalibrationParams(3.0, 1.0)
        assert params.tau_max == 3.0
        assert params.a == 1.0

    def test_default_slope_is_one(self) -> None:
        assert CalibrationParams(tau_max=2.0).a == 1.0

    def test_tau_max_below_floor_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CalibrationParams(tau_max=0.99)

    def test_tau_max_equal_to_floor_is_accepted(self) -> None:
        assert CalibrationParams(tau_max=TAU_MIN).tau_max == TAU_MIN

    @pytest.mark.parametrize("non_finite", [math.inf, -math.inf, math.nan])
    def test_non_finite_tau_max_is_rejected(self, non_finite: float) -> None:
        with pytest.raises(ValidationError):
            CalibrationParams(tau_max=non_finite)

    @pytest.mark.parametrize("non_finite", [math.inf, -math.inf, math.nan])
    def test_non_finite_slope_is_rejected(self, non_finite: float) -> None:
        with pytest.raises(ValidationError):
            CalibrationParams(tau_max=2.0, a=non_finite)

    def test_tau_max_is_immutable(self) -> None:
        params = CalibrationParams(tau_max=3.0)
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            params.tau_max = 9.0

    def test_slope_is_immutable(self) -> None:
        params = CalibrationParams(tau_max=3.0)
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            params.a = 0.0

    def test_has_exactly_two_free_parameters(self) -> None:
        fields = CalibrationParams.__dataclass_fields__
        assert set(fields) == {"tau_max", "a"}


class TestFrozenDecisions:
    def test_tau_min_is_fixed_at_one(self) -> None:
        assert TAU_MIN == 1.0

    def test_sigmoid_bias_is_fixed_at_zero(self) -> None:
        assert SIGMOID_BIAS == 0.0

    def test_calibration_module_has_no_forbidden_imports(self) -> None:
        source = pathlib.Path("src/bci_calib/domain/calibration.py").read_text(
            encoding="utf-8"
        )
        forbidden_roots = {"mne", "numpy", "torch", "scipy", "sklearn"}
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = {node.module.split(".")[0]}
            else:
                continue
            assert not imported & forbidden_roots
