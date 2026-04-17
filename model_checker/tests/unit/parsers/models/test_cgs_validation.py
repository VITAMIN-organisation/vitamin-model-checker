"""CGS validation: validate_model_structure error detection."""

import pytest

from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
    load_test_model,
)


@pytest.mark.unit
class TestCGSValidation:
    """Error detection for invalid models (missing/invalid sections)."""

    @pytest.mark.parametrize(
        "case_type,params,expected_error_pattern",
        [
            (
                "file",
                {"folder": "invalid", "filename": "missing_name_state.txt"},
                "Model must have at least one state",
            ),
            (
                "file",
                {"folder": "invalid", "filename": "missing_initial_state.txt"},
                "Initial_State section is missing",
            ),
            (
                "file",
                {"folder": "invalid", "filename": "invalid_initial_state.txt"},
                "Initial state.*not found in state list",
            ),
            (
                "file",
                {"folder": "invalid", "filename": "missing_number_of_agents.txt"},
                "Number_of_agents",
            ),
            (
                "content",
                {
                    "transitions": [
                        ["III", "0"],
                        ["0", "III"],
                        ["III", "0"],
                    ],
                    "state_names": ["s0", "s1"],
                    "initial_state": "s0",
                    "labelling": [["1"], ["0"]],
                    "num_agents": 1,
                },
                "Transition matrix",
            ),
            (
                "content",
                {
                    "transitions": [["III", "0"], ["0", "III"]],
                    "state_names": ["s0", "s1"],
                    "initial_state": "s0",
                    "labelling": [
                        ["1", "0"],
                        ["0", "1"],
                        ["1", "1"],
                    ],
                    "num_agents": 1,
                    "prop_names": ["p", "q"],
                },
                "Labelling",
            ),
        ],
    )
    def test_validate_model_structure_error_detection(
        self, test_data_dir, temp_file, case_type, params, expected_error_pattern
    ):
        if case_type == "file":
            parser = load_test_model(
                test_data_dir, f"{params['folder']}/{params['filename']}"
            )
        else:
            parser = load_cgs_from_content(temp_file, build_cgs_model_content(**params))
        with pytest.raises(ValueError, match=expected_error_pattern):
            parser.validate_model_structure()
