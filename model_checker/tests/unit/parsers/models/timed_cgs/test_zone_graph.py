"""Zone graph of a timedCGS: the symbolic states reachable from all clocks at zero.

In tctl_tol_minimal.txt only s0 -> s0 exists, guarded by x <= 1, and s0's
invariant is x <= 2, so x ranges over [0, 2] at s0 and s1 is never reached.
"""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.timed_cgs.semantics import (
    states_with_time_constraints,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

_FIXTURE = (
    Path(__file__).resolve().parents[4] / "fixtures/timedCGS/tctl_tol_minimal.txt"
)

_HEADER = (
    "Transition\n* 0\n0 *\nName_State\ns0 s1\nInitial_State\ns0\n"
    "Atomic_propositions\np\nLabelling\n1\n0\nNumber_of_agents\n1\nClocks\nx\n"
)


@pytest.fixture
def minimal_tcgs() -> TimedCGS:
    tcgs = TimedCGS()
    tcgs.read_file(_FIXTURE)
    return tcgs


def _load(tmp_path, content: str) -> TimedCGS:
    path = tmp_path / "model.txt"
    path.write_text(content)
    tcgs = TimedCGS()
    tcgs.read_file(path)
    return tcgs


@pytest.mark.unit
def test_initial_state_has_every_clock_at_zero(minimal_tcgs):
    """The start zone is x = 0 at the initial location."""
    initial = ZoneGraph(minimal_tcgs).initial_time_state
    assert initial.location == "s0"
    assert (
        initial.zone.elements[1][0].constant,
        initial.zone.elements[0][1].constant,
    ) == (0, 0)


@pytest.mark.unit
def test_reachable_zones_stop_at_the_invariant(minimal_tcgs):
    """At s0, x reaches up to 1 (the guard) and 2 (the invariant), never more; s1 is unreachable."""
    graph = ZoneGraph(minimal_tcgs)
    assert {state.location for state in graph.states} == {"s0"}
    assert sorted(state.zone.elements[1][0].constant for state in graph.states) == [
        0,
        1,
        2,
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("bounds", "reachable"),
    [
        ([(1, ">=", 0)], True),
        ([(1, ">=", 2)], True),
        ([(1, ">", 2)], False),
        ([(1, ">", 200)], False),
    ],
)
def test_path_exists_only_inside_the_invariant(minimal_tcgs, bounds, reachable):
    """x >= 2 is reachable at the invariant's edge; x > 2 is not."""
    assert ZoneGraph(minimal_tcgs).has_path_from("s0", bounds) is reachable


@pytest.mark.unit
@pytest.mark.parametrize(
    ("constraint", "states"),
    [("x>=0", {"s0"}), ("x==2", {"s0"}), ("x>2", set()), ("x>10", set())],
)
def test_states_where_a_clock_constraint_can_hold(minimal_tcgs, constraint, states):
    """A state counts when some reachable zone there meets the constraint."""
    graph = ZoneGraph(minimal_tcgs)
    assert states_with_time_constraints(minimal_tcgs, graph, constraint) == states


@pytest.mark.unit
def test_initial_zone_is_cut_by_the_location_invariant(tmp_path):
    """With invariant x <= 0 time cannot pass at s0, so every zone there has x = 0."""
    tcgs = _load(
        tmp_path,
        "Transition\n*\nName_State\ns0\nInitial_State\ns0\nAtomic_propositions\np\n"
        "Labelling\n1\nNumber_of_agents\n1\nClocks\nx\nClock_constraints\n0\nInvariants\nx<=0\n",
    )
    graph = ZoneGraph(tcgs)
    assert graph.states
    assert {state.zone.elements[1][0].constant for state in graph.states} == {0}


@pytest.mark.unit
def test_unbounded_clock_has_no_dead_ends(tmp_path):
    """Without invariants time can always pass, so every symbolic state has a successor."""
    tcgs = _load(
        tmp_path, _HEADER + "Clock_constraints\n0 x>=1\n0 0\nInvariants\n0\n0\n"
    )
    graph = ZoneGraph(tcgs)
    assert graph.graph
    assert all(successors for successors in graph.graph.values())
