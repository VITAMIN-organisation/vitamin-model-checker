"""
Verification result classes for model checking with witness and counterexample support.

This module provides data structures to hold verification results along with
witness traces (for positive results) and counterexamples (for negative results).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class TraceType(str, Enum):
    WITNESS = "witness"
    COUNTEREXAMPLE = "counterexample"


@dataclass
class StateTrace:
    """
    Represents a trace (path) through the state space.

    A trace is a sequence of states that demonstrates why a formula is
    satisfied (witness) or violated (counterexample).

    Attributes:
        states: Ordered list of state names forming the path
        trace_type: Type of trace ("witness" or "counterexample")
        description: Human-readable description of what this trace shows
    """

    states: List[str]
    trace_type: TraceType  # "witness" or "counterexample"
    description: str = ""

    def __post_init__(self) -> None:
        # Allow callers to pass either a TraceType or matching string literal.
        if not isinstance(self.trace_type, TraceType):
            self.trace_type = TraceType(self.trace_type)

    def __str__(self) -> str:
        """Format trace for human-readable output."""
        if not self.states:
            return f"{self.trace_type.capitalize()}: (empty trace)"

        trace_str = " -> ".join(self.states)
        result = f"{self.trace_type.capitalize()}: {trace_str}"
        if self.description:
            result += f"\n  Description: {self.description}"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary format for API responses."""
        return {
            "states": self.states,
            "type": self.trace_type,
            "description": self.description,
            "length": len(self.states),
        }


@dataclass
class StrategyTrace:
    """
    Represents a strategy for coalition operators with state-action mappings.

    Used for ATL-family logics where we need to show not just a path,
    but also the actions that achieve the goal.

    Attributes:
        agent_strategies: Mapping from agent ID to their strategy
        trace: Optional state trace showing execution of the strategy
        description: Human-readable description of the strategy
    """

    agent_strategies: Dict[str, List[tuple]]  # agent -> [(state, action), ...]
    trace: Optional[StateTrace] = None
    description: str = ""

    def __str__(self) -> str:
        """Format strategy for human-readable output."""
        result = "Strategy:\n"
        for agent_id, strategy in self.agent_strategies.items():
            result += f"  {agent_id}:\n"
            for state, action in strategy:
                result += f"    {state} -> {action}\n"
        if self.trace:
            result += f"\n{self.trace}"
        if self.description:
            result += f"\nDescription: {self.description}"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy to dictionary format for API responses."""
        return {
            "agent_strategies": {
                agent: [(s, a) for s, a in strat]
                for agent, strat in self.agent_strategies.items()
            },
            "trace": self.trace.to_dict() if self.trace else None,
            "description": self.description,
        }


@dataclass
class VerificationResult:
    """
    Complete verification result with states and optional trace/strategy information.

    This class replaces the simple set-of-states return type with a richer
    structure that includes witness traces for positive results and
    counterexamples for negative results.

    Attributes:
        states: Set of state names where the formula holds
        satisfied: Whether the initial state satisfies the formula
        initial_state: Name of the initial state
        trace: Optional trace showing why formula holds/doesn't hold
        strategy: Optional strategy for coalition operators (ATL-family)
        metadata: Additional information (algorithm used, time taken, etc.)
    """

    states: Set[str]
    satisfied: bool
    initial_state: str
    trace: Optional[StateTrace] = None
    strategy: Optional[StrategyTrace] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format result for human-readable output."""
        result = f"Result: {self.states}\n"
        result += f"Initial state {self.initial_state}: {self.satisfied}"

        if self.trace:
            result += f"\n\n{self.trace}"

        if self.strategy:
            result += f"\n\n{self.strategy}"

        if self.metadata:
            result += "\n\nMetadata:"
            for key, value in self.metadata.items():
                result += f"\n  {key}: {value}"

        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary format for API responses.

        This format is compatible with the existing API structure while
        adding optional trace/strategy fields.
        """
        return {
            "res": f"Result: {self.states}",
            "initial_state": f"Initial state {self.initial_state}: {self.satisfied}",
            "satisfied": self.satisfied,
            "states": sorted(self.states),
            "trace": self.trace.to_dict() if self.trace else None,
            "strategy": self.strategy.to_dict() if self.strategy else None,
            "metadata": self.metadata,
        }

    def to_compact_dict(self) -> Dict[str, str]:
        """
        Convert result to compact dictionary format.

        Returns only 'res' and 'initial_state' fields.
        """
        return {
            "res": f"Result: {self.states}",
            "initial_state": f"Initial state {self.initial_state}: {self.satisfied}",
        }
