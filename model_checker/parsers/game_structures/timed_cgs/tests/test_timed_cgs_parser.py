"""Unit tests for timedCGS file parsing."""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.timed_cgs import timed_cgs_parser
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS

_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "tests"
    / "fixtures"
    / "timedCGS"
    / "tctl_tol_minimal.txt"
)


@pytest.mark.unit
class TestTimedCgsParser:
    def test_filter_drops_timed_sections_but_keeps_cost_sections(self):
        lines = [
            "Transition\n",
            "0\n",
            "Clocks\n",
            "x\n",
            "Costs_for_actions\n",
            "a s0$1\n",
            "Name_State\n",
            "s0\n",
        ]
        filtered = cgs_parser.filter_lines_for_common_sections(
            lines,
            timed_cgs_parser.TIMED_SECTION_HEADERS,
            exit_skip_on=(
                cgs_parser.SECTION_HEADERS | cgs_parser.EXTENSION_SECTION_HEADERS
            ),
        )
        stripped = [line.strip() for line in filtered]
        assert "Clocks" not in stripped
        assert "x" not in stripped
        assert "Costs_for_actions" in stripped
        assert "a s0$1" in stripped
        assert "Name_State" in stripped

    def test_read_minimal_fixture(self):
        tcgs = TimedCGS()
        tcgs.read_file(_FIXTURE)
        assert list(tcgs.states) == ["s0", "s1"]
        assert tcgs.clocks == ["x"]
        assert tcgs.clocks_dict == {"x": 0}
        assert len(tcgs.clock_constraint_struct) == 2
        assert tcgs.clock_constraint_struct[0][0] == "x<=1"
        assert tcgs.invariants_arr[0] == ["x", 2.0]
