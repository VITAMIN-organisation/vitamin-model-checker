"""Reading a CGS model file: what is loaded, and which broken files are refused with which message."""

import warnings

import pytest

from model_checker.parsers.game_structures.cap_cgs.cap_cgs import CapCGS
from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
    load_costcgs_from_content,
)


def _lines(*, props="p", agents="2", extra=()):
    """A two-state CGS file as lines; `extra` goes after Number_of_agents."""
    return [
        "Transition",
        "0 1",
        "1 0",
        "Unknown_Transition_by",
        "Name_State",
        "s0 s1",
        "Initial_State",
        "s0",
        "Atomic_propositions",
        props,
        "Labelling",
        "1",
        "0",
        "Number_of_agents",
        agents,
        *extra,
    ]


def _two_state(**overrides):
    params = {
        "transitions": [["III", "0"], ["0", "III"]],
        "state_names": ["s0", "s1"],
        "initial_state": "s0",
        "prop_names": ["p"],
        "labelling": [["1"], ["0"]],
        "num_agents": 1,
    }
    params.update(overrides)
    return build_cgs_model_content(**params)


@pytest.mark.unit
def test_every_section_reaches_the_model():
    """States, initial state, agents, default agent labels, propositions, graph and labelling."""
    cgs = CGS()
    cgs_parser.parse_cgs_file(_lines(), cgs)
    assert cgs.states.tolist() == ["s0", "s1"]
    assert cgs.initial_state == "s0"
    assert cgs.get_number_of_agents() == 2
    assert cgs.get_agent_labels() == ["1", "2"]
    assert list(cgs.atomic_propositions) == ["p"]
    assert [list(row) for row in cgs.graph] == [[0, "1"], ["1", 0]]
    assert [list(row) for row in cgs.matrix_prop] == [[1], [0]]


@pytest.mark.unit
def test_agent_labels_replace_the_numbers():
    """`Agent_labels` names the agents in order."""
    cgs = CGS()
    cgs_parser.parse_cgs_file(_lines(extra=["Agent_labels", "Tianji Opponent"]), cgs)
    assert cgs.get_agent_labels() == ["Tianji", "Opponent"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("lines", "message"),
    [
        (
            _lines(extra=["Agent_labels", "bad@label"]),
            "Agent label 'bad@label' is invalid",
        ),
        (_lines(props="1goal"), "Atomic proposition '1goal' is invalid"),
        (_lines(props="Goal"), "Atomic proposition 'Goal' is invalid"),
        (
            _lines(props="true"),
            "Atomic proposition 'true' clashes with reserved keyword",
        ),
        (
            _lines(props="false"),
            "Atomic proposition 'false' clashes with reserved keyword",
        ),
        (
            _lines(props="True"),
            "Atomic proposition 'True' clashes with reserved keyword",
        ),
        (
            _lines(props="FALSE"),
            "Atomic proposition 'FALSE' clashes with reserved keyword",
        ),
        (
            _lines(agents="two"),
            "Invalid value for Number_of_agents.*Expected a valid integer",
        ),
    ],
)
def test_bad_value_is_refused_by_name(lines, message):
    """A bad label, proposition or agent count fails while parsing, naming the value."""
    with pytest.raises(ValueError, match=message):
        cgs_parser.parse_cgs_file(lines, CGS())


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("Goal", "Capacity 'Goal' is invalid"),
        ("Next", "Capacity 'Next' clashes with reserved keyword"),
        ("with", "Capacity 'with' clashes with reserved keyword"),
        ("kcap", "Capacity 'kcap' clashes with reserved keyword"),
        ("kcap42", "Capacity 'kcap42' spells the CapATL knowledge operator"),
    ],
)
def test_capacity_name_follows_the_name_rule(name, message):
    """A CapATL formula cannot name `Goal` or `with`, so the model may not declare them."""
    lines = _lines(extra=["Capacities", f"c {name}"])
    with pytest.raises(ValueError, match=message):
        CapCGS()._parse_lines(lines)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "message"),
    [("kcap", "clashes with reserved keyword"), ("kcap1", "spells the CapATL")],
)
def test_capcgs_proposition_kcap_is_refused(name, message):
    """A CapCGS model is read by CapATL, which reads `kcap1` as its operator and
    reserves `kcap`; a plain CGS keeps both, and `kcap1x` is a name everywhere."""
    lines = _lines(props=name, extra=["Capacities", "c"])
    with pytest.raises(ValueError, match=f"Atomic proposition '{name}' {message}"):
        CapCGS()._parse_lines(lines)
    cgs = CGS()
    cgs_parser.parse_cgs_file(lines, cgs)
    assert list(cgs.atomic_propositions) == [name]
    capcgs = CapCGS()
    capcgs._parse_lines(_lines(props="kcap1x", extra=["Capacities", "c"]))
    assert list(capcgs.atomic_propositions) == ["kcap1x"]


@pytest.mark.unit
def test_agent_label_count_must_match_the_agents():
    """One label for two agents is caught by structure validation."""
    cgs = CGS()
    cgs_parser.parse_cgs_file(_lines(extra=["Agent_labels", "OnlyOne"]), cgs)
    with pytest.raises(ValueError, match="Agent_labels has 1 label"):
        cgs.validate_model_structure()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("file_name", "message"),
    [
        ("invalid/missing_transition.txt", "Transition matrix is missing or empty"),
        ("invalid/missing_name_state.txt", "Model must have at least one state"),
        ("invalid/missing_initial_state.txt", "Initial_State section is missing"),
        (
            "invalid/invalid_initial_state.txt",
            "Initial state 's2' not found in state list",
        ),
        (
            "invalid/missing_number_of_agents.txt",
            "Number_of_agents is missing or empty",
        ),
        (
            "edge_cases/empty_number_of_agents.txt",
            "Number_of_agents is missing or empty",
        ),
        ("invalid/malformed_labelling.txt", "Labelling row 0 has 1 column"),
        ("invalid/wrong_transition_dimensions.txt", "Transition row 0 has 2 column"),
    ],
)
def test_broken_file_is_refused_on_load(test_data_dir, file_name, message):
    """Each missing section, unknown initial state or ragged matrix gives its own message."""
    with pytest.raises(ValueError, match=message):
        CGS().read_file(str(test_data_dir / "tests" / file_name))


@pytest.mark.unit
@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"transitions": [["III", "0"], ["0", "III"], ["III", "0"]]},
            "Transition matrix",
        ),
        (
            {
                "labelling": [["1", "0"], ["0", "1"], ["1", "1"]],
                "prop_names": ["p", "q"],
            },
            "Labelling",
        ),
        ({"transitions": [["A", "0"], ["0", "0"]]}, "no outgoing transitions"),
    ],
)
def test_matrix_size_or_deadlock_is_refused(temp_file, overrides, message):
    """A matrix with a row per state too many, or a state with no move out."""
    with pytest.raises(ValueError, match=message):
        load_cgs_from_content(temp_file, _two_state(**overrides))


@pytest.mark.unit
def test_declared_propositions_need_a_labelling(temp_file):
    """Without Labelling every proposition would be false everywhere, unnoticed."""
    content = _two_state().replace("Labelling\n1\n0\n", "")
    with pytest.raises(ValueError, match="Labelling.*'p'"):
        load_cgs_from_content(temp_file, content)


@pytest.mark.unit
@pytest.mark.parametrize("value", ["2", "abc"])
def test_non_binary_label_is_refused_with_its_position(temp_file, value):
    """A label must be 0 or 1; the message gives the value, row and column."""
    content = _two_state().replace("Labelling\n1\n0", f"Labelling\n1\n{value}")
    with pytest.raises(
        ValueError,
        match=f"Invalid labelling matrix value.*{value}.*row 1, column 0",
    ):
        load_cgs_from_content(temp_file, content)


@pytest.mark.unit
def test_state_names_may_hold_dashes_and_dots(temp_file):
    """`state-1` and `state.2` are state names, not syntax."""
    names = ["state_0", "state-1", "state.2"]
    transitions = [["III" if i == j else "0" for j in range(3)] for i in range(3)]
    content = _two_state(
        state_names=names,
        initial_state="state_0",
        labelling=[["1"], ["0"], ["1"]],
        transitions=transitions,
    )
    assert load_cgs_from_content(temp_file, content).states.tolist() == names


@pytest.mark.unit
def test_duplicate_section_warns_and_the_last_one_wins(temp_file):
    """A repeated header is a likely typo, so it warns; the later value is kept."""
    content = _two_state().replace(
        "Number_of_agents\n1", "Number_of_agents\n2\nNumber_of_agents\n3"
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cgs = load_cgs_from_content(temp_file, content)
    assert [str(w.message) for w in caught] == [
        str(caught[0].message)
    ] and "Duplicate 'Number_of_agents'" in str(caught[0].message)
    assert cgs.get_number_of_agents() == 3


@pytest.mark.unit
def test_extension_section_is_skipped_by_the_plain_cgs_parser():
    """A Capacities section inside a CGS file does not shift the sections after it."""
    lines = _lines()
    at = lines.index("Atomic_propositions")
    cgs = CGS()
    cgs_parser.parse_cgs_file(lines[:at] + ["Capacities", "cap1"] + lines[at:], cgs)
    assert list(cgs.atomic_propositions) == ["p"]
    assert cgs.initial_state == "s0"


@pytest.mark.unit
def test_common_section_filter_drops_whole_sections():
    """Extension parsers drop a section header and all its rows, and keep the rest in order."""
    lines = [
        "Transition",
        "0 1",
        "Name_State",
        "s0 s1",
        "Capacities",
        "cap1",
        "Initial_State",
        "s0",
    ]
    assert cgs_parser.filter_lines_for_common_sections(
        lines, {"Transition", "Capacities"}
    ) == ["Name_State", "s0 s1", "Initial_State", "s0"]


@pytest.mark.unit
def test_number_of_agents_accessor_fails_when_unset():
    """A model never loaded has no agent count; asking for it is an error, not 0."""
    with pytest.raises(ValueError, match="Number_of_agents is missing"):
        CGS().get_number_of_agents()


@pytest.mark.unit
def test_cost_lines_do_not_overwrite_the_initial_state(temp_file):
    """Cost lines name states too; they must not be read as the Initial_State section."""
    content = _two_state(costs_for_actions={"I*": "s0$0:0", "**": "s1$0:0"})
    cost_cgs = load_costcgs_from_content(temp_file, content)
    assert cost_cgs.initial_state == "s0"


@pytest.mark.unit
def test_capcgs_reads_capacities_and_keeps_the_initial_state(test_data_dir):
    """The capacity sections fill their tables; the initial state stays q0."""
    cap = CapCGS()
    cap.read_file(
        str(test_data_dir / "capCGS/CAPATL/capatl_3agents_3states_example.txt")
    )
    assert cap.initial_state == "q0"
    assert cap.capacities_list == ["c", "cap", "cop"]
    assert cap.action_capacities == [["c", "A", "B"], ["cap", "A"], ["cop", "B"]]
    assert cap.get_capacities_assignment() == [
        ["1", "c"],
        ["2", "c"],
        ["3", "cap", "cop"],
    ]
