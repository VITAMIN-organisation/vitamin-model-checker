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
        """Agent 1 idling at s1 never reaches r at s2; the model writes idle as I and
        the rule as IDLE."""
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

    def test_coalition_member_two_plays_its_own_action(self, temp_file):
        """Agent 2 reaches g only by playing A at s0; that rule and the idle rule have
        size 2, so k = 1 is not enough."""
        content = build_cgs_model_content(
            transitions=[["0", "IA", "II,IB"], ["0", "II", "0"], ["0", "0", "II"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1", "0"], ["0", "1"], ["0", "0"]],
            num_agents=2,
            prop_names=["p", "g"],
        )
        path = temp_file(content)
        assert model_checking("<{2},1>F g", path)["Satisfiability"] is False
        result = model_checking("<{2},2>F g", path)
        assert result["Satisfiability"] is True
        assert result["Winning Strategy per agent"] == [
            {"condition_action_pairs": [("p", "A"), ("true*", "IDLE")]}
        ]

    def test_goal_six_steps_away_is_reached(self, temp_file):
        """Playing A after every p history moves along the chain to g at s6; the
        rule true* . p costs 1 and the idle rule 1."""
        size = 7
        transitions = [
            ["I" if j == i else "A" if j == i + 1 else "0" for j in range(size)]
            for i in range(size)
        ]
        content = build_cgs_model_content(
            transitions=transitions,
            state_names=[f"s{i}" for i in range(size)],
            initial_state="s0",
            labelling=[["1", "0"]] * (size - 1) + [["0", "1"]],
            num_agents=1,
            prop_names=["p", "g"],
        )
        result = model_checking("<{1},2>F g", temp_file(content))
        assert result["Satisfiability"] is True

    def test_pattern_rule_applies_on_every_matching_history(self, temp_file):
        """Agent 2 picks s1 or s2 (both q); p . q then G reaches g on both. q alone
        is not a valid rule for G because s4 also has q, so the size is 4."""
        content = build_cgs_model_content(
            transitions=[
                ["0", "II", "IR", "0", "0"],
                ["0", "II", "0", "GI", "0"],
                ["0", "0", "II", "GI", "0"],
                ["0", "0", "0", "II", "0"],
                ["0", "0", "0", "0", "II"],
            ],
            state_names=["s0", "s1", "s2", "s3", "s4"],
            initial_state="s0",
            labelling=[
                ["1", "0", "0"],
                ["0", "1", "0"],
                ["0", "1", "0"],
                ["0", "0", "1"],
                ["0", "1", "0"],
            ],
            num_agents=2,
            prop_names=["p", "q", "g"],
        )
        path = temp_file(content)
        assert model_checking("<{1},3>F g", path)["Satisfiability"] is False
        assert model_checking("<{1},4>F g", path)["Satisfiability"] is True

    def test_first_state_with_only_a_self_loop_is_accepted(self, temp_file):
        """s0 only loops while s1 moves on to s2: histories start in any state, so
        the model need not hang together as one tree from s0."""
        content = build_cgs_model_content(
            transitions=[["I", "0", "0"], ["0", "I", "A"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        result = model_checking("<{1},1>G !p", temp_file(content))
        assert "error" not in result, result
        assert result["Satisfiability"] is True

    @pytest.mark.parametrize(("k", "holds"), [(1, False), (3, False), (4, True)])
    def test_bound_counts_the_idle_rule_of_each_member(self, temp_file, k, holds):
        """Two members need two idle rules, so k = 1 admits no profile; reaching p
        takes (true, A) and (true, B) on top of them, size 4."""
        content = build_cgs_model_content(
            transitions=[["II,AI,IB", "AB"], ["0", "II,AI,IB,AB"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=2,
            prop_names=["p"],
        )
        result = model_checking(f"<{{1,2}},{k}>F p", temp_file(content))
        assert "error" not in result, result
        assert result["Satisfiability"] is holds
