"""Benchmark case registry.

Cases are grouped by logic, then ordered by layout and state count.
Add new cases here; confirm logic support in adapters.py and model coverage in generators.py.
"""

from typing import Iterator, List, Optional

from model_checker.benchmarking.schemas import BenchmarkCase

_BENCHMARK_CASES: List[BenchmarkCase] = [
    # ------------------------------------------------------------------
    # ATL — Concurrent Game Structures, memoryless strategies
    # ------------------------------------------------------------------
    BenchmarkCase("ATL", "linear", 50, "<1>F p"),
    # BenchmarkCase("ATL", "linear",  50,  "<1>X p"),
    # BenchmarkCase("ATL", "linear", 100,  "<1>F p"),
    # BenchmarkCase("ATL", "linear", 100,  "<1>X p"),
    # BenchmarkCase("ATL", "linear", 200,  "<1>F p"),
    # BenchmarkCase("ATL", "linear", 200,  "<1>X p"),
    # BenchmarkCase("ATL", "linear", 500,  "<1>F p"),
    # BenchmarkCase("ATL", "cycle",   50,  "<1>G p"),
    # BenchmarkCase("ATL", "cycle",  100,  "<1>G p"),
    # ------------------------------------------------------------------
    # ATLF — ATL with Fixed-point semantics
    # ------------------------------------------------------------------
    BenchmarkCase("ATLF", "linear", 50, "<1>F p"),
    # BenchmarkCase("ATLF", "linear", 100,  "<1>F p"),
    # BenchmarkCase("ATLF", "linear", 100,  "<1>X p"),
    # BenchmarkCase("ATLF", "linear", 200,  "<1>F p"),
    # BenchmarkCase("ATLF", "linear", 200,  "<1>X p"),
    # ------------------------------------------------------------------
    # CapATL — ATL with capacity-bounded strategies
    # ------------------------------------------------------------------
    BenchmarkCase("CapATL", "linear", 50, "<{1}, 50>F p"),
    # BenchmarkCase("CapATL", "linear", 100,  "<{1}, 100>F p"),
    # BenchmarkCase("CapATL", "linear", 100,  "<{1}, 100>X p"),
    # BenchmarkCase("CapATL", "linear", 200,  "<{1}, 200>F p"),
    # BenchmarkCase("CapATL", "linear", 200,  "<{1}, 200>X p"),
    # ------------------------------------------------------------------
    # COTL — Coalitional Optimal Temporal Logic (costCGS)
    # ------------------------------------------------------------------
    # BenchmarkCase("COTL", "linear",  50,  "<1><50>F p"),
    # BenchmarkCase("COTL", "linear",  50,  "<1><50>X p"),
    # BenchmarkCase("COTL", "linear", 100,  "<1><100>F p"),
    # BenchmarkCase("COTL", "linear", 100,  "<1><100>X p"),
    # BenchmarkCase("COTL", "linear", 200,  "<1><200>F p"),
    # BenchmarkCase("COTL", "linear", 200,  "<1><200>X p"),
    # ------------------------------------------------------------------
    # CTL — Computation Tree Logic
    # ------------------------------------------------------------------
    BenchmarkCase("CTL", "linear", 50, "EF p"),
    BenchmarkCase("CTL", "linear", 50, "EX p"),
    # BenchmarkCase("CTL", "linear", 100,  "EF p"),
    # BenchmarkCase("CTL", "linear", 100,  "EG p"),
    # BenchmarkCase("CTL", "linear", 100,  "EX p"),
    # BenchmarkCase("CTL", "linear", 200,  "EF p"),
    # BenchmarkCase("CTL", "linear", 200,  "EX p"),
    # BenchmarkCase("CTL", "linear", 500,  "EF p"),
    # BenchmarkCase("CTL", "cycle",   50,  "EG p"),
    # BenchmarkCase("CTL", "cycle",  100,  "EG p"),
    # ------------------------------------------------------------------
    # LTL — Linear Temporal Logic
    # ------------------------------------------------------------------
    BenchmarkCase("LTL", "linear", 50, "F p"),
    # BenchmarkCase("LTL", "linear", 100,  "F p"),
    # BenchmarkCase("LTL", "linear", 100,  "G p"),
    # BenchmarkCase("LTL", "linear", 200,  "F p"),
    # BenchmarkCase("LTL", "linear", 500,  "F p"),
    # ------------------------------------------------------------------
    # NatATL — Natural ATL (memoryless strategies)
    # ------------------------------------------------------------------
    BenchmarkCase("NatATL", "linear", 50, "<{1}, 1>F p"),
    # BenchmarkCase("NatATL", "linear",  50,  "<{1}, 1>X p"),
    # BenchmarkCase("NatATL", "linear", 100,  "<{1}, 1>F p"),
    # BenchmarkCase("NatATL", "linear", 100,  "<{1}, 1>X p"),
    # BenchmarkCase("NatATL", "linear", 200,  "<{1}, 1>F p"),
    # BenchmarkCase("NatATL", "linear", 200,  "<{1}, 1>X p"),
    # ------------------------------------------------------------------
    # NatATL_Recall — Natural ATL with recall strategies (heavier)
    # ------------------------------------------------------------------
    BenchmarkCase("NatATL_Recall", "linear", 20, "<{1}, 1>F p"),
    # BenchmarkCase("NatATL_Recall", "linear",  50,  "<{1}, 1>F p"),
    # BenchmarkCase("NatATL_Recall", "linear",  50,  "<{1}, 1>X p"),
    # ------------------------------------------------------------------
    # NatATLF — Natural ATL with Fixed-point semantics
    # ------------------------------------------------------------------
    BenchmarkCase("NatATLF", "linear", 50, "<{1}, 1>F p"),
    # BenchmarkCase("NatATLF", "linear", 100,  "<{1}, 1>F p"),
    # BenchmarkCase("NatATLF", "linear", 100,  "<{1}, 1>X p"),
    # ------------------------------------------------------------------
    # NatSL_Alternated — Natural Strategy Logic (alternated semantics)
    # ------------------------------------------------------------------
    BenchmarkCase("NatSL_Alternated", "linear", 20, "<{1}, 1>F p"),
    # BenchmarkCase("NatSL_Alternated", "linear",  50,  "<{1}, 1>F p"),
    # BenchmarkCase("NatSL_Alternated", "linear",  50,  "<{1}, 1>X p"),
    # ------------------------------------------------------------------
    # NatSL_Sequential — Natural Strategy Logic (sequential semantics)
    # ------------------------------------------------------------------
    BenchmarkCase("NatSL_Sequential", "linear", 20, "<{1}, 1>F p"),
    # BenchmarkCase("NatSL_Sequential", "linear",  50,  "<{1}, 1>F p"),
    # BenchmarkCase("NatSL_Sequential", "linear",  50,  "<{1}, 1>X p"),
    # ------------------------------------------------------------------
    # OATL — One-sided ATL (costCGS)
    # ------------------------------------------------------------------
    BenchmarkCase("OATL", "linear", 50, "<1><50>F p"),
    # BenchmarkCase("OATL", "linear",  50,  "<1><50>X p"),
    # BenchmarkCase("OATL", "linear", 100,  "<1><100>F p"),
    # BenchmarkCase("OATL", "linear", 100,  "<1><100>X p"),
    # BenchmarkCase("OATL", "linear", 200,  "<1><200>F p"),
    # BenchmarkCase("OATL", "linear", 200,  "<1><200>X p"),
    # ------------------------------------------------------------------
    # OL — One-sided LTL (costCGS)
    # ------------------------------------------------------------------
    BenchmarkCase("OL", "linear", 50, "<J1>F p"),
    # BenchmarkCase("OL", "linear", 100,  "<J1>F p"),
    # BenchmarkCase("OL", "linear", 200,  "<J1>F p"),
    # ------------------------------------------------------------------
    # RABATL — Resource-Aware Bounded ATL (costCGS)
    # ------------------------------------------------------------------
    BenchmarkCase("RABATL", "linear", 50, "<1><50>F p"),
    # BenchmarkCase("RABATL", "linear", 100,  "<1><100>F p"),
    # BenchmarkCase("RABATL", "linear", 200,  "<1><200>F p"),
    # ------------------------------------------------------------------
    # RBATL — Resource-Bounded ATL (costCGS)
    # ------------------------------------------------------------------
    BenchmarkCase("RBATL", "linear", 50, "<1><50>F p"),
    # BenchmarkCase("RBATL", "linear", 100,  "<1><100>F p"),
    # BenchmarkCase("RBATL", "linear", 200,  "<1><200>F p"),
]


def get_benchmark_cases(logic: Optional[str] = None) -> List[BenchmarkCase]:
    """Return benchmark cases, optionally filtered by logic name.

    Args:
        logic: When given, only cases for that exact logic name are returned.
               Pass ``None`` (default) to get all cases.

    Returns:
        List of matching :class:`BenchmarkCase` instances.
    """
    if logic is None:
        return list(_BENCHMARK_CASES)
    selected = logic.strip()
    return [case for case in _BENCHMARK_CASES if case.logic == selected]


def get_supported_logics() -> Iterator[str]:
    """Return a sorted iterator of all logic names in the case registry."""
    return iter(sorted({case.logic for case in _BENCHMARK_CASES}))
