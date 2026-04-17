"""ATL and ATLF model checking: error handling, operators."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import (
    _core_atl_checking,
    model_checking,
)
from model_checker.algorithms.explicit.ATLF.ATLF import (
    model_checking as atlf_model_checking,
)


@pytest.mark.integration
@pytest.mark.model_checking
class TestATLErrorHandling:
    """Test ATL error handling for invalid inputs."""

    def test_atl_invalid_formula_syntax(self, cgs_simple_parser):
        """Test ATL with invalid formula syntax."""
        result = model_checking("INVALID_FORMULA", cgs_simple_parser.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")

    def test_atl_nonexistent_atomic_proposition(self, cgs_simple_parser):
        """Test ATL with non-existent atomic proposition."""
        result = _core_atl_checking(cgs_simple_parser, "<1>F nonexistent")
        assert "error" in result or "does not exist" in result.get("res", "").lower()


@pytest.mark.integration
@pytest.mark.model_checking
class TestATLFErrorHandling:
    """Test ATLF error handling for invalid inputs."""

    def test_atlf_invalid_formula_syntax(self, cgs_simple_parser):
        """Test ATLF with invalid formula syntax."""
        result = atlf_model_checking("INVALID_FORMULA", cgs_simple_parser.filename)
        assert "error" in result or "Syntax error" in result.get("res", "")


@pytest.mark.integration
@pytest.mark.model_checking
@pytest.mark.semantic
class TestATLFSemantics:
    """ATLF returns real-valued satisfaction; format differs from ATL."""

    def test_atlf_result_format_differs_from_atl(self, cgs_simple_parser):
        """Same formula on same model: ATLF result has real-valued format, not a state set."""
        formula = "<1>F p"
        atl_result = model_checking(formula, cgs_simple_parser.filename)
        atlf_result = atlf_model_checking(formula, cgs_simple_parser.filename)
        assert "error" not in atlf_result
        assert "res" in atlf_result and "initial_state" in atlf_result
        atl_res_str = atl_result.get("res", "")
        atlf_res_str = atlf_result.get("res", "")
        assert "Result:" in atlf_res_str
        assert (
            atl_res_str != atlf_res_str
        ), "ATLF should return real-valued result, not the same string as ATL"
        init_str = atlf_result.get("initial_state", "")
        assert "Initial state" in init_str and (":" in init_str)
