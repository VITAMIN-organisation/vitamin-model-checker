"""OATL performance: large state spaces, cost constraints, cost-based pre-image."""

import pytest

from model_checker.algorithms.explicit.OATL.OATL import (
    _core_oatl_checking,
)
from model_checker.tests.helpers.model_helpers import (
    generate_cost_cgs_linear_chain_content,
    load_costcgs_from_content,
)
from model_checker.tests.performance.performance_helpers import (
    run_model_checking_with_timeout,
)

OATL_PERFORMANCE_CASES = [
    (100, 2, "<1><100>F p", 15.0, "F_linear_100"),
    (100, 2, "<1><10>X p", 10.0, "X_linear_100"),
    (100, 2, "<1><100>G p", 15.0, "G_linear_100"),
    (150, 2, "<1><150>F p", 20.0, "F_linear_150"),
    (100, 3, "<1,2><200>F p", 20.0, "multi_agent_100"),
]

OATL_COST_BOUND_CASES = [
    (10, 15.0),
    (50, 15.0),
    (100, 15.0),
    (200, 15.0),
]


@pytest.mark.performance
@pytest.mark.model_checking
class TestOATLPerformanceLargeModels:
    """Performance tests for OATL operators with large state spaces."""

    @pytest.mark.parametrize(
        "num_states,num_agents,formula,max_time,case_id",
        OATL_PERFORMANCE_CASES,
        ids=[c[4] for c in OATL_PERFORMANCE_CASES],
    )
    def test_oatl_operator_scales(
        self, temp_file, num_states, num_agents, formula, max_time, case_id
    ):
        """OATL operators complete within time bound on linear chain."""
        model_content = generate_cost_cgs_linear_chain_content(num_states, num_agents)
        parser = load_costcgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser, _core_oatl_checking, formula, max_time
        )
        assert states is not None

    @pytest.mark.parametrize(
        "cost_bound,max_time",
        OATL_COST_BOUND_CASES,
        ids=[f"cost_{b}" for b, _ in OATL_COST_BOUND_CASES],
    )
    def test_cost_constraint_scalability(self, temp_file, cost_bound, max_time):
        """Cost bounds scale without exponential complexity."""
        num_states, num_agents = 100, 2
        model_content = generate_cost_cgs_linear_chain_content(num_states, num_agents)
        parser = load_costcgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser, _core_oatl_checking, f"<1><{cost_bound}>F p", max_time
        )
        assert states is not None
