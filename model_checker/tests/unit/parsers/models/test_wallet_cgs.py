"""WalletCGS feasibility and next-state helpers."""

import pytest

from model_checker.parsers.game_structures.wallet_cgs.wallet_cgs import WalletCGS


def _load_wallet_model(temp_file, content: str) -> WalletCGS:
    path = temp_file(content)
    model = WalletCGS()
    model.read_file(path)
    return model


@pytest.mark.unit
def test_get_valid_actions_filters_infeasible_consumption(temp_file):
    content = """
Transition
D20 *
0 *
Name_State
s0 s1
Initial_State
s0
Atomic_propositions
p
Labelling
1
0
Number_of_agents
1
Wallets
s0: 5
s1: 5
"""
    model = _load_wallet_model(temp_file, content)
    assert "D20" not in model.get_valid_actions("s0", 1)
    assert "*" in model.get_valid_actions("s0", 1)


@pytest.mark.unit
def test_get_valid_actions_keeps_feasible_consumption(temp_file):
    content = """
Transition
D3 *
0 *
Name_State
s0 s1
Initial_State
s0
Atomic_propositions
p
Labelling
1
0
Number_of_agents
1
Wallets
s0: 5
s1: 5
"""
    model = _load_wallet_model(temp_file, content)
    assert "D3" in model.get_valid_actions("s0", 1)


@pytest.mark.unit
def test_get_next_states_collects_all_matches(temp_file):
    content = """
Transition
A A
0 *
Name_State
s0 s1
Initial_State
s0
Atomic_propositions
p
Labelling
1
0
Number_of_agents
1
Wallets
s0: 5
s1: 5
"""
    model = _load_wallet_model(temp_file, content)
    assert model.get_next_states("s0", {1: "A"}) == ["s0", "s1"]


@pytest.mark.unit
def test_get_next_states_returns_empty_list_when_no_match(temp_file):
    content = """
Transition
A *
0 *
Name_State
s0 s1
Initial_State
s0
Atomic_propositions
p
Labelling
1
0
Number_of_agents
1
Wallets
s0: 5
s1: 5
"""
    model = _load_wallet_model(temp_file, content)
    assert model.get_next_states("s0", {1: "Z"}) == []


@pytest.mark.unit
def test_get_next_states_rejects_infeasible_consumption(temp_file):
    content = """
Transition
D20:I *
0:0 *
Name_State
s0 s1
Initial_State
s0
Atomic_propositions
p
Labelling
1
0
Number_of_agents
2
Wallets
s0:5:100
s1:5:100
"""
    model = _load_wallet_model(temp_file, content)
    assert model.get_next_states("s0", {1: "D20", 2: "I"}) == []
