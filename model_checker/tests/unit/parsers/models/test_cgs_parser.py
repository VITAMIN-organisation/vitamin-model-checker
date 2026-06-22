"""Unit tests for CGS file parser: constants, parse_cgs_file, and public helpers."""

import warnings

import pytest

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS


def _minimal_cgs_lines():
    """Minimal valid CGS file as list of lines (no trailing newlines)."""
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
        "p",
        "Labelling",
        "1",
        "0",
        "Number_of_agents",
        "2",
    ]


@pytest.mark.unit
class TestCgsParserConstants:
    """SECTION_HEADERS and EXTENSION_SECTION_HEADERS are frozensets with expected content."""

    def test_section_headers_is_frozenset(self):
        assert isinstance(cgs_parser.SECTION_HEADERS, frozenset)

    def test_section_headers_contains_expected_keys(self):
        expected = {
            "Transition",
            "Unknown_Transition_by",
            "Name_State",
            "Initial_State",
            "Atomic_propositions",
            "Labelling",
            "Number_of_agents",
            "Agent_labels",
        }
        assert cgs_parser.SECTION_HEADERS == expected

    def test_extension_section_headers_is_frozenset(self):
        assert isinstance(cgs_parser.EXTENSION_SECTION_HEADERS, frozenset)

    def test_extension_section_headers_contains_expected_keys(self):
        expected = {
            "Costs_for_actions",
            "Costs_for_actions_split",
            "Transition_With_Costs",
            "Capacities",
            "Capacities_assignment",
            "Actions_for_capacities",
            "Clocks",
            "Clock_constraints",
            "Invariants",
        }
        assert cgs_parser.EXTENSION_SECTION_HEADERS == expected


@pytest.mark.unit
class TestParseCgsFile:
    """parse_cgs_file(lines, instance) fills CGS instance correctly."""

    def test_minimal_content_fills_instance(self):
        cgs = CGS()
        cgs_parser.parse_cgs_file(_minimal_cgs_lines(), cgs)

        assert len(cgs.states) == 2
        assert cgs.states[0] == "s0" and cgs.states[1] == "s1"
        assert cgs.initial_state == "s0"
        assert cgs.number_of_agents == 2
        assert cgs.get_number_of_agents() == 2
        assert cgs.get_agent_labels() == ["1", "2"]
        assert len(cgs.atomic_propositions) == 1
        assert cgs.atomic_propositions[0] == "p"
        assert len(cgs.graph) == 2
        assert len(cgs.matrix_prop) == 2
        assert cgs.actions is not None

    def test_agent_labels_section_parsed(self):
        lines = _minimal_cgs_lines()
        idx = next(i for i, line in enumerate(lines) if line == "Number_of_agents")
        lines = lines[: idx + 2] + ["Agent_labels", "Tianji Opponent"] + lines[idx + 2 :]

        cgs = CGS()
        cgs_parser.parse_cgs_file(lines, cgs)

        assert cgs.get_agent_labels() == ["Tianji", "Opponent"]
        assert cgs.agent_labels == ["Tianji", "Opponent"]

    def test_invalid_agent_label_raises(self):
        lines = _minimal_cgs_lines()
        idx = next(i for i, line in enumerate(lines) if line == "Number_of_agents")
        lines = lines[: idx + 2] + ["Agent_labels", "bad@label"] + lines[idx + 2 :]

        with pytest.raises(ValueError, match=r"Agent label 'bad@label' is invalid"):
            cgs_parser.parse_cgs_file(lines, CGS())

    def test_agent_labels_count_mismatch_fails_validation(self):
        lines = _minimal_cgs_lines()
        idx = next(i for i, line in enumerate(lines) if line == "Number_of_agents")
        lines = lines[: idx + 2] + ["Agent_labels", "OnlyOne"] + lines[idx + 2 :]

        cgs = CGS()
        cgs_parser.parse_cgs_file(lines, cgs)
        with pytest.raises(ValueError, match="Agent_labels has 1 label"):
            cgs.validate_model_structure()

    def test_invalid_atomic_proposition_name_raises(self):
        lines = _minimal_cgs_lines()
        for i, line in enumerate(lines):
            if line == "p":
                lines[i] = "1goal"
                break

        with pytest.raises(
            ValueError,
            match=r"Atomic proposition '1goal' is invalid",
        ):
            cgs_parser.parse_cgs_file(lines, CGS())

    def test_uppercase_atomic_proposition_name_is_accepted(self):
        lines = _minimal_cgs_lines()
        for i, line in enumerate(lines):
            if line == "p":
                lines[i] = "Goal"
                break

        cgs = CGS()
        cgs_parser.parse_cgs_file(lines, cgs)
        assert "Goal" in cgs.atomic_propositions

    def test_invalid_number_of_agents_raises(self):
        lines = _minimal_cgs_lines()
        for i, line in enumerate(lines):
            if line == "2" and i > 0 and lines[i - 1] == "Number_of_agents":
                lines = lines[:i] + ["not_an_int"] + lines[i + 1 :]
                break

        with pytest.raises(
            ValueError,
            match="Invalid value for Number_of_agents.*Expected a valid integer",
        ):
            cgs_parser.parse_cgs_file(lines, CGS())

    def test_extension_section_skipped(self):
        lines = _minimal_cgs_lines()
        insert_at = next(i for i, L in enumerate(lines) if L == "Atomic_propositions")
        lines = lines[:insert_at] + ["Capacities", "cap1"] + lines[insert_at:]

        cgs = CGS()
        cgs_parser.parse_cgs_file(lines, cgs)
        assert cgs.initial_state == "s0"
        assert cgs.number_of_agents == 2
        assert len(cgs.atomic_propositions) == 1

    def test_duplicate_section_warns(self):
        lines = _minimal_cgs_lines()
        idx = next(i for i, L in enumerate(lines) if L == "Initial_State")
        lines = lines[: idx + 1] + ["Initial_State", "s1"] + lines[idx + 2 :]

        cgs = CGS()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cgs_parser.parse_cgs_file(lines, cgs)

        assert any("Duplicate 'Initial_State'" in str(m.message) for m in w)
        assert cgs.initial_state == "s1"

    def test_empty_transition_yields_empty_graph(self):
        lines = [
            "Name_State",
            "s0",
            "Initial_State",
            "s0",
            "Atomic_propositions",
            "p",
            "Labelling",
            "1",
            "Number_of_agents",
            "1",
        ]
        cgs = CGS()
        cgs_parser.parse_cgs_file(lines, cgs)

        assert cgs.graph == []
        assert cgs.states is not None and len(cgs.states) == 1
        assert cgs.number_of_agents == 1


@pytest.mark.unit
class TestFilterLinesForCommonSections:
    """filter_lines_for_common_sections drops extension sections."""

    def test_drops_capacity_sections(self):
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
        to_skip = {"Transition", "Capacities"}
        filtered = cgs_parser.filter_lines_for_common_sections(lines, to_skip)

        assert "Capacities" not in filtered
        assert "cap1" not in filtered
        assert "Name_State" in filtered
        assert "Initial_State" in filtered

    def test_preserves_common_sections_when_nothing_skipped(self):
        lines = ["Transition", "0 1", "Name_State", "s0 s1"]
        filtered = cgs_parser.filter_lines_for_common_sections(lines, set())
        assert "Name_State" in [line.strip() for line in filtered]
        assert "s0 s1" in [line.strip() for line in filtered]


@pytest.mark.unit
class TestProcessTransitionRow:
    """process_transition_row builds row and collects actions."""

    def test_zero_becomes_int(self):
        actions = []
        row = cgs_parser.process_transition_row(["0", "1"], actions)
        assert row == [0, "1"]
        assert "1" in actions

    def test_actions_extended(self):
        actions = []
        cgs_parser.process_transition_row(["a,b", "0"], actions)
        assert "a" in actions and "b" in actions


@pytest.mark.unit
class TestProcessLabellingRow:
    """process_labelling_row accepts 0/1 and rejects other values."""

    def test_binary_accepted(self):
        row = cgs_parser.process_labelling_row(["1", "0"])
        assert row == [1, 0]

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid labelling matrix value"):
            cgs_parser.process_labelling_row(["1", "2"])
        with pytest.raises(ValueError, match="Invalid labelling matrix value"):
            cgs_parser.process_labelling_row(["x"])
