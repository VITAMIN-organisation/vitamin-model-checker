"""ATL* semantics end-to-end: Next/Until/nested-coalition operators that
classical ATL cannot express, plus a real ATL fixture reused unchanged
(ATL* runs over plain CGS, no new game-structure type is needed)."""

# ruff: noqa: E402  -- imports deliberately follow importorskip("spot") below,
# to skip this whole file cleanly if Spot isn't installed
import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL_STAR.ATL_STAR import (
    _core_atl_star_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    extract_states_from_result,
    load_cgs_from_content,
)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestATLStarCoalitionSemantics:
    """Operators unique to ATL* (Next/Until under a coalition, nested coalitions)."""

    def test_single_agent_can_force_next(self, temp_file):
        """<<1>> X p: true at s0 (agent 1 alone forces it, agent 2's choice
        never matters) and trivially at s1 too (an absolute self-loop
        under any action, so any coalition "forces" staying there)."""
        content = build_cgs_model_content(
            transitions=[["iI,iO", "aI,aO"], ["0", "*"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=2,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_atl_star_checking(cgs, "<<1>> X p")
        assert extract_states_from_result(result) == {"s0", "s1"}

    def test_second_agent_alone_cannot_force_the_same_next(self, temp_file):
        """Dual of the above: agent 2 has no influence on reaching s1, so
        only s1's trivial self-loop case survives, not s0."""
        content = build_cgs_model_content(
            transitions=[["iI,iO", "aI,aO"], ["0", "*"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=2,
            prop_names=["p"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_atl_star_checking(cgs, "<<2>> X p")
        assert extract_states_from_result(result) == {"s1"}

    def test_until_forces_a_genuine_two_step_progression(self, temp_file):
        """<<1>> (mid U goal): mid holds on the way, goal only at the end.
        Also holds at s2 itself, since Until is satisfied wherever its
        right-hand side already holds, regardless of the left-hand side."""
        content = build_cgs_model_content(
            transitions=[["0", "a", "0"], ["0", "0", "b"], ["0", "0", "I"]],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1", "0"], ["1", "0"], ["0", "1"]],
            num_agents=1,
            prop_names=["mid", "goal"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_atl_star_checking(cgs, "<<1>> (mid U goal)")
        assert extract_states_from_result(result) == {"s0", "s1", "s2"}

    def test_nested_coalition_inside_a_path_formula(self, temp_file):
        """<<1>> F (<<2>> G goal): the ATL* feature classical ATL cannot
        express at all, since a coalition operator there is always the
        formula's own root, never nested inside another's path formula."""
        content = build_cgs_model_content(
            transitions=[["iI,iO", "aI,aO"], ["0", "*"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=2,
            prop_names=["goal"],
        )
        cgs = load_cgs_from_content(temp_file, content)

        result = _core_atl_star_checking(cgs, "<<1>> F (<<2>> G goal)")
        assert extract_states_from_result(result) == {"s0", "s1"}


@pytest.mark.semantic
@pytest.mark.model_checking
class TestATLStarOnRealFixture:
    """Reuses ATL's own real fixture unchanged (plain CGS, no ATL*-specific model)."""

    def test_grand_coalition_matches_the_known_verdict(self, cgs_simple_parser):
        """<<1,2>> F (p & q) on atl_2agents_4states_simple.txt: True."""
        result = _core_atl_star_checking(cgs_simple_parser, "<<1,2>> F (p & q)")
        states = extract_states_from_result(result)
        assert cgs_simple_parser.initial_state in states

    def test_first_agent_alone_matches_the_known_verdict(self, cgs_simple_parser):
        """<<1>> F (p & q) on the same fixture: also True — that fixture's
        rows never actually offer agent 2 a way to steer away from it."""
        result = _core_atl_star_checking(cgs_simple_parser, "<<1>> F (p & q)")
        states = extract_states_from_result(result)
        assert cgs_simple_parser.initial_state in states


@pytest.mark.integration
@pytest.mark.model_checking
class TestATLStarErrorHandling:
    """Mirrors ATL's own error-handling test shape."""

    def test_invalid_formula_syntax(self, cgs_simple_parser):
        result = _core_atl_star_checking(cgs_simple_parser, "<<1,2> F p")
        assert "error" in result
        assert result["error"]["type"] == "syntax"

    def test_coalition_agent_id_out_of_range(self, cgs_simple_parser):
        """Agent 5 doesn't exist on a 2-agent model; caught at parse time,
        same "syntax" category ATL uses for its own coalition validation."""
        result = _core_atl_star_checking(cgs_simple_parser, "<<5>> F p")
        assert "error" in result
        assert result["error"]["type"] == "syntax"
