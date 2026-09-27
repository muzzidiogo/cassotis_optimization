"""
Shake structures P1, P2, P3 of the GVNS (D015).

They are separate from the neighborhoods N1, N2, N3 used by the VND: the
neighborhoods intensify, the perturbations move the search to progressively
more distant regions. All of them preserve pile mass and mineral eligibility.

Unlike the local search, perturbations pick truck slots (positions) uniformly,
as in the position-based wording of the case: a random truck is chosen, so a
mineral that fills more slots of a pile is more likely to be touched.

    P1 (small):   replace the mineral of ``n_positions`` random slots.
    P2 (medium):  ejection chain over ``chain_length`` distinct piles:
                  p1 receives a new mineral, p_{i+1} receives the mineral that
                  left p_i, and the mineral of the last pile leaves the solution.
    P3 (strong):  cyclic permutation of one slot from each of ``n_piles`` piles
                  of the same sinter group (global usage is unchanged).
"""

from __future__ import annotations

import random

from cassotis_optimization.domain import ProblemInstance
from cassotis_optimization.solution import Solution

_MAX_ATTEMPTS = 200

Slot = tuple[str, int]


def _eligible_minerals(instance: ProblemInstance, group_id: str) -> list[str]:
    return [
        mineral_id
        for mineral_id, mineral in instance.minerals.items()
        if mineral.is_eligible(group_id)
    ]


def _with_assignments(solution: Solution, assignments: dict[Slot, str]) -> Solution:
    new_composition = dict(solution.composition)
    for (pile_id, position), mineral_id in assignments.items():
        slots = list(new_composition[pile_id])
        slots[position] = mineral_id
        new_composition[pile_id] = tuple(slots)
    return Solution(composition=new_composition)


def _random_slot(solution: Solution, pile_id: str, rng: random.Random) -> Slot:
    return pile_id, rng.randrange(len(solution.composition[pile_id]))


def p1_random_replacements(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
    n_positions: int = 2,
) -> Solution:
    """P1: replace the mineral of ``n_positions`` distinct random slots."""

    all_slots = [
        (pile_id, position)
        for pile_id, minerals in solution.composition.items()
        for position in range(len(minerals))
    ]

    assignments: dict[Slot, str] = {}
    for pile_id, position in rng.sample(all_slots, min(n_positions, len(all_slots))):
        current = solution.composition[pile_id][position]
        group_id = instance.piles[pile_id].group_id
        candidates = [m for m in _eligible_minerals(instance, group_id) if m != current]
        if candidates:
            assignments[(pile_id, position)] = rng.choice(candidates)

    return _with_assignments(solution, assignments)


def p2_ejection_chain(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
    chain_length: int = 3,
) -> Solution:
    """
    P2: ejection chain over ``chain_length`` distinct piles.

        p_1: m_1 -> z        (z is a new mineral, eligible for p_1)
        p_2: m_2 -> m_1
        ...
        p_L: m_L -> m_{L-1}  (m_L leaves the solution)

    Requires m_i eligible for p_{i+1} and m_i != m_{i+1}. Global usage changes
    by +1 for z and -1 for m_L.
    """

    pile_ids = list(instance.piles)
    chain_length = min(chain_length, len(pile_ids))

    for _ in range(_MAX_ATTEMPTS):
        piles = rng.sample(pile_ids, chain_length)
        slots = [_random_slot(solution, pile_id, rng) for pile_id in piles]
        minerals = [solution.composition[p][i] for p, i in slots]

        valid_chain = all(
            minerals[i] != minerals[i + 1]
            and instance.minerals[minerals[i]].is_eligible(
                instance.piles[piles[i + 1]].group_id
            )
            for i in range(chain_length - 1)
        )
        if not valid_chain:
            continue

        group_first = instance.piles[piles[0]].group_id
        candidates_z = [
            m for m in _eligible_minerals(instance, group_first) if m != minerals[0]
        ]
        if not candidates_z:
            continue

        assignments = {slots[0]: rng.choice(candidates_z)}
        for i in range(1, chain_length):
            assignments[slots[i]] = minerals[i - 1]
        return _with_assignments(solution, assignments)

    return solution


def p3_group_permutation(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
    n_piles: int = 5,
) -> Solution:
    """
    P3: cyclic permutation of one random slot from each of ``n_piles`` piles
    of the same sinter group.

    Piles of the same group share eligibility, so any mineral taken from one of
    them may enter the others. Global usage (availability) is unchanged; the
    move redistributes minerals among piles to change their quality.
    """

    piles_by_group: dict[str, list[str]] = {}
    for pile_id, pile in instance.piles.items():
        piles_by_group.setdefault(pile.group_id, []).append(pile_id)
    groups = [g for g, piles in piles_by_group.items() if len(piles) >= 2]

    for _ in range(_MAX_ATTEMPTS):
        group_piles = piles_by_group[rng.choice(groups)]
        piles = rng.sample(group_piles, min(n_piles, len(group_piles)))
        slots = [_random_slot(solution, pile_id, rng) for pile_id in piles]
        minerals = [solution.composition[p][i] for p, i in slots]

        if len(set(minerals)) < 2:
            continue

        # Slot i receives the mineral of slot i-1 (cyclic).
        assignments = {
            slots[i]: minerals[i - 1] for i in range(len(slots))
        }
        return _with_assignments(solution, assignments)

    return solution

