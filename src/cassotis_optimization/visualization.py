"""Figures for the report. Quality and usage always come from ``evaluate``."""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .domain import TRUCK_CAPACITY_KT, ProblemInstance
from .evaluator import evaluate
from .solution import Solution

OBJECTIVE_LABELS = {
    "f1": "f1 — custo total (R$)",
    "f2": "f2 — soma dos desvios quadráticos de SiO₂",
    "f3": "f3 — soma dos desvios quadráticos de Al₂O₃",
}


def plot_convergence(
    runs: Sequence[dict],
    objective: str,
) -> Figure:
    """
    Overlay the best-so-far curves of several runs.

    Each run is a dict with ``seed`` and ``history`` (list of dicts with
    ``evaluations``, ``feasible``, ``objective``, ``violation``) and
    ``evaluations`` (total evaluations used). Only the feasible part of each
    curve is drawn on the objective axis; the evaluation at which the run
    became feasible is marked.
    """

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for run in runs:
        feasible_points = [p for p in run["history"] if p["feasible"]]
        if not feasible_points:
            continue

        xs = [p["evaluations"] for p in feasible_points] + [run["evaluations"]]
        ys = [p["objective"] for p in feasible_points] + [feasible_points[-1]["objective"]]

        (line,) = ax.step(xs, ys, where="post", label=f"seed {run['seed']}")
        ax.plot(xs[0], ys[0], "o", color=line.get_color(), markersize=4)

    ax.set_xscale("symlog", linthresh=1000)
    ax.set_xlabel("Número de avaliações de soluções candidatas")
    ax.set_ylabel(OBJECTIVE_LABELS.get(objective, objective))
    ax.set_title(
        f"Convergência da GVNS — {objective} (melhor solução factível até o momento)"
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_solution(
    solution: Solution,
    instance: ProblemInstance,
    title: str,
) -> Figure:
    """Pile composition (stacked kt per mineral) and pile quality vs. limits."""

    evaluation = evaluate(solution, instance)
    pile_ids = list(instance.piles)
    mineral_ids = [
        m for m in instance.minerals if evaluation.usage_by_mineral[m] > 0
    ]
    counts = solution.counts_by_pile()

    fig, (ax_comp, ax_si, ax_al) = plt.subplots(
        3, 1, figsize=(11, 11), gridspec_kw={"height_ratios": [2.2, 1, 1]}
    )

    cmap = plt.get_cmap("tab20")
    bottoms = [0.0] * len(pile_ids)
    for index, mineral_id in enumerate(mineral_ids):
        heights = [counts[p][mineral_id] * TRUCK_CAPACITY_KT for p in pile_ids]
        ax_comp.bar(
            pile_ids,
            heights,
            bottom=bottoms,
            color=cmap(index % 20),
            label=f"{mineral_id} ({evaluation.usage_by_mineral[mineral_id]} cam.)",
            edgecolor="white",
            linewidth=0.5,
        )
        bottoms = [b + h for b, h in zip(bottoms, heights)]

    ax_comp.set_ylabel("Massa (kt)")
    ax_comp.set_title(
        f"{title}\ncusto = R$ {evaluation.cost_rs:,.0f} | "
        f"f2 = {evaluation.f2_sio2_sq_dev:.4f} | f3 = {evaluation.f3_al2o3_sq_dev:.4f} | "
        f"factível = {'sim' if evaluation.feasible else 'não'}"
    )
    ax_comp.legend(ncol=2, fontsize=8, bbox_to_anchor=(1.01, 1), loc="upper left")

    for ax, attr, lo, tg, hi, label in (
        (ax_si, "sio2_pct", "sio2_min", "sio2_target", "sio2_max", "SiO₂ (%)"),
        (ax_al, "al2o3_pct", "al2o3_min", "al2o3_target", "al2o3_max", "Al₂O₃ (%)"),
    ):
        values = [getattr(evaluation.quality_by_pile[p], attr) for p in pile_ids]
        ax.plot(pile_ids, values, "o-", color="black", label="pilha")

        for group_id, group in instance.groups.items():
            group_piles = [
                i for i, p in enumerate(pile_ids) if instance.piles[p].group_id == group_id
            ]
            x0, x1 = min(group_piles) - 0.4, max(group_piles) + 0.4
            ax.fill_between(
                [x0, x1], getattr(group, lo), getattr(group, hi), alpha=0.12, color="green"
            )
            ax.hlines(getattr(group, tg), x0, x1, colors="red", linestyles="--")
            ax.text(x0, getattr(group, hi), f" {group_id}", va="bottom", fontsize=8)

        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

    ax_al.set_xlabel("Pilha (faixa verde = limites do grupo; tracejado = alvo)")
    fig.tight_layout()
    return fig
