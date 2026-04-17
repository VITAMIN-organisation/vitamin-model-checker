"""NatATL Recall: tree building."""

from model_checker.algorithms.explicit.NatATL.Recall.tree_building import (
    build_tree_from_CGS,
    tree_to_initial_CGS,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


class TestBuildTreeFromCGS:
    """Test build_tree_from_CGS function."""

    def test_build_single_level_tree(self, temp_file):
        """Verify tree building for single level (height=2)."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["1"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        states = cgs.get_states()

        tree = build_tree_from_CGS(cgs, states, height=2)

        assert tree.state == "s0"
        assert len(tree.children) >= 1
        assert any(child.state == "s1" for child in tree.children)

    def test_build_two_level_tree(self, temp_file):
        """Verify tree building for two levels (height=3)."""
        content = build_cgs_model_content(
            transitions=[["0", "a", "0"], ["0", "0", "b"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        states = cgs.get_states()

        tree = build_tree_from_CGS(cgs, states, height=3)

        assert tree.state == "s0"
        assert len(tree.children) >= 1
        s1_child = next((c for c in tree.children if c.state == "s1"), None)
        assert s1_child is not None
        assert len(s1_child.children) >= 1

    def test_build_branching_tree(self, temp_file):
        """Verify tree building with branching transitions."""
        content = build_cgs_model_content(
            transitions=[["0", "a", "b"], ["0", "I", "0"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        states = cgs.get_states()

        tree = build_tree_from_CGS(cgs, states, height=2)

        assert tree.state == "s0"
        assert len(tree.children) >= 1
        child_states = {child.state for child in tree.children}
        assert "s1" in child_states or "s2" in child_states

    def test_build_tree_respects_height_limit(self, temp_file):
        """Verify tree stops building at specified height."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "b"], ["0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        states = cgs.get_states()

        tree = build_tree_from_CGS(cgs, states, height=2)

        assert tree.state == "s0"
        assert len(tree.children) >= 1
        for child in tree.children:
            assert len(child.children) == 0

    def test_build_tree_with_self_loop(self, temp_file):
        """Verify tree building with self-loop transitions."""
        content = build_cgs_model_content(
            transitions=[["I", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["1"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        states = cgs.get_states()

        tree = build_tree_from_CGS(cgs, states, height=2)

        assert tree.state == "s0"
        assert len(tree.children) >= 1

    def test_build_tree_tracks_predecessors(self, temp_file):
        """Verify tree nodes track predecessor states correctly."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "b"], ["0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)
        states = cgs.get_states()

        tree = build_tree_from_CGS(cgs, states, height=2)

        for child in tree.children:
            assert "s0" in child.predecessors


class TestTreeToInitialCGS:
    """Test tree_to_initial_CGS function."""

    def test_convert_simple_tree_to_matrix(self, temp_file):
        """Verify tree to matrix conversion for simple tree."""
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
        child = Node("s1", cgs, action="a")
        root.add_child(child, action=["a"])

        states = ["s0", "s1"]
        matrix = tree_to_initial_CGS(root, states, num_agents=1, max_depth=2)

        assert len(matrix) == 2
        assert len(matrix[0]) == 2
        assert matrix[0][1] == "['a']"
        assert matrix[0][0] == "0"

    def test_convert_branching_tree_to_matrix(self, temp_file):
        """Verify tree to matrix conversion for branching tree."""
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

        states = ["s0", "s1", "s2"]
        matrix = tree_to_initial_CGS(root, states, num_agents=1, max_depth=2)

        assert len(matrix) == 3
        assert matrix[0][1] == "['a']"
        assert matrix[0][2] == "['b']"

    def test_convert_respects_max_depth(self, temp_file):
        """Verify conversion respects max_depth parameter."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "b"], ["0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["0"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        root = Node("s0", cgs)
        child = Node("s1", cgs, action="a")
        grandchild = Node("s2", cgs, action="b")
        root.add_child(child, action=["a"])
        child.add_child(grandchild, action=["b"])

        states = ["s0", "s1", "s2"]
        matrix = tree_to_initial_CGS(root, states, num_agents=1, max_depth=1)

        assert len(matrix) == 3
        assert matrix[0][1] == "['a']"

    def test_convert_empty_tree(self, temp_file):
        """Verify conversion handles tree with no children."""
        content = build_cgs_model_content(
            transitions=[["I"]],
            state_names=["s0"],
            initial_state="s0",
            labelling=[["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        root = Node("s0", cgs)
        states = ["s0"]
        matrix = tree_to_initial_CGS(root, states, num_agents=1, max_depth=1)

        assert len(matrix) == 1
        assert matrix[0][0] == "0"
