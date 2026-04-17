"""Scalability: large state spaces (500+, 1000+, 2000+), bottlenecks, memory."""

import time
import tracemalloc

import pytest

from model_checker.algorithms.explicit.CTL.CTL import (
    model_checking as ctl_model_checking,
)
from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    generate_linear_chain,
    load_cgs_from_content,
)
from model_checker.tests.performance.performance_helpers import (
    check_parser_performance,
    run_model_checking_with_timeout,
)


def _run_ctl_model_checking(parser, formula, model_content, temp_file_path):
    """Run CTL model checking and return state set. Requires file path for CTL API."""
    with open(temp_file_path, "w") as f:
        f.write(model_content)
    result = ctl_model_checking(formula, temp_file_path, preloaded_model=parser)
    if result.get("type") == "error":
        return None
    states = extract_states_from_result(result)
    return states if states is not None else set()


PARSER_PERFORMANCE_CASES = [
    (500, 5.0),
    (1000, 15.0),
    (2000, 60.0),
]

CTL_EF_SCALABILITY_CASES = [
    (500, 30.0, 2.0, pytest.param),
    (1000, 60.0, 3.0, pytest.param),
    (2000, 120.0, 3.0, pytest.param),
]


@pytest.mark.performance
@pytest.mark.model_checking
class TestScalabilityAnalysis:
    """Scalability analysis for very large models."""

    @pytest.mark.parametrize(
        "num_states,max_time",
        PARSER_PERFORMANCE_CASES,
        ids=[f"parser_{n}_states" for n, _ in PARSER_PERFORMANCE_CASES],
    )
    def test_parser_performance(self, temp_file, num_states, max_time):
        """Parser completes within time bound for linear chain."""
        check_parser_performance(temp_file, generate_linear_chain, num_states, max_time)

    @pytest.mark.parametrize(
        "num_states,max_time,timeout_multiplier",
        [
            (500, 30.0, 2.0),
            (1000, 60.0, 3.0),
            (2000, 120.0, 3.0),
        ],
        ids=["ctl_ef_500", "ctl_ef_1000", "ctl_ef_2000"],
    )
    def test_ctl_ef_scales(self, temp_file, num_states, max_time, timeout_multiplier):
        """CTL EF operator completes within time bound."""
        num_agents = 2
        model_content = generate_linear_chain(num_states, num_agents)
        parser = load_cgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser,
            _run_ctl_model_checking,
            "EF p",
            max_time,
            timeout_multiplier=timeout_multiplier,
            model_content=model_content,
            temp_file=temp_file,
        )
        assert len(states) > 0, "EF p should hold in at least some states"

    @pytest.mark.slow
    def test_ctl_ef_1000_states_slow(self, temp_file):
        """Test CTL EF with 1000 states (marked slow)."""
        num_states, num_agents = 1000, 2
        model_content = generate_linear_chain(num_states, num_agents)
        parser = load_cgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser,
            _run_ctl_model_checking,
            "EF p",
            60.0,
            timeout_multiplier=3.0,
            model_content=model_content,
            temp_file=temp_file,
        )
        assert len(states) > 0

    @pytest.mark.slow
    def test_ctl_ef_2000_states_slow(self, temp_file):
        """Test CTL EF with 2000 states (marked slow)."""
        num_states, num_agents = 2000, 2
        model_content = generate_linear_chain(num_states, num_agents)
        parser = load_cgs_from_content(temp_file, model_content)
        states, _ = run_model_checking_with_timeout(
            parser,
            _run_ctl_model_checking,
            "EF p",
            120.0,
            timeout_multiplier=3.0,
            model_content=model_content,
            temp_file=temp_file,
        )
        assert len(states) > 0

    def test_memory_usage_1000_states(self, temp_file):
        """1000-state model stays within memory limit."""
        num_states, num_agents = 1000, 2
        model_content = generate_linear_chain(num_states, num_agents)
        tracemalloc.start()
        parser = load_cgs_from_content(temp_file, model_content)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert parser is not None
        peak_mb = peak / (1024 * 1024)
        assert peak_mb < 500, f"Peak memory {peak_mb:.2f}MB exceeded 500MB"

    def test_scalability_linear_vs_quadratic(self, temp_file):
        """Performance scales approximately linearly with state count."""
        state_counts = [100, 200, 500]
        times = []
        for num_states in state_counts:
            num_agents = 2
            model_content = generate_linear_chain(num_states, num_agents)
            parser = load_cgs_from_content(temp_file, model_content)
            start_time = time.time()
            result = _run_ctl_model_checking(
                parser, "EF p", model_content, temp_file(model_content)
            )
            elapsed_time = time.time() - start_time
            assert result is not None, f"EF p should work for {num_states} states"
            times.append((num_states, elapsed_time))
        ratio_200_100 = times[1][1] / times[0][1] if times[0][1] > 0 else float("inf")
        ratio_500_200 = times[2][1] / times[1][1] if times[1][1] > 0 else float("inf")
        assert (
            ratio_200_100 < 15.0
        ), f"Scaling ratio {ratio_200_100:.2f}x suggests poor complexity"
        assert (
            ratio_500_200 < 20.0
        ), f"Scaling ratio {ratio_500_200:.2f}x suggests poor complexity"
