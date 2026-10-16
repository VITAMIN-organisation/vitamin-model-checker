"""NatATL Recall model checking: correctness and error handling."""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.natatl_recall import (
    model_checking,
)
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    parse_joint_action_cell,
)


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLRecallErrorHandling:
    """Error handling for invalid inputs."""

    def test_recall_invalid_formula_syntax(self, natatl_standard_model):
        """Invalid formula syntax yields an error."""
        result = model_checking("INVALID_SYNTAX", natatl_standard_model.filename)
        assert "error" in result

    def test_recall_empty_formula(self, natatl_standard_model):
        """Empty formula yields an error."""
        result = model_checking("", natatl_standard_model.filename)
        assert "error" in result


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLRecallCorrectness:
    """Test NatATL Recall model checking."""

    @pytest.mark.parametrize(
        "formula,expected_satisfiability,check_strategy",
        [("<{1},1>Fa", True, True)],
    )
    def test_recall_model_checking(
        self, test_data_dir, formula, expected_satisfiability, check_strategy
    ):
        """Test Recall model checking with various formulas."""
        # The original natatl_standard_model is intentionally kept unchanged:
        # it encodes nondeterministic joint actions and is shared with NatSL.
        filename = test_data_dir / (
            "CGS/NATATL/natatl_recall_2agents_nominal_deterministic.txt"
        )
        model = CGS()
        model.read_file(str(filename))
        assert model.initial_state == "s0"
        assert model.matrix_prop[0][0] == 0  # F a is not trivially true.
        assert parse_joint_action_cell(model.graph[0][1], 2) == [["IDLE", "IDLE"]]
        assert parse_joint_action_cell(model.graph[0][2], 2) == [
            ["IDLE", "BLOCK_PATH"]
        ]

        result = model_checking(formula, str(filename))

        if expected_satisfiability is None:
            assert "error" in result
        else:
            assert "Satisfiability" in result
            assert isinstance(result["Satisfiability"], bool)
            assert result["Satisfiability"] == expected_satisfiability
            if check_strategy:
                assert "Winning Strategy per agent" in result


@pytest.mark.integration
@pytest.mark.semantic
def test_recall_nominal_actions_have_real_temporal_semantics(test_data_dir):
    """The opponent chooses left/right, but constant IDLE forces eventual a."""
    filename = test_data_dir / (
        "CGS/NATATL/natatl_recall_2agents_nominal_deterministic.txt"
    )
    model = CGS()
    model.read_file(str(filename))

    from model_checker.algorithms.explicit.NatATL.Recall.recall_cgs_semantics import (
        validate_recall_cgs_semantics,
    )

    transitions = validate_recall_cgs_semantics(model)
    assert transitions["s0"][("IDLE", "IDLE")] == "left"
    assert transitions["s0"][("IDLE", "BLOCK_PATH")] == "right"
    assert transitions["s0"][("MOVE_FORWARD", "BLOCK_PATH")] == "trap"
    assert all(len(choices) == 4 for choices in transitions.values())

    result = model_checking("<{1},1> F a", str(filename))
    assert result["Satisfiability"] is True, result
    assert result["Winning Strategy per agent"] == [
        {"condition_action_pairs": [("T*", "IDLE")]}
    ], result
    # It takes TWO transitions to force a; X a cannot hold at s0.
    next_result = model_checking("<{1},1> X a", str(filename))
    assert next_result["Satisfiability"] is False, next_result
    assert next_result["Status"] == "VERIFIED_FALSE", next_result


@pytest.mark.integration
def test_recall_preflight_accepts_unseparated_nominal_single_agent_action():
    """The Recall validator must agree with the shared CGS action parser."""
    from model_checker.algorithms.explicit.NatATL.Recall.recall_cgs_semantics import (
        validate_recall_cgs_semantics,
    )

    class SingleAgentCGS:
        states = ["s0", "goal"]
        initial_state = "s0"
        atomic_propositions = ["a"]
        matrix_prop = [[0], [1]]
        graph = [["IDLE", "MOVE_FORWARD"], [0, "IDLE,MOVE_FORWARD"]]

        def get_number_of_agents(self):
            return 1

    transitions = validate_recall_cgs_semantics(SingleAgentCGS())
    assert transitions["s0"][("MOVE_FORWARD",)] == "goal"
    assert transitions["s0"][("IDLE",)] == "s0"
