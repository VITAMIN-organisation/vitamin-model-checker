"""NatATLF model checking: at least one formula with known result."""

import pytest

from model_checker.algorithms.explicit.NatATLF.NatATL import model_checking


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLFCorrectness:
    """One formula that should produce a known satisfiability result."""

    def test_natatlf_known_formula_satisfiable(self, natatl_standard_model):
        """On the standard 1-agent 4-state model, <1>Fa is satisfiable."""
        result = model_checking("<{1},1>Fa", natatl_standard_model.filename)
        assert "error" not in result
        assert "Satisfiability" in result
        assert result["Satisfiability"] is True
        assert "res" in result
