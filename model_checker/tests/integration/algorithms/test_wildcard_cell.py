"""A `*` cell is a transition to its own column, whichever checker reads it."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import model_checking as atl_check
from model_checker.algorithms.explicit.ATL_STAR.ATL_STAR import (
    model_checking as atl_star_check,
)
from model_checker.algorithms.explicit.CTL.CTL import model_checking as ctl_check
from model_checker.tests.helpers.model_helpers import extract_states_from_result
from model_checker.tests.helpers.synthetic_models import build_cgs_model_content


@pytest.mark.integration
@pytest.mark.parametrize(
    ("check", "formula"),
    [(ctl_check, "EX p"), (atl_check, "<1>X p"), (atl_star_check, "<<1>> X p")],
)
def test_star_cell_leads_to_its_column(temp_file, check, formula):
    """s0 has only `*` towards s1, where p holds, so the next state is s1 from s0 too."""
    path = temp_file(
        build_cgs_model_content(
            transitions=[["0", "*"], ["0", "a"]],
            state_names=["s0", "s1"],
            initial_state="s0",
            prop_names=["p"],
            labelling=[["0"], ["1"]],
            num_agents=1,
        )
    )
    result = check(formula, path)
    assert extract_states_from_result(result) == {"s0", "s1"}, result
