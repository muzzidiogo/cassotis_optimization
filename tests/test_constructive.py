from pathlib import Path

from cassotis_optimization.algorithms.constructive import (
    construct_initial_solution,
)
from cassotis_optimization.io import load_instance

DATA_DIR = Path("data/example_instance")


def test_constructive_respects_pile_sizes() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    for pile_id, pile in instance.piles.items():
        assert len(solution.composition[pile_id]) == pile.n_trucks


def test_constructive_respects_eligibility() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    for pile_id, mineral_ids in solution.composition.items():
        pile = instance.piles[pile_id]

        for mineral_id in mineral_ids:
            mineral = instance.minerals[mineral_id]

            assert mineral.is_eligible(pile.group_id)


def test_constructive_respects_global_availability() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    usage = solution.total_usage(instance)

    for mineral_id, mineral in instance.minerals.items():
        assert usage[mineral_id] >= mineral.min_trucks
        assert usage[mineral_id] <= mineral.max_trucks