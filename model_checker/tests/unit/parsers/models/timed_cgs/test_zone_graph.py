"""Zone graph of a timedCGS: the symbolic states reachable from all clocks at zero.

In tctl_tol_minimal.txt only s0 -> s0 exists, guarded by x <= 1, and s0's
invariant is x <= 2, so x ranges over [0, 2] at s0 and s1 is never reached.
"""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.timed_cgs.formula_clocks import (
    extend_timed_cgs_clocks,
)
from model_checker.parsers.game_structures.timed_cgs.regions import (
    project_regions_to_locations,
    regions_with_clock_guard,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import (
    TICK_CLOCK,
    ZoneGraph,
)

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


def _locations_meeting(tcgs: TimedCGS, constraint: str) -> set[str]:
    graph = ZoneGraph(tcgs)
    return project_regions_to_locations(
        regions_with_clock_guard(tcgs, graph, constraint)
    )


def _load(tmp_path, content: str) -> TimedCGS:
    path = tmp_path / "model.txt"
    path.write_text(content)
    tcgs = TimedCGS()
    tcgs.read_file(path)
    return tcgs


@pytest.mark.unit
def test_tick_regions_only_reset_the_tick_clock(minimal_tcgs):
    """Each region where the tick clock has reached 1 is in tick_states, and its
    only successor is the same location and x with the tick clock at 0."""
    graph = ZoneGraph(minimal_tcgs, track_divergence=True)
    tick = minimal_tcgs.clocks_dict[TICK_CLOCK] + 1
    reached_one = {
        state for state in graph.states if -state.zone.elements[0][tick].constant >= 1
    }
    assert graph.tick_states == reached_one != set()
    for state in graph.tick_states:
        [reset] = graph.graph[state]
        assert reset.location == state.location
        assert reset.zone.elements[tick][0].constant == 0
        assert reset.zone.elements[0][1] == state.zone.elements[0][1]


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
def test_reachable_regions_stop_at_the_invariant(minimal_tcgs):
    """At s0, x runs through the regions 0, (0,1), 1, (1,2), 2 and stops at the
    invariant x<=2, each time step to the next; s1 is unreachable."""
    graph = ZoneGraph(minimal_tcgs)
    assert {state.location for state in graph.states} == {"s0"}
    assert sorted(len(steps) for steps in graph.delay_successors.values()) == [
        0,
        1,
        1,
        1,
        1,
    ]
    assert sorted(
        (-state.zone.elements[0][1].constant, state.zone.elements[1][0].constant)
        for state in graph.states
    ) == [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("constraint", "states"),
    [("x>=0", {"s0"}), ("x==2", {"s0"}), ("x>2", set()), ("x>10", set())],
)
def test_states_where_a_clock_constraint_can_hold(minimal_tcgs, constraint, states):
    """A state counts when some reachable zone there meets the constraint."""
    assert _locations_meeting(minimal_tcgs, constraint) == states


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


@pytest.mark.unit
@pytest.mark.parametrize(
    ("invariant", "constraint", "reachable"),
    [
        # x<3: time stops before 3, so x==3 and x>=3 are out, x>2 (e.g. 2.5) is in.
        ("x<3", "x==3", False),
        ("x<3", "x>=3", False),
        ("x<3", "x>2", True),
        # x<=3: x reaches 3 exactly.
        ("x<=3", "x==3", True),
        ("x<=3", "x>3", False),
    ],
)
def test_strict_invariant_excludes_its_bound(
    tmp_path, invariant, constraint, reachable
):
    tcgs = _load(
        tmp_path,
        "Transition\n*\nName_State\ns0\nInitial_State\ns0\nAtomic_propositions\np\n"
        "Labelling\n1\nNumber_of_agents\n1\nClocks\nx\nClock_constraints\n0\n"
        f"Invariants\n{invariant}\n",
    )
    assert ("s0" in _locations_meeting(tcgs, constraint)) is reachable


_TWO_STATES = (
    "Transition\n* 1\n0 *\nName_State\ns0 s1\nInitial_State\ns0\n"
    "Atomic_propositions\np\nLabelling\n1\n0\nNumber_of_agents\n1\n"
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("invariant", "states"),
    [
        # s0 has no invariant, so x==3 holds there. Entering s1 needs x < 3, so
        # under x<3 the clock is 3 at s1 never, and under x<=3 it is 3 at s1 once.
        ("x<3", {"s0"}),
        ("x<=3", {"s0", "s1"}),
    ],
)
def test_strict_invariant_of_a_target_blocks_the_edge_at_its_bound(
    tmp_path, invariant, states
):
    tcgs = _load(
        tmp_path,
        _TWO_STATES
        + f"Clocks\nx\nClock_constraints\n0 0\n0 0\nInvariants\n0\n{invariant}\n",
    )
    assert _locations_meeting(tcgs, "x==3") == states


@pytest.mark.unit
@pytest.mark.parametrize(
    ("constraint", "states"), [("x==1", {"locA", "locB"}), ("x==3", {"locA"})]
)
def test_locations_are_found_by_their_names(tmp_path, constraint, states):
    """Names other than sN: the invariant x<=1 belongs to locB, not to locA."""
    tcgs = _load(
        tmp_path,
        _TWO_STATES.replace("s0 s1", "locA locB").replace("\ns0\n", "\nlocA\n")
        + "Clocks\nx\nClock_constraints\n0 0\n0 0\nInvariants\n0\nx<=1\n",
    )
    assert _locations_meeting(tcgs, constraint) == states


@pytest.mark.unit
@pytest.mark.parametrize(
    ("invariants", "reachable"),
    [
        # Both clocks start at 0 and run together, so y<3 stops x before 3 even
        # though x<=5 alone would allow it.
        ("x<=5,y<3", False),
        # y<=3 allows y=3, and then x=3 as well.
        ("x<=5,y<=3", True),
    ],
)
def test_two_invariants_in_one_cell_both_apply(tmp_path, invariants, reachable):
    tcgs = _load(
        tmp_path,
        "Transition\n*\nName_State\ns0\nInitial_State\ns0\nAtomic_propositions\np\n"
        "Labelling\n1\nNumber_of_agents\n1\nClocks\nx y\nClock_constraints\n0\n"
        f"Invariants\n{invariants}\n",
    )
    assert ("s0" in _locations_meeting(tcgs, "x==3")) is reachable


@pytest.mark.unit
def test_freeze_reset_links_every_region_to_one_with_the_clock_at_zero(minimal_tcgs):
    """Resetting j at 0<x<1 gives 0<x<1, j=0, which no time or edge step reaches."""
    extend_timed_cgs_clocks(minimal_tcgs, ("j",))
    graph = ZoneGraph(minimal_tcgs, freeze_clocks=("j",))
    resets = graph.freeze_resets["j"]
    assert set(resets) == graph.states
    assert {reset.zone.elements[2][0].constant for reset in resets.values()} == {0}
    assert graph.reachable_states < graph.states
