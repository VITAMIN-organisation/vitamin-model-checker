"""Protocols for CGS (Concurrent Game Structure) interfaces.

Used by algorithm modules to type cgs parameters without depending on
concrete parser classes. Any object that implements these methods
satisfies the protocol.
"""

from typing import Any, Protocol


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
    def number_of_agents(self) -> int | None:
        """Number of agents; None if not set."""
        ...

    @property
    def actions(self) -> list[Any]:
        """Action data (structure is parser-specific)."""
        ...

    @property
    def atomic_propositions(self) -> Any:
        """Atomic proposition names."""
        ...

    @property
    def matrix_prop(self) -> Any:
        """Labelling / proposition matrix (state x prop)."""
        ...

    @property
    def states(self) -> Any:
        """State names (array or list)."""
        ...

    @property
    def all_states_set(self) -> set[str]:
        """Set of all state names."""
        ...

    def get_number_of_agents(self) -> int:
        """Return number of agents; raises if missing."""
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

    def build_action_list(self, action_string: Any) -> Any:
        """Turn action string into list of action strings."""
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
