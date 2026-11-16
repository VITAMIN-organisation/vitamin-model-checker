from collections import deque
from itertools import chain, pairwise

from model_checker.algorithms.explicit.shared.trace_utils import (
    any_backward_path,
    collect_backward_paths,
    reverse_adjacency,
)

from .DBM import DBMAdapter
from .DBM.DBM import DBM
from .timed_cgs import TimedCGS


class TimeState:
    def __init__(self, location: str, zone: DBM):
        self.location = location
        self.zone = zone

    def __hash__(self):
        return hash((self.location, self.zone))

    def __eq__(self, other):
        if not isinstance(other, TimeState):
            return NotImplemented
        return self.location == other.location and self.zone == other.zone


class _Exploration:
    """Breadth-first exploration of the reachable regions; each successor is stored
    once, as a delay step or as a discrete step to a named location."""

    def __init__(self, tcgs: TimedCGS, formula_constants: dict[str, int]):
        self.tcgs = tcgs
        self.max_constants = _max_constants(tcgs, formula_constants)
        self.location_targets = _location_targets(tcgs)
        self.delay_successors: dict[TimeState, set[TimeState]] = {}
        self.discrete_successors: dict[TimeState, dict[str, set[TimeState]]] = {}
        self.waitlist: deque[TimeState] = deque()

    def regions(self, location: str, zone: DBM) -> list[TimeState]:
        """The clock regions that make up ``zone`` after normalization."""
        zone.k_normalize(self.max_constants)
        return [
            TimeState(location, part)
            for part in DBMAdapter.split_into_regions(zone, self.max_constants)
        ]

    def add_state(self, state: TimeState) -> None:
        if state in self.delay_successors:
            return
        self.delay_successors[state] = set()
        self.discrete_successors[state] = {}
        self.waitlist.append(state)


def _location_targets(tcgs: TimedCGS) -> dict[str, tuple[str, ...]]:
    """Each location's edge targets, sorted."""
    targets: dict[str, set[str]] = {}
    for source, target in tcgs.get_edges():
        targets.setdefault(source, set()).add(target)
    return {
        str(location): tuple(sorted(targets.get(location, ()), key=str))
        for location in tcgs.states
    }


def _successor_lists(
    delay_successors: dict[TimeState, set[TimeState]],
    discrete_successors: dict[TimeState, dict[str, set[TimeState]]],
) -> dict[TimeState, list[TimeState]]:
    """Every successor of each state, delay steps first."""
    return {
        state: [*delays, *chain.from_iterable(discrete_successors[state].values())]
        for state, delays in delay_successors.items()
    }


def _max_constants(tcgs: TimedCGS, formula_constants: dict[str, int]) -> list[int]:
    """Each clock's largest constant in the model and the formula."""
    max_constants = DBMAdapter.get_max_clock_constraints(tcgs)
    for clock, constant in formula_constants.items():
        idx = tcgs.clocks_dict[clock]
        max_constants[idx] = max(max_constants[idx], constant)
    return max_constants


def _time_rank(region: TimeState) -> int:
    """Grows at every step along a delay path: each step raises some clock's lower
    bound, or makes it strict."""
    bounds = region.zone.elements[0][1:]
    return sum(2 * -bound.constant + (bound.operator == "<") for bound in bounds)


def _time_order(regions: list[TimeState]) -> list[TimeState]:
    """``regions`` of one delay path in the order time reaches them."""
    ordered = sorted(regions, key=_time_rank)
    for earlier, later in pairwise(ordered):
        if _time_rank(earlier) == _time_rank(later):
            raise ValueError(
                f"Delay regions at location {earlier.location} are not one time path"
            )
    return ordered


def _expand_delay_successors(exploration: _Exploration, state: TimeState) -> None:
    if exploration.delay_successors[state]:
        return  # linked when an earlier region's delay path was built
    zone = DBMAdapter.delay_zone(exploration.tcgs, state.zone, state.location)
    if zone is None:
        return
    path = _time_order(exploration.regions(state.location, zone))
    if path[0] != state:
        raise ValueError(f"Delay path at location {state.location} starts elsewhere")
    # A longer step would skip the regions between; a self-loop on the last would
    # suggest infinite time progress inside a bounded invariant.
    for earlier, later in pairwise(path):
        exploration.add_state(later)
        exploration.delay_successors[earlier].add(later)


def _expand_discrete_successors(exploration: _Exploration, state: TimeState) -> None:
    tcgs = exploration.tcgs
    source_idx = tcgs.get_index_by_state_name(state.location)
    for target in exploration.location_targets[state.location]:
        target_idx = tcgs.get_index_by_state_name(target)
        zone = DBMAdapter.forward_transition_zone(
            tcgs, state.zone, source_idx, target_idx
        )
        if zone is None:
            continue
        for successor in exploration.regions(target, zone):
            exploration.discrete_successors[state].setdefault(target, set()).add(
                successor
            )
            exploration.add_state(successor)


def _initial_zone(tcgs: TimedCGS) -> DBM | None:
    """Build the start zone: all clocks at zero, closed under the location invariant."""
    zone = DBM(len(tcgs.clocks))
    for clock_idx in range(1, zone.size):
        zone.add_constraint(clock_idx, 0, 0, "<=")
        zone.add_constraint(0, clock_idx, 0, "<=")
    loc_idx = tcgs.get_index_by_state_name(tcgs.initial_state)
    if tcgs.invariants_arr[loc_idx]:
        DBMAdapter.apply_location_invariants(zone, tcgs, loc_idx)
        if zone.is_empty():
            return None
    return zone


def _explore(
    tcgs: TimedCGS, formula_constants: dict[str, int]
) -> tuple[_Exploration, TimeState | None]:
    """Explore reachable regions from the zero-clock initial zone."""
    exploration = _Exploration(tcgs, formula_constants)
    initial_zone = _initial_zone(tcgs)
    if initial_zone is None:
        return exploration, None

    # Every clock is 0, so the initial zone is one region.
    [initial_state] = exploration.regions(tcgs.initial_state, initial_zone)
    exploration.add_state(initial_state)
    while exploration.waitlist:
        state = exploration.waitlist.popleft()
        _expand_delay_successors(exploration, state)
        _expand_discrete_successors(exploration, state)
    return exploration, initial_state


class ZoneGraph:
    def __init__(self, tcgs: TimedCGS, formula_constants: dict[str, int] | None = None):
        """The (location, clock region) graph for timed model checking;
        ``formula_constants`` adds the formula's largest constant per clock name."""
        self.tcgs = tcgs
        exploration, self.initial_time_state = _explore(tcgs, formula_constants or {})
        self.location_targets = exploration.location_targets
        self.delay_successors = exploration.delay_successors
        self.discrete_successors = exploration.discrete_successors
        self.graph = _successor_lists(self.delay_successors, self.discrete_successors)
        self.states = set(self.graph)
        self.reverse_graph = reverse_adjacency(self.graph, self.states)

    def _backward_path_starts(self, target_location: str) -> list[TimeState]:
        return sorted(
            (state for state in self.states if state.location == target_location),
            key=lambda item: item.location,
        )

    def _allows_node(self, node: TimeState, constraints: list | None) -> bool:
        if not constraints:
            return True
        return DBMAdapter.zone_satisfies_guards(
            self.tcgs, node.location, node.zone, constraints
        )

    def has_path_from(
        self, target_location: str, constraints: list | None = None
    ) -> bool:
        """True if a backward path exists from target_location to the initial location."""
        starts = self._backward_path_starts(target_location)
        if not self.states or not starts:
            return False

        initial_loc = self.tcgs.initial_state
        reverse_graph = reverse_adjacency(self.graph, self.states)
        return any_backward_path(
            starts,
            reverse_graph,
            is_goal=lambda node: node.location == initial_loc,
            allows_node=lambda node: self._allows_node(node, constraints),
            sort_neighbors=lambda neighbors: sorted(
                neighbors, key=lambda item: item.location
            ),
        )

    def find_path_from(
        self, target_location: str, constraints: list | None = None
    ) -> list[list[TimeState]]:
        """All backward paths from `target_location` to the initial location; with
        `constraints`, each step must meet the clock guard and the invariant."""
        starts = self._backward_path_starts(target_location)
        if not self.states or not starts:
            return []

        initial_loc = self.tcgs.initial_state
        reverse_graph = reverse_adjacency(self.graph, self.states)
        return collect_backward_paths(
            starts,
            reverse_graph,
            is_goal=lambda node: node.location == initial_loc,
            allows_node=lambda node: self._allows_node(node, constraints),
            sort_neighbors=lambda neighbors: sorted(
                neighbors, key=lambda item: item.location
            ),
        )
