"""Semantic review regressions. Expected values follow from the small games below.

No test treats an old implementation's answer as its correctness oracle.
"""

from copy import deepcopy
from unittest.mock import patch

import pytest

from model_checker.algorithms.explicit.LTL.pruning import pruning as ltl_pruning
from model_checker.algorithms.explicit.LTL.strategies import initialize
from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
    model_checking as memoryless,
)
from model_checker.algorithms.explicit.NatATL.Memoryless.pruning import (
    process_transition_matrix_data_fixed,
)
from model_checker.algorithms.explicit.NatATL.Recall.natatl_recall import (
    model_checking as recall,
)
from model_checker.parsers.game_structures.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    extract_actions_for_agents,
)
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


def game(tmp_path, graph, props, labels, *, n=1):
    states = [f"s{i}" for i in range(len(graph))]
    path = tmp_path / "game.txt"
    path.write_text(
        build_cgs_model_content(
            transitions=[[str(x) for x in row] for row in graph],
            state_names=states,
            initial_state="s0",
            labelling=[[str(x) for x in row] for row in labels],
            num_agents=n,
            prop_names=props,
        )
    )
    cgs = CGS()
    cgs.read_file(str(path))
    cgs.filename = str(path)
    return cgs, str(path)


def policy(*pairs):
    return {"condition_action_pairs": list(pairs)}


def adversarial(tmp_path):
    # Agent 2 can send MOVE to the trap instead of the goal; IDLE loops at s0.
    all_joints = "IDLE|BLOCK,IDLE|ALLOW,MOVE|BLOCK,MOVE|ALLOW"
    return game(
        tmp_path,
        [
            ["IDLE|BLOCK,IDLE|ALLOW", "MOVE|ALLOW", "MOVE|BLOCK"],
            [0, all_joints, 0],
            [0, 0, all_joints],
        ],
        ["goal", "safe"],
        [[0, 1], [1, 1], [0, 0]],
        n=2,
    )


def test_no_inferred_joint_arity():
    with pytest.raises(TypeError):
        extract_actions_for_agents([["AB,CD"]], [1])
    assert extract_actions_for_agents([["AB,CD", "0"]], [1], num_agents=2) == {
        "agent1": ["A", "C"]
    }


def test_ltl_initialize_partial_coalition(tmp_path):
    _cgs, path = game(tmp_path, [["II,IB,AI,AB"]], ["p"], [[1]], n=2)
    actions, *_ = initialize(path, "F p", 1, [1])
    assert set(actions["actions_agent1"]) == {"IDLE", "A"}


def test_no_vacuous_ltl_af_from_illegal_action(tmp_path):
    cgs, path = game(tmp_path, [["I", 0], [0, "I"]], ["p", "goal"], [[1, 0], [1, 0]])
    assert ltl_pruning(cgs, path, [1], "AF goal", [policy(("p", "MISSING"))]) is False


def test_ltl_invalid_candidate_never_reaches_temporal_backend(tmp_path):
    from model_checker.algorithms.explicit.LTL import pruning as module

    cgs, path = game(tmp_path, [["I"]], ["goal"], [[0]])
    with patch.object(
        module, "model_checking", side_effect=AssertionError("must not run CTL")
    ):
        assert (
            module.pruning(cgs, path, [1], "AF goal", [policy(("T", "MISSING"))])
            is False
        )


def test_idle_not_retained_with_selected_action(tmp_path):
    cgs, path = game(tmp_path, [["I", "A"], [0, "I,A"]], ["p"], [[0], [1]])
    before = deepcopy(cgs.graph)
    result = process_transition_matrix_data_fixed(cgs, path, [1], policy(("T", "A")))
    assert result[0][0] == 0 and result[0][1] == "A"
    assert cgs.graph == before
    assert memoryless("<{1},1>F p", path)["Satisfiability"] is True


def test_false_ltl_guard_does_not_override_previous_rule(tmp_path):
    from model_checker.algorithms.explicit.LTL.pruning import (
        process_transition_matrix_data,
    )

    cgs, path = game(tmp_path, [["I", "A"], [0, "I"]], ["p", "q"], [[1, 0], [0, 0]])
    result = process_transition_matrix_data(
        cgs, path, [1], policy(("p", "A"), ("q", "MISSING"), ("T", "I"))
    )
    assert result[0][0] == 0 and result[0][1] == "A"
    assert result[1][1] == "IDLE"


@pytest.mark.parametrize("name", ["G", "E", "AF"])
def test_temporal_looking_guard_names_are_boolean_atoms(tmp_path, name):
    _cgs, path = game(
        tmp_path, [["I", "A"], [0, "I"]], [name, "goal"], [[1, 0], [0, 1]]
    )
    answer = memoryless("<{1},2>F goal", path)
    assert answer.get("Satisfiability") is True, answer


def test_first_match_and_global_are_distinct_bounded_semantics(tmp_path):
    _cgs, path = game(
        tmp_path,
        [["I", "A", 0], [0, "I", "B"], [0, 0, "I"]],
        ["p", "q", "goal"],
        [[1, 1, 0], [0, 1, 0], [0, 0, 1]],
    )
    operational = memoryless("<{1},3>F goal", path)
    strict = memoryless("<{1},3>F goal", path, appropriateness="global")
    assert operational["Satisfiability"] is True, operational
    assert operational["Appropriateness"] == "first-match"
    assert strict["Satisfiability"] is False, strict
    assert strict["Appropriateness"] == "global"


@pytest.mark.parametrize("k,answer", [(1, False), (2, True), (3, True)])
def test_original_fixture_is_preserved(tmp_path, k, answer):
    _cgs, path = game(tmp_path, [[0, "a"], [0, "I"]], ["p"], [[0], [1]])
    # At k=1, no constant action works. p->I; T->a costs 2 under first-match.
    result = memoryless(f"<{{1}},{k}>F p", path)
    assert result["Satisfiability"] is answer, result


@pytest.mark.parametrize(
    "formula,answer",
    [
        ("<{1},1>X goal", False),
        ("<{1,2},2>X goal", True),
        ("<{1},2>(safe U goal)", False),
        ("<{1,2},2>(safe U goal)", True),
        ("<{1},1>G (!<{1},1>F goal)", True),
    ],
)
def test_public_opponent_and_nested_semantics(tmp_path, formula, answer):
    _cgs, path = adversarial(tmp_path)
    result = memoryless(formula, path)
    assert result.get("Satisfiability") is answer, result


def test_negation_and_distinct_existential_witnesses(tmp_path):
    _cgs, path = game(
        tmp_path,
        [["I", "A", "B"], [0, "I,A,B", 0], [0, 0, "I,A,B"]],
        ["p", "q"],
        [[0, 0], [1, 0], [0, 1]],
    )
    assert memoryless("(<{1},1>X p) && (<{1},1>X q)", path)["Satisfiability"] is True
    assert memoryless("!<{1},1>X p", path)["Satisfiability"] is False


def test_requested_bound_is_not_overwritten_by_witness_cost(tmp_path):
    _cgs, path = game(tmp_path, [["I", "A"], [0, "I,A"]], ["goal"], [[0], [1]])
    result = memoryless("<{1},5>F goal", path)
    assert result["Complexity Bound"] == 5
    assert result["Witness Complexity"] == 1
    assert result["res"] == "Result: {'s0', 's1'}"


def test_explicit_initial_only_query_does_not_claim_all_states(tmp_path):
    _cgs, path = game(
        tmp_path,
        [["I", "A", 0], [0, "I,A", 0], [0, 0, "I,A"]],
        ["goal"],
        [[0], [1], [0]],
    )
    full = memoryless("<{1},5>F goal", path)
    decision = memoryless("<{1},5>F goal", path, return_all_states=False)
    assert full["Satisfiability"] is decision["Satisfiability"] is True
    assert full["State Set Complete"] is True
    assert decision["State Set Complete"] is False
    assert "Satisfying States" not in decision
    assert decision["Satisfying Queried States"] == ["s0"]
    assert (
        decision["Search Statistics"]["Candidates Examined"]
        < full["Search Statistics"]["Candidates Examined"]
    )


@pytest.mark.performance
def test_exact_policy_deduplication_at_bound_five(tmp_path):
    _cgs, path = game(
        tmp_path,
        [["I", "A", 0], [0, "I,A", 0], [0, 0, "I,A"]],
        ["goal"],
        [[0], [1], [0]],
    )
    result = memoryless("<{1},5>F goal", path)
    stats = result["Search Statistics"]
    # Equal-labelled s0/s2 receive the same action. Only 2^2 behaviours exist.
    assert stats["Temporal Checks"] <= 4
    assert stats["Duplicate Policies Skipped"] > 0
    assert result["Satisfying States"] == ["s0", "s1"]


@pytest.mark.parametrize(
    "graph",
    [
        [["I", "I"], [0, "I"]],  # same joint has different targets
        [["II,AB", 0], [0, "II,AB"]],  # missing local Cartesian combinations
        [["ABC", 0], [0, "II"]],  # wrong compact arity
    ],
)
def test_memoryless_rejects_invalid_cgs(tmp_path, graph):
    n = 1 if graph[0][0] == "I" else 2
    _cgs, path = game(tmp_path, graph, ["goal"], [[0], [1]], n=n)
    result = memoryless("<{1},1>F goal", path)
    assert result.get("error", {}).get("type") == "model", result


@pytest.mark.parametrize(
    "formula", ["<{1},1>F goal", "!<{1},1>F goal", "<{1},0>G goal"]
)
def test_recall_missing_idle_is_model_error_before_shortcuts(tmp_path, formula):
    _cgs, path = game(tmp_path, [["I", 0], [0, "A"]], ["goal"], [[0], [0]])
    result = recall(formula, path)
    assert result.get("error", {}).get("type") == "model", result
    assert "Satisfiability" not in result


def test_recall_checks_idle_only_for_quantified_agents(tmp_path):
    _cgs, path = adversarial(tmp_path)  # Opponent 2 has no IDLE, and does not need it.
    answer = recall("<{1},1>G safe", path)
    assert answer["Satisfiability"] is True, answer
    assert answer["initial_state"] == "Initial state s0: True"


def test_recall_preparation_and_appropriateness_caches(tmp_path):
    from model_checker.algorithms.explicit.NatATL.Recall import recall_context

    _cgs, path = adversarial(tmp_path)
    with patch.object(
        recall_context, "prepare_cgs", wraps=recall_context.prepare_cgs
    ) as prepare:
        answer = recall("<{1},3>G (!<{1},3>F goal)", path)
        assert answer["Satisfiability"] is True, answer
        assert prepare.call_count == 1
    stats = answer["Search Statistics"]
    assert stats["Appropriateness Cache Hits"] > 0
    assert stats["Regex Compilations"] <= stats["Appropriateness Checks"]


def test_recall_result_bound_and_witness_cost_are_separate(tmp_path):
    _cgs, path = game(tmp_path, [[0, "I"], [0, "I"]], ["goal"], [[0], [1]])
    answer = recall("<{1},4>F goal", path)
    assert answer["Satisfiability"] is True
    assert answer["Complexity Bound"] == 4
    assert answer["Witness Complexity"] == 1


def test_unknown_ltl_guard_is_not_losing_candidate(tmp_path):
    cgs, path = game(tmp_path, [["I"]], ["goal"], [[0]])
    with pytest.raises(ValueError, match="condition"):
        ltl_pruning(cgs, path, [1], "AF goal", [policy(("unknown", "I"))])


def test_retired_unfolding_entry_fails_closed():
    from model_checker.algorithms.explicit.NatATL.Recall.solver import (
        solve_natatl_recall,
    )

    with pytest.raises(ValueError, match="retired"):
        solve_natatl_recall(1, {}, [], [], "AF p", [1], None, "unused")


def test_product_atom_helper_is_retained_as_supported_utility(tmp_path):
    from model_checker.algorithms.explicit.NatATL.Recall.recall_product import (
        build_validated_recall_product,
    )
    from model_checker.algorithms.explicit.NatATL.Recall.recall_temporal import (
        states_with_atom,
    )

    cgs, _path = game(tmp_path, [[0, "I"], [0, "I"]], ["goal"], [[0], [1]])
    product = build_validated_recall_product(cgs, [1], [policy(("T*", "IDLE"))])
    assert {s.state for s in states_with_atom(product, "goal")} == {"s1"}


def test_invalid_profile_is_not_nash_equilibrium(tmp_path):
    from model_checker.algorithms.explicit.NatATL.strategy_errors import (
        InadmissibleStrategy,
    )
    from model_checker.algorithms.explicit.SolutionConcepts.Solution_Concepts import (
        exists_nash,
        is_not_nash,
    )

    cgs, path = game(tmp_path, [["I"]], ["goal"], [[0]])
    bad = [policy(("T", "MISSING"))]
    args = (cgs, [1], "AF goal", bad, 1, {"actions_agent1": ["IDLE"]}, ["goal"])
    assert exists_nash(*args) is False
    with pytest.raises(InadmissibleStrategy):
        is_not_nash(path, *args)
