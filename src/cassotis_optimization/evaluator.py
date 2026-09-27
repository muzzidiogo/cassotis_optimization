from __future__ import annotations

from dataclasses import dataclass

from .domain import TONNES_PER_KT, TRUCK_CAPACITY_KT, ProblemInstance
from .solution import Solution


@dataclass(frozen=True)
class PileQuality:
    fet_pct: float
    sio2_pct: float
    al2o3_pct: float


@dataclass(frozen=True)
class Evaluation:
    cost_rs: float
    f2_sio2_sq_dev: float
    f3_al2o3_sq_dev: float
    feasible: bool
    violations: dict[str, float]
    quality_by_pile: dict[str, PileQuality]
    usage_by_mineral: dict[str, int]

    @property
    def total_raw_violation(self) -> float:
        """Diagnostic only. Do not use as the final infeasibility policy."""
        return sum(self.violations.values())


def _outside_amount(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower - value
    if value > upper:
        return value - upper
    return 0.0


def evaluate(solution: Solution, instance: ProblemInstance) -> Evaluation:
    violations: dict[str, float] = {}
    quality_by_pile: dict[str, PileQuality] = {}
    usage = {mineral_id: 0 for mineral_id in instance.minerals}

    cost_rs = 0.0
    f2 = 0.0
    f3 = 0.0

    expected_piles = set(instance.piles)
    actual_piles = set(solution.composition)
    if actual_piles != expected_piles:
        missing = expected_piles - actual_piles
        extra = actual_piles - expected_piles
        if missing:
            violations["missing_piles"] = float(len(missing))
        if extra:
            violations["extra_piles"] = float(len(extra))

    for pile_id, pile in instance.piles.items():
        minerals_in_pile = solution.composition.get(pile_id, ())
        if len(minerals_in_pile) != pile.n_trucks:
            violations[f"{pile_id}:mass_slots"] = float(
                abs(len(minerals_in_pile) - pile.n_trucks)
            )

        if not minerals_in_pile:
            continue

        sum_fet = 0.0
        sum_sio2 = 0.0
        sum_al2o3 = 0.0

        for mineral_id in minerals_in_pile:
            mineral = instance.minerals.get(mineral_id)
            if mineral is None:
                violations[f"{pile_id}:unknown_mineral:{mineral_id}"] = 1.0
                continue

            usage[mineral_id] += 1

            if not mineral.is_eligible(pile.group_id):
                key = f"{pile_id}:ineligible:{mineral_id}"
                violations[key] = violations.get(key, 0.0) + 1.0

            sum_fet += mineral.fet_pct
            sum_sio2 += mineral.sio2_pct
            sum_al2o3 += mineral.al2o3_pct
            cost_rs += (
                mineral.price_rs_per_t
                * TRUCK_CAPACITY_KT
                * TONNES_PER_KT
            )

        denominator = len(minerals_in_pile)
        quality = PileQuality(
            fet_pct=sum_fet / denominator,
            sio2_pct=sum_sio2 / denominator,
            al2o3_pct=sum_al2o3 / denominator,
        )
        quality_by_pile[pile_id] = quality

        group = instance.groups[pile.group_id]

        sio2_violation = _outside_amount(
            quality.sio2_pct, group.sio2_min, group.sio2_max
        )
        if sio2_violation > 0:
            violations[f"{pile_id}:sio2"] = sio2_violation

        al2o3_violation = _outside_amount(
            quality.al2o3_pct, group.al2o3_min, group.al2o3_max
        )
        if al2o3_violation > 0:
            violations[f"{pile_id}:al2o3"] = al2o3_violation

        f2 += (quality.sio2_pct - group.sio2_target) ** 2
        f3 += (quality.al2o3_pct - group.al2o3_target) ** 2

    for mineral_id, mineral in instance.minerals.items():
        used = usage[mineral_id]
        if used < mineral.min_trucks:
            violations[f"{mineral_id}:availability_min"] = float(
                mineral.min_trucks - used
            )
        if used > mineral.max_trucks:
            violations[f"{mineral_id}:availability_max"] = float(
                used - mineral.max_trucks
            )

    return Evaluation(
        cost_rs=cost_rs,
        f2_sio2_sq_dev=f2,
        f3_al2o3_sq_dev=f3,
        feasible=not violations,
        violations=violations,
        quality_by_pile=quality_by_pile,
        usage_by_mineral=usage,
    )
