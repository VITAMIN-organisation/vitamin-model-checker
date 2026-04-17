"""CapATL performance: capability constraints, large models, pre-image scaling."""

import time

from model_checker.tests.helpers.model_helpers import (
    build_cgs_model_content,
)


class TestCapATLScalability:
    """Test CapATL performance with varying model sizes."""

    def test_capatl_small_model_performance(self, temp_file):
        """Test CapATL model checking performance on small model."""
        from model_checker.algorithms.explicit.CapATL.CapATL import (
            model_checking,
        )

        content = build_cgs_model_content(
            transitions=[
                ["0", "1", "0"],
                ["0", "0", "1"],
                ["1", "0", "0"],
            ],
            state_names=["s0", "s1", "s2"],
            initial_state="s0",
            labelling=[["1"], ["0"], ["1"]],
            num_agents=2,
            prop_names=["p"],
            capacities=["c"],
            capacities_assignment=[["1"] for _ in range(2)],
            actions_for_capacities={"c": ["A"]},
        )
        model_path = temp_file(content)

        start_time = time.time()
        result = model_checking("<{1}, 1>F p", model_path)
        elapsed = time.time() - start_time

        assert (
            "error" not in result
        ), f"CapATL model checking should not error: {result}"
        assert (
            elapsed < 2.0
        ), f"CapATL model checking took {elapsed:.2f}s, expected < 2s for small model"


class TestCapATLComplexity:
    """Test CapATL computational complexity characteristics."""

    def test_capatl_fixpoint_iterations(self, temp_file):
        """Verify CapATL fixpoints converge in bounded iterations."""
        from model_checker.algorithms.explicit.CapATL.CapATL import (
            model_checking,
        )

        n_states = 10
        num_agents = 2

        state_names = [f"s{i}" for i in range(n_states)]
        transitions = []
        labelling = []

        for i in range(n_states):
            row = []
            for j in range(n_states):
                if j == (i + 1) % n_states:
                    action = "A" + "*" * (num_agents - 1)
                    row.append(action)
                else:
                    row.append("0")
            transitions.append(row)
            labelling.append(["1" if i == 0 else "0"])

        content = build_cgs_model_content(
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
        model_path = temp_file(content)

        start_time = time.time()
        result = model_checking("<{1}, 1>F p", model_path)
        elapsed = time.time() - start_time

        assert "error" not in result, f"CapATL model checking failed: {result}"
        assert (
            elapsed < 5.0
        ), f"CapATL model checking took {elapsed:.2f}s, expected < 5s for 10-state model"
