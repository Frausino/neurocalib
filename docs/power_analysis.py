# docs/power_analysis.py
"""Prints the power curve for n = 10..25 that is pre-registered in the OSF.

Usage (from the repository root):

    uv run python docs/power_analysis.py
    uv run python docs/power_analysis.py --output docs/power_curve.csv

Scenarios
---------
primary      d = 0.60, alpha = 0.05, one-sided (H1, pre-registered)
conservative d = 0.60, alpha = 0.025, one-sided (superseded family rule)
sensitivity  d = 0.50, alpha = 0.05, one-sided (declared limitation)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from bci_calib.application.power_analysis import (
    PowerScenario,
    analytic_power,
    minimum_sample_size,
    monte_carlo_power,
)

SAMPLE_SIZES = range(10, 26)
MONTE_CARLO_SIMULATIONS = 20_000
MONTE_CARLO_SEED = 42

SCENARIOS = {
    "primary": PowerScenario(effect_size_d=0.60, alpha=0.05),
    "conservative": PowerScenario(effect_size_d=0.60, alpha=0.025),
    "sensitivity": PowerScenario(effect_size_d=0.50, alpha=0.05),
}


def build_rows() -> list[dict[str, str]]:
    rows = []
    for name, scenario in SCENARIOS.items():
        for sample_size in SAMPLE_SIZES:
            analytic = analytic_power(sample_size, scenario)
            simulated = monte_carlo_power(
                sample_size, scenario, MONTE_CARLO_SIMULATIONS, MONTE_CARLO_SEED
            )
            rows.append(
                {
                    "scenario": name,
                    "d": f"{scenario.effect_size_d:.2f}",
                    "alpha": f"{scenario.alpha:.3f}",
                    "n": str(sample_size),
                    "power_analytic": f"{analytic:.3f}",
                    "power_monte_carlo": f"{simulated:.3f}",
                }
            )
    return rows


def print_table(rows: list[dict[str, str]]) -> None:
    header = list(rows[0])
    print(" | ".join(f"{column:>17}" for column in header))
    for row in rows:
        print(" | ".join(f"{row[column]:>17}" for column in header))
    print()
    for name, scenario in SCENARIOS.items():
        print(f"minimum n for power 0.80 ({name}): {minimum_sample_size(scenario)}")


def write_csv(rows: list[dict[str, str]], destination: Path) -> None:
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()
    rows = build_rows()
    print_table(rows)
    if arguments.output is not None:
        write_csv(rows, arguments.output)


if __name__ == "__main__":
    main()
