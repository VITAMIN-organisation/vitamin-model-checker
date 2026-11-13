"""NatATL Recall: scenarios with pinned Satisfiability (sat and unsat)."""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.natatl_recall import (
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.integration
@pytest.mark.semantic
class TestNatATLRecallCritical:
    """Pinned Satisfiability cases for NatATL Recall."""

    def test_linear_chain_bound_one_cannot_reach_distant_goal(self, temp_file):
        """On a 4-state chain, bound-1 natural strategies cannot force F goal at s3.

        Memoryless and recall both return False for <{1},1> F goal on this model;
        this pins the unsat oracle rather than claiming a recall-only win.
        """
        content = build_cgs_model_content(
            transitions=[
                ["I", "a", "0", "0"],
                ["0", "I", "a", "0"],
                ["0", "0", "I", "a"],
                ["0", "0", "0", "I"],
            ],
            state_names=["s0", "s1", "s2", "s3"],
            initial_state="s0",
            labelling=[["1", "0"], ["1", "0"], ["1", "0"], ["0", "1"]],
            num_agents=1,
            prop_names=["processing", "goal"],
        )
        parser = load_cgs_from_content(temp_file, content)

        result = model_checking("<{1}, 1> F goal", parser.filename)

        assert "error" not in result, result
        assert result.get("Satisfiability") is False
        assert result.get("Complexity Bound") == 1

    def test_recall_unsatisfiable_formula_returns_false(self, temp_file):
        """When goal is only at a state that is unreachable from s0, Satisfiability is False."""
        content = build_cgs_model_content(
            transitions=[
                ["0", "I", "0"],
                ["0", "I", "0"],
                ["0", "0", "I"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0", "0"], ["0", "0"], ["0", "1"]],
            num_agents=1,
            prop_names=["processing", "goal"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        result = model_checking("<{1}, 1>F goal", cgs.filename)
        assert "error" not in result
        assert "Satisfiability" in result
        assert result["Satisfiability"] is False

    def test_idle_rule_is_valid_and_keeps_away_from_r(self, temp_file):
        """Agent 1 idling at s1 never reaches r at s2; the model writes idle as I, the rule
        as IDLE, and the tree's cut-off leaves have no moves to check."""
        content = build_cgs_model_content(
            transitions=[["0", "II", "0"], ["0", "II", "bI"], ["0", "0", "II"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
            num_agents=2,
            prop_names=["p", "q", "r"],
        )
        result = model_checking("<{1},1>G !r", temp_file(content))
        assert result["Satisfiability"] is True
