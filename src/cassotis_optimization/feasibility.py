from __future__ import annotations

from dataclasses import dataclass

from .domain import ProblemInstance
from .evaluator import Evaluation


@dataclass(frozen=True)
class ViolationSummary:
    sio2: float
    al2o3: float
    availability_min: float
    availability_max: float

    @property
    def total(self) -> float:
        return (
            self.sio2
            + self.al2o3
            + self.availability_min
            + self.availability_max
        )


def normalized_violation(
    evaluation: Evaluation,
    instance: ProblemInstance,
) -> ViolationSummary:
    sio2 = 0.0
    al2o3 = 0.0

    for pile_id, quality in evaluation.quality_by_pile.items():
        pile = instance.piles[pile_id]
        group = instance.groups[pile.group_id]

        sio2_range = group.sio2_max - group.sio2_min
        al2o3_range = group.al2o3_max - group.al2o3_min

        if quality.sio2_pct < group.sio2_min:
            sio2 += (
                group.sio2_min - quality.sio2_pct
            ) / sio2_range

        elif quality.sio2_pct > group.sio2_max:
            sio2 += (
                quality.sio2_pct - group.sio2_max
            ) / sio2_range

        if quality.al2o3_pct < group.al2o3_min:
            al2o3 += (
                group.al2o3_min - quality.al2o3_pct
            ) / al2o3_range

        elif quality.al2o3_pct > group.al2o3_max:
            al2o3 += (
                quality.al2o3_pct - group.al2o3_max
            ) / al2o3_range

    availability_min = 0.0
    availability_max = 0.0

    for mineral_id, mineral in instance.minerals.items():
        used = evaluation.usage_by_mineral[mineral_id]

        # Maximum availability is used as the scale so that
        # violations are expressed relative to the mineral's capacity.
        scale = max(1, mineral.max_trucks)

        if used < mineral.min_trucks:
            availability_min += (
                mineral.min_trucks - used
            ) / scale

        elif used > mineral.max_trucks:
            availability_max += (
                used - mineral.max_trucks
            ) / scale

    return ViolationSummary(
        sio2=sio2,
        al2o3=al2o3,
        availability_min=availability_min,
        availability_max=availability_max,
    )

def feasibility_rule_key(
    feasible: bool,
    violation: float,
    objective: float,
) -> tuple[int, float, float]:
    """
    Sort key for the feasibility rule adopted in D007 (smaller is better).

    1. a feasible solution beats an infeasible one;
    2. between two feasible solutions, the smaller objective wins;
    3. between two infeasible solutions, the smaller normalized violation wins
       (objective used only as a tie-breaker).
    """

    if feasible:
        return (0, objective, 0.0)
    return (1, violation, objective)
