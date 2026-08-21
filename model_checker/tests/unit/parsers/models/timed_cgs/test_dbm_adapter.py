"""DBMAdapter tests using the in-repo minimal timedCGS fixture."""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS

_FIXTURE = (
    Path(__file__).resolve().parents[4]
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


@pytest.mark.unit
def test_apply_bounds_equality():
    from model_checker.parsers.game_structures.timed_cgs.DBM.DBM import DBM

    dbm = DBM(2)
    # x == 3 -> translates to x <= 3 and x >= 3
    DBMAdapter.apply_bounds(dbm, [(1, "==", "3")])
    assert dbm.elements[1][0].constant == 3
    assert dbm.elements[0][1].constant == -3


@pytest.mark.unit
def test_forward_transition_with_reset(minimal_tcgs):
    from model_checker.parsers.game_structures.timed_cgs.DBM.DBM import DBM

    original_constraints = minimal_tcgs.clock_constraint_struct
    minimal_tcgs.clock_constraint_struct = [["", "x>=1,x=0"], ["", ""]]

    zone = DBM(len(minimal_tcgs.clocks))
    # current zone: x >= 1
    DBMAdapter.apply_bounds(zone, [(1, ">=", "1")])

    successor_zone = DBMAdapter.forward_transition_zone(
        minimal_tcgs, zone, source_idx=0, target_idx=1
    )
    assert successor_zone is not None
    # Discrete step with reset yields clocks at the reset value; delay is separate.
    assert successor_zone.elements[1][0].constant == 0
    assert successor_zone.elements[0][1].constant == 0

    # restore
    minimal_tcgs.clock_constraint_struct = original_constraints


@pytest.mark.unit
def test_compute_predecessors_nested_logic(minimal_tcgs):
    # Test nested AST: E ((x<=2 and x>=1) or x<5) U p
    nested_formula = ("or", ("and", "x<=2", "x>=1"), "x<5")
    zones = DBMAdapter.compute_predecessors(
        minimal_tcgs, source="s0", target="s1", formulas=nested_formula
    )
    assert len(zones) == 2
    # One zone for x<=2 & x>=1 (predecessor bounds back to 0 due to down())
    assert all(
        z.elements[1][0].constant == 2 and z.elements[0][1].constant == 0 for z in zones
    )


@pytest.mark.unit
def test_parse_constraints_unknown_clock_in_reset():
    with pytest.raises(ValueError, match="Unknown clock 'y' in reset 'y=0'"):
        DBMAdapter.parse_constraints(["y=0"], {"x": 0})
