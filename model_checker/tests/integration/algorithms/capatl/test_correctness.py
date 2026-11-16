"""CapATL model checking: capacity constraints, error cases."""

import re
from pathlib import Path

import pytest

from model_checker.algorithms.explicit.CapATL.CapATL import (
    _core_capatl_checking,
    model_checking,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.tests.helpers.capatl_reference import CapATLReference
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    load_test_model,
)
from model_checker.tests.helpers.synthetic_models import (
    generate_capcgs_linear_chain_model,
    generate_random_capcgs_model,
)

RANDOM_MODEL_FORMULAS = [
    "<{1}>X p",
    "<{1,2}>X (p && !q)",
    "<{1}>F p",
    "<{2}>p U q",
    "<{1,2}>p U q",
    "<{1}>G p",
    "<{2}>p R q",
    "<{1,3}>G !q",
    "<{1}>F <{2}>G p",
    "!<{1}>(p U <{2}>X q)",
    "<{1}>X K2(1 is ca)",
    "<{1}>(p U K2(1 is ca and !(2 is cb)))",
]


@pytest.mark.unit
@pytest.mark.model_checking
class TestCapATLErrorHandling:
    """Test CapATL error handling for invalid inputs."""

    def test_capatl_invalid_formula_syntax(self, capatl_model):
        """Test CapATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", capatl_model.filename)
        assert "error" in result

    def test_capatl_nonexistent_atomic_proposition(self, capatl_model):
        """Test CapATL with non-existent atomic proposition."""
        result = _core_capatl_checking(capatl_model, "<{1,2}>F nonexistent")
        assert "error" in result
        assert result["error"]["type"] == "semantic"

    def test_capatl_invalid_coalition(self, capatl_model):
        """Test CapATL with invalid coalition (agent number out of range)."""
        result = _core_capatl_checking(capatl_model, "<{99}>F p")
        assert "error" in result

    def test_capatl_formula_bound_rejected(self, capatl_model):
        """Formula bound <{A}, k> is rejected; CapATL has no numeric k."""
        result = _core_capatl_checking(capatl_model, "<{1,2},5>F p")
        assert "error" in result

    def test_capatl_unknown_capacity_in_knowledge(self, capatl_model):
        """A capacity the model does not declare is named in the error."""
        result = _core_capatl_checking(capatl_model, "<{1}>F K2(3 is zzz)")
        assert result["error"]["type"] == "semantic"
        assert "'zzz'" in result["error"]["message"]

    def test_capatl_empty_coalition_rejected(self, capatl_model):
        """Empty coalition modality is invalid."""
        result = _core_capatl_checking(capatl_model, "<>F p")
        assert "error" in result

    def test_capatl_assignment_cell_other_than_0_or_1(self, test_data_dir, temp_file):
        """A 2 in Capacities_assignment is named, not read as 0."""
        fixture = test_data_dir / "capCGS/CAPATL/capatl_3agents_3states_example.txt"
        content = fixture.read_text().replace("0 1 1\n", "0 2 1\n")
        result = model_checking("<{1}>X g", temp_file(content))
        assert result["error"]["type"] == "model"
        assert "'2' (agent 3, capacity cap)" in result["error"]["message"]


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestCapATLSemantics:
    """Exact winning states on the 3-agent capacity fixture."""

    def test_capatl_eventually_winning_states(self, capatl_model):
        """Agent 1 can force g from every state (q0 via B**, q1 via q0, q2 already)."""
        result = _core_capatl_checking(capatl_model, "<{1}>F g")
        assert "error" not in result
        assert extract_states_from_result(result) == {"q0", "q1", "q2"}
        assert ": True" in result.get("initial_state", "")

    @pytest.mark.parametrize("name", ["pa", "p1", "g2"])
    def test_capatl_proposition_name_with_a_digit(self, name, test_data_dir, temp_file):
        """A name such as p1 is a proposition like pa, not a capacity reference; with g
        renamed, <{1}>F name gives the states of <{1}>F g."""
        fixture = test_data_dir / "capCGS/CAPATL/capatl_3agents_3states_example.txt"
        content = re.sub(r"^g a$", f"{name} a", fixture.read_text(), flags=re.M)
        result = model_checking(f"<{{1}}>F {name}", temp_file(content))
        assert "error" not in result
        assert extract_states_from_result(result) == {"q0", "q1", "q2"}

    def test_capatl_next_winning_states(self, capatl_model):
        """X g holds at q0 (B** to q2) and at q2 (self-loop), not at q1."""
        result = _core_capatl_checking(capatl_model, "<{1}>X g")
        assert "error" not in result
        assert extract_states_from_result(result) == {"q0", "q2"}
        assert ": True" in result.get("initial_state", "")

    def test_capatl_globally_only_goal(self, capatl_model):
        """G g holds only where g already holds (q2)."""
        result = _core_capatl_checking(capatl_model, "<{1}>G g")
        assert "error" not in result
        assert extract_states_from_result(result) == {"q2"}
        assert ": False" in result.get("initial_state", "")

    @pytest.mark.parametrize(
        "formula,expected",
        [
            ("<{3}>X g", {"q2"}),
            ("<{1,2}>X g", {"q0", "q2"}),
            ("<{1,2,3}>X g", {"q0", "q1", "q2"}),
            ("<{1}>a U g", {"q0", "q1", "q2"}),
            ("<{3}>a U g", {"q2"}),
            ("<{1,3}>a R g", {"q2"}),
            ("<{1,2}>F g", {"q0", "q1", "q2"}),
            ("<{1,2}>G a", {"q0", "q1", "q2"}),
            ("K1(1 is c)", {"q0", "q1", "q2"}),
            ("K3(3 is cap)", set()),
            ("<{1,2,3}>X K2(3 is cap)", {"q1"}),
            ("<{1,2}>F (K2(3 is cap) || K2(3 is cop))", {"q0", "q1"}),
            ("<{1}>F (K1(3 is cap) || K1(3 is cop))", set()),
        ],
    )
    def test_capatl_hand_computed_states(self, capatl_model, formula, expected):
        """Hand-computed: agent 3 may answer with either capacity, and only 2 learns which."""
        result = _core_capatl_checking(capatl_model, formula)
        assert extract_states_from_result(result) == expected

    def test_capatl_word_connectives(self, capatl_model):
        """`not` and `and` give the same states as `!` and `&&`."""
        negated = _core_capatl_checking(capatl_model, "not <{1}>X g")
        conjunction = _core_capatl_checking(capatl_model, "<{1}>X (g and a)")
        assert extract_states_from_result(negated) == {"q1"}
        assert extract_states_from_result(conjunction) == {"q0", "q2"}

    def test_capatl_pipe_separated_labels(self, test_data_dir, temp_file):
        """`A|A|A` is read like `AAA`."""
        fixture = test_data_dir / "capCGS/CAPATL/capatl_3agents_3states_example.txt"
        content = fixture.read_text().replace(
            "AAB,ABA 0 AAA,ABB", "A|A|B,A|B|A 0 A|A|A,A|B|B"
        )
        result = model_checking("<{1,2,3}>X g", temp_file(content))
        assert extract_states_from_result(result) == {"q0", "q1", "q2"}

    @pytest.mark.parametrize(
        "old,new,named",
        [
            ("cop B\n", "", "Capacity 'cop' of agent 3"),
            ("1 0 0\n0 1 1\n", "1 0 0\n0 0 0\n", "Agent 3 has no capacity"),
            ("1 0 0\n0 1 1\n", "1 0 0\n", "has 2 row(s); expected 3"),
        ],
    )
    def test_capatl_capacity_errors_name_the_part(
        self, test_data_dir, temp_file, old, new, named
    ):
        """A capacity with no action line, or an agent with no capacity, is named."""
        fixture = test_data_dir / "capCGS/CAPATL/capatl_3agents_3states_example.txt"
        result = model_checking(
            "<{1}>X g", temp_file(fixture.read_text().replace(old, new))
        )
        assert "Model structure validation failed" in result["error"]["message"]
        assert named in result["error"]["message"]

    def test_capatl_one_capacity_for_the_whole_strategy(self, test_data_dir):
        """Agent 2 needs A in sL and B in sR; no capacity of 2 allows both."""
        cgs = load_test_model(
            test_data_dir, "capCGS/CAPATL/capatl_one_capacity_per_strategy.txt"
        )
        alone = _core_capatl_checking(cgs, "<{2}>(!lost U goal)")
        with_one = _core_capatl_checking(cgs, "<{1,2}>(!lost U goal)")
        assert extract_states_from_result(alone) == {"goal", "sL", "sR"}
        assert extract_states_from_result(with_one) == {"goal", "s0", "sL", "sR"}

    @pytest.mark.parametrize("seed", range(30))
    def test_capatl_agrees_with_brute_force(self, seed, temp_file):
        """Every state the depth-4 brute-force search settles gets the same answer."""
        num_agents = 2 + seed % 2
        path = temp_file(
            generate_random_capcgs_model(seed, 2 + (seed // 2) % 2, num_agents)
        )
        cgs = load_test_model(Path(path).parent, Path(path).name)
        parser = FormulaParserFactory.get_parser_instance("CapATL")
        brute_force = CapATLReference(cgs, depth=4)
        for formula in RANDOM_MODEL_FORMULAS:
            if "3" in formula and num_agents < 3:
                continue
            reference = brute_force.satisfying_states(
                parser.parse(formula, n_agent=num_agents)
            )
            states = extract_states_from_result(_core_capatl_checking(cgs, formula))
            for state, value in reference.items():
                if value is not None:
                    assert (state in states) == value, (formula, state)

    def test_capatl_synthetic_linear_chain(self, temp_file):
        """<{1}>F p holds in every state of a 4-state synthetic capCGS chain."""
        content = generate_capcgs_linear_chain_model(
            num_states=4, num_agents=2, prop_names=["p"]
        )
        model_path = temp_file(content)
        result = model_checking("<{1}>F p", model_path)
        assert "error" not in result, result
        assert extract_states_from_result(result) == {"s0", "s1", "s2", "s3"}
        assert ": True" in result.get("initial_state", "")
