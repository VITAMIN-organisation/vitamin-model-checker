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


@pytest.mark.unit
def test_get_valid_actions_checks_middle_agent_in_three_agent_model(temp_file):
    content = """
Transition
I:D20:I *
0:0:0 *
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
3
Wallets
s0:10:5:100
s1:10:5:100
"""
    model = _load_wallet_model(temp_file, content)
    assert "D20" not in model.get_valid_actions("s0", 2)
    assert "I" in model.get_valid_actions("s0", 1)


@pytest.mark.unit
def test_simulate_transition_income_preserves_total_when_system_insufficient(temp_file):
    content = """
Transition
W50:I *
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
s0:0:10
s1:0:10
"""
    model = _load_wallet_model(temp_file, content)
    before = model.wallets["s0"]
    after = model.simulate_transition("s0", {1: "W50", 2: "I"})
    assert sum(after) == sum(before)
    assert after[0] == before[0]
    assert after[1] == before[1]


@pytest.mark.unit
def test_simulate_transition_income_transfers_when_system_has_funds(temp_file):
    content = """
Transition
W5:I *
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
s0:0:10
s1:0:10
"""
    model = _load_wallet_model(temp_file, content)
    after = model.simulate_transition("s0", {1: "W5", 2: "I"})
    assert after == (5, 5)
