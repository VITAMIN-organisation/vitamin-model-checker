"""DBMAdapter tests using the in-repo minimal timedCGS fixture."""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS

_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "tests"
    / "fixtures"
    / "timedCGS"
    / "tctl_tol_minimal.txt"
)


@pytest.fixture
def minimal_tcgs() -> TimedCGS:
    tcgs = TimedCGS()
    tcgs.read_file(_FIXTURE)
    return tcgs


@pytest.mark.unit
def test_compute_predecessors_feasible(minimal_tcgs):
    zone = DBMAdapter.compute_predecessors(
        minimal_tcgs, source="s0", target="s1", formulas="x>=0"
    )[0]
    assert not zone.is_empty()


@pytest.mark.unit
def test_compute_predecessors_infeasible(minimal_tcgs):
    with pytest.raises(ValueError, match="not consistent"):
        DBMAdapter.compute_predecessors(
            minimal_tcgs, source="s0", target="s1", formulas="x<0"
        )[0]


@pytest.mark.unit
def test_zone_at_target_tight_invariant(minimal_tcgs):
    zone = DBMAdapter._zone_at_target(minimal_tcgs, "s0", ["x>6"])
    assert zone.is_empty()


@pytest.mark.unit
def test_max_clock_constants(minimal_tcgs):
    assert DBMAdapter.get_max_clock_constraints(minimal_tcgs) == [2]


@pytest.mark.unit
def test_parse_constraints_rejects_unrecognized_token():
    with pytest.raises(ValueError, match="Unrecognized constraint token"):
        DBMAdapter.parse_constraints(["not-a-constraint"], {"x": 0})


@pytest.mark.unit
def test_parse_constraints_rejects_unknown_clock():
    with pytest.raises(ValueError, match="Unknown clock"):
        DBMAdapter.parse_constraints(["y>=1"], {"x": 0})


@pytest.mark.unit
def test_zone_helpers_use_state_name_mapping(tmp_path):
    """State indices must come from Name_State, not sN digit parsing."""
    content = """
Transition
* 0
0 *
Name_State
locA locB
Initial_State
locA
Atomic_propositions
p
Labelling
1
0
Number_of_agents
1
Clocks
x
Clock_constraints
x<=1
x<=1
Invariants
x<=2
x<=2
"""
    path = tmp_path / "custom_named_states.txt"
    path.write_text(content)
    tcgs = TimedCGS()
    tcgs.read_file(path)

    zone = DBMAdapter._zone_at_target(tcgs, "locA", ["x>6"])
    assert zone.is_empty()

    predecessors = DBMAdapter.compute_predecessors(
        tcgs, source="locA", target="locB", formulas="x>=0"
    )
    assert predecessors
    assert not predecessors[0].is_empty()
