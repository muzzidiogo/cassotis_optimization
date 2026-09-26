from __future__ import annotations

import random

from cassotis_optimization.domain import ProblemInstance
from cassotis_optimization.solution import Solution


def n1_replace(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    """Replace one truck slot by another eligible mineral."""

    pile_id = rng.choice(list(instance.piles.keys()))
    pile = instance.piles[pile_id]

    current_composition = list(solution.composition[pile_id])

    position = rng.randrange(len(current_composition))
    current_mineral = current_composition[position]

    candidates = [
        mineral_id
        for mineral_id, mineral in instance.minerals.items()
        if (
            mineral_id != current_mineral
            and mineral.is_eligible(pile.group_id)
        )
    ]

    if not candidates:
        return solution

    new_mineral = rng.choice(candidates)

    current_composition[position] = new_mineral

    new_composition = dict(solution.composition)
    new_composition[pile_id] = tuple(current_composition)

    return Solution(composition=new_composition)

def n2_swap(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    """Swap two truck slots from different piles while preserving eligibility."""

    pile_ids = list(instance.piles.keys())

    valid_moves: list[tuple[str, int, str, int]] = []

    for i, pile_a_id in enumerate(pile_ids):
        pile_a = instance.piles[pile_a_id]
        composition_a = solution.composition[pile_a_id]

        for pile_b_id in pile_ids[i + 1:]:
            pile_b = instance.piles[pile_b_id]
            composition_b = solution.composition[pile_b_id]

            for pos_a, mineral_a_id in enumerate(composition_a):
                mineral_a = instance.minerals[mineral_a_id]

                for pos_b, mineral_b_id in enumerate(composition_b):
                    if mineral_a_id == mineral_b_id:
                        continue

                    mineral_b = instance.minerals[mineral_b_id]

                    if (
                        mineral_a.is_eligible(pile_b.group_id)
                        and mineral_b.is_eligible(pile_a.group_id)
                    ):
                        valid_moves.append(
                            (
                                pile_a_id,
                                pos_a,
                                pile_b_id,
                                pos_b,
                            )
                        )

    if not valid_moves:
        return solution

    pile_a_id, pos_a, pile_b_id, pos_b = rng.choice(valid_moves)

    composition_a = list(solution.composition[pile_a_id])
    composition_b = list(solution.composition[pile_b_id])

    composition_a[pos_a], composition_b[pos_b] = (
        composition_b[pos_b],
        composition_a[pos_a],
    )

    new_composition = dict(solution.composition)
    new_composition[pile_a_id] = tuple(composition_a)
    new_composition[pile_b_id] = tuple(composition_b)

    return Solution(composition=new_composition)

def n3_relocate_replace(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    """
    Relocate one mineral between two piles while introducing another mineral.

    Given:
        pile_a: m_x
        pile_b: m_y

    The move produces:
        pile_a: m_z
        pile_b: m_x

    where m_z, m_x and m_y are distinct minerals.

    Mass and eligibility are preserved by construction.
    Global mineral usage may change.
    """

    pile_ids = list(instance.piles.keys())

    valid_moves: list[tuple[str, int, str, int, str]] = []

    # Unlike N2, the direction matters:
    # pile_a -> pile_b is different from pile_b -> pile_a.
    for pile_a_id in pile_ids:
        pile_a = instance.piles[pile_a_id]
        composition_a = solution.composition[pile_a_id]

        for pile_b_id in pile_ids:
            if pile_a_id == pile_b_id:
                continue

            pile_b = instance.piles[pile_b_id]
            composition_b = solution.composition[pile_b_id]

            for pos_a, mineral_x_id in enumerate(composition_a):
                mineral_x = instance.minerals[mineral_x_id]

                # m_x will be moved to pile_b.
                if not mineral_x.is_eligible(pile_b.group_id):
                    continue

                for pos_b, mineral_y_id in enumerate(composition_b):

                    # If m_x == m_y, the movement in pile_b would
                    # have no effect and N3 would degenerate into N1.
                    if mineral_x_id == mineral_y_id:
                        continue

                    for mineral_z_id, mineral_z in instance.minerals.items():

                        # Keep N3 distinct from N1 and N2.
                        if mineral_z_id in {
                            mineral_x_id,
                            mineral_y_id,
                        }:
                            continue

                        # m_z will enter pile_a.
                        if not mineral_z.is_eligible(pile_a.group_id):
                            continue

                        valid_moves.append(
                            (
                                pile_a_id,
                                pos_a,
                                pile_b_id,
                                pos_b,
                                mineral_z_id,
                            )
                        )

    if not valid_moves:
        return solution

    (
        pile_a_id,
        pos_a,
        pile_b_id,
        pos_b,
        mineral_z_id,
    ) = rng.choice(valid_moves)

    composition_a = list(solution.composition[pile_a_id])
    composition_b = list(solution.composition[pile_b_id])

    mineral_x_id = composition_a[pos_a]

    # Chain:
    # pile_a: m_x -> m_z
    # pile_b: m_y -> m_x
    composition_a[pos_a] = mineral_z_id
    composition_b[pos_b] = mineral_x_id

    new_composition = dict(solution.composition)
    new_composition[pile_a_id] = tuple(composition_a)
    new_composition[pile_b_id] = tuple(composition_b)

    return Solution(composition=new_composition)