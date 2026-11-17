from collections import deque
from itertools import chain, pairwise

from model_checker.algorithms.explicit.shared.trace_utils import reverse_adjacency

from .DBM import DBMAdapter
from .DBM.DBM import DBM
from .formula_clocks import extend_timed_cgs_clocks
from .timed_cgs import TimedCGS

# Not a valid clock name in a formula or a model file, so it never clashes.
TICK_CLOCK = "#tick"


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

    def __init__(
        self,
        tcgs: TimedCGS,
        formula_constants: dict[str, int],
        freeze_clocks: tuple[str, ...],
        tick_clock: int | None,
    ):
        self.tcgs = tcgs
        self.max_constants = _max_constants(tcgs, formula_constants)
        self.location_targets = _location_targets(tcgs)
        self.tick_clock = tick_clock
        self.delay_successors: dict[TimeState, set[TimeState]] = {}
        self.discrete_successors: dict[TimeState, dict[str, set[TimeState]]] = {}
        self.tick_resets: dict[TimeState, TimeState] = {}
        self.freeze_resets: dict[str, dict[TimeState, TimeState]] = {
            clock: {} for clock in freeze_clocks
        }
        self.reachable_states: set[TimeState] = set()
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

    def is_tick(self, state: TimeState) -> bool:
        """True when the tick clock has reached 1 in ``state``."""
        if self.tick_clock is None:
            return False
        return _lower_bound(state.zone, self.tick_clock) >= 1

    def reset_region(self, state: TimeState, clock_idx: int) -> TimeState:
        """The region reached from ``state`` by setting clock ``clock_idx`` to 0."""
        zone = state.zone.get_reset(clock_idx, 0)
        # A reset keeps the other clocks' region, so the result is one region.
        [region] = self.regions(state.location, zone)
        self.add_state(region)
        return region


def _lower_bound(zone: DBM, clock_idx: int) -> float:
    """The lower bound of clock ``clock_idx`` (DBM index) in ``zone``."""
    return -zone.elements[0][clock_idx].constant


def _location_targets(tcgs: TimedCGS) -> dict[str, tuple[str, ...]]:
    """Each location's edge targets, sorted."""
    targets: dict[str, set[str]] = {}
    for source, target in tcgs.get_edges():
        targets.setdefault(source, set()).add(target)
    return {
        str(location): tuple(sorted(targets.get(location, ()), key=str))
        for location in tcgs.states
    }


def _successor_lists(exploration: _Exploration) -> dict[TimeState, list[TimeState]]:
    """Every successor of each state, delay steps first."""
    return {
        state: [
            *delays,
            *chain.from_iterable(exploration.discrete_successors[state].values()),
            *filter(None, [exploration.tick_resets.get(state)]),
        ]
        for state, delays in exploration.delay_successors.items()
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
    zone = region.zone
    return sum(
        2 * _lower_bound(zone, idx) + (zone.elements[0][idx].operator == "<")
        for idx in range(1, zone.size)
    )


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
    # A longer step would skip the regions between; a tick region's only step is
    # its tick reset.
    for earlier, later in pairwise(path):
        exploration.add_state(later)
        exploration.delay_successors[earlier].add(later)
        if exploration.is_tick(later):
            break


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


def _link_freeze_resets(exploration: _Exploration, state: TimeState) -> None:
    """Record, for each freeze clock, the region reached by resetting it; the
    link is not an edge, so time and edge steps never follow it."""
    for clock, resets in exploration.freeze_resets.items():
        clock_idx = exploration.tcgs.clocks_dict[clock] + 1
        resets[state] = exploration.reset_region(state, clock_idx)


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
    tcgs: TimedCGS,
    formula_constants: dict[str, int],
    freeze_clocks: tuple[str, ...],
    track_divergence: bool,
) -> tuple[_Exploration, TimeState | None]:
    """Explore the regions reached from the zero-clock initial zone by time, edges
    and freeze resets."""
    tick_clock = None
    if track_divergence:
        extend_timed_cgs_clocks(tcgs, (TICK_CLOCK,))
        formula_constants = {**formula_constants, TICK_CLOCK: 1}
        tick_clock = tcgs.clocks_dict[TICK_CLOCK] + 1
    exploration = _Exploration(tcgs, formula_constants, freeze_clocks, tick_clock)
    initial_zone = _initial_zone(tcgs)
    if initial_zone is None:
        return exploration, None

    # Every clock is 0, so the initial zone is one region.
    [initial_state] = exploration.regions(tcgs.initial_state, initial_zone)
    exploration.add_state(initial_state)
    _expand_waitlist(exploration, link_freeze_resets=False)
    # Only time and edge steps reach the states found so far.
    exploration.reachable_states = set(exploration.delay_successors)
    for state in exploration.reachable_states:
        _link_freeze_resets(exploration, state)
    _expand_waitlist(exploration, link_freeze_resets=True)
    return exploration, initial_state


def _expand_waitlist(exploration: _Exploration, link_freeze_resets: bool) -> None:
    while exploration.waitlist:
        state = exploration.waitlist.popleft()
        if exploration.tick_clock is not None and exploration.is_tick(state):
            exploration.tick_resets[state] = exploration.reset_region(
                state, exploration.tick_clock
            )
        else:
            _expand_delay_successors(exploration, state)
            _expand_discrete_successors(exploration, state)
        if link_freeze_resets:
            _link_freeze_resets(exploration, state)


class ZoneGraph:
    def __init__(
        self,
        tcgs: TimedCGS,
        formula_constants: dict[str, int] | None = None,
        freeze_clocks: tuple[str, ...] = (),
        track_divergence: bool = False,
    ):
        """The (location, clock region) graph; with ``track_divergence`` a path is
        time-divergent iff it visits ``tick_states`` infinitely often."""
        self.tcgs = tcgs
        exploration, self.initial_time_state = _explore(
            tcgs, formula_constants or {}, freeze_clocks, track_divergence
        )
        self.location_targets = exploration.location_targets
        self.delay_successors = exploration.delay_successors
        self.discrete_successors = exploration.discrete_successors
        self.freeze_resets = exploration.freeze_resets
        self.tick_states = set(exploration.tick_resets)
        self.reachable_states = exploration.reachable_states
        self.graph = _successor_lists(exploration)
        self.states = set(self.graph)
        self.reverse_graph = reverse_adjacency(self.graph, self.states)
