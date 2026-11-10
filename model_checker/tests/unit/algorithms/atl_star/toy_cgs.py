"""Hand-built CGS objects for the ATL* tests, so each edge case needs no model file.

ToyCGS: agents 1 (requester) and 2 (granter), states s0 and s1. From s0 only
req|grant reaches s1, where `granted` holds; every other joint action stays at s0.
From s1 every joint action returns to s0. A cell is 0 (no edge) or `,`-separated
profiles with `|` between the agents' actions, as in a CGS file.
"""

from __future__ import annotations


def _get_edges(graph: list[list], states: list[str]) -> list[tuple[str, str]]:
    """One (source, target) per nonzero cell; a `*` cell is a self-loop, as in cgs_utils.get_edges."""
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


class AllWildcardToyCGS:
    """One state whose only cell is `*`: no concrete action exists anywhere in the model."""

    def __init__(self) -> None:
        self.states = ["s0"]
        self.initial_state = "s0"
        self.atomic_propositions = ["p"]
        self.matrix_prop = [[1]]
        self.graph = [["*"]]

    def get_number_of_agents(self) -> int:
        return 1

    def get_state_name_by_index(self, index: int) -> str:
        return self.states[index]

    def get_index_by_state_name(self, state: object) -> int:
        return self.states.index(state)

    def get_edges(self) -> list[tuple[str, str]]:
        return _get_edges(self.graph, self.states)

    def build_action_list(self, action_string: object) -> list[str]:
        if action_string == "*":
            action_string = "*" * self.get_number_of_agents()
        return str(action_string).split(",")


class MalformedToyCGS(ToyCGS):
    """s0's self-loop cell is `r`, one token for two agents."""

    def __init__(self) -> None:
        super().__init__()
        self.graph[0][0] = "r"


class BadInitialStateToyCGS(ToyCGS):
    """The initial state s99 is not a state of the model."""

    def __init__(self) -> None:
        super().__init__()
        self.initial_state = "s99"


class WildcardToyCGS(ToyCGS):
    """s0's self-loop cell is `*`, which must expand to the same self-loops ToyCGS lists."""

    def __init__(self) -> None:
        super().__init__()
        self.graph[0][0] = "*"

    def build_action_list(self, action_string: object) -> list[str]:
        if action_string == "*":
            action_string = "*" * self.get_number_of_agents()
        return str(action_string).split(",")


class CollidingMarkerToyCGS(ToyCGS):
    """Also declares `__atl_star_elim_0` (always false), the first name the verifier generates for a nested coalition."""

    def __init__(self) -> None:
        super().__init__()
        self.atomic_propositions = ["granted", "__atl_star_elim_0"]
        self.matrix_prop = [[0, 0], [1, 0]]


class CompactActionCGS:
    """ToyCGS's shape with compact cells (`AC` = agent 1 plays A, agent 2 plays C); only AC reaches s1."""

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
