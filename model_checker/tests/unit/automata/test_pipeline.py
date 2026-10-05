"""End-to-end validation of the whole pipeline: a toy concurrent transition
system + a toy LTL formula, run through every real stage of the library,
`Automaton.from_ltl`, `product()` (with a `label` function reconciling its
AP-set contract with `concurrent_to_turnbased`'s joint-action one),
`concurrent_to_turnbased`, `remap_priorities`, and `solve()`.

Requires Spot, see tests/test_automaton.py. Skipped entirely if spot isn't
importable.
"""

from dataclasses import replace

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceKind
from model_checker.automata.automaton import Automaton
from model_checker.automata.games.arena import (
    concurrent_to_turnbased,
    remap_priorities,
)
from model_checker.automata.games.solver import solve
from model_checker.automata.product import product
from model_checker.automata.transition_system import TransitionSystem


def _label(source, symbol):
    # reconciles product()'s AP-set contract with the toy system's
    # joint-action symbols: derive which atomic propositions hold from the
    # two players' chosen actions, without altering the symbol itself
    actions = dict(symbol)
    aps = set()
    if actions.get("env") == "request":
        aps.add("req")
    if actions.get("sys") == "grant":
        aps.add("grant")
    return aps


def _toy_system():
    # single state, one transition per joint action: sys grants or denies,
    # concurrently with env requesting or staying idle
    ts = TransitionSystem()
    for sys_action in ("grant", "deny"):
        for env_action in ("request", "idle"):
            joint = frozenset({("sys", sys_action), ("env", env_action)})
            ts.add_transition("s0", joint, "s0")
    ts.add_state("s0", initial=True)
    return ts


def test_coalition_forces_response_property_regardless_of_environment():
    # "every request is (immediately) followed by a grant" is trivially
    # forceable by sys alone: always grant, regardless of what env does
    automaton = Automaton.from_ltl("GF(req -> grant)")
    ts = _toy_system()

    product_ts, objective = product(automaton, ts, label=_label)
    game = concurrent_to_turnbased(product_ts, controlled_players={"sys"})
    game.objective = replace(objective, priorities=remap_priorities(objective.priorities, {"sys"}))

    solution = solve(game)

    aut_init = automaton.graph.get_init_state_number()
    initial = ("s0", aut_init)

    # sys wins from every reachable arena state, env wins nowhere
    assert solution.winning_regions[0] == game.arena.states
    assert solution.winning_regions[1] == set()

    # the witness strategy actually grants at the initial (coalition) state
    coalition_action = solution.strategies[0].move(initial)
    assert coalition_action is not None
    assert dict(coalition_action)["sys"] == "grant"


def test_environment_cannot_force_a_property_outside_its_control():
    # "grant happens infinitely often" is NOT forceable by env alone (env
    # doesn't control "grant" at all), the coalition {"env"} must lose
    automaton = Automaton.from_ltl("GFgrant")
    ts = _toy_system()

    product_ts, objective = product(automaton, ts, label=_label)
    game = concurrent_to_turnbased(product_ts, controlled_players={"env"})
    game.objective = replace(objective, priorities=remap_priorities(objective.priorities, {"env"}))

    solution = solve(game)

    aut_init = automaton.graph.get_init_state_number()
    initial = ("s0", aut_init)

    assert initial in solution.winning_regions[1]
    assert initial not in solution.winning_regions[0]


def _multi_state_system():
    # two ts states, "a" and "b", alternating regardless of any action taken
    ts = TransitionSystem()
    for state, other in (("a", "b"), ("b", "a")):
        for sys_action in ("x", "y"):
            for env_action in ("p", "q"):
                joint = frozenset({("sys", sys_action), ("env", env_action)})
                ts.add_transition(state, joint, other)
    ts.add_state("a", initial=True)
    return ts


def test_coalition_forces_property_across_multiple_ts_states():
    # "target" only holds while at "a" and sys picks "x" there, reachable
    # every other step regardless of env, so sys can force GF target
    def label(source, symbol):
        return {"target"} if source == "a" and dict(symbol).get("sys") == "x" else set()

    automaton = Automaton.from_ltl("GFtarget")
    ts = _multi_state_system()

    product_ts, objective = product(automaton, ts, label=label)
    game = concurrent_to_turnbased(product_ts, controlled_players={"sys"})
    game.objective = replace(objective, priorities=remap_priorities(objective.priorities, {"sys"}))

    solution = solve(game)

    # every reachable product state is won by sys, spanning both ts states
    assert solution.winning_regions[0] == game.arena.states
    assert solution.winning_regions[1] == set()
    assert {ts_state for ts_state, _aut_state in product_ts.states} == {"a", "b"}


def test_coalition_cannot_force_property_controlled_solely_by_environment():
    # "envtarget" depends only on env's own action, sys has no leverage
    def label(source, symbol):
        return {"envtarget"} if dict(symbol).get("env") == "p" else set()

    automaton = Automaton.from_ltl("GFenvtarget")
    ts = _multi_state_system()

    product_ts, objective = product(automaton, ts, label=label)
    game = concurrent_to_turnbased(product_ts, controlled_players={"sys"})
    game.objective = replace(objective, priorities=remap_priorities(objective.priorities, {"sys"}))

    solution = solve(game)

    assert solution.winning_regions[0] == set()
    assert solution.winning_regions[1] == game.arena.states


def test_genuine_parity_objective_through_the_whole_pipeline():
    # "GFa & FGb" needs real parity (not Büchi/co-Büchi alone) once
    # normalized by from_ltl, exercises product()/arena()/solve() with more
    # than the 2-color case the other pipeline tests happen to produce
    def label(source, symbol):
        action = dict(symbol).get("sys")
        aps = set()
        if action in ("both", "aonly"):
            aps.add("a")
        if action in ("both", "bonly"):
            aps.add("b")
        return aps

    automaton = Automaton.from_ltl("GFa & FGb")
    ts = TransitionSystem()
    for sys_action in ("both", "aonly", "bonly", "neither"):
        for env_action in ("e1", "e2"):
            joint = frozenset({("sys", sys_action), ("env", env_action)})
            ts.add_transition("s0", joint, "s0")
    ts.add_state("s0", initial=True)

    product_ts, objective = product(automaton, ts, label=label)
    assert objective.kind is AcceptanceKind.PARITY
    assert len(set(objective.priorities.values())) > 2  # genuinely more than 2 colors

    game = concurrent_to_turnbased(product_ts, controlled_players={"sys"})
    game.objective = replace(objective, priorities=remap_priorities(objective.priorities, {"sys"}))

    solution = solve(game)  # regression: used to raise KeyError (see test_solver.py)

    aut_init = automaton.graph.get_init_state_number()
    initial = ("s0", aut_init)
    assert initial in solution.winning_regions[0]
    # "both" satisfies GFa & FGb outright by itself, every step
    assert dict(solution.strategies[0].move(initial))["sys"] == "both"
