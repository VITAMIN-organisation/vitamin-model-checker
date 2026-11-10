"""The whole automata pipeline on toy systems: from_ltl, product, concurrent_to_turnbased, remap_priorities, solve.

Players `sys` and `env` move together. `label` says which propositions a joint
action makes true, so the product can read the system's moves. Needs Spot.
"""

from dataclasses import replace

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import AcceptanceKind
from model_checker.automata.automaton import Automaton
from model_checker.automata.games.arena import concurrent_to_turnbased, remap_priorities
from model_checker.automata.games.solver import solve
from model_checker.automata.product import product
from model_checker.automata.transition_system import TransitionSystem


def _system(sys_actions, env_actions, states=("s0",)):
    """Every joint action moves each state to the next one in `states`, cyclically."""
    ts = TransitionSystem()
    for i, state in enumerate(states):
        for sys_action in sys_actions:
            for env_action in env_actions:
                joint = frozenset({("sys", sys_action), ("env", env_action)})
                ts.add_transition(state, joint, states[(i + 1) % len(states)])
    ts.add_state(states[0], initial=True)
    return ts


def _game(formula, ts, label, coalition):
    automaton = Automaton.from_ltl(formula)
    product_ts, objective = product(automaton, ts, label=label)
    game = concurrent_to_turnbased(product_ts, controlled_players={coalition})
    game.objective = replace(
        objective, priorities=remap_priorities(objective.priorities, {coalition})
    )
    initial = (next(iter(ts.initial_states)), automaton.graph.get_init_state_number())
    return game, product_ts, objective, initial


def _props(**holds):
    """The propositions whose condition is true."""
    return {name for name, true in holds.items() if true}


def _request_grant(source, symbol):
    actions = dict(symbol)
    return _props(req=actions["env"] == "request", grant=actions["sys"] == "grant")


def test_sys_forces_a_response_by_always_granting():
    """GF(req -> grant): sys wins everywhere by granting, whatever env requests."""
    game, _, _, initial = _game(
        "GF(req -> grant)",
        _system(("grant", "deny"), ("request", "idle")),
        _request_grant,
        "sys",
    )
    solution = solve(game)
    assert solution.winning_regions == {0: game.arena.states, 1: set()}
    assert dict(solution.strategies[0].move(initial))["sys"] == "grant"


@pytest.mark.parametrize(
    ("formula", "label", "coalition"),
    [
        ("GFgrant", _request_grant, "env"),
        (
            "GFenvtarget",
            lambda source, symbol: _props(envtarget=dict(symbol)["env"] == "request"),
            "sys",
        ),
    ],
    ids=["env_cannot_grant", "sys_cannot_make_env_request"],
)
def test_coalition_loses_a_goal_only_the_other_player_controls(
    formula, label, coalition
):
    """The proposition depends only on the other player's action, so the coalition wins nowhere."""
    game, _, _, initial = _game(
        formula, _system(("grant", "deny"), ("request", "idle")), label, coalition
    )
    solution = solve(game)
    assert initial in solution.winning_regions[1]
    assert solution.winning_regions[0] == set()


def test_goal_reachable_every_other_step_across_two_states():
    """target holds when sys plays x at a; a and b alternate, so sys forces GF target from both."""
    game, product_ts, _, _ = _game(
        "GFtarget",
        _system(("x", "y"), ("p", "q"), states=("a", "b")),
        lambda source, symbol: _props(
            target=source == "a" and dict(symbol)["sys"] == "x"
        ),
        "sys",
    )
    assert solve(game).winning_regions == {0: game.arena.states, 1: set()}
    assert {ts_state for ts_state, _ in product_ts.states} == {"a", "b"}


def test_real_parity_objective_through_the_pipeline():
    """GFa & FGb needs more than two colors; sys wins by playing `both` (a and b) every step."""

    def label(source, symbol):
        action = dict(symbol)["sys"]
        return _props(a=action in ("both", "aonly"), b=action in ("both", "bonly"))

    game, _, objective, initial = _game(
        "GFa & FGb",
        _system(("both", "aonly", "bonly", "neither"), ("e1", "e2")),
        label,
        "sys",
    )
    assert objective.kind is AcceptanceKind.PARITY
    assert len(set(objective.priorities.values())) > 2
    solution = solve(game)
    assert initial in solution.winning_regions[0]
    assert dict(solution.strategies[0].move(initial))["sys"] == "both"
