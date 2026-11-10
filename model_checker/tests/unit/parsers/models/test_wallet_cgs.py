"""WalletCGS: `Dn` spends n from the agent's wallet, `Wn` moves n from the last agent (the system pool) to it.

An action an agent cannot pay for is not available, and a transition that needs
it leads nowhere.
"""

import pytest

from model_checker.parsers.game_structures.wallet_cgs.wallet_cgs import WalletCGS


def _model(temp_file, first_row: str, agents: int, wallet: str) -> WalletCGS:
    """Two states; s0's row is `first_row`, s1 loops on `*`; both states hold `wallet`."""
    content = (
        f"Transition\n{first_row}\n0 *\nName_State\ns0 s1\nInitial_State\ns0\n"
        f"Atomic_propositions\np\nLabelling\n1\n0\nNumber_of_agents\n{agents}\n"
        f"Wallets\ns0: {wallet}\ns1: {wallet}\n"
    )
    model = WalletCGS()
    model.read_file(temp_file(content))
    return model


@pytest.mark.unit
@pytest.mark.parametrize(
    ("action", "available"), [("D4", True), ("D5", True), ("D6", False)]
)
def test_spending_is_available_up_to_the_balance(temp_file, action, available):
    """With 5 in the wallet, D5 is allowed and D6 is not."""
    model = _model(temp_file, f"{action} *", agents=1, wallet="5")
    assert (action in model.get_valid_actions("s0", 1)) is available
    assert "*" in model.get_valid_actions("s0", 1)


@pytest.mark.unit
def test_balance_is_checked_for_the_acting_agent_only(temp_file):
    """In a 3-agent model, agent 2 (balance 5) cannot play D20; agent 1 may idle."""
    model = _model(temp_file, "I:D20:I *", agents=3, wallet="10:5:100")
    assert "D20" not in model.get_valid_actions("s0", 2)
    assert "I" in model.get_valid_actions("s0", 1)


@pytest.mark.unit
def test_next_states_are_every_cell_the_action_matches(temp_file):
    """`A` in both cells of s0's row reaches s0 and s1; an unknown action reaches nothing."""
    model = _model(temp_file, "A A", agents=1, wallet="5")
    assert model.get_next_states("s0", {1: "A"}) == ["s0", "s1"]
    assert model.get_next_states("s0", {1: "Z"}) == []


@pytest.mark.unit
def test_transition_needing_an_unaffordable_action_leads_nowhere(temp_file):
    """Agent 1 holds 5, so the D20 transition is not taken."""
    model = _model(temp_file, "D20:I *", agents=2, wallet="5:100")
    assert model.get_next_states("s0", {1: "D20", 2: "I"}) == []


@pytest.mark.unit
@pytest.mark.parametrize(
    ("action", "after"), [("W5", (5, 5)), ("W10", (10, 0)), ("W11", (0, 10))]
)
def test_income_moves_money_only_when_the_pool_can_pay(temp_file, action, after):
    """The pool holds 10: W5 and W10 are paid in full, W11 not at all; the total stays 10."""
    model = _model(temp_file, f"{action}:I *", agents=2, wallet="0:10")
    assert model.simulate_transition("s0", {1: action, 2: "I"}) == after
