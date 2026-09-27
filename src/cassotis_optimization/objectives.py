from __future__ import annotations

from typing import Literal

from .evaluator import Evaluation

ObjectiveName = Literal["f1", "f2", "f3"]


def objective_value(
    evaluation: Evaluation,
    objective: ObjectiveName,
) -> float:
    """Return the objective value to be minimized."""

    if objective == "f1":
        return evaluation.cost_rs

    if objective == "f2":
        return evaluation.f2_sio2_sq_dev

    if objective == "f3":
        return evaluation.f3_al2o3_sq_dev

    raise ValueError(f"Unknown objective: {objective}")