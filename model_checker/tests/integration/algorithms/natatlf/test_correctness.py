"""NatATLF model checking: at least one formula with known result."""

import pytest

from model_checker.algorithms.explicit.NatATLF.NatATL import model_checking


@pytest.mark.integration
@pytest.mark.model_checking
class TestNatATLFCorrectness:
    """One formula that should produce a known satisfiability result."""

    def test_natatlf_known_formula_satisfiable(self, natatl_standard_model):
        """On the standard 1-agent 4-state model, <{1},1>F a is satisfiable."""
        result = model_checking("<{1},1>F a", natatl_standard_model.filename)
        assert "error" not in result
        assert "Satisfiability" in result
        assert result["Satisfiability"] is True
        assert "res" in result

    def test_word_connective_checks_like_its_symbol(self, natatl_standard_model):
        """`and` between a true and a false coalition formula is false, as `&&` is
        (`or` in its place would give true)."""
        results = [
            model_checking(
                f"(<{{1}},1>F a) {op} (<{{1}},1>F false)",
                natatl_standard_model.filename,
            )
            for op in ("and", "&&")
        ]
        assert "error" not in results[0], results[0]
        assert results[0]["Satisfiability"] == results[1]["Satisfiability"] is False
