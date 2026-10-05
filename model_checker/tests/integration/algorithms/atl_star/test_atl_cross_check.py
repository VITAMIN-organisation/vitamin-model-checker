"""Cross-checks classical ATL against ATL* on the fragment ATL can already
express: coalition only at the formula's root, with exactly one temporal
operator (X/F/G/U) inside. ATL_STAR is a different algorithm end to end
(automata-theoretic reduction to a parity game, not a coalition pre-image
fixpoint), so the two implementations agreeing across this whole fragment,
on real VITAMIN fixtures, is the actual correctness evidence for the
reduction (a single known-verdict fixture isn't enough on its own).
"""

import pytest

spot = pytest.importorskip("spot")

from model_checker.algorithms.explicit.ATL.ATL import (
    model_checking as atl_model_checking,
)
from model_checker.algorithms.explicit.ATL_STAR.ATL_STAR import (
    model_checking as atl_star_model_checking,
)
from model_checker.tests.helpers.model_helpers import extract_states_from_result

pytestmark = pytest.mark.atl_star


def _assert_same_verdict(cgs, atl_formula, atl_star_formula):
    atl_result = atl_model_checking(atl_formula, cgs.filename)
    atl_star_result = atl_star_model_checking(atl_star_formula, cgs.filename)
    assert "error" not in atl_result, atl_result
    assert "error" not in atl_star_result, atl_star_result

    atl_states = extract_states_from_result(atl_result)
    atl_star_states = extract_states_from_result(atl_star_result)
    assert atl_states == atl_star_states, (
        f"{atl_formula!r} (ATL) vs {atl_star_formula!r} (ATL*) disagree: "
        f"ATL says {atl_states}, ATL* says {atl_star_states}"
    )


@pytest.mark.integration
@pytest.mark.semantic
@pytest.mark.model_checking
class TestATLFragmentCrossCheckSmallFixture:
    """atl_2agents_4states_simple.txt: every operator in the shared
    fragment, across the grand coalition and each agent alone."""

    @pytest.mark.parametrize(
        ("atl_formula", "atl_star_formula"),
        [
            ("<1,2>X p", "<<1,2>> X p"),
            ("<1>X p", "<<1>> X p"),
            ("<2>X p", "<<2>> X p"),
            ("<1,2>F q", "<<1,2>> F q"),
            ("<1>F q", "<<1>> F q"),
            ("<2>F q", "<<2>> F q"),
            ("<1,2>G p", "<<1,2>> G p"),
            ("<1>G p", "<<1>> G p"),
            ("<2>G p", "<<2>> G p"),
            ("<1,2>p U q", "<<1,2>> (p U q)"),
            ("<1>p U q", "<<1>> (p U q)"),
            ("<2>p U q", "<<2>> (p U q)"),
        ],
    )
    def test_same_verdict(self, cgs_simple_parser, atl_formula, atl_star_formula):
        _assert_same_verdict(cgs_simple_parser, atl_formula, atl_star_formula)


@pytest.mark.integration
@pytest.mark.semantic
@pytest.mark.model_checking
class TestATLFragmentCrossCheckLargeFixture:
    """atl_tianji_game_full_2agents_49states.txt: the same fragment on a
    real, larger game, not just the small toy one."""

    @pytest.mark.parametrize(
        ("atl_formula", "atl_star_formula"),
        [
            ("<1>F kingwin", "<<1>> F kingwin"),
            ("<2>F tianjiwin", "<<2>> F tianjiwin"),
            ("<1,2>F tie", "<<1,2>> F tie"),
        ],
    )
    def test_same_verdict(self, atl_large_model, atl_formula, atl_star_formula):
        _assert_same_verdict(atl_large_model, atl_formula, atl_star_formula)
