"""CTL on small models, every expected set worked out by hand.

The main model is atl_2agents_4states_simple.txt, read as a Kripke structure:
s0 -> s1, s2;  s1 -> s2, s3;  s2 -> s3;  s3 -> s3.  p holds at s0 and s3,
q at s1 and s3, so s2 is the only state with neither.
"""

import pytest

from model_checker.algorithms.explicit.CTL.CTL import model_checking
from model_checker.tests.helpers.model_helpers import extract_states_from_result
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content

_ALL = {"s0", "s1", "s2", "s3"}


def _states(formula, path):
    result = model_checking(formula, path)
    assert "error" not in result, result
    return extract_states_from_result(result)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        # next
        ("EX p", {"s1", "s2", "s3"}),  # s0's successors s1, s2 both lack p
        ("AX p", {"s2", "s3"}),  # s1 can step to s2, where p is false
        ("EX q", _ALL),  # every state has a successor in {s1, s3}
        ("AX q", {"s2", "s3"}),  # s0 and s1 can step to s2
        ("!EX p", {"s0"}),
        # eventually and globally
        # only s0 has p without q, and nothing leads back to it
        ("EF (p && !q)", {"s0"}),
        # s2 is reachable from s0 and s1, not from s3
        ("EF (!p && !q)", {"s0", "s1", "s2"}),
        ("AF q", _ALL),  # both branches from s0 pass s1 or reach s3
        ("AF (!p && !q)", {"s2"}),  # s0 and s1 can go round s2 to s3
        ("EG p", {"s3"}),  # s0 must leave p at once; s3 loops on p
        ("EG !p", set()),  # every path reaches s3, where p holds
        ("AG (p || q)", {"s3"}),  # every other state can reach s2
        # until
        ("E[p U q]", {"s0", "s1", "s3"}),  # s0 (p) steps to s1 (q); s2 has neither
        ("A[p U q]", {"s1", "s3"}),  # from s0 the path to s2 breaks p U q
        ("E[!q U p]", {"s0", "s2", "s3"}),  # s2 (!q) steps to s3 (p); s1 has q and no p
        # p already holds at s0: the until is met at once
        ("E[q U p]", {"s0", "s1", "s3"}),
        # nesting
        ("AG (EX p)", {"s1", "s2", "s3"}),  # s0 itself fails EX p
        ("EF (AG (EX p))", _ALL),
    ],
)
def test_formula_on_the_four_state_model(cgs_simple_parser, formula, expected):
    """Each set follows from the edges and labels in the module docstring."""
    assert _states(formula, cgs_simple_parser.filename) == expected


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("EG p", {"s0"}),  # s0 can loop on itself forever
        ("AG p", set()),  # s0 can also leave to s1
        ("AF !p", {"s1"}),  # s0 may loop forever and never reach !p
        ("EF !p", {"s0", "s1"}),
    ],
)
def test_self_loop_with_an_exit(temp_file, formula, expected):
    """s0 loops or moves to s1, which loops; p holds only at s0."""
    path = temp_file(
        build_cgs_model_content(
            transitions=[["I", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            prop_names=["p"],
            labelling=[["1"], ["0"]],
            num_agents=1,
        )
    )
    assert _states(formula, path) == expected


@pytest.mark.integration
@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("EX p", {"s58"}),
        ("EF p", {f"s{i}" for i in range(60)}),
        ("AF p", {f"s{i}" for i in range(60)}),
        ("EG !p", set()),
    ],
)
def test_ring_of_sixty_states_uses_the_indexed_pre_image(temp_file, formula, expected):
    """At 50 edges and more the pre-image uses a reverse index; s0 -> s1 -> ... -> s59 -> s0, p only at s59."""
    n = 60
    path = temp_file(
        build_cgs_model_content(
            transitions=[
                ["a" if j == (i + 1) % n else "0" for j in range(n)] for i in range(n)
            ],
            state_names=[f"s{i}" for i in range(n)],
            initial_state="s0",
            prop_names=["p"],
            labelling=[["0"]] * (n - 1) + [["1"]],
            num_agents=1,
        )
    )
    assert _states(formula, path) == expected
