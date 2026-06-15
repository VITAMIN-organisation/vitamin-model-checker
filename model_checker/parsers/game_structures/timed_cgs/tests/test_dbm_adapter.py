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
