"""Schemas used by the benchmarking package."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    """Benchmark input tuple for one model checking run."""

    logic: str
    layout: str
    num_states: int
    formula: str
    formula_shape_hint: str | None = None
    formula_family: str | None = None

    @property
    def name(self) -> str:
        """Stable benchmark name for reports."""
        return f"{self.logic}:{self.layout}:{self.num_states}:{self.formula}"
