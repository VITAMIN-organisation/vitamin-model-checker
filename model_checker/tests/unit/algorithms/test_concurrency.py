"""Checks run in parallel threads give the same results as run one after another.

The checkers cache parsed formulas and models (for example the lru_caches in
CapATL/utils.py), so a cache shared badly between threads would mix results.
"""

import concurrent.futures

import pytest

from model_checker.algorithms.explicit.ATL.ATL import model_checking as atl_check
from model_checker.algorithms.explicit.CTL.CTL import model_checking as ctl_check


@pytest.mark.unit
def test_parallel_results_equal_sequential_results(ctl_small_model, cgs_simple_parser):
    """Several CTL and ATL formulas on two models, each run 6 times across 8 threads."""
    jobs = [
        (ctl_check, formula, ctl_small_model.filename)
        for formula in ("EF p", "AG p", "EX p", "E p U q")
    ] + [
        (atl_check, formula, cgs_simple_parser.filename)
        for formula in ("<1>F p", "<2>G q", "<1,2>X p")
    ]
    sequential = [check(formula, path) for check, formula, path in jobs]
    assert all("error" not in result for result in sequential), sequential

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(check, formula, path) for check, formula, path in jobs * 6
        ]
        parallel = [future.result() for future in futures]

    assert parallel == sequential * 6
