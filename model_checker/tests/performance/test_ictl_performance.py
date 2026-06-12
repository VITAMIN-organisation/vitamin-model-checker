"""ICTL performance benchmarks (manual / slow; not run in default CI)."""

import time

import numpy as np
import pytest

from model_checker.algorithms.explicit.ICTL.checker import ICTLModelChecker
from model_checker.algorithms.explicit.ICTL.ICTL import run_model_checking
from model_checker.algorithms.explicit.ICTL.util.generators import (
    generate_3n_model,
    generate_experiment_model,
)


@pytest.mark.performance
@pytest.mark.skip(reason="Manual ICTL grid benchmark; writes results240x240.txt")
def test_ictl_generated_grid_benchmark():
    formula = "EF e"
    grid_size = 240
    with open(f"results{grid_size}x{grid_size}.txt", "a", encoding="utf-8") as out:
        out.write(
            f"Matrix {grid_size} x {grid_size}, Tot states:{grid_size * grid_size}\n"
        )
        for run in range(10):
            out.write(f"exec:{run}\n")
            t0 = time.time()
            data = generate_experiment_model(grid_size, grid_size)
            relation_count = int(np.count_nonzero(data["graph"] != "0"))
            t1 = time.time()
            out.write(f"Relations:{relation_count}\n")
            out.write(f"Generation_Time:{t1 - t0}\n")
            t2 = time.time()
            checker = ICTLModelChecker(data)
            t3 = time.time()
            out.write(f"Processing_preorder_time:{t3 - t2}\n")
            run_model_checking(formula, checker)
            out.write(f"MC_Time:{time.time() - t3}\n")


@pytest.mark.performance
@pytest.mark.skip(reason="Manual ICTL 3k benchmark; writes results_k_model.txt")
def test_ictl_3k_model_benchmark():
    agent_counts = [200]
    with open("results_k_model.txt", "a", encoding="utf-8") as out:
        out.write("n°agents,n°states,T_MC (sec)\n")
        for n in agent_counts:
            formula = (
                f"{' & '.join(f'p{k}' for k in range(n))} -> "
                f"(EF an0 & (an{n - 1} -> know) & (know -> an{n - 1}))"
            )
            data = generate_3n_model(n)
            checker = ICTLModelChecker(data)
            total_time = 0.0
            for _ in range(10):
                start = time.time()
                run_model_checking(formula, checker)
                total_time += time.time() - start
            out.write(f"{n},{data['states_counter']},{total_time / 10}\n")
