from __future__ import annotations

import random
from bisect import bisect_right
from collections.abc import Callable
from itertools import accumulate

from cassotis_optimization.domain import ProblemInstance
from cassotis_optimization.solution import Solution

# A move is a tuple of slot substitutions (pile_id, mineral_out, mineral_in).
#
#   N1: ((p, m_old, m_new),)
#   N2: ((p_a, m_a, m_b), (p_b, m_b, m_a))
#   N3: ((p_a, m_x, m_z), (p_b, m_y, m_x))
#
# Slots holding the same mineral inside a pile are interchangeable: choosing
# any of them yields the same pile composition. Moves are therefore defined
# over the distinct minerals of each pile, which removes duplicated neighbors
# without changing the set of reachable solutions (D014).
Substitution = tuple[str, str, str]
Move = tuple[Substitution, ...]


def apply_move(solution: Solution, move: Move) -> Solution:
    """Return a new solution with the move applied. The input is not modified."""

    new_composition = dict(solution.composition)

    for pile_id, mineral_out, mineral_in in move:
        slots = list(new_composition[pile_id])
        slots[slots.index(mineral_out)] = mineral_in
        new_composition[pile_id] = tuple(slots)

    return Solution(composition=new_composition)


def _distinct_minerals(solution: Solution, pile_id: str) -> list[str]:
    return sorted(set(solution.composition[pile_id]))


def _eligible_minerals(instance: ProblemInstance, group_id: str) -> list[str]:
    return [
        mineral_id
        for mineral_id, mineral in instance.minerals.items()
        if mineral.is_eligible(group_id)
    ]


# ---------------------------------------------------------------------------
# Full enumeration (used by the local search)
# ---------------------------------------------------------------------------


def n1_moves(solution: Solution, instance: ProblemInstance) -> list[Move]:
    """All N1 moves: replace one mineral of a pile by another eligible mineral."""

    moves: list[Move] = []

    for pile_id, pile in instance.piles.items():
        eligible = _eligible_minerals(instance, pile.group_id)

        for mineral_out in _distinct_minerals(solution, pile_id):
            for mineral_in in eligible:
                if mineral_in != mineral_out:
                    moves.append(((pile_id, mineral_out, mineral_in),))

    return moves


def n2_moves(solution: Solution, instance: ProblemInstance) -> list[Move]:
    """All N2 moves: swap two different minerals between two piles."""

    moves: list[Move] = []
    pile_ids = list(instance.piles)

    for i, pile_a_id in enumerate(pile_ids):
        group_a = instance.piles[pile_a_id].group_id

        for pile_b_id in pile_ids[i + 1:]:
            group_b = instance.piles[pile_b_id].group_id

            for mineral_a in _distinct_minerals(solution, pile_a_id):
                if not instance.minerals[mineral_a].is_eligible(group_b):
                    continue

                for mineral_b in _distinct_minerals(solution, pile_b_id):
                    if mineral_a == mineral_b:
                        continue
                    if not instance.minerals[mineral_b].is_eligible(group_a):
                        continue

                    moves.append(
                        (
                            (pile_a_id, mineral_a, mineral_b),
                            (pile_b_id, mineral_b, mineral_a),
                        )
                    )

    return moves


def n3_moves(solution: Solution, instance: ProblemInstance) -> list[Move]:
    """
    All N3 moves (relocation with chained replacement, D008).

        pile_a: m_x -> m_z
        pile_b: m_y -> m_x

    with m_x, m_y and m_z distinct. The neighborhood is large (order of 10^5
    moves on the example instance), so the local search samples it instead of
    enumerating it (see ``sample_moves`` and D014).
    """

    moves: list[Move] = []

    for pile_a_id, pile_a in instance.piles.items():
        eligible_a = _eligible_minerals(instance, pile_a.group_id)

        for pile_b_id, pile_b in instance.piles.items():
            if pile_a_id == pile_b_id:
                continue

            for mineral_x in _distinct_minerals(solution, pile_a_id):
                if not instance.minerals[mineral_x].is_eligible(pile_b.group_id):
                    continue

                for mineral_y in _distinct_minerals(solution, pile_b_id):
                    if mineral_y == mineral_x:
                        continue

                    for mineral_z in eligible_a:
                        if mineral_z in (mineral_x, mineral_y):
                            continue

                        moves.append(
                            (
                                (pile_a_id, mineral_x, mineral_z),
                                (pile_b_id, mineral_y, mineral_x),
                            )
                        )

    return moves


# ---------------------------------------------------------------------------
# Uniform sampling without replacement (used by the sampled local search)
# ---------------------------------------------------------------------------


def _n3_prefixes(
    solution: Solution,
    instance: ProblemInstance,
) -> tuple[list[tuple[str, str, str, str, list[str]]], list[int]]:
    """
    Group the N3 moves by prefix (pile_a, pile_b, m_x, m_y).

    Each prefix carries the list of valid m_z; its weight is the length of that
    list. Drawing a prefix proportionally to its weight and then m_z uniformly
    gives every distinct N3 move the same probability, without enumerating the
    whole neighborhood.
    """

    prefixes: list[tuple[str, str, str, str, list[str]]] = []
    weights: list[int] = []

    for pile_a_id, pile_a in instance.piles.items():
        eligible_a = _eligible_minerals(instance, pile_a.group_id)

        for pile_b_id, pile_b in instance.piles.items():
            if pile_a_id == pile_b_id:
                continue

            for mineral_x in _distinct_minerals(solution, pile_a_id):
                if not instance.minerals[mineral_x].is_eligible(pile_b.group_id):
                    continue

                for mineral_y in _distinct_minerals(solution, pile_b_id):
                    if mineral_y == mineral_x:
                        continue

                    candidates_z = [
                        m for m in eligible_a if m not in (mineral_x, mineral_y)
                    ]
                    if candidates_z:
                        prefixes.append(
                            (pile_a_id, pile_b_id, mineral_x, mineral_y, candidates_z)
                        )
                        weights.append(len(candidates_z))

    return prefixes, weights


def _sample_n3_moves(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
    k: int,
) -> list[Move]:
    prefixes, weights = _n3_prefixes(solution, instance)
    total = sum(weights)

    if k >= total:
        moves = n3_moves(solution, instance)
        rng.shuffle(moves)
        return moves

    cumulative = list(accumulate(weights))
    chosen: dict[Move, None] = {}

    while len(chosen) < k:
        index = bisect_right(cumulative, rng.randrange(total))
        pile_a_id, pile_b_id, mineral_x, mineral_y, candidates_z = prefixes[index]
        move = (
            (pile_a_id, mineral_x, rng.choice(candidates_z)),
            (pile_b_id, mineral_y, mineral_x),
        )
        chosen.setdefault(move)

    return list(chosen)


def sample_moves(
    name: str,
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
    k: int,
) -> list[Move]:
    """
    Up to ``k`` distinct moves of N_name(solution), drawn uniformly without
    replacement over the distinct moves (D014). If ``k`` is at least the size of
    the neighborhood, the whole neighborhood is returned in random order.
    """

    if name == "N3":
        return _sample_n3_moves(solution, instance, rng, k)

    moves = ENUMERATORS[name](solution, instance)
    if k >= len(moves):
        rng.shuffle(moves)
        return moves
    return rng.sample(moves, k)


def sample_move(
    name: str,
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Move | None:
    """One move of N_name(solution), uniformly over the distinct moves."""

    moves = sample_moves(name, solution, instance, rng, 1)
    return moves[0] if moves else None


MoveEnumerator = Callable[[Solution, ProblemInstance], list[Move]]

ENUMERATORS: dict[str, MoveEnumerator] = {
    "N1": n1_moves,
    "N2": n2_moves,
    "N3": n3_moves,
}


# ---------------------------------------------------------------------------
# Single random neighbor
# ---------------------------------------------------------------------------


def _random_neighbor(
    name: str,
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    move = sample_move(name, solution, instance, rng)
    if move is None:
        return solution
    return apply_move(solution, move)


def n1_replace(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    """Replace one truck slot by another eligible mineral."""

    return _random_neighbor("N1", solution, instance, rng)


def n2_swap(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    """Swap two truck slots from different piles while preserving eligibility."""

    return _random_neighbor("N2", solution, instance, rng)


def n3_relocate_replace(
    solution: Solution,
    instance: ProblemInstance,
    rng: random.Random,
) -> Solution:
    """
    Relocate one mineral between two piles while introducing another mineral.

        pile_a: m_x -> m_z
        pile_b: m_y -> m_x

    Mass and eligibility are preserved by construction.
    Global mineral usage may change.
    """

    return _random_neighbor("N3", solution, instance, rng)
