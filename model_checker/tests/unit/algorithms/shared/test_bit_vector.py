"""BitVectorStateSet must behave as a Python set of indices 0..n-1.

The checkers switch to it on large models (ATL at 300 states and up), so every
operation is compared with `set` on random subsets of a 350-state universe.
"""

import random

import pytest

from model_checker.algorithms.explicit.shared.bit_vector import BitVectorStateSet

_N = 350
_ROUNDS = 50


def _random_pairs():
    rng = random.Random(1234)
    for _ in range(_ROUNDS):
        yield (
            {i for i in range(_N) if rng.random() < 0.3},
            {i for i in range(_N) if rng.random() < 0.3},
        )


@pytest.mark.unit
def test_binary_operations_match_set():
    """|, &, -, subset, superset, disjoint and == agree with set on random inputs."""
    for left, right in _random_pairs():
        a, b = BitVectorStateSet(_N, left), BitVectorStateSet(_N, right)
        assert (a | b).to_set() == left | right
        assert (a & b).to_set() == left & right
        assert (a - b).to_set() == left - right
        assert a.issubset(b) is left.issubset(right)
        assert a.issuperset(a & b)
        assert a.isdisjoint(b) is left.isdisjoint(right)
        assert (a == b) is (left == right)
        assert a == left


@pytest.mark.unit
@pytest.mark.parametrize("as_bits", [True, False])
def test_in_place_operations_match_set(as_bits):
    """update, intersection_update and difference_update take a bit set or any iterable."""
    for left, right in _random_pairs():
        other = BitVectorStateSet(_N, right) if as_bits else sorted(right)
        for method in ("update", "intersection_update", "difference_update"):
            bits, expected = BitVectorStateSet(_N, left), set(left)
            getattr(bits, method)(other)
            getattr(expected, method)(right)
            assert bits.to_set() == expected, method


@pytest.mark.unit
def test_membership_size_iteration_and_removal_match_set():
    """`in`, len, sorted iteration, add and discard follow the set they mirror."""
    for left, right in _random_pairs():
        bits, expected = BitVectorStateSet(_N, left), set(left)
        assert len(bits) == len(expected)
        assert bool(bits) is bool(expected)
        assert list(bits) == sorted(expected)
        assert all((i in bits) is (i in expected) for i in range(_N))
        for i in right:
            bits.add(i)
            expected.add(i)
        for i in list(left)[:10]:
            bits.discard(i)
            expected.discard(i)
        assert bits.to_set() == expected


@pytest.mark.unit
def test_full_empty_and_zero_size():
    """full(n) holds 0..n-1; an empty universe holds nothing."""
    assert BitVectorStateSet.full(_N).to_set() == set(range(_N))
    assert BitVectorStateSet.empty(_N).to_set() == set()
    assert list(BitVectorStateSet(0)) == []


@pytest.mark.unit
@pytest.mark.parametrize("index", [-1, _N])
def test_index_outside_the_universe_is_an_error(index):
    """add and the constructor reject an index outside 0..n-1; numpy would read -1 as n-1."""
    with pytest.raises(IndexError, match=str(index)):
        BitVectorStateSet(_N, [index])
    with pytest.raises(IndexError, match=str(index)):
        BitVectorStateSet(_N).add(index)


@pytest.mark.unit
def test_copy_is_independent():
    """Changing a copy leaves the original alone."""
    original = BitVectorStateSet(_N, [1, 2, 3])
    copy = original.copy()
    copy.add(4)
    copy.discard(1)
    assert original.to_set() == {1, 2, 3}


@pytest.mark.unit
def test_is_not_hashable():
    """It is mutable, so it must not be usable as a dict key."""
    with pytest.raises(TypeError):
        hash(BitVectorStateSet(_N, [1]))
