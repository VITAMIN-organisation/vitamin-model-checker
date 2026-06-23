"""NatSL to NatATL conversion helpers."""

import pytest

from model_checker.parsers.formulas.NatSL.conversion import (
    convert_parsed_natsl_to_natatl_separated,
)


@pytest.mark.unit
class TestNatSLConversion:
    """Conversion from parsed NatSL AST to NatATL strings."""

    def test_not_eventually_converts_without_crash(self):
        parsed = (
            [("E", "x", 1)],
            [("x", 1)],
            ("!", "F", "goal"),
        )
        existential, universal = convert_parsed_natsl_to_natatl_separated(
            parsed, original_formula="E{1}x:(x,1)!F goal"
        )
        assert existential == ["!<{1}, 1>Fgoal"]
        assert universal == []

    def test_eventually_converts_normally(self):
        parsed = (
            [("E", "x", 1)],
            [("x", 1)],
            ("F", "p"),
        )
        existential, universal = convert_parsed_natsl_to_natatl_separated(parsed)
        assert existential == ["<{1}, 1>Fp"]
        assert universal == []

    def test_multiple_universal_quantifiers(self):
        parsed = (
            [("E", "x", 1), ("A", "y", 1), ("A", "z", 2)],
            [("x", 1), ("y", 1), ("z", 2)],
            ("F", "p"),
        )
        existential, universal = convert_parsed_natsl_to_natatl_separated(parsed)
        assert len(universal) == 2
        assert universal[0] == "<{1}, 1>Fp"
        assert universal[1] == "<{2}, 2>Fp"
