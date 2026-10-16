"""NatATLF compatibility with exact shared NatATL pruning."""
import pytest

from model_checker.algorithms.explicit.NatATLF.NatATL import model_checking


@pytest.mark.integration
class TestNatATLFCorrectness:
    def test_original_nondeterministic_fixture_is_rejected(self, natatl_standard_model):
        result = model_checking("<{1},1>Fa", natatl_standard_model.filename)
        assert result["error"]["type"] == "model"
        assert "Nondeterministic" in result["error"]["message"]

    def test_known_formula_on_separate_valid_cgs(self, test_data_dir):
        path = test_data_dir / "CGS/NATATL/natatl_1agent_2states_deterministic.txt"
        result = model_checking("<{1},1>Fa", str(path))
        assert "error" not in result, result
        assert result["Satisfiability"] is True
