"""Calibração dos parâmetros experimentais da GVNS — Entrega 1."""

from __future__ import annotations

import argparse
import csv
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

from cassotis_optimization.algorithms.gvns import GVNSConfig, run_gvns
from cassotis_optimization.io import load_instance

OBJECTIVES = ("f1", "f2", "f3")


def git_version() -> str:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        return f"{commit}{'-dirty' if dirty else ''}"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def parse_shake_config(value: str) -> tuple[int, int, int]:
    try:
        parts = tuple(int(x) for x in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Use o formato P1,P2,P3, por exemplo 2,3,5."
        ) from exc

    if len(parts) != 3 or any(x <= 0 for x in parts):
        raise argparse.ArgumentTypeError(
            "Use três inteiros positivos: P1,P2,P3."
        )

    return parts


def mean_or_blank(values: list[float]) -> float | str:
    return statistics.mean(values) if values else ""


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=("grid", "budget"),
        required=True,
    )
    parser.add_argument(
        "--instance",
        default="data/example_instance",
    )
    parser.add_argument(
        "--out",
        default="results/calibration",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[3101, 3102, 3103],
    )

    # Fase 1: calibração de sample_size + SHAKE
    parser.add_argument(
        "--budget",
        type=int,
        default=50_000,
    )
    parser.add_argument(
        "--sample-sizes",
        type=int,
        nargs="+",
        default=[250, 500, 1000],
    )
    parser.add_argument(
        "--shake-configs",
        type=parse_shake_config,
        nargs="+",
        default=[
            (1, 2, 5),
            (2, 3, 5),
            (3, 4, 5),
        ],
    )

    # Fase 2: calibração do orçamento.
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=[50_000, 100_000, 200_000],
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
    )
    parser.add_argument(
        "--p1-positions",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--p2-chain-length",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--p3-piles",
        type=int,
        default=5,
    )

    args = parser.parse_args()

    instance = load_instance(args.instance)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    version = git_version()

    configurations: list[dict] = []

    if args.mode == "grid":
        for sample_size in args.sample_sizes:
            for p1, p2, p3 in args.shake_configs:
                configurations.append(
                    {
                        "budget": args.budget,
                        "sample_size": sample_size,
                        "p1_positions": p1,
                        "p2_chain_length": p2,
                        "p3_piles": p3,
                    }
                )

    else:
        for budget in args.budgets:
            configurations.append(
                {
                    "budget": budget,
                    "sample_size": args.sample_size,
                    "p1_positions": args.p1_positions,
                    "p2_chain_length": args.p2_chain_length,
                    "p3_piles": args.p3_piles,
                }
            )

    rows: list[dict] = []

    total_runs = (
        len(configurations)
        * len(args.seeds)
        * len(OBJECTIVES)
    )
    current_run = 0

    for configuration in configurations:
        config_id = (
            f"b{configuration['budget']}"
            f"_s{configuration['sample_size']}"
            f"_p{configuration['p1_positions']}"
            f"-{configuration['p2_chain_length']}"
            f"-{configuration['p3_piles']}"
        )

        for objective in OBJECTIVES:
            for seed in args.seeds:
                current_run += 1

                print(
                    f"[{current_run}/{total_runs}] "
                    f"{config_id} | {objective} | seed={seed}",
                    flush=True,
                )

                config = GVNSConfig(
                    objective=objective,
                    seed=seed,
                    max_evaluations=configuration["budget"],
                    sample_size=configuration["sample_size"],
                    p1_positions=configuration["p1_positions"],
                    p2_chain_length=configuration["p2_chain_length"],
                    p3_piles=configuration["p3_piles"],
                )

                result = run_gvns(instance, config)

                rows.append(
                    {
                        "git_commit": version,
                        "config_id": config_id,
                        "budget": configuration["budget"],
                        "sample_size": configuration["sample_size"],
                        "p1_positions": configuration["p1_positions"],
                        "p2_chain_length": configuration["p2_chain_length"],
                        "p3_piles": configuration["p3_piles"],
                        "objective": objective,
                        "seed": seed,
                        "feasible": result.best.feasible,
                        "objective_value": result.best.objective,
                        "total_violation": result.best.violation,
                        "first_feasible_at": result.first_feasible_at,
                        "iterations": result.iterations,
                        "outer_improvements": result.improvements,
                        "improvements_N1": result.stats.get(
                            "improvements_N1", 0
                        ),
                        "improvements_N2": result.stats.get(
                            "improvements_N2", 0
                        ),
                        "improvements_N3": result.stats.get(
                            "improvements_N3", 0
                        ),
                        "shake_P1": result.stats.get("shake_P1", 0),
                        "shake_P2": result.stats.get("shake_P2", 0),
                        "shake_P3": result.stats.get("shake_P3", 0),
                        "runtime_seconds": result.runtime_seconds,
                    }
                )

    raw_path = out / "raw_runs.csv"

    with raw_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for row in rows:
        grouped[
            (
                row["config_id"],
                row["objective"],
            )
        ].append(row)

    summary_rows: list[dict] = []

    for (config_id, objective), group in grouped.items():
        feasible = [row for row in group if row["feasible"]]
        values = [
            row["objective_value"]
            for row in feasible
        ]

        first_feasible = [
            row["first_feasible_at"]
            for row in feasible
            if row["first_feasible_at"] is not None
        ]

        template = group[0]

        summary_rows.append(
            {
                "config_id": config_id,
                "budget": template["budget"],
                "sample_size": template["sample_size"],
                "p1_positions": template["p1_positions"],
                "p2_chain_length": template["p2_chain_length"],
                "p3_piles": template["p3_piles"],
                "objective": objective,
                "feasible_runs": len(feasible),
                "total_runs": len(group),
                "min_objective": min(values) if values else "",
                "mean_objective": (
                    statistics.mean(values)
                    if values
                    else ""
                ),
                "std_objective": (
                    statistics.stdev(values)
                    if len(values) > 1
                    else ""
                ),
                "max_objective": max(values) if values else "",
                "mean_first_feasible": mean_or_blank(
                    first_feasible
                ),
                "mean_violation": statistics.mean(
                    row["total_violation"]
                    for row in group
                ),
                "mean_iterations": statistics.mean(
                    row["iterations"]
                    for row in group
                ),
                "mean_outer_improvements": statistics.mean(
                    row["outer_improvements"]
                    for row in group
                ),
                "mean_runtime_seconds": statistics.mean(
                    row["runtime_seconds"]
                    for row in group
                ),
            }
        )

    summary_path = out / "summary.csv"

    with summary_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(summary_rows[0]),
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    print()
    print(f"Raw runs: {raw_path}")
    print(f"Resumo:   {summary_path}")


if __name__ == "__main__":
    main()