"""IATL models (BCGS files) are checked when loaded, like ICTL frames but with agents' actions.

Each state's diagonal cell must be the all-idle cell `II,II` (two agents), the
preorder must be a boolean partial order, and labels must not vanish going up it.
"""

import pytest

from model_checker.parsers.game_structures.bcgs.bcgs import BCGS

_IDLE = "II,II"


def _load(temp_file, transitions, preorder, labelling, names="s0 s1"):
    content = (
        f"Transition\n{transitions}\nPreorder\n{preorder}\nName_State\n{names}\n"
        f"Initial_State\ns0\nAtomic_propositions\np\nLabelling\n{labelling}\n"
        "Number_of_agents\n2\n"
    )
    model = BCGS()
    model.read_file(temp_file(content))
    return model


@pytest.mark.unit
def test_valid_model_loads(temp_file):
    """s0 below s1 with p only at s1 respects the preorder."""
    model = _load(temp_file, f"{_IDLE} 0\n0 {_IDLE}", "1 1\n0 1", "0\n1")
    assert list(model.states) == ["s0", "s1"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("transitions", "preorder", "labelling", "names", "message"),
    [
        ("AA,AA BB\n0 II,II", "1 0\n0 1", "1\n0", "s0 s1", "no Idle"),
        (
            "I II,II\n0 II,II",
            "1 0\n0 1",
            "1\n0",
            "s0 s1",
            "don't have available actions",
        ),
        (f"{_IDLE} 0\n0 {_IDLE}", "0 0\n0 1", "0\n0", "s0 s1", "not reflective"),
        (f"{_IDLE} 0\n0 {_IDLE}", "1 1\n1 1", "0\n0", "s0 s1", "not antisymmetric"),
        (
            f"{_IDLE} 0 0\n0 {_IDLE} 0\n0 0 {_IDLE}",
            "1 1 0\n0 1 1\n0 0 1",
            "0\n0\n0",
            "s0 s1 s2",
            "not transitive",
        ),
        (f"{_IDLE} 0\n0 {_IDLE}", "2 0\n0 1", "0\n0", "s0 s1", "boolean preorder"),
        (f"{_IDLE} 0\n0 {_IDLE}", "1 1\n0 1", "1\n0", "s0 s1", "Labeling function"),
    ],
    ids=[
        "no_idle_cell",
        "profile_shorter_than_the_agents",
        "preorder_not_reflexive",
        "preorder_not_antisymmetric",
        "preorder_not_transitive",
        "preorder_not_0_or_1",
        "p_lost_going_up",
    ],
)
def test_invalid_model_is_refused_with_the_broken_condition(
    temp_file, transitions, preorder, labelling, names, message
):
    """Each condition has its own message."""
    with pytest.raises(AssertionError, match=message):
        _load(temp_file, transitions, preorder, labelling, names)
