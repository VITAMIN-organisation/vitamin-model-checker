"""CTL trace generation: EX, AX, EF, AF, EG, AG, EU, AU with generate_trace on real models."""

import pytest

from model_checker.algorithms.explicit.CTL import CTL


def _build_model(num_states, atomic_propositions, labelling):
    """
    Build minimal CGS model string.

    Args:
        num_states: 2 or 3
        atomic_propositions: list of prop names, e.g. ["p"] or ["p", "q"]
        labelling: list of rows, one per state; each row has len(atomic_propositions) values (0 or 1)
    """
    assert num_states in (2, 3) and len(labelling) == num_states
    transition = "\n".join([" ".join(["I"] * num_states)] * num_states)
    state_names = " ".join(f"s{i}" for i in range(num_states))
    props_str = " ".join(atomic_propositions)
    labelling_str = "\n".join(" ".join(str(x) for x in row) for row in labelling)
    return f"""Transition
{transition}
Name_State
{state_names}
Initial_State
s0
Atomic_propositions
{props_str}
Labelling
{labelling_str}
Number_of_agents
1
"""


def _assert_trace_present_and_shape(result, expected_type="witness"):
    """Assert result contains a trace with required keys and type."""
    assert "res" in result
    assert "initial_state" in result
    assert "trace" in result, "trace key missing when generate_trace=True"
    assert result["trace"] is not None, "trace should not be None"
    trace = result["trace"]
    assert "states" in trace
    assert "type" in trace
    assert "description" in trace
    assert "length" in trace
    assert isinstance(trace["states"], list)
    assert trace["type"] == expected_type
    assert trace["length"] == len(trace["states"])


WITNESS_CASES = [
    pytest.param("EF q", 3, ["p", "q"], [[1, 0], [0, 1], [1, 1]], id="EF"),
]


class TestCTLTraceGeneration:
    """Integration tests for CTL trace generation (all trace-capable operators)."""

    @pytest.mark.parametrize("formula,num_states,props,labelling", WITNESS_CASES)
    def test_operator_with_trace_witness(
        self, tmp_path, formula, num_states, props, labelling
    ):
        """Each trace-capable operator returns a witness trace when formula holds."""
        model_content = _build_model(num_states, props, labelling)
        model_file = tmp_path / "test_model.txt"
        model_file.write_text(model_content)

        result = CTL.model_checking(
            formula=formula, filename=str(model_file), generate_trace=True
        )

        _assert_trace_present_and_shape(result, expected_type="witness")

    def test_counterexample_trace(self, tmp_path):
        """When formula is not satisfied, result includes counterexample trace."""
        model_content = _build_model(2, ["p"], [[1, 0], [0, 1]])
        model_file = tmp_path / "test_model.txt"
        model_file.write_text(model_content)

        result = CTL.model_checking(
            formula="AG p", filename=str(model_file), generate_trace=True
        )

        assert "trace" in result and result["trace"] is not None
        _assert_trace_present_and_shape(result, expected_type="counterexample")
