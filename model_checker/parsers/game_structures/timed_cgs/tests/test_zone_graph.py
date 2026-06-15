"""ZoneGraph tests using the in-repo minimal timedCGS fixture."""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.semantics import (
    states_with_time_constraints,
)
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.zone_graph import ZoneGraph

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


@pytest.fixture
def minimal_zone_graph(minimal_tcgs) -> ZoneGraph:
    return ZoneGraph(minimal_tcgs)


@pytest.mark.unit
def test_zone_graph_builder(minimal_zone_graph):
    assert len(minimal_zone_graph.states) > 0


@pytest.mark.unit
def test_has_path_from_initial(minimal_zone_graph):
    assert minimal_zone_graph.has_path_from("s0")


@pytest.mark.unit
def test_has_path_from_with_feasible_guard(minimal_zone_graph):
    assert minimal_zone_graph.has_path_from("s0", [(1, ">=", 0)])


@pytest.mark.unit
def test_has_path_from_with_infeasible_guard(minimal_zone_graph):
    assert not minimal_zone_graph.has_path_from("s0", [(1, ">", 200)])


@pytest.mark.unit
def test_has_path_from_guard_exceeds_invariant(minimal_zone_graph):
    # s0 invariant is x<=2; x>2 is infeasible on every zone including delay states
    assert not minimal_zone_graph.has_path_from("s0", [(1, ">", 2)])


@pytest.mark.unit
def test_find_path_from_returns_paths_when_feasible(minimal_zone_graph):
    assert len(minimal_zone_graph.find_path_from("s0")) > 0


@pytest.mark.unit
def test_states_with_time_constraints_respects_invariants(minimal_tcgs):
    zone_graph = ZoneGraph(minimal_tcgs)
    states = states_with_time_constraints(minimal_tcgs, zone_graph, "x>10")
    assert "s0" not in states


@pytest.mark.unit
def test_states_with_time_constraints_feasible_guard(minimal_tcgs):
    zone_graph = ZoneGraph(minimal_tcgs)
    states = states_with_time_constraints(minimal_tcgs, zone_graph, "x>=0")
    assert "s0" in states


@pytest.mark.unit
def test_zone_graph_pre_image_uses_invariants(minimal_tcgs):
    zone_graph = ZoneGraph(minimal_tcgs)
    bounds, _ = DBMAdapter.parse_constraints(["x>10"], minimal_tcgs.clocks_dict)
    assert not zone_graph.has_path_from("s0", bounds)
    feasible, _ = DBMAdapter.parse_constraints(["x<=1"], minimal_tcgs.clocks_dict)
    assert zone_graph.has_path_from("s0", feasible)
