import io

from .DBM import DBMAdapter
from .DBM.DBM import DBM
from .timed_cgs import TimedCGS


class TimeState:
    def __init__(self, location: str, zone: DBM):
        self.location = location
        self.zone = zone

    def apply_constraint(self, guards: list[str], resets: list[str] | None = None):
        for clock_index, op, bound in guards:
            if op in (">", ">="):
                self.zone.add_constraint(
                    0, clock_index, -int(bound), op.replace(">", "<")
                )
            else:
                self.zone.add_constraint(clock_index, 0, int(bound), op)

        # Apply resets if any (rare for path filters, but supported)
        if resets:
            for clock_idx, reset_value in resets:
                self.zone.reset(clock_idx, reset_value)

    def copy(self):
        return TimeState(self.location, self.zone.copy())

    def __str__(self):
        return f"(location: {self.location} zone:\n {self.zone}\n)"

    def __repr__(self):
        self.__str__()

    def __hash__(self):
        return hash((self.location, self.zone))

    def __eq__(self, other):
        if not isinstance(other, TimeState):
            return NotImplemented
        return self.location == other.location and self.zone == other.zone


class ZoneGraph:
    def __init__(self, tcgs: TimedCGS):
        self.tcgs = tcgs
        self.graph, self.states = self._build_zone_graph(tcgs)

    def _build_zone_graph(self, tcgs: TimedCGS):
        """
        Builds the zone graph using forward reachability.
        Returns a dictionary where keys are TimeState objects and values are lists of successor TimeState objects.
        Also returns a list of all TimeState objects for easy iteration.
        """
        zone_graph = {}
        all_states = set()
        self.graph_ids = {}

        # === Initial state construction ===
        initial_state = TimeState(
            location=tcgs.initial_state, zone=DBM(len(tcgs.clocks))
        )
        all_states.add(initial_state)
        zone_graph[initial_state] = []
        waitlist = [initial_state]
        visited = []
        while waitlist:
            current_state = waitlist.pop(0)

            if any(
                (
                    current_state.location == s.location
                    and current_state.zone.includes(s.zone)
                )
                for s in visited
            ):
                continue

            delay_zone = current_state.zone.copy()
            delay_zone.up()

            loc_idx = tcgs.get_index_by_state_name(current_state.location)
            if len(tcgs.invariants_arr[loc_idx]):
                for k in range(0, len(tcgs.invariants_arr[loc_idx]), 2):
                    clock, bound = tcgs.invariants_arr[loc_idx][k : k + 2]
                    clock_idx = (
                        tcgs.clocks_dict[clock] + 1
                    )  # we up by 1 because the DBM adds one clock (the zero clock)
                    delay_zone.add_constraint(clock_idx, 0, bound)

            # re apply location invariants

            if delay_zone.is_empty():
                continue

            delay_state = TimeState(location=current_state.location, zone=delay_zone)

            zone_graph[current_state].append(delay_state)
            visited.append(current_state)
            waitlist.append(delay_state)
            if delay_state not in zone_graph:
                zone_graph[delay_state] = []
            all_states.add(delay_state)

            # discrete transitions
            edges = tcgs.get_edges()
            outgoing = sorted(
                [(s, t) for (s, t) in edges if s == current_state.location],
                key=lambda pair: pair[1],
            )
            for source, target in outgoing:
                if source == current_state.location:
                    source_index = tcgs.get_index_by_state_name(source)
                    target_index = tcgs.get_index_by_state_name(target)
                    constraints = [
                        c.strip()
                        for c in tcgs.clock_constraint_struct[source_index][
                            target_index
                        ].split(",")
                        if c.strip()
                    ]
                    guards, resets = DBMAdapter.parse_constraints(
                        constraints, tcgs.clocks_dict
                    )
                    successor_zone = current_state.zone.copy()

                    for clock_index, op, bound in guards:
                        if op in (">=", ">"):
                            successor_zone.add_constraint(
                                0, clock_index, -int(bound), op.replace(">", "<")
                            )  # ex: x>2 == x-x0 > 2 == x0 - x < -2
                        else:
                            successor_zone.add_constraint(
                                clock_index, 0, int(bound), op
                            )

                    if successor_zone.is_empty():
                        continue

                    if resets:
                        for clock_idx, reset_value in resets:
                            successor_zone.reset(clock_idx, reset_value)
                        successor_zone.up()  # This allows time to progress from the reset value, i.e., x1 can now increase from 0.

                    for k in range(0, len(tcgs.invariants_arr[target_index]), 2):
                        clock, bound = tcgs.invariants_arr[target_index][k : k + 2]
                        clock_idx = tcgs.clocks_dict[clock] + 1
                        successor_zone.add_constraint(clock_idx, 0, bound)

                    if successor_zone.is_empty():
                        continue

                    successor_state = TimeState(location=target, zone=successor_zone)

                    zone_graph[current_state].append(successor_state)

                    if successor_state not in zone_graph:
                        all_states.add(current_state)
                        zone_graph[successor_state] = []
                        waitlist.append(successor_state)
                    all_states.add(successor_state)

        for i, state in enumerate(all_states):
            self.graph_ids[state] = i

        return zone_graph, all_states

    def find_path_from(
        self, target_location: str, contraints: list[str] | None = None
    ) -> list[list[TimeState]]:
        """
        Returns all paths (as lists of TimeState) from any state at target_location
        back to any state whose location is the initial location.
        Paths are ordered from target -> ... -> initial.

        Constraints (optional) to apply at each step.
        """
        initial_loc = self.tcgs.initial_state
        if not self.states:
            return []

        # Build reverse graph for easy backward traversal
        reverse_graph = {}
        for state in self.states:
            reverse_graph[state] = []
        for src, succs in self.graph.items():
            for dst in succs:
                reverse_graph[dst].append(src)

        # Collect start nodes at target_location
        start_nodes = sorted(
            [s for s in self.states if s.location == target_location],
            key=lambda s: s.location,
        )
        if not start_nodes:
            return []

        all_paths: list[list] = []

        def dfs(node: TimeState, path):
            if contraints:
                nd = node.copy()
                nd.apply_constraint(contraints)
                if nd.zone.is_empty():
                    return

            new_path = path + [node]
            if node.location == initial_loc:
                all_paths.append(new_path)
                return
            for pred in sorted(reverse_graph.get(node, []), key=lambda s: s.location):
                if pred not in path:  # avoid cycles in current path
                    dfs(pred, new_path)

        for start in start_nodes:
            dfs(start, [])

        return all_paths

    def __str__(self) -> str:
        """
        Provides a human-readable string representation of the ZoneGraph.
        It lists all states with a short ID (S0, S1, ...) and then
        shows the graph structure using these IDs.
        """
        if not self.states:
            return "<ZoneGraph (empty)>"

        # Use a string builder
        s = io.StringIO()

        num_states = len(self.states)
        s.write(f"--- ZoneGraph ({num_states} states) ---\n")

        # 1. Print State Definitions (Node list)
        s.write("\n== States (Nodes) ==\n")
        for state, id in self.graph_ids.items():
            s.write(f"  S{id}: {state}\n")

        # 2. Print Graph Structure (Adjacency List)
        s.write("\n== Transitions (Edges) ==\n")
        for state in self.states:
            successors = self.graph.get(state, [])
            if not successors:
                s.write(f"  S{self.graph_ids[state]} -> []\n")
            else:
                # Format successor list as [S1, S2, ...]
                succ_str = ", ".join([f"S{self.graph_ids[j]}" for j in successors])
                s.write(f"  S{self.graph_ids[state]} -> [{succ_str}]\n")

        return s.getvalue()
