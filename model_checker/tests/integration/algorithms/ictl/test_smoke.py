"""Smoke tests for ICTL model checking."""

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.ICTL import (
    process_model_checking_generated,
    run_model_checking,
)
from model_checker.algorithms.explicit.ICTL.util.generators import (
    generate_experiment_model,
)


def test_generate_experiment_model_passes_validation():
    data = generate_experiment_model(2, 3)
    assert data["states_counter"] == 6
    assert data["initial_state"] == "s0"


def test_run_model_checking_on_generated_model():
    data = generate_experiment_model(2, 3)
    checker = ICTLModelChecker(data)
    result = run_model_checking("EF e", checker)
    assert "States_Satisfying_Formula" in result
    assert "Res_Initial_state" in result


def test_process_model_checking_generated():
    result = process_model_checking_generated(2, 3, "AG e")
    assert result["Tot_states"] >= 0
