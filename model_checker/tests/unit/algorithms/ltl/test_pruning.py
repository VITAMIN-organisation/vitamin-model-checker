"""LTL pruning applies the first rule whose condition holds: a state follows one rule."""

import pytest

from model_checker.algorithms.explicit.LTL.pruning import (
    process_transition_matrix_data,
    pruning,
)
from model_checker.parsers.game_structures.cgs import CGS

# One agent, three states, two actions: every state can move to s0 and s2 by A and to
# s1 by B. p holds at s0 and s1, q at s1, r at s1 and s2.
_MODEL = """Transition
A B A
A B A
A B A
Unknown_Transition_by
Name_State
s0 s1 s2
Initial_State
s0
Atomic_propositions
p q r
Labelling
1 0 0
1 1 1
0 0 1
Number_of_agents
1
"""


def _load(temp_file, text=_MODEL):
    path = temp_file(text)
    cgs = CGS()
    cgs.read_file(path)
    return cgs, path


@pytest.mark.unit
def test_a_state_follows_the_first_rule_that_holds(temp_file):
    """Rules (p, A), (q, B), (r, B): s1 satisfies all three but follows rule 1."""
    cgs, path = _load(temp_file)
    strategy = {"condition_action_pairs": [("p", "A"), ("q", "B"), ("r", "B")]}

    graph = process_transition_matrix_data(cgs, path, [1], strategy)

    # s0 and s1 follow rule 1 (A only); s2 follows rule 3 (B only), since only the
    # states no earlier rule covered are left for it.
    assert graph == [["A", 0, "A"], ["A", 0, "A"], [0, "B", 0]]


@pytest.mark.unit
def test_a_rule_that_holds_nowhere_leaves_the_graph_alone(temp_file):
    """The condition `p && q && !r` holds in no state; the rule selects nothing."""
    cgs, path = _load(temp_file)
    strategy = {"condition_action_pairs": [("p && q && !r", "A")]}

    graph = process_transition_matrix_data(cgs, path, [1], strategy)

    assert graph == [["A", "B", "A"]] * 3


@pytest.mark.unit
def test_a_profile_that_leaves_a_state_without_successor_is_not_admissible(temp_file):
    """s0 has only action A on its edges; the rule (p && !q, B) holds at s0 only, so
    it cuts every edge of s0. `EF p` holds at s0 itself, so a profile with a dead end
    would pass if the dead end were ignored."""
    cgs, path = _load(temp_file, _MODEL.replace("A B A", "A A A", 1))
    strategy = {"condition_action_pairs": [("p && !q", "B")]}

    assert pruning(cgs, path, [1], "EF p", [strategy]) is False
