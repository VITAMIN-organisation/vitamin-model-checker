"""NatATL Recall: boolean pruning."""

from model_checker.algorithms.explicit.NatATL.Recall.boolean_pruning import (
    boolean_pruning,
    prune_tree_nodes,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


class TestPruneTreeNodes:
    """Test prune_tree_nodes function."""

    def test_prune_matching_state(self, temp_file):
        """Verify pruning removes children when state matches and action differs."""
        content = build_cgs_model_content(
            transitions=[["0", "a", "b"], ["0", "I", "0"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        root = Node("s0", cgs)
        child1 = Node("s1", cgs, action="a")
        child2 = Node("s2", cgs, action="b")
        root.add_child(child1, action=["a"])
        root.add_child(child2, action=["b"])

        state_set = {"s0"}
        result = prune_tree_nodes(root, state_set, "a", strategy_index=1)

        assert result == 1
        assert len(root.children) == 1
        assert root.children[0].state == "s1"


class TestBooleanPruning:
    """Test boolean_pruning function."""

    def test_boolean_pruning_with_simple_condition(self, temp_file):
        """Verify boolean pruning with simple propositional condition."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["1"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        root = Node("s0", cgs)
        child1 = Node("s1", cgs, action="a")
        child2 = Node("s1", cgs, action="b")
        root.add_child(child1, action=["a"])
        root.add_child(child2, action=["b"])

        result = boolean_pruning(cgs, root, "p", "a", 1, temp_file)
        assert result == 1
