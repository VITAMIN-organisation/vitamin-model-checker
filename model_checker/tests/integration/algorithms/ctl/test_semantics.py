"""CTL semantics: expected state sets from temporal definitions vs implementation output."""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import (
    _core_ctl_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestCTLSemanticVerificationSimpleModel:
    """Semantic verification tests using cgs_simple.txt model.

    Model structure:
        States: s0, s1, s2, s3
        Transitions:
            s0 -> s1 (AC,AD)
            s0 -> s2 (BC,BD)
            s1 -> s2 (AD,BD)
            s1 -> s3 (AC,BC)
            s2 -> s3 (AD,BC)
            s3 -> s3 (*)
        Labelling:
            s0: p=1, q=0
            s1: p=0, q=1
            s2: p=0, q=0
            s3: p=1, q=1
    """

    @pytest.mark.parametrize(
        "formula,expected,reason",
        [
            ("EF p", {"s0", "s1", "s2", "s3"}, "Eventually p on some path"),
            ("EG p", {"s3"}, "Globally p on some path"),
        ],
    )
    def test_simple_model_semantics(self, cgs_simple_parser, formula, expected, reason):
        """Table-driven semantic checks on cgs_simple.txt."""
        result = _core_ctl_checking(cgs_simple_parser, formula)

        states = extract_states_from_result(result)
        assert states is not None, "Failed to extract states from result"
        assert (
            states == expected
        ), f"{formula} expected {expected} ({reason}) but got {states}"


@pytest.mark.semantic
@pytest.mark.model_checking
class TestCTLSemanticVerificationCustomModels:
    """Semantic verification tests using custom models designed for specific scenarios."""

    @pytest.mark.parametrize(
        "formula,transitions,state_names,labelling,expected,reason",
        [
            (
                "AF p",
                [
                    ["0", "AC", "BC", "0"],
                    ["0", "0", "0", "AC"],
                    ["0", "0", "0", "BC"],
                    ["0", "0", "0", "*"],
                ],
                ["s0", "s1", "s2", "s3"],
                [["0"], ["0"], ["0"], ["1"]],
                {"s0", "s1", "s2", "s3"},
                "All paths converge to target",
            ),
        ],
    )
    def test_custom_models_semantics(
        self, temp_file, formula, transitions, state_names, labelling, expected, reason
    ):
        """Table-driven semantic checks on purpose-built custom models."""
        content = build_cgs_model_content(
            transitions=transitions,
            state_names=state_names,
            initial_state=state_names[0],
            labelling=labelling,
        )
        parser = load_cgs_from_content(temp_file, content)
        result = _core_ctl_checking(parser, formula)

        states = extract_states_from_result(result)
        assert states is not None, "Failed to extract states from result"
        assert (
            states == expected
        ), f"{formula} expected {expected} ({reason}) but got {states}"

    @pytest.mark.parametrize(
        "formula,expected,reason",
        [("EF (p and q)", {"s0", "s1", "s2", "s3"}, "Eventually p and q on some path")],
    )
    def test_complex_nested_formulas(
        self, cgs_simple_parser, formula, expected, reason
    ):
        """Table-driven checks for complex nested CTL formulas on cgs_simple.txt."""
        result = _core_ctl_checking(cgs_simple_parser, formula)

        states = extract_states_from_result(result)
        assert states is not None, "Failed to extract states from result"
        assert (
            states == expected
        ), f"{formula} expected {expected} ({reason}) but got {states}"
