"""Smoke and theory-aligned tests for IATL model checking."""

from pathlib import Path

import pytest

from model_checker.algorithms.explicit.IATL.checker import IATLModelChecker
from model_checker.algorithms.explicit.IATL.IATL import model_checking
from model_checker.algorithms.explicit.IATL.preimage import (
    pre_image_exists,
    pre_image_forall,
)
from model_checker.algorithms.explicit.IATL.util.graph import read_file
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "CGS"
    / "IATL"
    / "iatl_2agents_2states_minimal.txt"
)


def test_read_file_loads_minimal_model():
    data = read_file(str(_FIXTURE))
    assert data["states_counter"] == 2
    assert data["initial_state"] == "s0"
    assert data["number_of_agents"] == 2


def test_pre_d_and_pre_f_match_kr2025_proposition_2():
    data = read_file(str(_FIXTURE))
    targets = {"s0"}
    exists = pre_image_exists(
        data["graph"],
        data["states"],
        "1",
        targets,
        data["number_of_agents"],
    )
    forall = pre_image_forall(
        data["graph"],
        data["states"],
        "1",
        targets,
        data["number_of_agents"],
    )
    assert "s0" in exists
    assert "s0" not in forall


@pytest.mark.parametrize(
    "formula,initial_true",
    [
        ("<1>X p", True),
        ("[1]X p", False),
        ("<1>F p", True),
        ("<1>G p", True),
        ("<1>p U p", True),
        ("p -> p", True),
        ("p && p", True),
        ("p || p", True),
    ],
)
def test_model_checking_operators(formula, initial_true):
    result = model_checking(formula, str(_FIXTURE))
    assert "error" not in result
    assert result["initial_state"] == f"Initial state s0: {initial_true}"


def test_vmi_entry_point_on_fixture():
    result = model_checking("<1>X p", str(_FIXTURE))
    assert "error" not in result
    assert result["res"].startswith("Result:")
    assert result["initial_state"] == "Initial state s0: True"


def test_vmi_syntax_error():
    result = model_checking("<1>X p (", str(_FIXTURE))
    assert result["res"].startswith("Error:")


def test_vmi_missing_model_returns_error():
    result = model_checking("<1>X p", "nonexistent_iatl_model.txt")
    assert result["res"].startswith("Error:")
    assert result["error"]["type"] == "system"


def test_intuitionistic_not_uses_preorder_with_custom_state_names(tmp_path):
    model_text = """\
Transition
II,II AA,AA
0 II,II
Preorder
1 0
0 1
Name_State
alpha beta
Initial_State
beta
Atomic_propositions
p
Labelling
1
0
Number_of_agents
2
"""
    model_path = tmp_path / "iatl_custom_states.txt"
    model_path.write_text(model_text, encoding="utf-8")
    checker = IATLModelChecker(read_file(str(model_path)))
    assert "alpha" in checker.upward_closure

    result = model_checking("!p", str(model_path))
    assert "error" not in result
    states = parse_state_set_literal(result["res"].removeprefix("Result: "))
    assert "beta" in states
    assert "alpha" not in states
