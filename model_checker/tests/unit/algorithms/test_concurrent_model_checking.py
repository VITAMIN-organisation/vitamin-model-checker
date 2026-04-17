"""Thread-safety tests: concurrent model checking with correctness checks."""

import concurrent.futures

import pytest

from model_checker.algorithms.explicit.ATL.ATL import (
    model_checking as atl_check,
)
from model_checker.algorithms.explicit.CTL.CTL import (
    model_checking as ctl_check,
)


def _run_pair(ctl_model_path: str, atl_model_path: str) -> None:
    """Run one CTL and one ATL check; assert dict and no error."""
    ctl_result = ctl_check("EF p", ctl_model_path)
    atl_result = atl_check("<1>F p", atl_model_path)
    assert isinstance(ctl_result, dict)
    assert isinstance(atl_result, dict)
    assert "error" not in ctl_result
    assert "error" not in atl_result


@pytest.mark.unit
@pytest.mark.robustness
class TestConcurrentModelChecking:
    """Run model checking concurrently and assert no races and correct results."""

    def test_concurrent_calls_same_models(self, ctl_small_model, cgs_simple_parser):
        """CTL and ATL on two models run concurrently; no error, valid dicts."""
        ctl_path = ctl_small_model.filename
        atl_path = cgs_simple_parser.filename

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_run_pair, ctl_path, atl_path) for _ in range(8)]
            for f in futures:
                f.result()

    def test_concurrent_results_match_sequential(self, ctl_small_model):
        """Same (model, formula) run sequentially once and N times in parallel; all match."""
        path = ctl_small_model.filename
        formula = "EF p"
        sequential = ctl_check(formula, path)
        assert isinstance(sequential, dict)
        assert "error" not in sequential

        num_parallel = 12
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(ctl_check, formula, path) for _ in range(num_parallel)
            ]
            parallel_results = [f.result() for f in futures]

        for result in parallel_results:
            assert (
                result == sequential
            ), "Concurrent result must equal sequential result (determinism)."

    def test_same_model_same_logic_many_formulas_parallel(self, ctl_small_model):
        """Same CTL model, different formulas run in parallel; each result matches sequential."""
        path = ctl_small_model.filename
        formulas = ["EF p", "AF p", "EX p", "AG p", "EG p"]

        sequential_by_formula = {}
        for f in formulas:
            r = ctl_check(f, path)
            assert "error" not in r, f"Sequential run failed for {f}: {r}"
            sequential_by_formula[f] = r

        def check_formula(formula: str):
            result = ctl_check(formula, path)
            assert (
                result == sequential_by_formula[formula]
            ), f"Parallel result for {formula} must match sequential."

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(check_formula, f) for f in formulas for _ in range(4)
            ]
            for f in futures:
                f.result()

    def test_concurrent_different_models(self, test_data_dir):
        """Different model files checked in parallel; no error, valid dicts."""
        from pathlib import Path

        from model_checker.algorithms.explicit.OL.OL import (
            model_checking as ol_check,
        )

        base = Path(test_data_dir)
        model_formula_pairs = [
            (str(base / "CGS/CTL/ctl_1agent_4states.txt"), "EF p", ctl_check),
            (str(base / "CGS/ATL/atl_2agents_4states_simple.txt"), "<1>F p", atl_check),
            (
                str(base / "costCGS/OL/ol_2agents_medium_6states_costs.txt"),
                "<J1>F r",
                ol_check,
            ),
        ]

        def run_one(pair):
            path, formula, checker = pair
            result = checker(formula, path)
            assert isinstance(result, dict)
            assert "error" not in result
            return result

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(run_one, pair)
                for pair in model_formula_pairs
                for _ in range(4)
            ]
            for f in futures:
                f.result()

    def test_concurrent_stress_many_workers(self, ctl_small_model, cgs_simple_parser):
        """Many workers and tasks; all complete without error and results are correct."""
        ctl_path = ctl_small_model.filename
        atl_path = cgs_simple_parser.filename
        sequential_ctl = ctl_check("EF p", ctl_path)
        sequential_atl = atl_check("<1>F p", atl_path)
        assert "error" not in sequential_ctl and "error" not in sequential_atl

        num_tasks = 32
        max_workers = 16

        def run_ctl():
            r = ctl_check("EF p", ctl_path)
            assert r == sequential_ctl
            return r

        def run_atl():
            r = atl_check("<1>F p", atl_path)
            assert r == sequential_atl
            return r

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(num_tasks):
                if i % 2 == 0:
                    futures.append(executor.submit(run_ctl))
                else:
                    futures.append(executor.submit(run_atl))
            for f in futures:
                f.result()
