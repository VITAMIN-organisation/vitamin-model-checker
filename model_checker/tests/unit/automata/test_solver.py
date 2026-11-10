"""games/solver.py: winning regions and strategies from Spot, for each acceptance condition. Needs Spot."""

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.acceptance import (
    AcceptanceCondition,
    AcceptanceKind,
    ParityKind,
    ParityStyle,
)
from model_checker.automata.games.game import Game
from model_checker.automata.games.solver import solve
from model_checker.automata.transition_system import TransitionSystem


def _ts(*edges, initial=("s0",)):
    ts = TransitionSystem()
    for source, action, target in edges:
        ts.add_transition(source, action, target)
    for state in initial:
        ts.add_state(state, initial=True)
    return ts


def _marked(kind, *edges):
    return AcceptanceCondition(kind=kind, priorities=dict.fromkeys(edges, 0))


def _parity(kind, style, priorities=None):
    return AcceptanceCondition(
        kind=AcceptanceKind.PARITY,
        parity_kind=kind,
        parity_style=style,
        priorities=priorities or {},
    )


def _solve(ts, objective, opponent=frozenset()):
    return solve(
        Game(
            arena=ts,
            player_states={0: ts.states - opponent, 1: set(opponent)},
            objective=objective,
        )
    )


def test_buchi_player_takes_the_edge_to_the_accepting_loop():
    """s0 -a-> loop, and the loop is accepting, so player 0 wins by playing a."""
    ts = _ts(("s0", "a", "loop"), ("loop", "b", "loop"))
    solution = _solve(ts, _marked(AcceptanceKind.BUCHI, ("loop", "b", "loop")))
    assert solution.winning_regions == {0: {"s0", "loop"}, 1: set()}
    assert solution.strategies[0].move("s0") == "a"


def test_buchi_opponent_who_owns_the_choice_stalls():
    """The opponent at s0 picks stall into the rejecting dead end."""
    ts = _ts(
        ("s0", "escape", "target"),
        ("s0", "stall", "dead_end"),
        ("target", "loop", "target"),
        ("dead_end", "loop", "dead_end"),
    )
    solution = _solve(
        ts, _marked(AcceptanceKind.BUCHI, ("target", "loop", "target")), opponent={"s0"}
    )
    assert solution.winning_regions == {0: {"target"}, 1: {"s0", "dead_end"}}
    assert solution.strategies[1].move("s0") == "stall"


@pytest.mark.parametrize(
    ("edges", "marked", "player0_wins"),
    [
        ([("s0", "a", "s1"), ("s1", "b", "s1")], ("s0", "a", "s1"), True),
        ([("s0", "a", "s0")], ("s0", "a", "s0"), False),
    ],
    ids=["mark_seen_once", "mark_seen_forever"],
)
def test_co_buchi_accepts_when_the_mark_is_seen_finitely_often(
    edges, marked, player0_wins
):
    """Co-Büchi: a marked edge taken once is fine, a marked self-loop forever is not."""
    ts = _ts(*edges)
    regions = _solve(ts, _marked(AcceptanceKind.CO_BUCHI, marked)).winning_regions
    assert regions[0 if player0_wins else 1] == ts.states


def test_min_even_parity_takes_the_smallest_recurring_color():
    """The cycle s0 -0-> s1 -1-> s0 sees 0 and 1 forever; min is 0, even, so player 0 wins."""
    ts = _ts(("s0", "a", "s1"), ("s1", "b", "s0"))
    objective = _parity(
        ParityKind.MIN, ParityStyle.EVEN, {("s0", "a", "s1"): 0, ("s1", "b", "s0"): 1}
    )
    assert _solve(ts, objective).winning_regions == {0: {"s0", "s1"}, 1: set()}


@pytest.mark.parametrize(
    ("style", "player0_wins"), [(ParityStyle.ODD, True), (ParityStyle.EVEN, False)]
)
def test_parity_without_priorities_is_one_unused_color(style, player0_wins):
    """Max-odd with no colors is Fin(0), always met; max-even is Inf(0), never met."""
    ts = _ts(("s0", "a", "s0"))
    regions = _solve(ts, _parity(ParityKind.MAX, style)).winning_regions
    assert regions[0 if player0_wins else 1] == {"s0"}


def test_many_colors_with_a_losing_opponent_does_not_crash():
    """Regression: Spot can return edge numbers outside the automaton for a player who loses everywhere."""
    ts = _ts(
        *[
            ("hub", choice, f"int_{choice}")
            for choice in ("both", "aonly", "bonly", "neither")
        ],
        *[
            (f"int_{choice}", "loop", "hub")
            for choice in ("both", "aonly", "bonly", "neither")
        ],
        initial=("hub",),
    )
    objective = _parity(
        ParityKind.MAX,
        ParityStyle.ODD,
        {
            ("int_both", "loop", "hub"): 1,
            ("int_aonly", "loop", "hub"): 2,
            ("int_bonly", "loop", "hub"): 0,
            ("int_neither", "loop", "hub"): 2,
        },
    )
    opponent = {"int_both", "int_aonly", "int_bonly", "int_neither"}
    solution = _solve(ts, objective, opponent=opponent)
    assert solution.winning_regions == {0: ts.states, 1: set()}
    assert solution.strategies[0].move("hub") == "both"


def test_every_state_gets_its_own_verdict_initial_or_not():
    """Regression: s0 wins, t0 loses, and u0 (never marked initial) wins, each in its own component."""
    ts = _ts(
        ("s0", "a", "s0"), ("t0", "a", "t0"), ("u0", "a", "u0"), initial=("s0", "t0")
    )
    objective = _marked(AcceptanceKind.BUCHI, ("s0", "a", "s0"), ("u0", "a", "u0"))
    assert _solve(ts, objective).winning_regions == {0: {"s0", "u0"}, 1: {"t0"}}


@pytest.mark.parametrize(
    ("game", "error", "message"),
    [
        (
            lambda: Game(
                arena=_ts(("s0", "a", "s0")), player_states={0: {"s0"}, 1: set()}
            ),
            ValueError,
            "objective",
        ),
        (
            lambda: Game(
                arena=TransitionSystem(),
                player_states={0: set(), 1: set()},
                objective=_marked(AcceptanceKind.BUCHI),
            ),
            ValueError,
            "at least one state",
        ),
        (
            lambda: Game(
                arena=_ts(("s0", "a", "s0")),
                player_states={0: set(), 1: set()},
                objective=_marked(AcceptanceKind.BUCHI),
            ),
            ValueError,
            "exactly one",
        ),
        (
            lambda: Game(
                arena=_ts(("s0", "a", "s1"), ("s0", "a", "s2")),
                player_states={0: {"s0", "s1", "s2"}, 1: set()},
                objective=_marked(AcceptanceKind.BUCHI),
            ),
            ValueError,
            "deterministic",
        ),
    ],
    ids=[
        "no_objective",
        "no_state",
        "state_without_owner",
        "action_with_two_successors",
    ],
)
def test_malformed_game_is_refused(game, error, message):
    """A strategy records only the action, so an action with two successors cannot be replayed."""
    with pytest.raises(error, match=message):
        solve(game())


def test_wrong_number_of_winners_from_spot_is_an_error(monkeypatch):
    """Spot must return one winner per state plus the anchor; a short list must not be zipped silently."""
    import model_checker.automata.games.solver as solver_module

    real = solver_module.spot.get_state_winners
    monkeypatch.setattr(
        solver_module.spot, "get_state_winners", lambda aut: real(aut)[:-1]
    )
    ts = _ts(("s0", "a", "s0"))
    with pytest.raises(RuntimeError, match="unexpected number of"):
        _solve(ts, _marked(AcceptanceKind.BUCHI, ("s0", "a", "s0")))
