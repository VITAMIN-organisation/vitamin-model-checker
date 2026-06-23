"""NatATLF result contract."""

import pytest

from model_checker.algorithms.explicit.NatATLF.NatATL import model_checking
from model_checker.synthetic_models import generate_natatl_linear_chain_model


@pytest.mark.unit
def test_natatlf_res_not_literal_placeholder(temp_file):
    content = generate_natatl_linear_chain_model(
        num_states=3, num_agents=1, prop_names=["p"]
    )
    model_path = temp_file(content)
    result = model_checking("<{1}, 1>F p", model_path)
    assert "error" not in result, result
    assert result["res"] != "Result: {satisfied}"
    assert result["res"] != "Result: {}"
    assert "initial_state" in result
