"""Every registered logic answers bad input with an error result instead of a verdict or an exception.

Each logic runs on one of its fixtures with a valid formula, a formula cut short,
an undeclared proposition `zz`, and an agent the model does not have. A logic
added to the vitamin.benchmarks entry points without a row here fails the first
test.
"""

from importlib.metadata import entry_points
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_F = f"{_HERE.parents[1] / 'fixtures'}/"
_ICTL = str(_HERE / "ictl" / "fixtures" / "experiment_2x3.txt")

# logic -> (model file, valid formula, formula cut short, undeclared name, agent out of range)
_CASES = {
    "ATL": (
        _F + "CGS/ATL/atl_2agents_4states_simple.txt",
        "<1>F p",
        "<1>F",
        "<1>F zz",
        "<3>F p",
    ),
    "ATLF": (
        _F + "CGS/ATL/atl_2agents_4states_simple.txt",
        "<1>F p",
        "<1>F",
        "<1>F zz",
        "<3>F p",
    ),
    "ATL_STAR": (
        _F + "CGS/ATL/atl_2agents_4states_simple.txt",
        "<<1>> F p",
        "<<1>> F",
        "<<1>> F zz",
        "<<3>> F p",
    ),
    "CTL": (_F + "CGS/ATL/atl_2agents_4states_simple.txt", "EF p", "EF", "EF zz", None),
    "LTL": (_F + "CGS/LTL/ltl_1agent_3states_minimal.txt", "F p", "F", "F zz", None),
    "CapATL": (
        _F + "capCGS/CAPATL/capatl_3agents_3states_example.txt",
        "<{1}>F g",
        "<{1}>F",
        "<{1}>F zz",
        "<{4}>F g",
    ),
    "COTL": (
        _F + "ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt",
        "<1><2>F q",
        "<1><2>F",
        "<1><2>F zz",
        "<9><2>F q",
    ),
    "IATL": (
        _F + "CGS/IATL/iatl_2agents_2states_minimal.txt",
        "<1>F p",
        "<1>F",
        "<1>F zz",
        "<3>F p",
    ),
    "ICTL": (_ICTL, "EF e", "EF", "EF zz", None),
    "NatATL": (
        _F + "CGS/NATATL/natatl_1agent_4states_standard.txt",
        "<{1}, 1>F b",
        "<{1}, 1>F",
        "<{1}, 1>F zz",
        "<{2}, 1>F b",
    ),
    "NatATL_Recall": (
        _F + "CGS/NATATL/natatl_1agent_4states_standard.txt",
        "<{1}, 1>F b",
        "<{1}, 1>F",
        "<{1}, 1>F zz",
        "<{2}, 1>F b",
    ),
    "NatATLF": (
        _F + "CGS/NATATL/natatl_1agent_4states_standard.txt",
        "<{1}, 1>F b",
        "<{1}, 1>F",
        "<{1}, 1>F zz",
        "<{2}, 1>F b",
    ),
    "NatSL": (
        _F + "CGS/NatSL/bounded_controller.txt",
        "E{1}x: (x, 1) F goal",
        "E{1}x: (x, 1) F",
        "E{1}x: (x, 1) F zz",
        None,
    ),
    "OATL": (
        _F + "costCGS/OATL/oatl_3agents_medium_6states_costs.txt",
        "<1><5>F r",
        "<1><5>F",
        "<1><5>F zz",
        "<4><5>F r",
    ),
    "OL": (
        _F + "costCGS/OL/ol_2agents_medium_6states_costs.txt",
        "<J5>F r",
        "<J5>F",
        "<J5>F zz",
        None,
    ),
    "RABATL": (
        _F + "costCGS/RABATL/rabatl_3agents_medium_6states_costs.txt",
        "<1><5>F r",
        "<1><5>F",
        "<1><5>F zz",
        "<4><5>F r",
    ),
    "RBATL": (
        _F + "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt",
        "<1><5>F r",
        "<1><5>F",
        "<1><5>F zz",
        "<4><5>F r",
    ),
    "TCTL": (_F + "timedCGS/tctl_tol_minimal.txt", "EF p", "EF", "EF zz", None),
    "TOL": (_F + "timedCGS/tol_cost_2states.txt", "{J1}F p", "{J1}F", "{J1}F zz", None),
    "Wallet_ATL": (
        _F + "WalletCGS/WALLET_ATL/wallet_1agent_2states.txt",
        "<<1>>F p",
        "<<1>>F",
        "<<1>>F zz",
        "<<2>>F p",
    ),
}

_CHECKERS = {entry.name: entry for entry in entry_points(group="vitamin.benchmarks")}


def _check(logic: str, column: int):
    model, *formulas = _CASES[logic]
    return _CHECKERS[logic].load()(formulas[column], model)


@pytest.mark.integration
def test_every_registered_logic_has_a_row():
    """A new logic must say how it reports bad input."""
    assert set(_CHECKERS) == set(_CASES)


@pytest.mark.integration
@pytest.mark.parametrize("logic", sorted(_CASES))
def test_valid_formula_gives_a_verdict(logic):
    """The row's valid formula is checked without error, so the error rows below test the input, not the fixture."""
    result = _check(logic, 0)
    assert "error" not in result, result
    assert result["initial_state"].startswith("Initial state")


@pytest.mark.integration
@pytest.mark.parametrize("logic", sorted(set(_CASES) - {"NatSL"}))
def test_formula_cut_short_is_a_syntax_error(logic):
    """An operator with no operand is a syntax error (NatSL reports its goal grammar as validation)."""
    assert _check(logic, 1)["error"]["type"] == "syntax"


@pytest.mark.integration
@pytest.mark.parametrize("logic", sorted(_CASES))
def test_undeclared_proposition_is_an_error(logic):
    """A typo in a name must not be read as a proposition that is false everywhere (NatSL calls it validation)."""
    expected = "validation" if logic == "NatSL" else "semantic"
    assert _check(logic, 2)["error"]["type"] == expected


@pytest.mark.integration
@pytest.mark.parametrize("logic", sorted(_CASES))
def test_undeclared_proposition_is_named_in_the_message(logic):
    """The user sees which name is wrong."""
    assert "'zz'" in _check(logic, 2)["error"]["message"]


_CHECKED_THROUGH_CTL = {
    "LTL": "F q",
    "NatATL": "<{1}, 2>F q",
    "NatATL_Recall": "<{1}, 2>F q",
    "NatATLF": "<{1}, 2>F q",
}


@pytest.mark.integration
@pytest.mark.parametrize("logic", sorted(_CHECKED_THROUGH_CTL))
@pytest.mark.parametrize("name", ["A", "E", "AF"])
def test_proposition_the_ctl_parser_reads_as_an_operator_is_refused(
    temp_file, logic, name
):
    """CTL reads A and E as quantifiers, so such a name must not give a verdict;
    a name starts lowercase, so the model is refused on load."""
    model = temp_file(
        f"Transition\nI a\nI a\nName_State\ns0 s1\nInitial_State\ns0\n"
        f"Atomic_propositions\n{name} q\nLabelling\n0 0\n1 1\nNumber_of_agents\n1\n"
    )
    error = _CHECKERS[logic].load()(_CHECKED_THROUGH_CTL[logic], model)["error"]
    assert error["type"] == "semantic"
    assert f"Atomic proposition '{name}' is invalid" in error["message"]


@pytest.mark.integration
@pytest.mark.parametrize("logic", sorted(set(_CASES) - {"NatSL"}))
def test_undeclared_proposition_under_negation_is_an_error(logic):
    """`!zz` is true everywhere if zz is read as false, so a nested typo flips the verdict."""
    model, _, _, undeclared, _ = _CASES[logic]
    result = _CHECKERS[logic].load()(undeclared.replace("zz", "(!zz)"), model)
    assert result["error"]["type"] == "semantic"


@pytest.mark.integration
@pytest.mark.parametrize(
    "logic", sorted(logic for logic, case in _CASES.items() if case[4])
)
def test_agent_outside_the_model_is_a_syntax_error(logic):
    """Coalitions are checked against the model's agent count before solving."""
    assert _check(logic, 3)["error"]["type"] == "syntax"
