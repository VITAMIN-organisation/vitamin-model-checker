"""Unit tests for CTL temporal operator handlers."""

import ast
from types import SimpleNamespace

import pytest

from model_checker.algorithms.explicit.CTL.operators import handle_au, handle_er
from model_checker.tests.helpers.model_helpers import load_cgs_from_content
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


@pytest.mark.unit
def test_handle_er_matches_until_duality(temp_file):
    """E(phi R psi) equals the complement of A(~phi U ~psi).

    Countermodel: s0 -> s1 -> s1 with phi={s1}, psi={s0}. Under the Until
    duality both sides are empty on this graph.
    """
    content = build_cgs_model_content(
        transitions=[["0", "A"], ["0", "*"]],
        state_names=["s0", "s1"],
        initial_state="s0",
        labelling=[["0", "1"], ["1", "0"]],
        num_agents=1,
        prop_names=["p", "q"],
    )
    cgs = load_cgs_from_content(temp_file, content)
    all_states = {"s0", "s1"}
    phi_states = {"s1"}
    psi_states = {"s0"}

    au_node = SimpleNamespace(
        left=SimpleNamespace(value=str(tuple(sorted(all_states - phi_states)))),
        right=SimpleNamespace(value=str(tuple(sorted(all_states - psi_states)))),
    )
    handle_au(cgs, au_node)
    expected_er = all_states - set(ast.literal_eval(au_node.value))

    er_node = SimpleNamespace(
        left=SimpleNamespace(value=str(tuple(sorted(phi_states)))),
        right=SimpleNamespace(value=str(tuple(sorted(psi_states)))),
    )
    handle_er(cgs, er_node)
    assert set(ast.literal_eval(er_node.value)) == expected_er == set()
