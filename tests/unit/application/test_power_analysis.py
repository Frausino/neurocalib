# tests/unit/application/test_power_analysis.py
"""Oracle and consistency tests for bci_calib.application.power_analysis.

Oracle values were computed independently with the noncentral t approximation
and ARE = 3 / pi (d = 0.60). They are the numbers cited in the OSF pre-registration.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
from pydantic import ValidationError
from scipy import stats

from bci_calib.application.power_analysis import (
    PowerPoint,
    PowerScenario,
    analytic_power,
    minimum_sample_size,
    monte_carlo_power,
    one_sided_critical_value,
    power_curve,
    signed_rank_null_counts,
)

PRIMARY = PowerScenario(effect_size_d=0.60, alpha=0.05)
CONSERVATIVE = PowerScenario(effect_size_d=0.60, alpha=0.025)
TWO_SIDED = PowerScenario(effect_size_d=0.60, alpha=0.05, one_sided=False)
SENSITIVITY = PowerScenario(effect_size_d=0.50, alpha=0.05)


class TestAnalyticPowerOracle:
    @pytest.mark.parametrize(
        ("sample_size", "expected"),
        [(15, 0.694), (19, 0.790), (20, 0.810), (21, 0.828)],
    )
    def test_primary_scenario(self, sample_size: int, expected: float) -> None:
        assert analytic_power(sample_size, PRIMARY) == pytest.approx(
            expected, abs=0.002
        )

    def test_alpha_0025_with_19_subjects_is_below_target(self) -> None:
        assert analytic_power(19, CONSERVATIVE) == pytest.approx(0.674, abs=0.002)

    def test_two_sided_is_not_above_one_sided_at_same_alpha(self) -> None:
        assert analytic_power(19, TWO_SIDED) < analytic_power(19, PRIMARY)

    def test_sensitivity_scenario_with_19_subjects(self) -> None:
        assert analytic_power(19, SENSITIVITY) == pytest.approx(0.655, abs=0.002)

    def test_power_increases_with_sample_size(self) -> None:
        powers = [analytic_power(n, PRIMARY) for n in range(10, 26)]
        assert powers == sorted(powers)


class TestMinimumSampleSize:
    def test_primary_scenario_needs_20_subjects(self) -> None:
        assert minimum_sample_size(PRIMARY) == 20

    def test_conservative_scenario_needs_25_subjects(self) -> None:
        assert minimum_sample_size(CONSERVATIVE) == 25

    def test_unreachable_target_raises(self) -> None:
        with pytest.raises(ValueError, match="not reached"):
            minimum_sample_size(PRIMARY, target_power=0.99, search_limit=5)

    @pytest.mark.parametrize("target", [0.0, 1.0, -0.1, 1.5])
    def test_invalid_target_power_raises(self, target: float) -> None:
        with pytest.raises(ValueError, match="target_power"):
            minimum_sample_size(PRIMARY, target_power=target)


class TestPowerCurve:
    def test_curve_covers_pre_registered_range(self) -> None:
        curve = power_curve(range(10, 26), PRIMARY)
        assert [point.sample_size for point in curve] == list(range(10, 26))

    def test_points_are_frozen(self) -> None:
        point = power_curve([20], PRIMARY)[0]
        with pytest.raises(dataclasses.FrozenInstanceError):
            point.power = 0.5

    def test_point_matches_analytic_power(self) -> None:
        assert power_curve([19], PRIMARY)[0] == PowerPoint(
            sample_size=19, power=analytic_power(19, PRIMARY)
        )


class TestScenarioValidation:
    @pytest.mark.parametrize("effect_size", [0.0, -0.5, float("nan")])
    def test_invalid_effect_size_is_rejected(self, effect_size: float) -> None:
        with pytest.raises(ValidationError):
            PowerScenario(effect_size_d=effect_size, alpha=0.05)

    @pytest.mark.parametrize("alpha", [0.0, 1.0, -0.01, float("inf")])
    def test_invalid_alpha_is_rejected(self, alpha: float) -> None:
        with pytest.raises(ValidationError):
            PowerScenario(effect_size_d=0.6, alpha=alpha)

    def test_sample_size_below_two_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            analytic_power(1, PRIMARY)


class TestSignedRankNullDistribution:
    def test_counts_for_three_subjects(self) -> None:
        assert signed_rank_null_counts(3) == (1, 1, 1, 2, 1, 1, 1)

    @pytest.mark.parametrize("sample_size", [5, 12, 19])
    def test_counts_cover_every_subset_once(self, sample_size: int) -> None:
        assert sum(signed_rank_null_counts(sample_size)) == 2**sample_size

    def test_distribution_is_symmetric(self) -> None:
        counts = signed_rank_null_counts(10)
        assert counts == counts[::-1]

    def test_tiny_sample_never_rejects(self) -> None:
        assert one_sided_critical_value(3, 0.05) == 7

    def test_critical_value_decision_matches_scipy_exact_test(self) -> None:
        sample_size, alpha = 12, 0.05
        critical_value = one_sided_critical_value(sample_size, alpha)
        generator = np.random.default_rng(7)
        for _ in range(300):
            differences = generator.normal(0.5, 1.0, sample_size)
            ranks = stats.rankdata(np.abs(differences))
            positive_rank_sum = float(np.sum(ranks[differences > 0.0]))
            scipy_rejects = (
                stats.wilcoxon(differences, alternative="greater").pvalue <= alpha
            )
            assert (positive_rank_sum >= critical_value) == scipy_rejects


class TestMonteCarloPower:
    @pytest.mark.parametrize("sample_size", [19, 20])
    def test_agrees_with_analytic_within_tolerance(self, sample_size: int) -> None:
        simulated = monte_carlo_power(sample_size, PRIMARY, simulations=4000, seed=42)
        assert simulated == pytest.approx(
            analytic_power(sample_size, PRIMARY), abs=0.03
        )

    def test_same_seed_gives_same_result(self) -> None:
        first = monte_carlo_power(15, PRIMARY, simulations=500, seed=1)
        second = monte_carlo_power(15, PRIMARY, simulations=500, seed=1)
        assert first == second

    def test_two_sided_scenario_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="one-sided"):
            monte_carlo_power(19, TWO_SIDED, simulations=10, seed=1)

    def test_non_positive_simulations_are_rejected(self) -> None:
        with pytest.raises(ValueError, match="simulations"):
            monte_carlo_power(19, PRIMARY, simulations=0, seed=1)
