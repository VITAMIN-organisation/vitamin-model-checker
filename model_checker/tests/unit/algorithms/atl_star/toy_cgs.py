"""Hand-built, minimal objects matching `CGSProtocol`'s shape, no file
parsing, for isolated `cgs_adapter.py` unit tests (edge cases like a
malformed profile, a bad initial state, or a wildcard cell, in complete
isolation). Tests against a real VITAMIN fixture load the real `CGS`
class directly instead (see `test_cgs_adapter.py`).

Two agents (1: requester, 2: granter), states `s0`/`s1`. From `s0`,
`req|grant` moves to `s1` (where `granted` holds); every other joint action
self-loops on `s0`. From `s1`, every joint action resets to `s0`. Cell
values are transition-matrix entries: `0` for "no edge", otherwise one or
more `,`-separated `|`-joined-per-agent profiles, mirroring the real CGS
encoding `cgs_adapter.adapt()` reads.
"""

from __future__ import annotations


def _get_edges(graph: list[list], states: list[str]) -> list[tuple[str, str]]:
    """Mirrors VITAMIN's own `cgs_utils.get_edges`: one `(source, target)`
    pair per nonzero cell, using the real column for an ordinary cell but
    collapsing to `(source, source)` for a wildcard regardless of column.

    A wildcard (`"*"`, a `str`) is never `== 0` (an `int`), so `element !=
    0` alone is equivalent to VITAMIN's own `element == "*" or element !=
    0` without the redundant second comparison on every cell; `source` is
    looked up once per row instead of once per matched cell.
    """
    edges: list[tuple[str, str]] = []
    for i, row in enumerate(graph):
        source = states[i]
        for j, element in enumerate(row):
            if element == 0:
                continue
            edges.append((source, source if element == "*" else states[j]))
    return edges


class ToyCGS:
    def __init__(self) -> None:
        self.states = ["s0", "s1"]
        self.initial_state = "s0"
        self.atomic_propositions = ["granted"]
        self.matrix_prop = [[0], [1]]
        self.graph = [
            ["req|deny,idle|grant,idle|deny", "req|grant"],
            ["req|grant,req|deny,idle|grant,idle|deny", 0],
        ]

    def get_number_of_agents(self) -> int:
        return 2

    def get_state_name_by_index(self, index: int) -> str:
        return self.states[index]

    def get_index_by_state_name(self, state: object) -> int:
        return self.states.index(state)

    def get_edges(self) -> list[tuple[str, str]]:
        return _get_edges(self.graph, self.states)

    def build_action_list(self, action_string: object) -> list[str]:
        return str(action_string).split(",")


class MalformedToyCGS(ToyCGS):
    """Same shape, but `s0`'s self-loop cell has a single-character profile,
    too short for 2 agents under either format (compact-per-character or
    `|`-separated), used to test `adapt()`'s token-count validation."""

    def __init__(self) -> None:
        super().__init__()
        self.graph[0][0] = "r"


class BadInitialStateToyCGS(ToyCGS):
    """Same shape, but `initial_state` names a state that doesn't exist."""

    def __init__(self) -> None:
        super().__init__()
        self.initial_state = "s99"


class WildcardToyCGS(ToyCGS):
    """Same shape, but `s0`'s self-loop cell is the real CGS wildcard `"*"`
    instead of the explicit profiles `ToyCGS` writes out, behaviorally
    equivalent to `ToyCGS` once `adapt()` expands the wildcard, since the
    real transition out of `s0` (`req|grant` -> `s1`) stays on its own cell
    and every other joint action known in the model self-loops either way."""

    def __init__(self) -> None:
        super().__init__()
        self.graph[0][0] = "*"

    def build_action_list(self, action_string: object) -> list[str]:
        if action_string == "*":
            action_string = "*" * self.get_number_of_agents()
        return str(action_string).split(",")


class CompactActionCGS:
    """Same 2-state/2-agent shape as `ToyCGS`, but using the real, compact
    one-character-per-agent action encoding (`"AC"` = agent 1 does `A`,
    agent 2 does `C`) instead of `|`-separated tokens, exactly the format
    VITAMIN's own `atl_2agents_4states_simple.txt` fixture uses, confirmed
    against `cgs_actions.parse_joint_action_cell`."""

    def __init__(self) -> None:
        self.states = ["s0", "s1"]
        self.initial_state = "s0"
        self.atomic_propositions = ["reached"]
        self.matrix_prop = [[0], [1]]
        self.graph = [
            ["AD,BC,BD", "AC"],
            ["AC,AD,BC,BD", 0],
        ]

    def get_number_of_agents(self) -> int:
        return 2

    def get_state_name_by_index(self, index: int) -> str:
        return self.states[index]

    def get_index_by_state_name(self, state: object) -> int:
        return self.states.index(state)

    def get_edges(self) -> list[tuple[str, str]]:
        return _get_edges(self.graph, self.states)

    def build_action_list(self, action_string: object) -> list[str]:
        return str(action_string).split(",")
