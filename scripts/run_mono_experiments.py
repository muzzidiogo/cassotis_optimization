"""
Entrega 1 — runs the GVNS 5 times for each objective (f1, f2, f3).

Outputs (in --out, default results/mono):
    runs/<objective>_seed<seed>.json   one file per run (config, final values, curve)
    summary.csv                        one row per run
    summary.md                         min / std / max per objective
    convergence_<objective>.png        5 overlaid convergence curves
    best_solution_<objective>.png      best solution of the 5 runs

Seeds are mandatory: the final seeds are chosen and recorded before the final
run, after the algorithm and its parameters are frozen (D017).

Usage:
    python scripts/run_mono_experiments.py --seeds S1 S2 S3 S4 S5
    python scripts/run_mono_experiments.py --seeds 1 2 --budget 20000 --out results/smoke
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
from dataclasses import asdict
from pathlib import Path

from cassotis_optimization.algorithms.gvns import GVNSConfig, run_gvns
from cassotis_optimization.io import load_instance
from cassotis_optimization.solution import Solution
from cassotis_optimization.visualization import plot_convergence, plot_solution, plt

OBJECTIVES = ("f1", "f2", "f3")


def git_version() -> str:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return f"{commit}{'-dirty' if dirty else ''}"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", default="data/example_instance")
    parser.add_argument("--out", default="results/mono")
    parser.add_argument("--budget", type=int, default=GVNSConfig.max_evaluations)
    parser.add_argument("--sample-size", type=int, default=GVNSConfig.sample_size)
    parser.add_argument("--p1-positions", type=int, default=GVNSConfig.p1_positions)
    parser.add_argument("--p2-chain-length", type=int, default=GVNSConfig.p2_chain_length)
    parser.add_argument("--p3-piles", type=int, default=GVNSConfig.p3_piles)    
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--objectives", nargs="+", default=list(OBJECTIVES))
    args = parser.parse_args()

    instance = load_instance(args.instance)
    out = Path(args.out)
    (out / "runs").mkdir(parents=True, exist_ok=True)
    version = git_version()

    rows: list[dict] = []
    runs_by_objective: dict[str, list[dict]] = {}

    for objective in args.objectives:
        runs_by_objective[objective] = []

        for seed in args.seeds:
            config = GVNSConfig(
                objective=objective,
                seed=seed,
                max_evaluations=args.budget,
                sample_size=args.sample_size,
                p1_positions=args.p1_positions,
                p2_chain_length=args.p2_chain_length,
                p3_piles=args.p3_piles,
            )
            result = run_gvns(instance, config)
            evaluation = result.best.evaluation

            record = {
                "run_id": f"{objective}_seed{seed}",
                "git_commit": version,
                "instance": args.instance,
                "objective": objective,
                "seed": seed,
                "algorithm": "GVNS",
                "parameters": asdict(config),
                "stopping_rule": "max_evaluations",
                "evaluation_budget": config.max_evaluations,
                "evaluations": result.evaluations,
                "runtime_seconds": round(result.runtime_seconds, 3),
                "iterations": result.iterations,
                "improvements": result.improvements,
                "first_feasible_at": result.first_feasible_at,
                "feasible": result.best.feasible,
                "objective_value": result.best.objective,
                "f1": evaluation.cost_rs,
                "f2": evaluation.f2_sio2_sq_dev,
                "f3": evaluation.f3_al2o3_sq_dev,
                "total_violation": result.best.violation,
                "initial": {
                    "feasible": result.initial.feasible,
                    "f1": result.initial.evaluation.cost_rs,
                    "f2": result.initial.evaluation.f2_sio2_sq_dev,
                    "f3": result.initial.evaluation.f3_al2o3_sq_dev,
                    "total_violation": result.initial.violation,
                },
                "stats": result.stats,
                "composition": {
                    pile_id: list(minerals)
                    for pile_id, minerals in result.best.solution.composition.items()
                },
                "history": result.history_as_dicts(),
            }

            (out / "runs" / f"{record['run_id']}.json").write_text(
                json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            runs_by_objective[objective].append(record)
            rows.append({k: v for k, v in record.items()
                         if k not in {"parameters", "initial", "stats", "composition", "history"}})

            print(
                f"{record['run_id']}: feasible={record['feasible']} "
                f"{objective}={record['objective_value']:.6g} "
                f"evals={record['evaluations']} time={record['runtime_seconds']}s",
                flush=True,
            )

    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Resultados mono-objetivo (GVNS)\n",
        (
            f"Versão do código: `{version}` — instância: `{args.instance}` — "
            f"orçamento: {args.budget} avaliações — seeds: {args.seeds}\n"
        ),
        "Desvio-padrão amostral (n-1) sobre o valor final de cada execução.\n",
        "| Objetivo | factíveis | mín | std | máx | tempo médio (s) |",
        "|---|---|---|---|---|---|",
    ]
    for objective, runs in runs_by_objective.items():
        values = [r["objective_value"] for r in runs if r["feasible"]]
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        mean_time = statistics.mean(r["runtime_seconds"] for r in runs)
        lines.append(
            f"| {objective} | {len(values)}/{len(runs)} | {min(values):.6g} | "
            f"{std:.4g} | {max(values):.6g} | {mean_time:.1f} |"
            if values else f"| {objective} | 0/{len(runs)} | – | – | – | {mean_time:.1f} |"
        )

        fig = plot_convergence(runs, objective)
        fig.savefig(out / f"convergence_{objective}.png", dpi=150)

        feasible_runs = [r for r in runs if r["feasible"]] or runs
        best = min(feasible_runs, key=lambda r: r["objective_value"])
        solution = Solution({p: tuple(m) for p, m in best["composition"].items()})
        fig = plot_solution(solution, instance, f"Melhor solução para {objective} ({best['run_id']})")
        fig.savefig(out / f"best_solution_{objective}.png", dpi=150, bbox_inches="tight")
        plt.close("all")

    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
