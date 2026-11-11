"""WalletCGS: a consumption action `Dn` needs n in the acting agent's wallet
(AAMAS26b Def. 4.1); income and neutral actions are always feasible; every state
has a wallet row (Def. 3.1).
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
