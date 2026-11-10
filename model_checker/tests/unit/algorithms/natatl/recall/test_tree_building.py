"""NatATL with recall unfolds the model into a tree of histories, prunes it by a strategy, and folds it back.

`height` counts levels of nodes (height 2 is the root and its children);
`max_depth` is the deepest edge level written back into the matrix.
"""

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.boolean_pruning import (
    boolean_pruning,
    prune_tree_nodes,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_building import (
    build_tree_from_CGS,
    tree_to_initial_CGS,
)
from model_checker.algorithms.explicit.NatATL.Recall.tree_structure import Node
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content

# s0 -a-> s1 -b-> s2, s2 idles
_CHAIN = [["0", "a", "0"], ["0", "0", "b"], ["0", "0", "I"]]


def _model(temp_file, transitions):
    names = [f"s{i}" for i in range(len(transitions))]
    content = build_cgs_model_content(
        transitions=transitions,
        state_names=names,
        initial_state="s0",
        labelling=[["1"]] + [["0"]] * (len(names) - 1),
        num_agents=1,
        prop_names=["p"],
    )
    return load_cgs_from_content(temp_file, content)


def _shape(node):
    """(state, actions, [children]) all the way down."""
    return (node.state, node.actions, [_shape(child) for child in node.children])


@pytest.mark.unit
@pytest.mark.parametrize(
    ("transitions", "height", "shape"),
    [
        (_CHAIN, 1, ("s0", [], [])),
        (_CHAIN, 2, ("s0", ["a"], [("s1", [], [])])),
        (_CHAIN, 3, ("s0", ["a"], [("s1", ["b"], [("s2", [], [])])])),
        (
            [["I", "a"], ["0", "I"]],
            2,
            ("s0", ["I", "a"], [("s0", [], []), ("s1", [], [])]),
        ),
    ],
    ids=["root_only", "one_level", "two_levels", "self_loop_is_a_child"],
)
def test_tree_unfolds_each_move_to_the_given_height(
    temp_file, transitions, height, shape
):
    """Each move becomes a child labelled by its action, a self-loop included."""
    cgs = _model(temp_file, transitions)
    assert _shape(build_tree_from_CGS(cgs, cgs.states, height=height)) == shape


@pytest.mark.unit
def test_nodes_remember_the_history_above_them(temp_file):
    """The leaf of s0 -> s1 -> s2 has predecessors s0 then s1."""
    cgs = _model(temp_file, _CHAIN)
    leaf = build_tree_from_CGS(cgs, cgs.states, height=3).children[0].children[0]
    assert leaf.predecessors == ["s0", "s1"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("max_depth", "matrix"),
    [
        (0, [["0", "['a']", "0"], ["0", "0", "0"], ["0", "0", "0"]]),
        (1, [["0", "['a']", "0"], ["0", "0", "['b']"], ["0", "0", "0"]]),
    ],
)
def test_folding_back_writes_edges_down_to_max_depth(temp_file, max_depth, matrix):
    """Depth 0 writes only s0 -> s1; depth 1 adds s1 -> s2."""
    cgs = _model(temp_file, _CHAIN)
    root, child, grandchild = (
        Node("s0", cgs),
        Node("s1", cgs, action="a"),
        Node("s2", cgs, action="b"),
    )
    root.add_child(child, action=["a"])
    child.add_child(grandchild, action=["b"])
    assert tree_to_initial_CGS(root, ["s0", "s1", "s2"], max_depth=max_depth) == matrix


@pytest.mark.unit
def test_folding_a_lone_root_gives_an_empty_matrix(temp_file):
    """A root with no children has no edge to write."""
    cgs = _model(temp_file, [["I"]])
    assert tree_to_initial_CGS(Node("s0", cgs), ["s0"], max_depth=1) == [["0"]]


@pytest.mark.unit
def test_pruning_keeps_only_the_strategy_action_in_matching_states(temp_file):
    """At s0 the strategy plays a, so the b branch goes and the a branch stays."""
    cgs = _model(temp_file, [["0", "a", "b"], ["0", "I", "0"], ["0", "0", "I"]])
    root = Node("s0", cgs)
    root.add_child(Node("s1", cgs, action="a"), action=["a"])
    root.add_child(Node("s2", cgs, action="b"), action=["b"])
    assert prune_tree_nodes(root, {"s0"}, "a", strategy_index=1) == 1
    assert [
        (child.state, actions)
        for child, actions in zip(root.children, root.actions, strict=True)
    ] == [("s1", ["a"])]


@pytest.mark.unit
def test_pruning_leaves_states_outside_the_condition(temp_file):
    """s0 is not in the state set, so nothing is pruned and the result is 0."""
    cgs = _model(temp_file, [["0", "a", "b"], ["0", "I", "0"], ["0", "0", "I"]])
    root = Node("s0", cgs)
    root.add_child(Node("s1", cgs, action="a"), action=["a"])
    root.add_child(Node("s2", cgs, action="b"), action=["b"])
    assert prune_tree_nodes(root, {"s1"}, "a", strategy_index=1) == 0
    assert [child.state for child in root.children] == ["s1", "s2"]


@pytest.mark.unit
def test_boolean_pruning_uses_the_states_where_the_condition_holds(temp_file):
    """p holds at s0, so the strategy's guard `p` applies there and removes the b child."""
    cgs = _model(temp_file, [["0", "a"], ["0", "I"]])
    root = Node("s0", cgs)
    root.add_child(Node("s1", cgs, action="a"), action=["a"])
    root.add_child(Node("s1", cgs, action="b"), action=["b"])
    assert boolean_pruning(cgs, root, "p", "a", 1, cgs.filename) == 1
    assert root.actions == [["a"]]
