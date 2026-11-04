"""COTL model checking tests; expected verdicts on the attack graph are those of the COTL paper's case study."""

import pytest

from model_checker.algorithms.explicit.COTL.COTL import model_checking
from model_checker.algorithms.explicit.COTL.preimage import _cheapest_unlisted_action
from model_checker.tests.helpers.model_helpers import extract_states_from_result


def _obstruction_model(transitions, labelling, demons, actions, curses):
    """Model file text; states are s0, s1, ...; one proposition p."""
    names = " ".join(f"s{i}" for i in range(len(transitions)))
    return "\n".join(
        [
            "Transition",
            *(" ".join(row) for row in transitions),
            "Name_State",
            names,
            "Initial_State",
            "s0",
            "Atomic_propositions",
            "p",
            "Labelling",
            *labelling,
            "Number_of_demons",
            str(demons),
            "Demon_actions",
            *actions,
            "Curses",
            *curses,
        ]
    )


# s0 -> s1 (p) and s0 -> s2. Demon 1 can disable either edge at cost 1;
# demon 2 can disable s0 -> s1 at cost 1.
FORK = {
    "transitions": [["0", "1", "1"], ["0", "0", "0"], ["0", "0", "0"]],
    "labelling": ["0", "1", "0"],
    "demons": 2,
    "actions": ["1 s0 cut_bad 1", "1 s0 cut_good 1", "2 s0 cut_good 1"],
    "curses": [
        "s0 cut_bad,* s2",
        "s0 cut_good,* s1",
        "s0 *,cut_good s1",
        "s0 cut_bad,cut_good s1 s2",
        "s0 cut_good,cut_good s1",
    ],
}


def _holds_initially(result) -> bool:
    assert "error" not in result, result
    return result["initial_state"].endswith(": True")


@pytest.mark.semantic
@pytest.mark.model_checking
class TestCOTLSemantics:
    """What a legion can enforce by disabling edges, and how each operator uses it."""

    @pytest.mark.parametrize(
        "legion,holds",
        [("1,2", False), ("2,3", False), ("1,3", True), ("1,2,3", True)],
    )
    def test_attack_is_blocked_only_when_teams_1_and_3_cooperate(
        self, attack_graph, legion, holds
    ):
        """Each path to the target crosses an edge only team 1 or team 3 can block."""
        result = model_checking(f"<{legion}><1> G !q", attack_graph)
        assert _holds_initially(result) is holds

    def test_release_holds_on_a_path_the_legion_stops(self, attack_graph):
        """Blocking the only edge out of s1 ends the path there, which G accepts."""
        result = model_checking("<1,3><1> G !q", attack_graph)
        assert extract_states_from_result(result) == {"s0", "s1", "s3"}

    @pytest.mark.parametrize(
        "formula,holds", [("<1><1> X p", False), ("<1><1> WX p", True)]
    )
    def test_next_needs_a_successor_while_weak_next_does_not(
        self, temp_file, formula, holds
    ):
        """At s0 demon 1 may cut s0 -> s2, but demon 2 may then cut s0 -> s1 as well."""
        content = _obstruction_model(**FORK)
        assert _holds_initially(model_checking(formula, temp_file(content))) is holds

    def test_demons_outside_the_legion_work_against_it(self, temp_file):
        """With demon 2 in the legion nobody cuts s0 -> s1, so X p holds."""
        content = _obstruction_model(**FORK)
        assert _holds_initially(model_checking("<1,2><1> X p", temp_file(content)))

    @pytest.mark.parametrize("budget,holds", [(0, False), (1, True)])
    def test_budget_bounds_what_the_legion_pays_per_step(
        self, attack_graph, budget, holds
    ):
        """Blocking a1 or a2 costs 1, so budget 0 cannot stop the attack."""
        result = model_checking(f"<1,3><{budget}> G !q", attack_graph)
        assert _holds_initially(result) is holds

    def test_empty_legion_with_budget_0_quantifies_over_all_demon_choices(
        self, attack_graph
    ):
        """<><0> X: every curse of every demon must leave a next state, so s1 and s3 fail."""
        result = model_checking("<><0> X !q", attack_graph)
        assert extract_states_from_result(result) == {"s0"}

    @pytest.mark.parametrize(
        "formula,holds",
        [("<1,3><1> !q U false", False), ("<1,3><1> !q W false", True)],
    )
    def test_until_needs_the_goal_while_weak_until_accepts_never_reaching_it(
        self, attack_graph, formula, holds
    ):
        """With the goal false, U fails and W reduces to G !q, which teams 1 and 3 enforce."""
        assert _holds_initially(model_checking(formula, attack_graph)) is holds


@pytest.mark.unit
class TestCheapestUnlistedAction:
    """Actions of the legion that no curse lists all leave every edge enabled."""

    @pytest.mark.parametrize(
        "listed,expected",
        [
            (set(), 0),
            ({("*",)}, 1),
            ({("*",), ("a",)}, 2),
            ({("*",), ("a",), ("b",)}, None),
        ],
    )
    def test_one_member(self, listed, expected):
        assert _cheapest_unlisted_action([{"*": 0, "a": 1, "b": 2}], listed) == expected

    def test_combines_members_by_total_cost(self):
        actions = [{"*": 0, "a": 1}, {"*": 0, "b": 5}]
        listed = {("*", "*"), ("a", "*")}
        assert _cheapest_unlisted_action(actions, listed) == 5

    def test_empty_legion_has_one_action(self):
        assert _cheapest_unlisted_action([], set()) == 0
        assert _cheapest_unlisted_action([], {()}) is None


@pytest.mark.unit
@pytest.mark.model_checking
class TestObstructionModelErrors:
    """Invalid model files fail with a message that names the offending line."""

    @pytest.mark.parametrize(
        "field,value,message",
        [
            ("actions", ["1 s0 cut 0"], "cost must be an integer >= 1"),
            ("actions", ["3 s0 cut 1"], "demon must be between 1 and 2"),
            ("curses", ["s0 cut,* s1"], "demon 1 has no action 'cut'"),
            ("curses", ["s0 cut_bad s2"], "one action per demon"),
            ("curses", ["s1 *,* s0"], "no edge from 's1' to 's0'"),
            ("curses", ["s0 cut_bad,* s2", "s0 cut_bad,* s1"], "curse listed twice"),
        ],
    )
    def test_invalid_demon_section(self, temp_file, field, value, message):
        model = {**FORK, field: value}
        result = model_checking("<1><1> X p", temp_file(_obstruction_model(**model)))
        assert "error" in result
        assert message in result["error"]["message"]

    @pytest.mark.timeout(10)
    def test_memory_follows_the_file_not_the_declared_number_of_demons(self, temp_file):
        """A short file declaring 10^9 demons must load without one table entry per demon."""
        model = {**FORK, "demons": 10**9, "actions": ["1 s0 cut_bad 1"], "curses": []}
        result = model_checking("<1><1> X p", temp_file(_obstruction_model(**model)))
        assert "error" not in result, result

    def test_cost_model_is_rejected(self, temp_file):
        content = "\n".join(
            [
                "Transition",
                "0 A",
                "0 *",
                "Name_State",
                "s0 s1",
                "Initial_State",
                "s0",
                "Costs_for_actions",
                "A s0$1",
                "Atomic_propositions",
                "p",
                "Labelling",
                "0",
                "1",
                "Number_of_agents",
                "1",
            ]
        )
        result = model_checking("<1><1> X p", temp_file(content))
        assert "error" in result
        assert "Number_of_demons" in result["error"]["message"]
