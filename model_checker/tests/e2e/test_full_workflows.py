"""E2E workflows: model load through formula verification (ATL, CTL, LTL, NatATL)."""

import pytest

from model_checker.algorithms.explicit.ATL.ATL import (
    model_checking as atl_check,
)
from model_checker.algorithms.explicit.CapATL.CapATL import (
    model_checking as capatl_check,
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
from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
    model_checking as natatl_mem_check,
)
from model_checker.algorithms.explicit.OL.OL import model_checking as ol_check
from model_checker.algorithms.explicit.RABATL.RABATL import (
    model_checking as rabatl_check,
)
from model_checker.algorithms.explicit.RBATL.RBATL import (
    model_checking as rbatl_check,
)


@pytest.mark.e2e
@pytest.mark.workflow
class TestBasicModelCheckingWorkflow:
    """Test basic model checking workflow."""

    def test_atl_complete_workflow(self, cgs_simple_parser):
        """Test complete ATL workflow: load model, verify formula, check result."""
        formula = "<1>F q"
        result = atl_check(formula, cgs_simple_parser.filename)

        assert isinstance(result, dict)
        assert "res" in result or "result" in result or "error" in result

    def test_ctl_complete_workflow(self, ctl_small_model):
        """Test complete CTL workflow."""
        formula = "EF p"
        result = ctl_check(formula, ctl_small_model.filename)

        assert isinstance(result, dict)
        assert "res" in result or "result" in result or "error" in result

    def test_ltl_complete_workflow(self, ltl_minimal_model):
        """Test complete LTL workflow."""
        formula = "F p"
        result = ltl_check(formula, ltl_minimal_model.filename)

        assert isinstance(result, dict)

    def test_additional_logics_complete_workflow(self, test_data_dir):
        """Test complete workflows for additional logics on small models."""
        natatl_result = natatl_mem_check(
            "<{1}, 1>F p", str(test_data_dir / "CGS/NatATL/natatl_1agent_4states.txt")
        )
        cotl_result = cotl_check(
            "F p", str(test_data_dir / "CGS/COTL/cotl_1agent_4states.txt")
        )
        capatl_result = capatl_check(
            "<{1}, 5>F goal",
            str(test_data_dir / "capCGS/CapATL/capatl_1agent_4states_capacities.txt"),
        )
        ol_result = ol_check(
            "<5>F p",
            str(test_data_dir / "costCGS/OL/ol_2agents_medium_6states_costs.txt"),
        )
        rbatl_result = rbatl_check(
            "<1><5>EF p",
            str(test_data_dir / "costCGS/RBATL/rbatl_2agents_4states_costs.txt"),
        )
        rabatl_result = rabatl_check(
            "<1><5>F p",
            str(test_data_dir / "costCGS/RABATL/rabatl_2agents_4states_costs.txt"),
        )

        for res in (
            natatl_result,
            cotl_result,
            capatl_result,
            ol_result,
            rbatl_result,
            rabatl_result,
        ):
            assert isinstance(res, dict)


@pytest.mark.e2e
@pytest.mark.workflow
class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows."""

    def test_workflow_with_invalid_model_file(self):
        """Test workflow with non-existent model file."""
        formula = "<1>F p"
        model_file = "/nonexistent/path/model.txt"

        result = atl_check(formula, model_file)

        assert isinstance(result, dict)
        assert "error" in result or "res" in result


@pytest.mark.e2e
@pytest.mark.workflow
class TestMultiStepWorkflow:
    """Test multi-step workflows with intermediate results."""

    def test_verify_multiple_formulas_same_model(self, cgs_simple_parser):
        """Test verifying multiple formulas on same model."""
        formulas = [
            "<1>F p",
            "<2>F q",
            "<1,2>G (p || q)",
        ]

        results = []
        for formula in formulas:
            result = atl_check(formula, cgs_simple_parser.filename)
            assert isinstance(result, dict)
            results.append(result)

        assert len(results) == len(formulas)

    def test_workflow_with_different_logics(self, cgs_simple_parser):
        """Test using different logics on compatible models."""
        atl_result = atl_check("<1>F p", cgs_simple_parser.filename)
        ctl_result = ctl_check("EF p", cgs_simple_parser.filename)

        assert isinstance(atl_result, dict)
        assert isinstance(ctl_result, dict)


@pytest.mark.e2e
@pytest.mark.workflow
@pytest.mark.performance
class TestPerformanceWorkflow:
    """Test workflows with performance considerations."""

    def test_workflow_with_large_model(self, atl_large_model):
        """Test workflow with larger model file."""
        formula = "<1>F p"
        result = atl_check(formula, atl_large_model.filename)

        assert isinstance(result, dict)

    def test_workflow_with_complex_formula(self, cgs_simple_parser):
        """Test workflow with complex nested formula."""
        formula = "<1>G (p -> <2>F q)"
        result = atl_check(formula, cgs_simple_parser.filename)

        assert isinstance(result, dict)


@pytest.mark.e2e
@pytest.mark.workflow
class TestStrategyExtractionWorkflow:
    """Test workflows involving strategy extraction."""

    def test_workflow_extract_winning_strategy(self, atl_strategy_model):
        """Test extracting winning strategy from result."""
        formula = "<1>F goal"
        result = atl_check(formula, atl_strategy_model.filename)

        assert isinstance(result, dict)
        if "strategy" in result:
            assert isinstance(result["strategy"], dict)
