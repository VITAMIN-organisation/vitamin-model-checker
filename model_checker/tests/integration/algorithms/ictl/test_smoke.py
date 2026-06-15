"""Smoke tests for ICTL model checking."""

from pathlib import Path

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.ICTL import (
    model_checking,
    run_model_checking,
)
from model_checker.algorithms.explicit.ICTL.util.generators import (
    generate_experiment_model,
)
from model_checker.algorithms.explicit.ICTL.util.graph import read_file
from model_checker.utils.literals import parse_state_set_literal

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "experiment_2x3.txt"


def _states(result):
    assert "error" not in result
    return parse_state_set_literal(result["res"].removeprefix("Result: "))


def test_generate_experiment_model_passes_validation():
    data = generate_experiment_model(2, 3)
    assert data["states_counter"] == 6
    assert data["initial_state"] == "s0"


def test_run_model_checking_on_checker():
    data = read_file(str(_FIXTURE))
    checker = ICTLModelChecker(data)
    result = run_model_checking("EF e", checker)
    assert _states(result) == {"s0", "s1", "s2", "s3", "s4", "s5"}
    assert result["initial_state"] == "Initial state s0: True"


def test_model_checking_on_fixture():
    result = model_checking("AG e", str(_FIXTURE))
    assert _states(result) == {"s1"}
    assert result["initial_state"] == "Initial state s0: False"
    assert result["res"].startswith("Result:")
