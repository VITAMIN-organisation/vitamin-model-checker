"""CapATL performance: capability constraints, large models, pre-image scaling."""

import time

import pytest

from model_checker.algorithms.explicit.CapATL.CapATL import model_checking
from model_checker.tests.helpers.model_helpers import build_cgs_model_content


def _capatl_cycle_content(num_states, num_agents=2):
    """Build a cycle CapCGS with a shared capacity for agent action A."""
    state_names = [f"s{i}" for i in range(num_states)]
    forward = "A" + "*" * (num_agents - 1)
    transitions = []
    labelling = []
    for i in range(num_states):
        row = ["0"] * num_states
        row[(i + 1) % num_states] = forward
        transitions.append(row)
        labelling.append(["1" if i == 0 else "0"])
    return build_cgs_model_content(
        transitions=transitions,
        state_names=state_names,
        initial_state="s0",
        labelling=labelling,
        num_agents=num_agents,
        prop_names=["p"],
        capacities=["c"],
        capacities_assignment=[["1"] for _ in range(num_agents)],
        actions_for_capacities={"c": ["A"]},
    )


CAPATL_SCALE_CASES = [
    (3, 2.0, "small_cycle_3"),
    (10, 5.0, "cycle_10"),
]


@pytest.mark.performance
class TestCapATLScalability:
    """Test CapATL performance with varying model sizes."""

    @pytest.mark.parametrize(
        "num_states,max_time,case_id",
        CAPATL_SCALE_CASES,
        ids=[c[2] for c in CAPATL_SCALE_CASES],
    )
    def test_capatl_cycle_scales(self, temp_file, num_states, max_time, case_id):
        """CapATL completes within the time bound on cycle models."""
        model_path = temp_file(_capatl_cycle_content(num_states))
        start_time = time.time()
        result = model_checking("<{1}>F p", model_path)
        elapsed = time.time() - start_time
        assert "error" not in result, f"{case_id}: {result}"
        assert (
            elapsed < max_time
        ), f"{case_id} took {elapsed:.2f}s, expected < {max_time}s"
