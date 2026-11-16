"""NatATL memoryless semantics: action-guarded strategies vs output."""

import pytest

from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
    model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestNatATLMemorylessSemantics:
    """Test NatATL memoryless strategy semantics."""

    def test_memoryless_strategy_suffices(self, temp_file):
        """s0 offers only a and s1 only I, so no single (true, action) rule is valid;
        (p, I); (true, a) of size 2 reaches p."""
        content = build_cgs_model_content(
            transitions=[["0", "a"], ["0", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["0"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        file_path = temp_file(content)
        load_cgs_from_content(temp_file, content)

        assert model_checking("<{1}, 1>F p", file_path)["Satisfiability"] is False
        assert model_checking("<{1}, 2>F p", file_path)["Satisfiability"] is True

    def test_memoryless_strategy_maintains_globally(self, temp_file):
        """Verify memoryless strategy can maintain global property."""
        content = build_cgs_model_content(
            transitions=[["I", "a"], ["a", "I"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            labelling=[["1"], ["1"]],
            num_agents=1,
            prop_names=["p"],
        )
        file_path = temp_file(content)

        result = model_checking("<{1}, 1>G p", file_path)

        assert "Satisfiability" in result
        assert isinstance(result["Satisfiability"], bool)
        assert result["Satisfiability"] is True


def _satisfied(temp_file, content, formula):
    result = model_checking(formula, temp_file(content))
    assert "error" not in result, result
    return result["Satisfiability"]


# s0 (p): idle stays, a goes to s1 (g); s1 (g) only idles.
_IDLE_OR_GO = build_cgs_model_content(
    transitions=[["II", "aI"], ["0", "II"]],
    state_names=["s0", "s1"],
    initial_state="s0",
    labelling=[["1", "0"], ["0", "1"]],
    num_agents=2,
    prop_names=["p", "g"],
)

# s0 (p) and s1 (q) need a to reach s2 (r); idle or b leads to the sink s3 (t).
_TWO_STEPS_THEN_IDLE = build_cgs_model_content(
    transitions=[
        ["0", "aI", "0", "II,bI"],
        ["0", "0", "aI", "II,bI"],
        ["0", "0", "II", "0"],
        ["0", "0", "0", "II"],
    ],
    state_names=["s0", "s1", "s2", "s3"],
    initial_state="s0",
    labelling=[["1", "0", "0", "0"], ["0", "1", "0", "0"]]
    + [["0", "0", "1", "0"], ["0", "0", "0", "1"]],
    num_agents=2,
    prop_names=["p", "q", "r", "t"],
)

# Agent 1 can play a everywhere; agent 2 must play c at s0 and d at s1 to reach s2 (g).
_UNEVEN_COALITION = build_cgs_model_content(
    transitions=[
        ["0", "ac", "0", "ad,bc,bd"],
        ["0", "0", "ad", "ac"],
        ["0", "0", "ad", "0"],
        ["0", "0", "0", "ad"],
    ],
    state_names=["s0", "s1", "s2", "s3"],
    initial_state="s0",
    labelling=[["1", "0"], ["0", "0"], ["0", "1"], ["0", "0"]],
    num_agents=2,
    prop_names=["p", "g"],
)


@pytest.mark.semantic
@pytest.mark.model_checking
class TestNaturalStrategies:
    """Strategies are rule lists ending in (true, action); k bounds the coalition's total size."""

    @pytest.mark.parametrize(("k", "holds"), [(1, False), (2, True)])
    def test_rule_action_is_played_not_idle(self, temp_file, k, holds):
        """(p, a); (true, idle) has size 2 and forces s1; a under (p, a) never idles."""
        assert _satisfied(temp_file, _IDLE_OR_GO, f"<{{1}},{k}>F g") is holds

    @pytest.mark.parametrize(("k", "holds"), [(2, False), (3, True)])
    def test_last_rule_action_must_be_available(self, temp_file, k, holds):
        """a is missing at s2 and s3, so (p, a); (q, a); (true, idle) of size 3 is needed."""
        assert _satisfied(temp_file, _TWO_STEPS_THEN_IDLE, f"<{{1}},{k}>F r") is holds

    def test_bound_below_the_coalition_size_is_false(self, temp_file):
        """Each member needs its true rule, so no profile of size 1 covers two agents."""
        result = model_checking("<{1,2},1>F g", temp_file(_UNEVEN_COALITION))
        assert "error" not in result
        assert result["Satisfiability"] is False

    @pytest.mark.parametrize(("k", "holds"), [(2, False), (3, True)])
    def test_bound_is_the_total_over_the_coalition(self, temp_file, k, holds):
        """Agent 1 plays a everywhere (size 1); agent 2 needs (p, c); (true, d) (size 2)."""
        assert _satisfied(temp_file, _UNEVEN_COALITION, f"<{{1,2}},{k}>F g") is holds
