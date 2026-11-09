"""`synthesize_strategy`: the separate, follow-up-scoped entry point for ATL*
strategy synthesis, kept out of `model_checking` so that one stays focused on
plain model checking. Only supports a formula whose outermost operator is a
single coalition with no further coalition nested inside its path formula."""

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


def _two_state_model(temp_file):
    """Same model `test_semantics.py` uses for `<<...>> X p`: agent 1 alone
    forces reaching s1 from s0, agent 2 has no influence; s1 is an absolute
    self-loop under any action."""
    content = build_cgs_model_content(
        transitions=[["iI,iO", "aI,aO"], ["0", "*"]],
        state_names=["s0", "s1"],
        initial_state="s0",
        labelling=[["0"], ["1"]],
        num_agents=2,
        prop_names=["p"],
    )
    return load_cgs_from_content(temp_file, content)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestSynthesizeStrategyCore:
    """`_core_synthesize_strategy` directly."""

    def test_synthesizes_a_strategy_when_the_formula_holds(self, temp_file):
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<1>> X p", None)
        assert "error" not in result
        assert result["satisfied"] is True
        assert result["strategy"]
        json.dumps(result["strategy"])  # must not raise
        moves = result["strategy"]["moves"]
        assert all(row["agent"] == 1 for row in moves)
        assert {(r["agent"], r["action"]) for r in moves if r["state"] == "s0"} == {
            (1, "a")
        }

        transitions = result["strategy"]["transitions"]
        s0_transitions = [t for t in transitions if t["source"]["state"] == "s0"]
        assert s0_transitions, "expected at least one recorded transition out of s0"
        for row in s0_transitions:
            joint = dict(row["joint_action"])
            assert (
                joint[1] == "a"
            )  # agent 1's committed move, present in every full joint action
            assert row["target"]["state"] == "s1"  # the only way <<1>> X p can be won
        # agent 2 isn't in the coalition, so every real response of theirs must be covered
        assert {dict(row["joint_action"])[2] for row in s0_transitions} == {"IDLE", "O"}

    def test_reports_the_formula_does_not_hold_without_erroring(self, temp_file):
        """<<2>> X p doesn't hold at s0 (only agent 1 controls reaching s1) --
        a clean "doesn't hold" report, not an error."""
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<2>> X p", None)
        assert "error" not in result
        assert result["satisfied"] is False
        assert result["strategy"] is None

    def test_respects_an_explicit_state_argument(self, temp_file):
        """<<2>> X p does hold at s1 (an absolute self-loop under any action)."""
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<2>> X p", "s1")
        assert result["satisfied"] is True
        assert result["strategy"]["start"]["state"] == "s1"
        assert all(row["state"] != "s0" for row in result["strategy"]["moves"])

    def test_rejects_a_nested_coalition(self, temp_file):
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<1>> F (<<2>> G p)", None)
        assert "error" in result
        assert result["error"]["type"] == "semantic"
        assert "nested" in result["error"]["message"]

    def test_rejects_a_top_level_boolean_combination(self, temp_file):
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "(<<1>> X p) & (<<2>> X p)", None)
        assert "error" in result
        assert result["error"]["type"] == "semantic"
        assert "single coalition" in result["error"]["message"]

    def test_rejects_an_unknown_state(self, temp_file):
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<1>> X p", "nosuch")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_rejects_an_unknown_proposition(self, temp_file):
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<1>> X zz", None)
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_rejects_a_syntax_error(self, temp_file):
        cgs = _two_state_model(temp_file)
        result = _core_synthesize_strategy(cgs, "<<1>> X (", None)
        assert "error" in result
        assert result["error"]["type"] == "syntax"


@pytest.mark.integration
@pytest.mark.model_checking
class TestSynthesizeStrategyRealEntryPoint:
    """Exercises the real, registered `synthesize_strategy(formula, filename,
    state=None)` entry point end to end (file loading included), mirroring
    `test_semantics.py`'s `TestATLStarRealEntryPoint` for `model_checking`."""

    def test_valid_formula_through_the_real_entry_point(self, cgs_simple_parser):
        result = synthesize_strategy("<<1,2>> F (p & q)", cgs_simple_parser.filename)
        assert "error" not in result
        assert result["satisfied"] is True
        json.dumps(result["strategy"])
        assert result["formula"] == "<<1,2>> F (p & q)"
        assert result["model"] == cgs_simple_parser.filename

    def test_transitions_support_continued_replay(self, cgs_simple_parser):
        """An empty `transitions` list would otherwise pass every other
        assertion here. Checks every transition's target has its own move
        entry to continue replay from -- including s3, which this fixture's
        automaton reaches at two different memory values depending on how
        it got there, a real same-CGS-state-different-memory case."""
        result = synthesize_strategy("<<1,2>> F (p & q)", cgs_simple_parser.filename)
        strategy = result["strategy"]
        positions = {(m["state"], m["memory"]) for m in strategy["moves"]}
        assert strategy["transitions"]
        for row in strategy["transitions"]:
            target = (row["target"]["state"], row["target"]["memory"])
            assert target in positions, (
                f"no move recorded to continue replay from {target}"
            )
        assert {memory for state, memory in positions if state == "s3"} == {0, 1}

    def test_an_explicit_state_is_threaded_through(self, cgs_simple_parser):
        """<<1,2>> F (p & q) also holds at s0, so only checking `satisfied`
        wouldn't catch `state` being silently ignored -- the witness's own
        `start` (and the states it reaches) must reflect s2, not s0."""
        result = synthesize_strategy(
            "<<1,2>> F (p & q)", cgs_simple_parser.filename, state="s2"
        )
        assert "error" not in result
        assert result["satisfied"] is True
        assert result["strategy"]["start"]["state"] == "s2"
        assert all(row["state"] != "s0" for row in result["strategy"]["moves"])

    def test_nested_coalition_through_the_real_entry_point(self, cgs_simple_parser):
        result = synthesize_strategy("<<1>> F (<<2>> G p)", cgs_simple_parser.filename)
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_top_level_combination_through_the_real_entry_point(
        self, cgs_simple_parser
    ):
        result = synthesize_strategy(
            "(<<1>> F p) & (<<2>> F q)", cgs_simple_parser.filename
        )
        assert "error" in result
        assert result["error"]["type"] == "semantic"
