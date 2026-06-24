"""Result objects with optional witness or counterexample traces."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TraceType(str, Enum):
    WITNESS = "witness"
    COUNTEREXAMPLE = "counterexample"


@dataclass
class StateTrace:
    """A path through the model (witness or counterexample)."""

    states: list[str]
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

    def to_dict(self) -> dict[str, Any]:
        """Convert trace to dictionary format for API responses."""
        return {
            "states": self.states,
            "type": self.trace_type,
            "description": self.description,
            "length": len(self.states),
        }


@dataclass
class StrategyTrace:
    """Coalition strategy as state-action pairs, with an optional path."""

    agent_strategies: dict[str, list[tuple]]  # agent -> [(state, action), ...]
    trace: StateTrace | None = None
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

    def to_dict(self) -> dict[str, Any]:
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
    """Model-checking outcome: satisfying states plus optional trace or strategy."""

    states: set[str]
    satisfied: bool
    initial_state: str
    trace: StateTrace | None = None
    strategy: StrategyTrace | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

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

    def to_dict(self) -> dict[str, Any]:
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

    def to_compact_dict(self) -> dict[str, str]:
        """
        Convert result to compact dictionary format.

        Returns only 'res' and 'initial_state' fields.
        """
        return {
            "res": f"Result: {self.states}",
            "initial_state": f"Initial state {self.initial_state}: {self.satisfied}",
        }
