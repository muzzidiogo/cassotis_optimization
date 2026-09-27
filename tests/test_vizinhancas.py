import random
from pathlib import Path

from cassotis_optimization.algorithms.constructive import (
    construct_initial_solution,
)
from cassotis_optimization.algorithms.vizinhancas import n1_replace, n2_swap, n3_relocate_replace
from cassotis_optimization.io import load_instance

DATA_DIR = Path("data/example_instance")


def test_n1_preserves_pile_sizes() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n1_replace(
        solution,
        instance,
        random.Random(42),
    )

    for pile_id, pile in instance.piles.items():
        assert len(neighbor.composition[pile_id]) == pile.n_trucks


def test_n1_preserves_eligibility() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n1_replace(
        solution,
        instance,
        random.Random(42),
    )

    for pile_id, mineral_ids in neighbor.composition.items():
        pile = instance.piles[pile_id]

        for mineral_id in mineral_ids:
            mineral = instance.minerals[mineral_id]
            assert mineral.is_eligible(pile.group_id)


def test_n1_does_not_modify_original_solution() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    original = dict(solution.composition)

    _ = n1_replace(
        solution,
        instance,
        random.Random(42),
    )

    assert solution.composition == original

def test_n2_preserves_pile_sizes() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n2_swap(
        solution,
        instance,
        random.Random(42),
    )

    for pile_id, pile in instance.piles.items():
        assert len(neighbor.composition[pile_id]) == pile.n_trucks


def test_n2_preserves_eligibility() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n2_swap(
        solution,
        instance,
        random.Random(42),
    )

    for pile_id, mineral_ids in neighbor.composition.items():
        pile = instance.piles[pile_id]

        for mineral_id in mineral_ids:
            assert instance.minerals[mineral_id].is_eligible(
                pile.group_id
            )


def test_n2_preserves_global_mineral_usage() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n2_swap(
        solution,
        instance,
        random.Random(42),
    )

    assert neighbor.total_usage(instance) == solution.total_usage(instance)


def test_n2_does_not_modify_original_solution() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    original = dict(solution.composition)

    _ = n2_swap(
        solution,
        instance,
        random.Random(42),
    )

    assert solution.composition == original

def test_n3_preserves_pile_sizes() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n3_relocate_replace(
        solution,
        instance,
        random.Random(42),
    )

    for pile_id, pile in instance.piles.items():
        assert len(neighbor.composition[pile_id]) == pile.n_trucks


def test_n3_preserves_eligibility() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n3_relocate_replace(
        solution,
        instance,
        random.Random(42),
    )

    for pile_id, mineral_ids in neighbor.composition.items():
        pile = instance.piles[pile_id]

        for mineral_id in mineral_ids:
            assert instance.minerals[mineral_id].is_eligible(
                pile.group_id
            )


def test_n3_changes_exactly_two_piles() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n3_relocate_replace(
        solution,
        instance,
        random.Random(42),
    )

    changed_piles = [
        pile_id
        for pile_id in instance.piles
        if neighbor.composition[pile_id]
        != solution.composition[pile_id]
    ]

    assert len(changed_piles) == 2


def test_n3_changes_global_mineral_usage() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    neighbor = n3_relocate_replace(
        solution,
        instance,
        random.Random(42),
    )

    before = solution.total_usage(instance)
    after = neighbor.total_usage(instance)

    differences = {
        mineral_id: after[mineral_id] - before[mineral_id]
        for mineral_id in instance.minerals
        if after[mineral_id] != before[mineral_id]
    }

    assert len(differences) == 2
    assert sorted(differences.values()) == [-1, 1]


def test_n3_does_not_modify_original_solution() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    original = dict(solution.composition)

    _ = n3_relocate_replace(
        solution,
        instance,
        random.Random(42),
    )

    assert solution.composition == original