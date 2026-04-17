"""Unit tests for costCGS cost section parsing."""

import pytest

from model_checker.parsers.game_structures.cost_cgs import cost_cgs_parser
from model_checker.parsers.game_structures.cost_cgs.cost_cgs import costCGS


@pytest.mark.unit
class TestCostCGSCostParsing:
    def test_malformed_cost_line_too_few_fields_raises(self):
        instance = costCGS()
        with pytest.raises(ValueError, match="Malformed cost line"):
            cost_cgs_parser.parse_costs_for_actions("I*", instance)

    def test_malformed_cost_entry_missing_cost_raises(self):
        instance = costCGS()
        # Missing cost part after '$'
        with pytest.raises(ValueError, match="Malformed cost entry"):
            cost_cgs_parser.parse_costs_for_actions("I* s0$", instance)

    def test_invalid_numeric_cost_raises_clear_error(self):
        instance = costCGS()
        with pytest.raises(ValueError, match="Invalid cost value"):
            cost_cgs_parser.parse_costs_for_actions("I* s0$1:x", instance)

    def test_invalid_numeric_cost_split_raises_clear_error(self):
        instance = costCGS()
        with pytest.raises(ValueError, match="Invalid cost value"):
            cost_cgs_parser.parse_costs_for_actions_split("I* s0$1:x,y", instance)
