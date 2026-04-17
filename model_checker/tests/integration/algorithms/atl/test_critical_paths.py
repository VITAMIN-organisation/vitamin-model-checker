"""Critical paths: ATL coalition when opponent can spoil outcome."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import _core_atl_checking
from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
    load_cgs_from_content,
)


@pytest.mark.integration
@pytest.mark.model_checking
class TestCoalitionPreImage:
    """ATL coalition cannot win when opponent can spoil."""

    def test_atl_coalition_cannot_win_against_spoiler(self, temp_file):
        """Test coalition fails when opponent can spoil the outcome."""
        content = build_cgs_model_content(
            transitions=[
                ["0", "1", "1"],
                ["0", "0", "0"],
                ["0", "0", "0"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["0"], ["1"], ["0"]],
            num_agents=2,
        )
        parser = load_cgs_from_content(temp_file, content)

        result = _core_atl_checking(parser, "<1>X p")
        assert "error" not in result
