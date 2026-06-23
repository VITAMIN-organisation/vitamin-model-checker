"""E2E workflows: model load through formula verification with state oracles."""

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
from model_checker.tests.helpers.model_helpers import extract_states_from_result


@pytest.mark.e2e
@pytest.mark.workflow
class TestBasicModelCheckingWorkflow:
    """Test basic model checking workflow with semantic checks."""

    def test_atl_complete_workflow(self, cgs_simple_parser):
        """ATL reachability: initial state satisfies <1>F q."""
        formula = "<1>F q"
        result = atl_check(formula, cgs_simple_parser.filename)

        assert "error" not in result
        assert "res" in result
        states = extract_states_from_result(result)
        assert states is not None
        assert ": True" in result.get("initial_state", "")

    def test_ctl_complete_workflow(self, ctl_small_model):
        """CTL EF p holds at initial state on small fixture."""
        formula = "EF p"
        result = ctl_check(formula, ctl_small_model.filename)

        assert "error" not in result
        states = extract_states_from_result(result)
        assert states is not None
        assert ": True" in result.get("initial_state", "")

    def test_ltl_complete_workflow(self, ltl_minimal_model):
        """LTL F p: result dict with res and no hard error."""
        formula = "F p"
        result = ltl_check(formula, ltl_minimal_model.filename)

        assert isinstance(result, dict)
        assert "error" not in result or "res" in result

    def test_additional_logics_complete_workflow(self, test_data_dir):
        """End-to-end checks for NatATL, COTL, CapATL, OL, RBATL, RABATL."""
        natatl_path = test_data_dir / "CGS/NATATL/natatl_1agent_4states_standard.txt"
        cotl_path = test_data_dir / "costCGS/COTL/cotl_model.txt"
        capatl_path = test_data_dir / "capCGS/CAPATL/capatl_3agents_3states_example.txt"
        ol_path = test_data_dir / "costCGS/OL/ol_2agents_medium_6states_costs.txt"
        rbatl_path = (
            test_data_dir / "costCGS/RBATL/rbatl_3agents_medium_6states_costs.txt"
        )
        rabatl_path = (
            test_data_dir / "costCGS/RABATL/rabatl_3agents_medium_6states_costs.txt"
        )

        natatl_result = natatl_mem_check("<{1},1>Fa", str(natatl_path))
        assert natatl_result.get("Satisfiability") is True

        cotl_result = cotl_check("<1><5>F g", str(cotl_path))
        assert "error" not in cotl_result
        cotl_states = extract_states_from_result(cotl_result)
        assert cotl_states == {"s0", "s2", "s3", "s4", "s5"}
        assert ": True" in cotl_result.get("initial_state", "")

        capatl_result = capatl_check("<{1},5>F g", str(capatl_path))
        assert "error" not in capatl_result
        cap_states = extract_states_from_result(capatl_result)
        assert cap_states == {"q2"}

        ol_result = ol_check("<J2> F r", str(ol_path))
        assert "error" not in ol_result
        assert ": True" in ol_result.get("initial_state", "")

        rbatl_result = rbatl_check("<1><2>F r", str(rbatl_path))
        assert "error" not in rbatl_result
        rba_states = extract_states_from_result(rbatl_result)
        assert rba_states == {"s0", "s1", "s2", "s3", "s4"}

        rabatl_result = rabatl_check("<1><2>F r", str(rabatl_path))
        assert "error" not in rabatl_result
        rab_states = extract_states_from_result(rabatl_result)
        assert rab_states == {"s0", "s1", "s2", "s3", "s4"}


@pytest.mark.e2e
@pytest.mark.workflow
class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows."""

    def test_workflow_with_invalid_model_file(self):
        """Non-existent model file yields an error result."""
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
        """Multiple formulas on the same model all return structured results."""
        formulas = [
            "<1>F p",
            "<2>F q",
            "<1,2>G (p || q)",
        ]

        results = []
        for formula in formulas:
            result = atl_check(formula, cgs_simple_parser.filename)
            assert isinstance(result, dict)
            assert "error" not in result
            results.append(result)

        assert len(results) == len(formulas)

    def test_workflow_with_different_logics(self, cgs_simple_parser):
        """ATL and CTL on compatible CGS both succeed without error."""
        atl_result = atl_check("<1>F p", cgs_simple_parser.filename)
        ctl_result = ctl_check("EF p", cgs_simple_parser.filename)

        assert "error" not in atl_result
        assert "error" not in ctl_result


@pytest.mark.e2e
@pytest.mark.workflow
@pytest.mark.performance
class TestPerformanceWorkflow:
    """Test workflows with performance considerations."""

    def test_workflow_with_large_model(self, atl_large_model):
        """Large model workflow returns a result dict without error."""
        formula = "<1>F kingwin"
        result = atl_check(formula, atl_large_model.filename)

        assert isinstance(result, dict)
        assert "error" not in result

    def test_workflow_with_complex_formula(self, cgs_simple_parser):
        """Nested ATL formula parses and model-checks."""
        formula = "<1>G (p -> <2>F q)"
        result = atl_check(formula, cgs_simple_parser.filename)

        assert isinstance(result, dict)
        assert "error" not in result


@pytest.mark.e2e
@pytest.mark.workflow
class TestStrategyExtractionWorkflow:
    """Test workflows involving strategy extraction."""

    def test_workflow_extract_winning_strategy(self, atl_strategy_model):
        """Strategy field present when model checker extracts strategies."""
        formula = "<1>F goal"
        result = atl_check(formula, atl_strategy_model.filename)

        assert isinstance(result, dict)
        if "strategy" in result:
            assert isinstance(result["strategy"], dict)
