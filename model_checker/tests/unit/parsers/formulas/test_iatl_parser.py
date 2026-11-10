"""IATL has two strategic prefixes: `<A>` (A can enforce) and its dual `[A]`.

Both take the operators X, F, G, U and R. Other logics' prefixes (`<<A>>`, a
bound after the coalition) are not IATL.
"""

import pytest

from model_checker.tests.helpers.formula_cases import parse


@pytest.mark.unit
@pytest.mark.parametrize(
    ("formula", "tree"),
    [
        ("<1>G p", ("<1>G", "p")),
        ("[1]G p", ("[1]G", "p")),
        ("[1,2]X r", ("[1,2]X", "r")),
        ("[1] p U q", ("[1]U", "p", "q")),
        ("[1](p R q)", ("[1]R", "p", "q")),
        ("<1>(p R q)", ("<1>R", "p", "q")),
    ],
)
def test_diamond_and_box_keep_their_kind_in_the_tree(formula, tree):
    """`[A]` must not be read as `<A>`: the node label keeps the bracket."""
    assert parse("IATL", formula) == tree


@pytest.mark.unit
@pytest.mark.parametrize("formula", ["<<1>>X p", "<1><2>F p"])
def test_prefixes_of_other_logics_are_rejected(formula):
    """ATL* coalitions and bounded coalitions are not IATL syntax."""
    assert parse("IATL", formula) is None
