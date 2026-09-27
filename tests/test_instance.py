from pathlib import Path

from cassotis_optimization.io import load_instance
from cassotis_optimization.validation import validate_instance

DATA_DIR = Path("data/example_instance")


def test_example_instance_is_structurally_valid() -> None:
    instance = load_instance(DATA_DIR)

    assert validate_instance(instance) == []
    assert len(instance.minerals) == 20
    assert len(instance.groups) == 2
    assert len(instance.piles) == 10
    assert sum(pile.n_trucks for pile in instance.piles.values()) == 145


def test_confirmed_global_minimum_availabilities() -> None:
    instance = load_instance(DATA_DIR)

    minimums = {
        mineral_id: mineral.min_trucks
        for mineral_id, mineral in instance.minerals.items()
        if mineral.min_trucks > 0
    }

    assert minimums == {
        "M4": 2,
        "M10": 2,
        "M11": 1,
        "M20": 1,
    }


def test_group_targets_match_example_data() -> None:
    instance = load_instance(DATA_DIR)

    assert instance.groups["Sinter1"].sio2_target == 5.55
    assert instance.groups["Sinter1"].al2o3_target == 1.25
    assert instance.groups["Sinter2"].sio2_target == 5.50
    assert instance.groups["Sinter2"].al2o3_target == 1.50
