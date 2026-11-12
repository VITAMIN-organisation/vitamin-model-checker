"""DBMAdapter: from a timedCGS and clock formulas to zones.

The fixture tctl_tol_minimal.txt has one clock x, the invariant x <= 2 in both
states and no guard on s0 -> s1, so every predecessor zone below is 0 <= x <= 2.
"""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.DBM.DBM import DBM
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS

_FIXTURE = (
    Path(__file__).resolve().parents[4] / "fixtures/timedCGS/tctl_tol_minimal.txt"
)


@pytest.fixture
def minimal_tcgs() -> TimedCGS:
    tcgs = TimedCGS()
    tcgs.read_file(_FIXTURE)
    return tcgs


def _bounds(zone: DBM) -> tuple:
    """(upper bound of x, minus its lower bound)."""
    return zone.elements[1][0].constant, zone.elements[0][1].constant


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["x>=0", "x>=1"])
def test_predecessor_zone_lets_time_run_back_to_zero(minimal_tcgs, formula):
    """Reaching s1 with x >= 0 or x >= 1 is possible from any x in [0, 2] at s0."""
    [zone] = DBMAdapter.compute_predecessors(minimal_tcgs, "s0", "s1", formula)
    assert _bounds(zone) == (2.0, 0)


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["x<0", "x>6"])
def test_formula_outside_the_invariant_has_no_predecessor(minimal_tcgs, formula):
    """x < 0 never holds and x > 6 breaks s1's invariant, so the zone is inconsistent."""
    with pytest.raises(ValueError, match="not consistent"):
        DBMAdapter.compute_predecessors(minimal_tcgs, "s0", "s1", formula)


@pytest.mark.unit
def test_disjunction_gives_one_zone_per_branch(minimal_tcgs):
    """`(x<=2 and x>=1) or x<5` gives two zones; the invariant cuts both to [0, 2]."""
    formula = ("or", ("and", "x<=2", "x>=1"), "x<5")
    zones = DBMAdapter.compute_predecessors(minimal_tcgs, "s0", "s1", formula)
    assert [_bounds(zone) for zone in zones] == [(2.0, 0), (2.0, 0)]


@pytest.mark.unit
def test_state_names_come_from_name_state(tmp_path):
    """Locations named locA and locB work; indices are not read from `sN` names."""
    content = (
        "Transition\n* 0\n0 *\nName_State\nlocA locB\nInitial_State\nlocA\n"
        "Atomic_propositions\np\nLabelling\n1\n0\nNumber_of_agents\n1\n"
        "Clocks\nx\nClock_constraints\nx<=1 0\nx<=1 0\nInvariants\nx<=2\nx<=2\n"
    )
    path = tmp_path / "named.txt"
    path.write_text(content)
    tcgs = TimedCGS()
    tcgs.read_file(path)
    [zone] = DBMAdapter.compute_predecessors(tcgs, "locA", "locB", "x>=0")
    assert _bounds(zone) == (2.0, 0)


@pytest.mark.unit
def test_max_clock_constant_is_the_largest_bound(minimal_tcgs):
    """Guards use 1 and invariants 2, so extrapolation must keep values up to 2."""
    assert DBMAdapter.get_max_clock_constraints(minimal_tcgs) == [2]


@pytest.mark.unit
def test_constraint_tokens_keep_two_character_operators():
    """`x>=3` is >=, `x==2` is ==, and `x=0` is a reset, not a bound."""
    bounds, resets = DBMAdapter.parse_constraints(
        ["x>=3", "x>1", "x==2", "x=0"], {"x": 0}
    )
    assert [op for _clock, op, _value in bounds] == [">=", ">", "=="]
    assert resets == [(1, 0)]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("token", "message"),
    [
        ("not-a-constraint", "Unrecognized constraint token"),
        ("y>=1", "Unknown clock"),
        ("y=0", "Unknown clock 'y' in reset 'y=0'"),
    ],
)
def test_bad_constraint_token_is_refused(token, message):
    """A malformed token or an undeclared clock, in a guard or a reset."""
    with pytest.raises(ValueError, match=message):
        DBMAdapter.parse_constraints([token], {"x": 0})


@pytest.mark.unit
def test_equality_bound_fixes_the_clock():
    """x == 3 is x <= 3 and x >= 3."""
    dbm = DBM(2)
    DBMAdapter.apply_bounds(dbm, [(1, "==", "3")])
    assert _bounds(dbm) == (3, -3)


@pytest.mark.unit
def test_forward_step_applies_guard_then_reset(minimal_tcgs):
    """With guard x >= 1 and reset x = 0 on s0 -> s1, x is 0 right after the step."""
    minimal_tcgs.clock_constraint_struct = [["", "x>=1,x=0"], ["", ""]]
    zone = DBM(len(minimal_tcgs.clocks))
    DBMAdapter.apply_bounds(zone, [(1, ">=", "1")])
    successor = DBMAdapter.forward_transition_zone(
        minimal_tcgs, zone, source_idx=0, target_idx=1
    )
    assert successor is not None
    assert _bounds(successor) == (0, 0)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("invariant", "has_predecessor"),
    [
        # Reaching s1 with x>=3 needs x=3 to satisfy s1's invariant: x<3 rules it out.
        ("x<3", False),
        ("x<=3", True),
    ],
)
def test_strict_target_invariant_limits_the_predecessor_zone(
    tmp_path, invariant, has_predecessor
):
    path = tmp_path / "strict.txt"
    path.write_text(
        "Transition\n* 1\n0 *\nName_State\ns0 s1\nInitial_State\ns0\n"
        "Atomic_propositions\np\nLabelling\n1\n0\nNumber_of_agents\n1\n"
        f"Clocks\nx\nClock_constraints\n0 0\n0 0\nInvariants\n0\n{invariant}\n"
    )
    tcgs = TimedCGS()
    tcgs.read_file(path)
    if has_predecessor:
        assert DBMAdapter.compute_predecessors(tcgs, "s0", "s1", "x>=3")
    else:
        with pytest.raises(ValueError, match="not consistent"):
            DBMAdapter.compute_predecessors(tcgs, "s0", "s1", "x>=3")
