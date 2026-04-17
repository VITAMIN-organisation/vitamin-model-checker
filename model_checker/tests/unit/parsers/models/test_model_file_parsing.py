"""Model file parsing: missing sections, malformed matrices, labelling, extensions, robustness."""

import warnings

import pytest

from model_checker.parsers.game_structures.cap_cgs.cap_cgs import capCGS
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
    load_costcgs_from_content,
    load_test_model,
)


def _base_content(
    transitions=None,
    state_names=None,
    initial_state="s0",
    prop_names=None,
    labelling=None,
    num_agents=1,
):
    if transitions is None:
        transitions = [["III", "0"], ["0", "III"]]
    if state_names is None:
        state_names = ["s0", "s1"]
    if prop_names is None:
        prop_names = ["p"]
    if labelling is None:
        labelling = [["1"], ["0"]]
    return build_cgs_model_content(
        transitions=transitions,
        state_names=state_names,
        initial_state=initial_state,
        prop_names=prop_names,
        labelling=labelling,
        num_agents=num_agents,
    )


def _assert_duplicate_warning(warnings_list, section_name, expected_count=1):
    assert len(warnings_list) == expected_count
    assert issubclass(warnings_list[0].category, UserWarning)
    assert f"Duplicate '{section_name}'" in str(warnings_list[0].message)


@pytest.mark.unit
class TestMissingSectionsAndMalformedMatrices:
    """Missing sections and malformed transition/labelling matrices."""

    @pytest.mark.parametrize(
        "file_name, expectation, error_msg",
        [
            ("missing_transition.txt", lambda p: len(p.states) > 0, None),
            (
                "missing_number_of_agents.txt",
                lambda p: p.number_of_agents == "",
                "Number_of_agents is missing",
            ),
        ],
    )
    def test_missing_sections_handling(
        self, test_data_dir, file_name, expectation, error_msg
    ):
        parser = load_test_model(test_data_dir, f"invalid/{file_name}")
        if error_msg:
            with pytest.raises(ValueError, match=error_msg):
                parser.get_number_of_agents()
        else:
            assert expectation(parser)
            if hasattr(parser, "graph"):
                assert parser.graph is not None

    @pytest.mark.parametrize(
        "file_name, match", [("malformed_labelling.txt", "inhomogeneous")]
    )
    def test_malformed_matrices_raise_errors(self, test_data_dir, file_name, match):
        parser = CGS()
        file_path = test_data_dir / "tests" / "invalid" / file_name
        with pytest.raises(ValueError, match=match):
            parser.read_file(str(file_path))


@pytest.mark.unit
class TestLabellingValidation:
    """Labelling matrix: non-binary rejection and error message content."""

    @pytest.mark.parametrize("invalid_value", ["2", "abc"])
    def test_labelling_rejects_non_binary(self, temp_file, invalid_value):
        content = _base_content(labelling=[["1"], ["1"]])
        content = content.replace("Labelling\n1\n1", f"Labelling\n1\n{invalid_value}")
        with pytest.raises(
            ValueError,
            match=f"Invalid labelling matrix value.*{invalid_value}.*row 1, column 0",
        ):
            load_cgs_from_content(temp_file, content)

    @pytest.mark.parametrize(
        "labelling, replacement, expected_value, expected_row, expected_col",
        [
            (
                [["1", "0"], ["0", "1"], ["1", "1"]],
                "Labelling\n1 0\n0 2\n1 1",
                "2",
                "row 1",
                "column 1",
            ),
        ],
    )
    def test_labelling_error_includes_location(
        self,
        temp_file,
        labelling,
        replacement,
        expected_value,
        expected_row,
        expected_col,
    ):
        base = _base_content(
            state_names=["s0", "s1", "s2"][: len(labelling)],
            prop_names=["p", "q"][: len(labelling[0])],
            labelling=labelling,
        )
        orig = "\n".join(" ".join(row) for row in labelling)
        content = base.replace(f"Labelling\n{orig}", replacement)
        with pytest.raises(ValueError) as exc_info:
            load_cgs_from_content(temp_file, content)
        msg = str(exc_info.value)
        assert expected_value in msg
        assert "row" in msg.lower() or expected_row in msg
        assert "column" in msg.lower() or expected_col in msg
        assert "binary" in msg.lower() or "0 or 1" in msg


@pytest.mark.unit
class TestSpecialCharactersAndDuplicateSections:
    """State names with special characters; duplicate sections (warning, last wins)."""

    @pytest.mark.parametrize(
        "state_names, initial_state, labelling",
        [(["state_0", "state-1", "state.2"], "state_0", [["1"], ["0"], ["1"]])],
    )
    def test_state_names_special_characters(
        self, temp_file, state_names, initial_state, labelling
    ):
        content = _base_content(
            state_names=state_names,
            initial_state=initial_state,
            labelling=labelling,
        )
        parser = load_cgs_from_content(temp_file, content)
        for name in state_names:
            assert name in parser.states
        assert len(parser.states) == len(state_names)

    @pytest.mark.parametrize(
        "section_name, content, attr_name, expected, is_method",
        [
            (
                "Number_of_agents",
                """Transition
III 0
0 III
Name_State
s0 s1
Initial_State
s0
Atomic_propositions
p
Labelling
1
0
Number_of_agents
2
Number_of_agents
3
""",
                "get_number_of_agents",
                3,
                True,
            ),
        ],
    )
    def test_duplicate_section_warns(
        self, temp_file, section_name, content, attr_name, expected, is_method
    ):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            parser = load_cgs_from_content(temp_file, content)
        _assert_duplicate_warning(w, section_name)
        attr = getattr(parser, attr_name)
        value = attr() if is_method else attr
        assert value == expected


@pytest.mark.unit
class TestExtensionSectionInitialState:
    """Cost/cap extension sections must not overwrite Initial_State."""

    def test_costcgs_initial_state_not_overwritten_by_costs(self, temp_file):
        content = build_cgs_model_content(
            transitions=[["III", "0"], ["0", "III"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            prop_names=["p"],
            labelling=[["1"], ["0"]],
            num_agents=1,
            costs_for_actions={"I*": "s0$0:0", "**": "s9$0:0;s10$0:0"},
        )
        parser = load_costcgs_from_content(temp_file, content)
        assert parser.initial_state == "s0"
        assert parser.initial_state in parser.states

    def test_capcgs_initial_state_not_overwritten(self, test_data_dir):
        path = (
            test_data_dir / "capCGS" / "CAPATL" / "capatl_3agents_3states_example.txt"
        )
        if not path.exists():
            pytest.skip("capCGS example not found")
        parser = capCGS()
        parser.read_file(str(path))
        assert parser.initial_state == "q0"
        assert parser.initial_state in parser.states
