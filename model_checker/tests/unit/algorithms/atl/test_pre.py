"""ATL pre-image: the states where a coalition has one move that reaches the target whatever the others do.

Cells list joint actions as agent 1's letter then agent 2's, so `AC` is agent 1
playing A while agent 2 plays C.
"""

import pytest

from model_checker.algorithms.explicit.ATL.preimage import build_transition_cache, pre
from model_checker.algorithms.explicit.shared.bit_vector import BIT_VECTOR_THRESHOLD
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


def _two_agent_model(temp_file, to_s1: str, to_s2: str):
    """From s0, the joint actions `to_s1` reach s1 and `to_s2` reach s2; s1 and s2 loop."""
    content = build_cgs_model_content(
        transitions=[["0", to_s1, to_s2], ["0", "**", "0"], ["0", "0", "**"]],
        state_names=["s0", "s1", "s2"],
        initial_state="s0",
        prop_names=["p"],
        labelling=[["0"], ["1"], ["0"]],
        num_agents=2,
    )
    return load_cgs_from_content(temp_file, content)


@pytest.mark.unit
def test_single_agent_forces_its_only_successor(temp_file):
    """s0 moves only to s1 and s1 loops, so both are in pre({s1})."""
    content = build_cgs_model_content(
        transitions=[["0", "a"], ["0", "I"]],
        state_names=["s0", "s1"],
        initial_state="s0",
        prop_names=["p"],
        labelling=[["0"], ["1"]],
        num_agents=1,
    )
    assert pre(load_cgs_from_content(temp_file, content), "1", {"s1"}) == {"s0", "s1"}


@pytest.mark.unit
def test_move_that_works_against_every_reply_forces_the_target(temp_file):
    """Agent 1's B reaches s1 against C and D, so s0 is in pre_1({s1}) although A can fail."""
    cgs = _two_agent_model(temp_file, to_s1="AC,BC,BD", to_s2="AD")
    assert pre(cgs, "1", {"s1"}) == {"s0", "s1"}


@pytest.mark.unit
def test_opponent_who_can_always_escape_blocks_the_coalition(temp_file):
    """A fails against D and B fails against C, so agent 1 cannot force s1 from s0."""
    cgs = _two_agent_model(temp_file, to_s1="AC,BD", to_s2="AD,BC")
    assert pre(cgs, "1", {"s1"}) == {"s1"}


@pytest.mark.unit
@pytest.mark.parametrize("coalition", ["1", "1,2"])
def test_joint_action_with_two_outcomes_forces_only_if_both_are_targets(
    temp_file, coalition
):
    """AC leads to s1 or s2 nondeterministically, so it does not force s1, even for both agents."""
    cgs = _two_agent_model(temp_file, to_s1="AC", to_s2="AC")
    assert pre(cgs, coalition, {"s1"}) == {"s1"}
    assert pre(cgs, coalition, {"s1", "s2"}) == {"s0", "s1", "s2"}


@pytest.mark.unit
def test_grand_coalition_needs_only_one_joint_action(temp_file):
    """With both agents in the coalition there is no opponent, so AC alone suffices."""
    cgs = _two_agent_model(temp_file, to_s1="AC,BD", to_s2="AD,BC")
    assert pre(cgs, "1,2", {"s1"}) == {"s0", "s1"}


@pytest.mark.unit
@pytest.mark.parametrize(("to_s1", "to_s2"), [("AC,BC,BD", "AD"), ("AC,BD", "AD,BC")])
@pytest.mark.parametrize("coalition", ["1", "2", "1,2"])
def test_every_cache_gives_the_same_pre_image(temp_file, to_s1, to_s2, coalition):
    """No cache, the per-state move cache, and the cache grouped by the coalition agree."""
    cgs = _two_agent_model(temp_file, to_s1=to_s1, to_s2=to_s2)
    plain = pre(cgs, coalition, {"s1"})
    assert pre(cgs, coalition, {"s1"}, build_transition_cache(cgs)) == plain
    grouped = build_transition_cache(cgs, coalition=coalition)
    assert pre(cgs, coalition, {"s1"}, grouped) == plain


@pytest.mark.unit
def test_large_model_takes_the_bit_vector_path_with_the_same_answer(temp_file):
    """On a ring of 301 states, pre of the even states is exactly the odd states before them."""
    n = BIT_VECTOR_THRESHOLD + 1
    transitions = [
        ["a" if j == (i + 1) % n else "0" for j in range(n)] for i in range(n)
    ]
    content = build_cgs_model_content(
        transitions=transitions,
        state_names=[f"s{i}" for i in range(n)],
        initial_state="s0",
        prop_names=["p"],
        labelling=[["0"]] * n,
        num_agents=1,
    )
    cgs = load_cgs_from_content(temp_file, content)
    evens = {f"s{i}" for i in range(0, n, 2)}
    # s300 steps to s0, which is even, so it joins the odd predecessors.
    expected = {f"s{(i - 1) % n}" for i in range(0, n, 2)}
    assert pre(cgs, "1", evens) == expected
