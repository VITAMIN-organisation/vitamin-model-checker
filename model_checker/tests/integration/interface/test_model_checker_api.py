"""Model checker API: correctness (ATL, CTL, NatATL_Recall, NatSL variants), error-path regression for other logics."""

from pathlib import Path
from typing import Callable, Dict, Tuple

import pytest

from model_checker.algorithms.explicit.ATL.ATL import (
    model_checking as atl_check,
)
from model_checker.algorithms.explicit.COTL.COTL import (
    model_checking as cotl_check,
)
from model_checker.algorithms.explicit.CTL.CTL import (
    model_checking as ctl_check,
)
from model_checker.algorithms.explicit.LTL.LTL import (
    model_checking as ltl_check,
)
from model_checker.algorithms.explicit.OATL.OATL import (
    model_checking as oatl_check,
)
from model_checker.algorithms.explicit.OL.OL import model_checking as ol_check
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
)

LogicConfig = Dict[str, Tuple[Callable[[str, str], Dict[str, str]], Tuple[str, ...]]]


LOGIC_CONFIG: LogicConfig = {
    "ATL": (atl_check, ("CGS", "ATL", "atl_2agents_4states_simple.txt")),
    "ATLF": (
        __import__(
            "model_checker.algorithms.explicit.ATLF.ATLF",
            fromlist=["model_checking"],
        ).model_checking,
        ("CGS", "ATL", "atl_2agents_4states_simple.txt"),
    ),
    "CapATL": (
        __import__(
            "model_checker.algorithms.explicit.CapATL.CapATL",
            fromlist=["model_checking"],
        ).model_checking,
        ("capCGS", "CAPATL", "capatl_3agents_3states_example.txt"),
    ),
    "CTL": (ctl_check, ("CGS", "CTL", "ctl_1agent_4states.txt")),
    "LTL": (
        ltl_check,
        ("CGS", "LTL", "ltl_1agent_3states_minimal.txt"),
    ),
    "NatATL": (
        __import__(
            "model_checker.algorithms.explicit.NatATL.Memoryless.NatATL",
            fromlist=["model_checking"],
        ).model_checking,
        ("CGS", "NATATL", "natatl_1agent_4states_standard.txt"),
    ),
    "NatATLF": (
        __import__(
            "model_checker.algorithms.explicit.NatATLF.NatATL",
            fromlist=["model_checking"],
        ).model_checking,
        ("CGS", "NATATL", "natatl_1agent_4states_standard.txt"),
    ),
    "NatSL_Sequential": (
        __import__(
            "model_checker.algorithms.explicit.NatSL.Sequential.natSL",
            fromlist=["model_checking"],
        ).model_checking,
        ("CGS", "NATATL", "natatl_1agent_4states_standard.txt"),
    ),
    "NatSL_Alternated": (
        __import__(
            "model_checker.algorithms.explicit.NatSL.Alternated.natSL",
            fromlist=["model_checking"],
        ).model_checking,
        ("CGS", "NATATL", "natatl_1agent_4states_standard.txt"),
    ),
    "NatATL_Recall": (
        __import__(
            "model_checker.algorithms.explicit.NatATL.Recall.natatl_recall",
            fromlist=["model_checking"],
        ).model_checking,
        ("CGS", "NATATL", "natatl_1agent_4states_standard.txt"),
    ),
    "OATL": (oatl_check, ("costCGS", "OATL", "oatl_3agents_medium_6states_costs.txt")),
    "COTL": (cotl_check, ("costCGS", "COTL", "cotl_model.txt")),
    "OL": (ol_check, ("costCGS", "OL", "ol_2agents_medium_6states_costs.txt")),
    "RABATL": (
        __import__(
            "model_checker.algorithms.explicit.RABATL.RABATL",
            fromlist=["model_checking"],
        ).model_checking,
        ("costCGS", "RABATL", "rabatl_3agents_medium_6states_costs.txt"),
    ),
    "RBATL": (
        __import__(
            "model_checker.algorithms.explicit.RBATL.RBATL",
            fromlist=["model_checking"],
        ).model_checking,  # lazy import to avoid circulars
        ("costCGS", "RBATL", "rbatl_3agents_medium_6states_costs.txt"),
    ),
}


@pytest.mark.unit
@pytest.mark.model_checking
@pytest.mark.parametrize(
    "logic, formula, expected_states, initial_expected",
    [
        ("ATL", "<1>F p", {"s0", "s1", "s2", "s3"}, True),
        ("CTL", "AF p", {"s0", "s1", "s2", "s3"}, True),
        ("OL", "<J1>F r", {"s0", "s1", "s2", "s3", "s4", "s5"}, True),
    ],
)
def test_model_checking_exact_state_sets(
    test_data_dir, logic, formula, expected_states, initial_expected
):
    """
    Validate model_checking returns the exact expected state set and consistent initial-state truth.
    """
    checker, model_parts = LOGIC_CONFIG[logic]
    model = Path(test_data_dir).joinpath(*model_parts)

    result = checker(formula, str(model))
    states = extract_states_from_result(result)
    assert states is not None, "Expected a state set in result"
    assert states == expected_states
    assert ("s0" in states) is initial_expected


@pytest.mark.unit
@pytest.mark.model_checking
@pytest.mark.parametrize(
    "logic, formula, expected_error_type, model_override",
    [
        ("ATL", "", "validation", None),
        ("NatATL_Recall", "<{1}, 1>F p", "system", "tests/invalid/missing.txt"),
        ("OL", "<J1>F nonexistent", "semantic", None),
    ],
)
def test_model_checking_error_paths(
    test_data_dir, logic, formula, expected_error_type, model_override
):
    """
    Edge cases: empty input, unknown atom, and malformed syntax should surface structured errors.
    """
    checker, model_parts = LOGIC_CONFIG[logic]
    if model_override is None:
        model = str(Path(test_data_dir).joinpath(*model_parts))
    else:
        model = str(Path(test_data_dir) / model_override)

    result = checker(formula, model)

    assert "error" in result
    assert result["error"]["type"] == expected_error_type
