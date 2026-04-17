"""Witness/counterexample: VerificationResult, StateTrace, StrategyTrace, trace reconstruction (BFS, predecessor map)."""

from model_checker.algorithms.explicit.shared.trace_utils import (
    build_predecessor_map_bfs,
    build_predecessor_map_forward,
    extract_shortest_trace,
    reconstruct_trace_bfs,
    reconstruct_trace_from_predecessors,
)
from model_checker.algorithms.explicit.shared.verification_result import (
    StateTrace,
    StrategyTrace,
    VerificationResult,
)


class TestStateTrace:
    """Test StateTrace class functionality."""

    def test_state_trace_creation(self):
        """Test creating a StateTrace object."""
        trace = StateTrace(
            states=["s0", "s1", "s2"], trace_type="witness", description="Test trace"
        )

        assert trace.states == ["s0", "s1", "s2"]
        assert trace.trace_type == "witness"
        assert trace.description == "Test trace"

    def test_state_trace_str(self):
        """Test string representation of StateTrace."""
        trace = StateTrace(
            states=["s0", "s1", "s2"], trace_type="witness", description="Path to goal"
        )

        trace_str = str(trace)
        assert "Witness:" in trace_str
        assert "s0 -> s1 -> s2" in trace_str
        assert "Path to goal" in trace_str

    def test_state_trace_to_dict(self):
        """Test dictionary conversion of StateTrace."""
        trace = StateTrace(
            states=["s0", "s1"],
            trace_type="counterexample",
            description="Violation found",
        )

        trace_dict = trace.to_dict()
        assert trace_dict["states"] == ["s0", "s1"]
        assert trace_dict["type"] == "counterexample"
        assert trace_dict["description"] == "Violation found"
        assert trace_dict["length"] == 2

    def test_empty_trace(self):
        """Test empty trace handling."""
        trace = StateTrace(states=[], trace_type="witness")

        trace_str = str(trace)
        assert "empty trace" in trace_str.lower()


class TestVerificationResult:
    """Test VerificationResult class functionality."""

    def test_verification_result_creation(self):
        """Test creating a VerificationResult object."""
        result = VerificationResult(
            states={"s0", "s1"}, satisfied=True, initial_state="s0"
        )

        assert result.states == {"s0", "s1"}
        assert result.satisfied is True
        assert result.initial_state == "s0"
        assert result.trace is None
        assert result.strategy is None

    def test_verification_result_with_trace(self):
        """Test VerificationResult with trace."""
        trace = StateTrace(states=["s0", "s1"], trace_type="witness")

        result = VerificationResult(
            states={"s0", "s1"}, satisfied=True, initial_state="s0", trace=trace
        )

        assert result.trace is not None
        assert result.trace.states == ["s0", "s1"]

    def test_verification_result_to_dict(self):
        """Test dictionary conversion."""
        trace = StateTrace(states=["s0"], trace_type="witness")

        result = VerificationResult(
            states={"s0"}, satisfied=True, initial_state="s0", trace=trace
        )

        result_dict = result.to_dict()
        assert "res" in result_dict
        assert "initial_state" in result_dict
        assert "satisfied" in result_dict
        assert "states" in result_dict
        assert "trace" in result_dict

    def test_verification_result_compact_format(self):
        """to_compact_dict returns only res and initial_state."""
        result = VerificationResult(
            states={"s0", "s1"}, satisfied=True, initial_state="s0"
        )

        compact_dict = result.to_compact_dict()
        assert "res" in compact_dict
        assert "initial_state" in compact_dict
        assert len(compact_dict) == 2


class TestTraceReconstruction:
    """Test trace reconstruction utilities."""

    def test_reconstruct_trace_from_predecessors_simple(self):
        """Test simple trace reconstruction."""
        predecessors = {"s1": "s0", "s2": "s1", "s3": "s2"}

        trace = reconstruct_trace_from_predecessors(
            initial_state="s0", target_states={"s3"}, predecessors=predecessors
        )

        assert trace == ["s0", "s1", "s2", "s3"]

    def test_reconstruct_trace_from_predecessors_no_path(self):
        """Test when no path exists."""
        predecessors = {"s1": "s0", "s2": "s1"}

        trace = reconstruct_trace_from_predecessors(
            initial_state="s0",
            target_states={"s5"},  # Unreachable
            predecessors=predecessors,
        )

        assert trace is None

    def test_reconstruct_trace_from_predecessors_cycle_detection(self):
        """Test cycle detection in predecessor map."""
        predecessors = {"s1": "s2", "s2": "s1"}  # Cycle

        trace = reconstruct_trace_from_predecessors(
            initial_state="s0", target_states={"s1"}, predecessors=predecessors
        )

        assert trace is None

    def test_reconstruct_trace_bfs(self):
        """Test BFS-based trace reconstruction."""
        edges = [("s0", "s1"), ("s1", "s2"), ("s2", "s3"), ("s1", "s4")]

        trace = reconstruct_trace_bfs(
            edges=edges, initial_state="s0", target_states={"s3"}
        )

        assert trace == ["s0", "s1", "s2", "s3"]

    def test_reconstruct_trace_bfs_shortest_path(self):
        """Test that BFS finds shortest path."""
        edges = [("s0", "s1"), ("s1", "s2"), ("s2", "s3"), ("s0", "s3")]  # Direct path

        trace = reconstruct_trace_bfs(
            edges=edges, initial_state="s0", target_states={"s3"}
        )

        assert len(trace) == 2
        assert trace == ["s0", "s3"]

    def test_reconstruct_trace_bfs_no_path(self):
        """Test BFS when no path exists."""
        edges = [("s0", "s1"), ("s2", "s3")]

        trace = reconstruct_trace_bfs(
            edges=edges, initial_state="s0", target_states={"s3"}
        )

        assert trace is None

    def test_build_predecessor_map_bfs(self):
        """Test building predecessor map using backward BFS."""
        edges = [("s0", "s1"), ("s1", "s2"), ("s2", "s3")]

        predecessors = build_predecessor_map_bfs(edges=edges, target_states={"s3"})

        assert "s2" in predecessors
        assert predecessors["s2"] == "s3"
        assert "s1" in predecessors
        assert predecessors["s1"] == "s2"

    def test_build_predecessor_map_forward(self):
        """Test building predecessor map using forward BFS."""
        edges = [("s0", "s1"), ("s1", "s2"), ("s2", "s3")]

        predecessors = build_predecessor_map_forward(edges=edges, initial_state="s0")

        assert "s1" in predecessors
        assert predecessors["s1"] == "s0"
        assert "s2" in predecessors
        assert predecessors["s2"] == "s1"

    def test_extract_shortest_trace(self):
        """Test complete trace extraction."""
        edges = [("s0", "s1"), ("s1", "s2"), ("s0", "s2")]  # Shorter path

        trace = extract_shortest_trace(
            initial_state="s0",
            target_states={"s2"},
            all_states={"s0", "s1", "s2"},
            edges=edges,
        )

        assert trace is not None
        assert trace[0] == "s0"
        assert trace[-1] == "s2"
        assert len(trace) == 2

    def test_extract_shortest_trace_invalid_initial(self):
        """Test with invalid initial state."""
        edges = [("s0", "s1")]

        trace = extract_shortest_trace(
            initial_state="invalid",
            target_states={"s1"},
            all_states={"s0", "s1"},
            edges=edges,
        )

        assert trace is None


class TestStrategyTrace:
    """Test StrategyTrace class functionality."""

    def test_strategy_trace_creation(self):
        """Test creating a StrategyTrace object."""
        strategy = StrategyTrace(
            agent_strategies={
                "agent1": [("s0", "a"), ("s1", "b")],
                "agent2": [("s0", "c"), ("s1", "d")],
            },
            description="Coalition strategy",
        )

        assert "agent1" in strategy.agent_strategies
        assert "agent2" in strategy.agent_strategies
        assert strategy.description == "Coalition strategy"

    def test_strategy_trace_with_path(self):
        """Test StrategyTrace with execution path."""
        trace = StateTrace(states=["s0", "s1"], trace_type="witness")

        strategy = StrategyTrace(
            agent_strategies={"agent1": [("s0", "a")]}, trace=trace
        )

        assert strategy.trace is not None
        assert strategy.trace.states == ["s0", "s1"]

    def test_strategy_trace_to_dict(self):
        """Test dictionary conversion."""
        strategy = StrategyTrace(
            agent_strategies={"agent1": [("s0", "a")]}, description="Test strategy"
        )

        strategy_dict = strategy.to_dict()
        assert "agent_strategies" in strategy_dict
        assert "trace" in strategy_dict
        assert "description" in strategy_dict
