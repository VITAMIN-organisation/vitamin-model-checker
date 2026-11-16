from collections import deque
from itertools import chain

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


ClockBound = tuple[int, str, int]


class _Exploration:
    """Breadth-first exploration of the reachable regions; each successor is stored
    once, as a delay step or as a discrete step to a named location."""

    def __init__(self, tcgs: TimedCGS, formula_bounds: list[ClockBound]):
        self.tcgs = tcgs
        self.formula_bounds = formula_bounds
        self.max_constants = _max_constants(tcgs, formula_bounds)
        self.location_targets = _location_targets(tcgs)
        self.delay_successors: dict[TimeState, set[TimeState]] = {}
        self.discrete_successors: dict[TimeState, dict[str, set[TimeState]]] = {}
        self.waitlist: deque[TimeState] = deque()

    def regions(self, location: str, zone: DBM) -> list[TimeState]:
        """The regions of ``zone`` after normalization, split on the formula bounds."""
        zone.k_normalize(self.max_constants)
        return [
            TimeState(location, part)
            for part in DBMAdapter.split_zone(zone, self.formula_bounds)
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


def _max_constants(tcgs: TimedCGS, formula_bounds: list[ClockBound]) -> list[int]:
    """Each clock's largest constant in the model and the formula bounds."""
    max_constants = DBMAdapter.get_max_clock_constraints(tcgs)
    for clock_index, _op, constant in formula_bounds:
        idx = clock_index - 1
        max_constants[idx] = max(max_constants[idx], constant)
    return max_constants


def _expand_delay_successors(exploration: _Exploration, state: TimeState) -> None:
    zone = DBMAdapter.delay_zone(exploration.tcgs, state.zone, state.location)
    if zone is None:
        return
    for successor in exploration.regions(state.location, zone):
        # A region closed under delay+invariant gets no self-loop: it would
        # suggest infinite time progress inside a bounded invariant.
        if successor != state:
            exploration.delay_successors[state].add(successor)
            exploration.add_state(successor)


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
    tcgs: TimedCGS, formula_bounds: list[ClockBound]
) -> tuple[_Exploration, TimeState | None]:
    """Explore reachable regions from the zero-clock initial zone."""
    exploration = _Exploration(tcgs, formula_bounds)
    initial_zone = _initial_zone(tcgs)
    if initial_zone is None:
        return exploration, None

    # Every clock is 0, so the initial zone lies on one side of each bound.
    [initial_state] = exploration.regions(tcgs.initial_state, initial_zone)
    exploration.add_state(initial_state)
    while exploration.waitlist:
        state = exploration.waitlist.popleft()
        _expand_delay_successors(exploration, state)
        _expand_discrete_successors(exploration, state)
    return exploration, initial_state


class ZoneGraph:
    def __init__(self, tcgs: TimedCGS, formula_bounds: list[ClockBound] | None = None):
        """The (location, zone) graph for timed model checking, each zone split so it
        lies wholly inside or wholly outside every bound in ``formula_bounds``."""
        self.tcgs = tcgs
        exploration, self.initial_time_state = _explore(tcgs, formula_bounds or [])
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
