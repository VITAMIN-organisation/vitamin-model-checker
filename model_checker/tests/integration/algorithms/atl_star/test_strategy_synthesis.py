"""ATL* strategy synthesis: a replayable strategy when the formula holds, for one top-level coalition.

The two-state model: from s0 agent 1's a moves to s1 (p) and i stays, whatever
agent 2 plays; s1 loops under every action. Needs Spot.
"""

import json

import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL_STAR.ATL_STAR import (
    _core_synthesize_strategy,
    synthesize_strategy,
)
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content

pytestmark = pytest.mark.atl_star


@pytest.fixture
def two_states(temp_file):
    return load_cgs_from_content(
        temp_file,
        build_cgs_model_content(
            transitions=[["iI,iO", "aI,aO"], ["0", "*"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            prop_names=["p"],
            labelling=[["0"], ["1"]],
            num_agents=2,
        ),
    )


@pytest.mark.integration
def test_strategy_commits_agent_one_and_covers_every_reply(two_states):
    """For <<1>> X p agent 1 plays a at s0; both of agent 2's replies must be listed, all reaching s1."""
    result = _core_synthesize_strategy(two_states, "<<1>> X p", None)
    assert result["satisfied"] is True
    strategy = result["strategy"]
    json.dumps(strategy)
    assert {
        (m["agent"], m["action"]) for m in strategy["moves"] if m["state"] == "s0"
    } == {(1, "a")}
    from_s0 = [t for t in strategy["transitions"] if t["source"]["state"] == "s0"]
    assert {dict(t["joint_action"])[2] for t in from_s0} == {"IDLE", "O"}
    assert all(
        dict(t["joint_action"])[1] == "a" and t["target"]["state"] == "s1"
        for t in from_s0
    )


@pytest.mark.integration
@pytest.mark.parametrize(("state", "satisfied"), [(None, False), ("s1", True)])
def test_formula_that_fails_is_reported_not_raised(two_states, state, satisfied):
    """<<2>> X p fails at s0 (agent 2 cannot move) but holds at s1, which loops."""
    result = _core_synthesize_strategy(two_states, "<<2>> X p", state)
    assert result["satisfied"] is satisfied
    if satisfied:
        assert result["strategy"]["start"]["state"] == "s1"
        assert all(m["state"] != "s0" for m in result["strategy"]["moves"])
    else:
        assert result["strategy"] is None


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "state", "error_type", "message"),
    [
        ("<<1>> F (<<2>> G p)", None, "semantic", "nested"),
        ("(<<1>> X p) && (<<2>> X p)", None, "semantic", "single coalition"),
        ("<<1>> X p", "nosuch", "semantic", ""),
        ("<<1>> X zz", None, "semantic", ""),
        ("<<1>> X (", None, "syntax", ""),
    ],
    ids=[
        "nested_coalition",
        "boolean_of_coalitions",
        "unknown_state",
        "unknown_name",
        "syntax",
    ],
)
def test_unsupported_request_is_an_error(
    two_states, formula, state, error_type, message
):
    """Synthesis handles one coalition with no coalition inside it, at a state of the model."""
    error = _core_synthesize_strategy(two_states, formula, state)["error"]
    assert error["type"] == error_type
    assert message in error["message"]


@pytest.mark.integration
def test_entry_point_loads_the_file_and_labels_the_result(cgs_simple_parser):
    """The registered entry point returns the formula and model with the strategy."""
    result = synthesize_strategy("<<1,2>> F (p && q)", cgs_simple_parser.filename)
    assert result["satisfied"] is True
    assert (result["formula"], result["model"]) == (
        "<<1,2>> F (p && q)",
        cgs_simple_parser.filename,
    )


@pytest.mark.integration
def test_every_transition_target_has_a_move_to_continue_from(cgs_simple_parser):
    """Replay never gets stuck; s3 is reached with automaton memory 0 and 1, both covered."""
    strategy = synthesize_strategy("<<1,2>> F (p && q)", cgs_simple_parser.filename)[
        "strategy"
    ]
    positions = {(m["state"], m["memory"]) for m in strategy["moves"]}
    assert strategy["transitions"]
    assert all(
        (t["target"]["state"], t["target"]["memory"]) in positions
        for t in strategy["transitions"]
    )
    assert {memory for state, memory in positions if state == "s3"} == {0, 1}


@pytest.mark.integration
def test_explicit_state_is_where_the_strategy_starts(cgs_simple_parser):
    """From s2 the strategy starts at s2 and never visits s0, which s2 cannot reach."""
    result = synthesize_strategy(
        "<<1,2>> F (p && q)", cgs_simple_parser.filename, state="s2"
    )
    assert result["strategy"]["start"]["state"] == "s2"
    assert all(m["state"] != "s0" for m in result["strategy"]["moves"])
