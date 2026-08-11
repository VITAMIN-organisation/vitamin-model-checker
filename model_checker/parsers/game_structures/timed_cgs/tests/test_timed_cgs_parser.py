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

    def test_malformed_clock_constraint_raises(self):
        instance = type("T", (), {})()
        instance.clock_constraint_struct = [[""]]
        with pytest.raises(ValueError, match="Malformed clock constraint"):
            timed_cgs_parser._parse_clock_constraints_row(instance, "x>3y", 0)

    def test_malformed_invariant_raises(self):
        instance = type("T", (), {})()
        instance.invariants_arr = [[]]
        with pytest.raises(ValueError, match="Malformed invariant"):
            timed_cgs_parser._parse_invariants_row(instance, "x>=5", 0)

    def test_no_constraint_tokens_are_skipped(self):
        instance = type("T", (), {})()
        instance.clock_constraint_struct = [["", ""]]
        timed_cgs_parser._parse_clock_constraints_row(instance, "0 *", 0)
        assert instance.clock_constraint_struct[0] == ["", ""]
