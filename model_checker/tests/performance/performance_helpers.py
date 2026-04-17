"""Timing, timeout, and result extraction for performance tests."""

import concurrent.futures
import time

from model_checker.tests.helpers.model_helpers import (
    extract_states_from_result,
    load_cgs_from_content,
)


def check_parser_performance(
    temp_file, model_generator, num_states, max_time, num_agents=2, **kwargs
):
    """Parse model with model_generator(num_states, ...); assert time < max_time. Returns (parser, parse_time)."""
    model_content = model_generator(num_states, num_agents=num_agents, **kwargs)
    start_time = time.time()
    parser = load_cgs_from_content(temp_file, model_content)
    parse_time = time.time() - start_time
    assert parser is not None, f"Parser should succeed for {num_states} states"
    assert len(parser.get_states()) == num_states, f"Expected {num_states} states"
    assert (
        parse_time < max_time
    ), f"Parser took {parse_time:.2f}s for {num_states} states, expected < {max_time}s"
    return parser, parse_time


def _run_with_timeout(func, timeout_seconds, *args, **kwargs):
    """Run func(*args, **kwargs) in a thread; raise TimeoutError if it exceeds timeout_seconds."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(
                f"Function {func.__name__} exceeded timeout of {timeout_seconds}s"
            ) from None


def run_model_checking_with_timeout(
    parser,
    checking_func,
    formula,
    max_time,
    timeout_multiplier=2.0,
    model_content=None,
    temp_file=None,
    **checking_kwargs,
):
    """Run checking_func with a timeout; assert result valid and elapsed time < max_time. Returns (states, elapsed_time)."""
    timeout = max_time * timeout_multiplier

    def _run_checking():
        start_time = time.time()
        if model_content and temp_file:
            result = checking_func(
                parser,
                formula,
                model_content,
                temp_file(model_content),
                **checking_kwargs,
            )
        else:
            result = checking_func(parser, formula, **checking_kwargs)
        return result, time.time() - start_time

    try:
        result, elapsed_time = _run_with_timeout(_run_checking, timeout)
    except TimeoutError as e:
        raise TimeoutError(
            f"{formula} computation exceeded timeout of {timeout:.1f}s "
            f"(expected < {max_time}s). This may indicate a performance regression."
        ) from e
    states = extract_states_from_result(result) if isinstance(result, dict) else result
    assert states is not None, f"{formula} should return valid result"
    assert isinstance(states, set), f"{formula} result should be a set"
    assert (
        elapsed_time < max_time
    ), f"{formula} computation took {elapsed_time:.2f}s, expected < {max_time}s"
    return states, elapsed_time
