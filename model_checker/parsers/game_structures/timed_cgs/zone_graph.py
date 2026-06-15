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


def _is_subsumed_by_visited(state: TimeState, visited: list[TimeState]) -> bool:
    return any(
        state.location == other.location and state.zone.includes(other.zone)
        for other in visited
    )


def _register_state(
    zone_graph: dict,
    all_states: set,
    waitlist: list,
    predecessor: TimeState,
    successor: TimeState,
) -> None:
    zone_graph[predecessor].append(successor)
    if successor not in zone_graph:
        zone_graph[successor] = []
        waitlist.append(successor)
    all_states.add(successor)


class ZoneGraph:
    def __init__(self, tcgs: TimedCGS):
        self.tcgs = tcgs
        self.graph, self.states = self._build_zone_graph(tcgs)

    def _build_zone_graph(self, tcgs: TimedCGS):
        zone_graph: dict[TimeState, list[TimeState]] = {}
        all_states: set[TimeState] = set()

        initial_state = TimeState(
            location=tcgs.initial_state, zone=DBM(len(tcgs.clocks))
        )
        all_states.add(initial_state)
        zone_graph[initial_state] = []
        waitlist = [initial_state]
        visited: list[TimeState] = []

        while waitlist:
            current_state = waitlist.pop(0)
            if _is_subsumed_by_visited(current_state, visited):
                continue

            delay_zone = DBMAdapter.delay_zone(
                tcgs, current_state.zone, current_state.location
            )
            if delay_zone is not None:
                delay_state = TimeState(current_state.location, delay_zone)
                _register_state(
                    zone_graph, all_states, waitlist, current_state, delay_state
                )
                visited.append(current_state)

            source_idx = tcgs.get_index_by_state_name(current_state.location)
            outgoing = sorted(
                (
                    target
                    for source, target in tcgs.get_edges()
                    if source == current_state.location
                ),
                key=str,
            )
            for target in outgoing:
                target_idx = tcgs.get_index_by_state_name(target)
                successor_zone = DBMAdapter.forward_transition_zone(
                    tcgs, current_state.zone, source_idx, target_idx
                )
                if successor_zone is None:
                    continue
                successor_state = TimeState(target, successor_zone)
                _register_state(
                    zone_graph, all_states, waitlist, current_state, successor_state
                )

        return zone_graph, all_states

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
        if not self.states:
            return False

        starts = self._backward_path_starts(target_location)
        if not starts:
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
        """
        All backward paths from target_location to the initial location.

        When constraints are given, each step must satisfy the clock guard
        together with the location invariant.
        """
        if not self.states:
            return []

        starts = self._backward_path_starts(target_location)
        if not starts:
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
