"""Pure-Python tests for TransitionSystem. No Spot dependency."""

from model_checker.automata.transition_system import TransitionSystem


def test_new_transition_system_is_empty():
    ts = TransitionSystem()
    assert ts.states == set()
    assert ts.initial_states == set()
    assert ts.alphabet == set()
    assert ts.transitions == {}


def test_add_state_without_initial_flag():
    ts = TransitionSystem()
    ts.add_state("s0")
    assert ts.states == {"s0"}
    assert ts.initial_states == set()


def test_add_state_with_initial_flag():
    ts = TransitionSystem()
    ts.add_state("s0", initial=True)
    assert ts.states == {"s0"}
    assert ts.initial_states == {"s0"}


def test_add_transition_registers_states_and_alphabet():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    assert ts.states == {"s0", "s1"}
    assert ts.alphabet == {"a"}
    assert ts.successors("s0", "a") == {"s1"}


def test_add_transition_is_nondeterministic_by_default():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    ts.add_transition("s0", "a", "s2")
    assert ts.successors("s0", "a") == {"s1", "s2"}


def test_successors_of_unknown_state_or_symbol_is_empty():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s1")
    assert ts.successors("s0", "b") == set()
    assert ts.successors("nope", "a") == set()


def test_default_collections_are_not_shared_between_instances():
    a = TransitionSystem()
    b = TransitionSystem()
    a.add_transition("s0", "a", "s1")
    assert b.states == set()
    assert b.transitions == {}
