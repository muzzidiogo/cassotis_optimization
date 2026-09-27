import random
from pathlib import Path

import pytest

from cassotis_optimization.algorithms.constructive import construct_initial_solution
from cassotis_optimization.algorithms.gvns import GVNSConfig, is_better, run_gvns
from cassotis_optimization.algorithms.perturbacoes import (
    p1_random_replacements,
    p2_ejection_chain,
    p3_group_permutation,
)
from cassotis_optimization.algorithms.vizinhancas import (
    ENUMERATORS,
    _n3_prefixes,
    apply_move,
    sample_move,
    sample_moves,
)
from cassotis_optimization.evaluator import evaluate
from cassotis_optimization.io import load_instance

DATA_DIR = Path("data/example_instance")


def _assert_structure_preserved(solution, instance) -> None:
    for pile_id, pile in instance.piles.items():
        assert len(solution.composition[pile_id]) == pile.n_trucks
        for mineral_id in solution.composition[pile_id]:
            assert instance.minerals[mineral_id].is_eligible(pile.group_id)


@pytest.mark.parametrize("name", ["N1", "N2"])
def test_enumerated_moves_preserve_mass_and_eligibility(name) -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    moves = ENUMERATORS[name](solution, instance)

    assert moves
    assert len(set(moves)) == len(moves)
    for move in moves:
        _assert_structure_preserved(apply_move(solution, move), instance)


@pytest.mark.parametrize("name", ["N1", "N2", "N3"])
def test_sampled_moves_belong_to_the_enumerated_neighborhood(name) -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)
    rng = random.Random(7)

    enumerated = set(ENUMERATORS[name](solution, instance))

    for _ in range(50):
        assert sample_move(name, solution, instance, rng) in enumerated

    sample = sample_moves(name, solution, instance, rng, 500)
    assert len(sample) == min(500, len(enumerated))
    assert len(set(sample)) == len(sample)
    assert set(sample) <= enumerated


@pytest.mark.parametrize("name", ["N1", "N2", "N3"])
def test_large_sample_returns_whole_neighborhood(name) -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    enumerated = ENUMERATORS[name](solution, instance)
    sample = sample_moves(name, solution, instance, random.Random(1), 10**7)

    assert sorted(sample) == sorted(enumerated)


def test_n3_prefix_weights_cover_each_distinct_move_once() -> None:
    # Uniformity of the N3 sampler: a prefix is drawn with probability
    # proportional to its number of m_z, then m_z uniformly, so each distinct
    # move has probability 1 / |N3| exactly when the weights add up to |N3|
    # and the (prefix, m_z) pairs are exactly the enumerated moves.
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)

    prefixes, weights = _n3_prefixes(solution, instance)
    moves_from_prefixes = {
        ((a, x, z), (b, y, x))
        for a, b, x, y, candidates in prefixes
        for z in candidates
    }

    assert sum(weights) == len(moves_from_prefixes)
    assert moves_from_prefixes == set(ENUMERATORS["N3"](solution, instance))


def test_sampling_does_not_favor_frequent_minerals() -> None:
    # Pile P1 gets 9 slots of M1 and 1 slot of M2. A slot-based sampler would
    # pick M1 as the outgoing mineral ~90% of the time; over distinct moves
    # both minerals are equally likely.
    instance = load_instance(DATA_DIR)
    base = construct_initial_solution(instance)
    composition = dict(base.composition)
    composition["P1"] = ("M1",) * 9 + ("M2",)
    solution = type(base)(composition)

    rng = random.Random(0)
    for name, k in (("N1", 600), ("N3", 20000)):
        outgoing = {"M1": 0, "M2": 0}
        for move in sample_moves(name, solution, instance, rng, k):
            pile_id, mineral_out, _ = move[0]
            if pile_id == "P1":
                outgoing[mineral_out] += 1

        share_m1 = outgoing["M1"] / (outgoing["M1"] + outgoing["M2"])
        assert 0.35 < share_m1 < 0.65, (name, outgoing)


@pytest.mark.parametrize(
    "perturbation",
    [p1_random_replacements, p2_ejection_chain, p3_group_permutation],
)
def test_perturbations_preserve_mass_and_eligibility(perturbation) -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)
    rng = random.Random(13)

    for _ in range(50):
        shaken = perturbation(solution, instance, rng)
        _assert_structure_preserved(shaken, instance)
        assert shaken != solution
        solution = shaken


def test_perturbation_sizes() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)
    rng = random.Random(21)

    def changed_slots(a, b):
        return sum(
            x != y
            for pile_id in a.composition
            for x, y in zip(a.composition[pile_id], b.composition[pile_id])
        )

    for _ in range(30):
        assert changed_slots(solution, p1_random_replacements(solution, instance, rng)) <= 2
        assert changed_slots(solution, p2_ejection_chain(solution, instance, rng)) <= 3
        assert changed_slots(solution, p3_group_permutation(solution, instance, rng)) <= 5


def test_p3_preserves_global_usage_and_stays_in_one_group() -> None:
    instance = load_instance(DATA_DIR)
    solution = construct_initial_solution(instance)
    rng = random.Random(17)

    for _ in range(30):
        shaken = p3_group_permutation(solution, instance, rng)
        assert shaken.total_usage(instance) == solution.total_usage(instance)

        changed_groups = {
            instance.piles[p].group_id
            for p in instance.piles
            if shaken.composition[p] != solution.composition[p]
        }
        assert len(changed_groups) == 1


def test_feasibility_rule_ordering() -> None:
    instance = load_instance(DATA_DIR)
    result = run_gvns(instance, GVNSConfig(objective="f1", seed=0, max_evaluations=3000))

    assert result.best.feasible
    assert not result.initial.feasible
    assert is_better(result.best, result.initial)
    assert not is_better(result.initial, result.best)


@pytest.mark.parametrize("objective", ["f1", "f2", "f3"])
def test_gvns_respects_budget_and_returns_consistent_best(objective) -> None:
    instance = load_instance(DATA_DIR)
    config = GVNSConfig(objective=objective, seed=3, max_evaluations=4000)

    result = run_gvns(instance, config)

    assert result.evaluations == config.max_evaluations
    _assert_structure_preserved(result.best.solution, instance)

    evaluation = evaluate(result.best.solution, instance)
    assert evaluation.feasible == result.best.feasible
    assert evaluation.cost_rs == result.best.evaluation.cost_rs


def test_convergence_history_is_monotone() -> None:
    instance = load_instance(DATA_DIR)
    result = run_gvns(instance, GVNSConfig(objective="f2", seed=5, max_evaluations=4000))

    evaluations = [p.evaluations for p in result.history]
    assert evaluations == sorted(evaluations)

    feasible_values = [p.objective for p in result.history if p.feasible]
    assert feasible_values == sorted(feasible_values, reverse=True)

    # Once feasible, the best-so-far never becomes infeasible again.
    flags = [p.feasible for p in result.history]
    assert flags == sorted(flags)


def test_gvns_is_reproducible_with_same_seed() -> None:
    instance = load_instance(DATA_DIR)
    config = GVNSConfig(objective="f3", seed=11, max_evaluations=3000)

    first = run_gvns(instance, config)
    second = run_gvns(instance, config)

    assert first.best.solution == second.best.solution
    assert first.history == second.history
