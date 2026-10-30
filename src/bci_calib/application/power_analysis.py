# src/bci_calib/application/power_analysis.py
"""Statistical power of the H1 test (one-sided paired Wilcoxon, unit = subject).

Two independent estimators are provided so that each one can check the other.

Analytic
    Noncentral t approximation for the paired t-test, with the sample size
    replaced by its Wilcoxon-equivalent n * ARE, where
    ARE = 3 / pi is the asymptotic relative efficiency of the Wilcoxon
    signed-rank test against the t-test under normality.

Monte Carlo
    Simulates paired differences ~ Normal(d, 1) and applies the exact
    one-sided signed-rank test. Its critical value comes from the exact
    null distribution, which is what ``scipy.stats.wilcoxon`` uses for
    samples without ties.

Both estimates are the power of the Wilcoxon test alone. The composite H1
corroboration rule (effect size, bootstrap bound, Brier, NLL, AUROC) has a
power that is at most this value and is not estimated here.

The exact test is slightly more conservative than the ARE approximation
because its null distribution is discrete. Both estimates are reported by
``docs/power_analysis.py``.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Final

import numpy as np
from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass
from scipy import stats

WILCOXON_ASYMPTOTIC_RELATIVE_EFFICIENCY: Final[float] = 3.0 / math.pi
DEFAULT_TARGET_POWER: Final[float] = 0.80
DEFAULT_SEARCH_LIMIT: Final[int] = 500


@dataclass(config=ConfigDict(frozen=True, allow_inf_nan=False))
class PowerScenario:
    """Effect size and significance level of one pre-registered test."""

    effect_size_d: float = Field(gt=0.0)
    alpha: float = Field(gt=0.0, lt=1.0)
    one_sided: bool = True


@dataclass(config=ConfigDict(frozen=True, allow_inf_nan=False))
class PowerPoint:
    """One point of a power curve."""

    sample_size: int = Field(ge=2)
    power: float = Field(ge=0.0, le=1.0)


def analytic_power(sample_size: int, scenario: PowerScenario) -> float:
    """Approximate power of the Wilcoxon test with ``sample_size`` subjects."""
    _require_valid_sample_size(sample_size)
    equivalent_sample_size = sample_size * WILCOXON_ASYMPTOTIC_RELATIVE_EFFICIENCY
    degrees_of_freedom = equivalent_sample_size - 1.0
    noncentrality = scenario.effect_size_d * math.sqrt(equivalent_sample_size)
    tail_probability = scenario.alpha if scenario.one_sided else scenario.alpha / 2.0
    critical_value = float(stats.t.ppf(1.0 - tail_probability, degrees_of_freedom))
    upper_tail_power = float(
        stats.nct.sf(critical_value, degrees_of_freedom, noncentrality)
    )
    if scenario.one_sided:
        return upper_tail_power
    lower_tail_power = float(
        stats.nct.cdf(-critical_value, degrees_of_freedom, noncentrality)
    )
    return upper_tail_power + lower_tail_power


def minimum_sample_size(
    scenario: PowerScenario,
    target_power: float = DEFAULT_TARGET_POWER,
    search_limit: int = DEFAULT_SEARCH_LIMIT,
) -> int:
    """Smallest number of subjects whose analytic power reaches ``target_power``."""
    if not 0.0 < target_power < 1.0:
        raise ValueError(f"target_power must be in (0, 1), got {target_power}")
    for sample_size in range(2, search_limit + 1):
        if analytic_power(sample_size, scenario) >= target_power:
            return sample_size
    raise ValueError(
        f"target_power {target_power} not reached up to {search_limit} subjects"
    )


def power_curve(
    sample_sizes: Iterable[int], scenario: PowerScenario
) -> tuple[PowerPoint, ...]:
    """Analytic power for each sample size, in the given order."""
    return tuple(
        PowerPoint(sample_size=size, power=analytic_power(size, scenario))
        for size in sample_sizes
    )


def signed_rank_null_counts(sample_size: int) -> tuple[int, ...]:
    """Number of rank subsets that sum to each value of the statistic W+.

    Entry ``k`` counts the subsets of ``{1, ..., n}`` with sum ``k``. Under the
    null hypothesis every subset is equally likely, so dividing by ``2**n``
    gives the exact null distribution of W+.
    """
    _require_valid_sample_size(sample_size)
    maximum_sum = sample_size * (sample_size + 1) // 2
    counts = [0] * (maximum_sum + 1)
    counts[0] = 1
    for rank in range(1, sample_size + 1):
        for total in range(maximum_sum, rank - 1, -1):
            counts[total] += counts[total - rank]
    return tuple(counts)


def one_sided_critical_value(sample_size: int, alpha: float) -> int:
    """Smallest W+ at which the exact one-sided test rejects at level ``alpha``.

    Returns ``n * (n + 1) / 2 + 1`` when no value of W+ reaches the level, which
    happens for very small samples. The test then never rejects.
    """
    counts = signed_rank_null_counts(sample_size)
    total_subsets = 2**sample_size
    critical_value = len(counts)
    upper_tail_count = 0
    for statistic in range(len(counts) - 1, -1, -1):
        upper_tail_count += counts[statistic]
        if upper_tail_count / total_subsets > alpha:
            break
        critical_value = statistic
    return critical_value


def monte_carlo_power(
    sample_size: int,
    scenario: PowerScenario,
    simulations: int,
    seed: int,
) -> float:
    """Power of the exact one-sided Wilcoxon test under Normal(d, 1) differences."""
    _require_valid_sample_size(sample_size)
    if not scenario.one_sided:
        raise ValueError("monte_carlo_power supports only one-sided scenarios")
    if simulations < 1:
        raise ValueError(f"simulations must be positive, got {simulations}")
    generator = np.random.default_rng(seed)
    differences = generator.normal(
        loc=scenario.effect_size_d, scale=1.0, size=(simulations, sample_size)
    )
    ranks = stats.rankdata(np.abs(differences), axis=1)
    positive_rank_sums = (ranks * (differences > 0.0)).sum(axis=1)
    critical_value = one_sided_critical_value(sample_size, scenario.alpha)
    return float(np.mean(positive_rank_sums >= critical_value))


def _require_valid_sample_size(sample_size: int) -> None:
    if sample_size < 2:
        raise ValueError(f"sample_size must be at least 2, got {sample_size}")
