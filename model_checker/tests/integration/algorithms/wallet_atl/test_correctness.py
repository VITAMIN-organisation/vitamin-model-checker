"""Wallet_ATL integration tests on WalletCGS fixtures."""

import pytest

from model_checker.algorithms.explicit.Wallet_ATL.Wallet_ATL import (
    _core_walletatl_checking,
    _extract_state_name,
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    load_test_model,
)


@pytest.fixture
def wallet_atl_model(test_data_dir):
    """Load wallet_1agent_2states.txt (WalletCGS/WALLET_ATL)."""
    return load_test_model(
        test_data_dir, "WalletCGS/WALLET_ATL/wallet_1agent_2states.txt"
    )


@pytest.mark.unit
@pytest.mark.model_checking
class TestWalletATLErrorHandling:
    """Wallet_ATL rejects invalid inputs."""

    def test_invalid_formula_syntax(self, wallet_atl_model):
        result = model_checking("INVALID_FORMULA", wallet_atl_model.filename)
        assert "error" in result

    def test_nonexistent_atomic_proposition(self, wallet_atl_model):
        result = _core_walletatl_checking(wallet_atl_model, "<<1>>F missing")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_extract_state_name_strips_wallet_suffixes_only(self):
        assert _extract_state_name("s9:10:20") == "s9"
        assert _extract_state_name("locA:5") == "locA"
        assert _extract_state_name("s_init") == "s_init"
        assert _extract_state_name("s0") == "s0"


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestWalletATLSemantics:
    """Exact winning states on the minimal WalletCGS fixture."""

    @pytest.mark.parametrize(
        "formula, expected_states, initial_expected",
        [
            ("<<1>>F q", {"s0", "s1"}, True),
            ("<<1>>X p", {"s0"}, True),
            ("<<1>>X q", {"s0", "s1"}, True),
            ("<<1>>G p", {"s0"}, True),
            ("<<1>>F true", {"s0", "s1"}, True),
            ("<<1>>F false", set(), False),
        ],
    )
    def test_exact_state_sets(
        self, wallet_atl_model, formula, expected_states, initial_expected
    ):
        result = _core_walletatl_checking(wallet_atl_model, formula)
        assert "error" not in result, result
        states = extract_states_from_result(result)
        assert states == expected_states
        init = str(result.get("initial_state", ""))
        assert (": True" in init) is initial_expected

    @pytest.mark.parametrize("goal", ["p", "q"])
    def test_eventually_equals_true_until(self, wallet_atl_model, goal):
        """`<<A:C>>F psi` equals `<<A:C>>true U psi` (docs/Wallet_ATL/algorithm.md)."""
        coalition = "<<1:wallet(1, >= 10)>>"
        eventually = _core_walletatl_checking(wallet_atl_model, f"{coalition}F {goal}")
        until = _core_walletatl_checking(wallet_atl_model, f"{coalition} true U {goal}")
        assert "error" not in until, until
        assert extract_states_from_result(until) == extract_states_from_result(
            eventually
        )

    def test_wallet_guard_filters_states_by_balance(self, wallet_atl_model):
        """Both states hold 5 and q holds only at s1.

        With >= 5 the guard holds everywhere and s0 can move to s1: {s0, s1}.
        With >= 10 no state can start a guarded move, so s0 is out; s1 stays
        because q already holds there (Algorithm 1 line 20 starts from [[q]]).
        """
        ok = _core_walletatl_checking(wallet_atl_model, "<<1:wallet(1, >= 5)>>F q")
        assert "error" not in ok, ok
        assert extract_states_from_result(ok) == {"s0", "s1"}

        blocked = _core_walletatl_checking(
            wallet_atl_model, "<<1:wallet(1, >= 10)>>F q"
        )
        assert "error" not in blocked, blocked
        assert extract_states_from_result(blocked) == {"s1"}

    def test_wallet_until_applies_guards(self, wallet_atl_model):
        """Same sets as F: the guard is checked where a move starts, and the states
        where q already holds count from the start (Algorithm 1 lines 18-25)."""
        unconstrained = _core_walletatl_checking(wallet_atl_model, "<<1>> p U q")
        assert "error" not in unconstrained, unconstrained
        assert extract_states_from_result(unconstrained) == {"s0", "s1"}

        allowed = _core_walletatl_checking(
            wallet_atl_model, "<<1:wallet(1, >= 5)>> p U q"
        )
        assert "error" not in allowed, allowed
        assert extract_states_from_result(allowed) == {"s0", "s1"}

        blocked = _core_walletatl_checking(
            wallet_atl_model, "<<1:wallet(1, >= 10)>> p U q"
        )
        assert "error" not in blocked, blocked
        assert extract_states_from_result(blocked) == {"s1"}


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestWalletATLResultSet:
    """`res` is the exact state set, also when the initial state is False."""

    def test_guard_no_state_satisfies_gives_empty_set(self, wallet_atl_model):
        """Wallets are s0: 5 and s1: 5, so no state meets wallet >= 10 and the set is empty.

        Plain ATL `<1>G q` holds at s1 (q holds there and s1 loops), so an ATL
        result would wrongly list s1.
        """
        result = _core_walletatl_checking(
            wallet_atl_model, "<< 1 : wallet(1, >= 10) >> G q"
        )
        assert "error" not in result
        assert extract_states_from_result(result) == set()
        assert ": False" in result["initial_state"]

    def test_guard_every_state_satisfies_keeps_the_atl_set(self, wallet_atl_model):
        """With wallet >= 0 every state passes the guard, so the set is the ATL one: s1."""
        result = _core_walletatl_checking(
            wallet_atl_model, "<< 1 : wallet(1, >= 0) >> G q"
        )
        assert extract_states_from_result(result) == {"s1"}


def _two_agent_model(
    rows: str, wallet_s0: str, wallet_s1: str = "0:0", p_at_s0: bool = False
) -> str:
    """Agent 1 acts, agent 2 is the contract; s1 loops on `*`. goal holds only at
    s1; p holds at s1, and also at s0 when `p_at_s0`."""
    return (
        f"Transition\n{rows}\n0 *\nName_State\ns0 s1\nInitial_State\ns0\n"
        f"Atomic_propositions\ngoal p\nLabelling\n0 {int(p_at_s0)}\n1 1\n"
        f"Number_of_agents\n2\nWallets\ns0: {wallet_s0}\ns1: {wallet_s1}\n"
    )


def _states(temp_file, content: str, formula: str) -> set:
    result = model_checking(formula, temp_file(content))
    assert "error" not in result, result
    return extract_states_from_result(result)


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestWalletATLFeasibleMoves:
    """AAMAS26b Def. 3.1 and 4.1: a consumption action `Dv` is a move only when the
    acting agent holds at least v; income (`Wv`) and neutral moves are always moves
    ("Actions in Act↑ are always permitted", p. 3). Strategies use only such moves."""

    @pytest.mark.parametrize(
        ("alice", "expected"),
        [
            # 5 < 20: D20 is not a move, Alice can only idle in s0; s1 loops on goal
            ("5:0", {"s1"}),
            # 20 >= 20: Alice plays D20 to reach s1
            ("20:0", {"s0", "s1"}),
        ],
    )
    def test_unaffordable_deposit_is_not_a_move(self, temp_file, alice, expected):
        content = _two_agent_model("I|0 D20|0", alice)
        assert _states(temp_file, content, "<<1>>X goal") == expected

    @pytest.mark.parametrize(
        ("wallets", "expected"),
        [
            # the contract holds 0, so D5 is not its move: s0 can only go to s1
            ("100:0", {"s0", "s1"}),
            # the contract holds 5 and may play D5, keeping the game in s0
            ("100:5", {"s1"}),
        ],
    )
    def test_opponent_moves_are_checked_too(self, temp_file, wallets, expected):
        content = _two_agent_model("I|D5 I|0", wallets)
        assert _states(temp_file, content, "<<1>>X goal") == expected

    @pytest.mark.parametrize("move", ["W50|0", "I|0", "IDLE|0"])
    def test_income_and_idle_need_no_funds(self, temp_file, move):
        """All wallets are 0, yet income (W50) and idle (I, IDLE) are moves, so s0 reaches s1."""
        content = _two_agent_model(f"0 {move}", "0:0")
        assert _states(temp_file, content, "<<1>>X goal") == {"s0", "s1"}

    def test_state_without_a_feasible_move_is_refused(self, temp_file):
        """s0's only move is D20 with 5 in the wallet; a CGS needs a move per state
        (JACM 2002 Def. 2.1), so the model is rejected and the message names s0."""
        content = _two_agent_model("0 D20|0", "5:0")
        result = model_checking("<<1>>X goal", temp_file(content))
        assert "error" in result, result
        assert "s0" in result["error"]["message"]


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestWalletATLGuards:
    """AAMAS26b Algorithm 1: the guard filters the states a coalition move starts
    from (wPre(Pre(A, S))), not the states it moves to.

    Two-state model: s0 -I|0-> s1, s1 loops; goal only at s1; agent 1 holds 10 at s0."""

    @pytest.mark.parametrize(
        ("wallet_s1", "expected"),
        [
            # Pre(1, {s1}) = {s0, s1}; wPre keeps s0 (10 >= 10) and drops s1 (5 < 10)
            ("5:0", {"s0"}),
            # the guard holds at both states, so wPre keeps all of Pre
            ("10:0", {"s0", "s1"}),
        ],
    )
    def test_guard_is_checked_where_the_move_starts(
        self, temp_file, wallet_s1, expected
    ):
        content = _two_agent_model("0 I|0", "10:0", wallet_s1)
        assert _states(temp_file, content, "<<1:wallet(1, >= 10)>>X goal") == expected

    @pytest.mark.parametrize(
        "formula",
        [
            # Algorithm 1 lines 18-25: start {s1}; s0 holds 10 and moves to s1
            "<<1:wallet(1, >= 10)>>F goal",
            # same, and p holds at s0 on the way
            "<<1:wallet(1, >= 10)>> p U goal",
        ],
    )
    def test_eventually_holds_where_next_does(self, temp_file, formula):
        """<<1:C>>X goal holds at s0, so the F and U forms hold there too, and s1
        counts because goal holds there (the start set has no guard)."""
        content = _two_agent_model("0 I|0", "10:0", "5:0", p_at_s0=True)
        assert _states(temp_file, content, formula) == {"s0", "s1"}

    def test_globally_checks_the_guard_at_every_step(self, temp_file):
        """Three states: s0 (holds 10, p) -> s1 (holds 5, p) -> s1; s2 (holds 10,
        no p) loops.

        Algorithm 1 lines 10-17: rho = all states, tau = [[p]] = {s0, s1}; round 1
        keeps wPre(Pre({s0, s1})) & [[p]] = {s0} (s1 fails the guard); round 2 finds
        no move from any state into {s0}; the result is empty. Def. 4.5 would check
        the guard only at s0 and keep it, an open question in
        docs/Wallet_ATL/algorithm.md.
        """
        content = (
            "Transition\n0 I|0 0\n0 * 0\n0 0 *\nName_State\ns0 s1 s2\n"
            "Initial_State\ns0\nAtomic_propositions\np\nLabelling\n1\n1\n0\n"
            "Number_of_agents\n2\nWallets\ns0: 10:0\ns1: 5:0\ns2: 10:0\n"
        )
        assert _states(temp_file, content, "<<1:wallet(1, >= 10)>>G p") == set()

    def test_one_guard_per_coalition_agent_is_accepted(self, temp_file):
        """Both agents hold enough at s0 and s1 (10 >= 10, 0 >= 0), and s0 moves to
        s1, so the pair can force goal next from both states."""
        content = _two_agent_model("0 I|0", "10:0", "10:0")
        formula = "<<1,2:wallet(1, >= 10) && wallet(2, >= 0)>>X goal"
        assert _states(temp_file, content, formula) == {"s0", "s1"}

    @pytest.mark.parametrize(
        ("guards", "expected"),
        [
            # 4 >= 100 fails at both states, whatever the second guard says
            ("wallet(1, >= 100) && wallet(1, >= 3)", set()),
            ("wallet(1, >= 3) && wallet(1, >= 100)", set()),
            # 3 <= 4 <= 5 at both states, and both can move to s1
            ("wallet(1, >= 3) && wallet(1, <= 5)", {"s0", "s1"}),
            # 4 <= 3 fails at both states
            ("wallet(1, >= 3) && wallet(1, <= 3)", set()),
        ],
    )
    def test_every_guard_on_one_agent_must_hold(self, temp_file, guards, expected):
        """Agent 1 holds 4 at s0 and s1. C is a conjunction, so two guards on the
        same agent must both hold (a range when they are >= and <=)."""
        content = _two_agent_model("0 I|0", "4:0", "4:0")
        assert _states(temp_file, content, f"<<1:{guards}>>X goal") == expected
