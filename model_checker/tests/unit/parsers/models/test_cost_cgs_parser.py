"""Unit tests for costCGS cost section parsing."""

import pytest

from model_checker.parsers.game_structures.cost_cgs import cost_cgs_parser
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS


@pytest.mark.unit
class TestCostCGSCostParsing:
    def test_malformed_cost_line_too_few_fields_raises(self):
        instance = CostCGS()
        with pytest.raises(ValueError, match="Malformed cost line"):
            cost_cgs_parser.parse_cost_line("I*", instance, parse_split=False)

    def test_malformed_cost_entry_missing_cost_raises(self):
        instance = CostCGS()
        # Missing cost part after '$'
        with pytest.raises(ValueError, match="Malformed cost entry"):
            cost_cgs_parser.parse_cost_line("I* s0$", instance, parse_split=False)

    def test_invalid_numeric_cost_raises_clear_error(self):
        instance = CostCGS()
        with pytest.raises(ValueError, match="Invalid cost value"):
            cost_cgs_parser.parse_cost_line("I* s0$1:x", instance, parse_split=False)

    def test_invalid_numeric_cost_split_raises_clear_error(self):
        instance = CostCGS()
        with pytest.raises(ValueError, match="Invalid cost value"):
            cost_cgs_parser.parse_cost_line("I* s0$1:x,y", instance, parse_split=True)

    def test_get_cost_for_action_accepts_pipe_and_compact(self):
        """Pipe-normalized profiles resolve to compact cost table keys."""
        instance = CostCGS()
        instance.number_of_agents = 3
        cost_cgs_parser.parse_cost_line("AAC s0$1,1,1", instance, parse_split=True)
        cost_cgs_parser.parse_cost_line("*** s1$2:2", instance, parse_split=False)

        assert instance.get_cost_for_action("AAC", "s0") == [[1, 1, 1]]
        assert instance.get_cost_for_action("A|A|C", "s0") == [[1, 1, 1]]
        assert instance.get_cost_for_action("*|*|*", "s1") == [2, 2]
        assert instance.get_cost_for_action("***", "s1") == [2, 2]
