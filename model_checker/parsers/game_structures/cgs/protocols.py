"""Protocols for CGS (Concurrent Game Structure) interfaces.

Used by algorithm modules to type cgs parameters without depending on
concrete parser classes. Any object that implements these methods
satisfies the protocol.
"""

from typing import Any, List, Optional, Protocol, Set


class CGSProtocol(Protocol):
    """Protocol for CGS-like models used by explicit model-checking algorithms."""

    @property
    def graph(self) -> Any:
        """Transition structure (e.g. list of edges or adjacency)."""
        ...

    @property
    def initial_state(self) -> str:
        """Name of the initial state."""
        ...

    @property
    def number_of_agents(self) -> Optional[int]:
        """Number of agents; None if not set."""
        ...

    @property
    def actions(self) -> List[Any]:
        """Action data (structure is parser-specific)."""
        ...

    @property
    def matrix_prop(self) -> Any:
        """Labelling / proposition matrix (state x prop)."""
        ...

    @property
    def all_states_set(self) -> Set[str]:
        """Set of all state names."""
        ...

    def get_number_of_agents(self) -> int:
        """Return number of agents; raises if missing."""
        ...

    def get_states(self) -> Any:
        """Return state names (array or list)."""
        ...

    def get_initial_state(self) -> str:
        """Return initial state name."""
        ...

    def get_edges(self) -> Any:
        """Return edge list or cached edges for traversal."""
        ...

    def get_reverse_index(self) -> Any:
        """Return reverse edge index for backward traversal; optional."""
        ...

    def get_index_by_state_name(self, state: Any) -> int:
        """Return index of the state with the given name."""
        ...

    def get_state_name_by_index(self, index: int) -> Any:
        """Return state name at the given index."""
        ...

    def get_actions(self, agents: Any) -> Any:
        """Return actions for the given agent(s)."""
        ...

    def get_atomic_prop(self) -> Any:
        """Return atomic propositions (array or list)."""
        ...

    def get_atom_index(self, element: Any) -> Optional[int]:
        """Return index of the given proposition, or None if unknown."""
        ...

    def get_matrix_proposition(self) -> Any:
        """Return labelling / proposition matrix."""
        ...

    def get_agents_from_coalition(self, coalition: Any) -> Any:
        """Parse coalition string into agent set."""
        ...

    def get_coalition_action(self, actions: Any, agents: Any) -> Any:
        """Return coalition action representation."""
        ...

    def build_action_list(self, action_string: Any) -> Any:
        """Turn action string into list of action strings."""
        ...

    def get_opponent_moves(self, actions: Any, agents: Any) -> Any:
        """Return opponent moves for the given coalition actions."""
        ...


class CapCGSProtocol(CGSProtocol, Protocol):
    """Extension of CGSProtocol for capability CGS (used by CapATL)."""

    def get_action_capacities(self) -> Any:
        """Return action capacity data."""
        ...

    def get_capacities_assignment(self) -> Any:
        """Return capacity assignment per agent."""
        ...


class CostCGSProtocol(CGSProtocol, Protocol):
    """Extension of CGSProtocol for cost CGS (used by RBATL, RABATL)."""

    def get_cost_for_action(self, action: Any, state_name: Any) -> Any:
        """Return cost vector for the given action at the given state."""
        ...
