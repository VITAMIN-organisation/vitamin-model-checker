"""WalletCGS: `Dn` spends n from the agent's wallet, `Wn` moves n from the last agent (the system pool) to it.

An action an agent cannot pay for is not available, and a transition that needs
it leads nowhere.
"""

import pytest

from model_checker.parsers.game_structures.wallet_cgs.wallet_cgs import WalletCGS


def _content(first_row: str, agents: int, wallet_rows: str) -> str:
    """Two states; s0's row is `first_row`, s1 loops on `*`; `wallet_rows` follows `Wallets`."""
    return (
        f"Transition\n{first_row}\n0 *\nName_State\ns0 s1\nInitial_State\ns0\n"
        f"Atomic_propositions\np\nLabelling\n1\n0\nNumber_of_agents\n{agents}\n"
        f"Wallets\n{wallet_rows}"
    )


def _model(temp_file, first_row: str, agents: int, wallet: str) -> WalletCGS:
    """`_content` with both states holding `wallet`."""
    model = WalletCGS()
    model.read_file(
        temp_file(_content(first_row, agents, f"s0: {wallet}\ns1: {wallet}\n"))
    )
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
@pytest.mark.parametrize(("action", "states"), [("D5", ["s0"]), ("D6", [])])
def test_single_agent_pays_for_its_own_transition(temp_file, action, states):
    """With one agent there is no contract agent, so the lone agent's wallet (5) is checked.

    D5 is affordable and D6 is not, as in `get_valid_actions`.
    """
    model = _model(temp_file, f"{action} *", agents=1, wallet="5")
    assert model.get_next_states("s0", {1: action}) == states


@pytest.mark.unit
@pytest.mark.parametrize(
    ("action", "after"), [("W5", (5, 5)), ("W10", (10, 0)), ("W11", (0, 10))]
)
def test_income_moves_money_only_when_the_pool_can_pay(temp_file, action, after):
    """The pool holds 10: W5 and W10 are paid in full, W11 not at all; the total stays 10."""
    model = _model(temp_file, f"{action}:I *", agents=2, wallet="0:10")
    assert model.simulate_transition("s0", {1: action, 2: "I"}) == after


@pytest.mark.unit
@pytest.mark.parametrize(
    ("action", "feasible"),
    [
        ("D5", True),  # 5 >= 5
        ("D6", False),  # 5 < 6
        ("W50", True),  # income is always permitted (AAMAS26b p. 3)
        ("I", True),  # neutral
    ],
)
def test_feasibility_follows_the_paper(temp_file, action, feasible):
    model = _model(temp_file, f"{action} *", agents=1, wallet="5")
    assert model.check_action_feasibility("s0", 1, action)[0] is feasible


@pytest.mark.unit
@pytest.mark.parametrize(
    ("profile", "feasible"),
    [
        ("D20|0", False),  # agent 1 holds 5 < 20
        ("D5|0", True),  # agent 1 holds 5
        ("IDLE|D5", False),  # agent 2, the contract, holds 0 < 5: no exemption
        ("IDLE|0", True),
    ],
)
def test_profile_is_feasible_only_if_every_agent_can_pay(temp_file, profile, feasible):
    model = _model(temp_file, "I|0 *", agents=2, wallet="5:0")
    assert model.is_profile_feasible("s0", profile) is feasible


@pytest.mark.unit
@pytest.mark.parametrize(
    ("rows", "named"),
    [
        ("s0: 5\n", r"state\(s\) s1;"),  # only s1 lacks a row
        ("", r"state\(s\) s0, s1;"),  # empty section: both lack one
    ],
)
def test_state_without_a_wallet_row_is_rejected(temp_file, rows, named):
    """AAMAS26b Def. 3.1 makes W total on Q x Ag, so a state with no row is an error."""
    with pytest.raises(ValueError, match=named):
        WalletCGS().read_file(temp_file(_content("I *", 1, rows)))
