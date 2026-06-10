"""BitVectorStateSet: empty set, add/remove, intersection/union/difference, threshold, indices conversion."""

import pytest

from model_checker.algorithms.explicit.shared.bit_vector import (
    BIT_VECTOR_THRESHOLD,
    BitVectorStateSet,
)


@pytest.mark.unit
class TestBitVectorStateSet:
    """Test BitVectorStateSet operations."""

    def test_empty_set(self):
        """Test empty BitVectorStateSet."""
        bv = BitVectorStateSet(10)
        assert len(bv) == 0
        assert not bv
        assert 0 not in bv
        assert list(bv) == []

    def test_add_and_contains(self):
        """Test adding elements and membership."""
        bv = BitVectorStateSet(10)
        bv.add(3)
        bv.add(7)
        assert 3 in bv
        assert 7 in bv
        assert 0 not in bv
        assert len(bv) == 2

    def test_remove_and_discard(self):
        """Test removing elements."""
        bv = BitVectorStateSet(10, [1, 2, 3])
        bv.remove(2)
        assert 2 not in bv
        assert len(bv) == 2
        bv.discard(5)  # Should not raise
        assert len(bv) == 2

    def test_from_indices(self):
        """Test creating from an index iterable."""
        indices = {1, 3, 5, 7}
        bv = BitVectorStateSet(10, indices)
        assert len(bv) == 4
        assert bv.to_set() == indices

    def test_full_set(self):
        """Test creating full set."""
        bv = BitVectorStateSet.full(5)
        assert len(bv) == 5
        assert all(i in bv for i in range(5))

    def test_empty_factory(self):
        """Test empty factory method."""
        bv = BitVectorStateSet.empty(10)
        assert len(bv) == 0

    def test_copy(self):
        """Test copying."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = bv1.copy()
        bv2.add(4)
        assert 4 in bv2
        assert 4 not in bv1

    def test_clear(self):
        """Test clearing."""
        bv = BitVectorStateSet(10, [1, 2, 3])
        bv.clear()
        assert len(bv) == 0

    def test_union(self):
        """Test union operation."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [3, 4, 5])
        result = bv1 | bv2
        assert result.to_set() == {1, 2, 3, 4, 5}

    def test_intersection(self):
        """Test intersection operation."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [2, 3, 4])
        result = bv1 & bv2
        assert result.to_set() == {2, 3}

    def test_difference(self):
        """Test difference operation."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [2, 3, 4])
        result = bv1 - bv2
        assert result.to_set() == {1}

    def test_update(self):
        """Test in-place union."""
        bv1 = BitVectorStateSet(10, [1, 2])
        bv2 = BitVectorStateSet(10, [3, 4])
        bv1.update(bv2)
        assert bv1.to_set() == {1, 2, 3, 4}

    def test_intersection_update(self):
        """Test in-place intersection."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [2, 3, 4])
        bv1.intersection_update(bv2)
        assert bv1.to_set() == {2, 3}

    def test_difference_update(self):
        """Test in-place difference."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [2, 3])
        bv1.difference_update(bv2)
        assert bv1.to_set() == {1}

    def test_inplace_mutations(self):
        """Test in-place union, intersection, and difference."""
        bv1 = BitVectorStateSet(10, [1, 2])
        bv2 = BitVectorStateSet(10, [2, 3])
        bv1.update(bv2)
        assert bv1.to_set() == {1, 2, 3}

        bv3 = BitVectorStateSet(10, [1, 2, 3])
        bv4 = BitVectorStateSet(10, [2, 3])
        bv3.intersection_update(bv4)
        assert bv3.to_set() == {2, 3}

        bv5 = BitVectorStateSet(10, [1, 2, 3])
        bv6 = BitVectorStateSet(10, [2])
        bv5.difference_update(bv6)
        assert bv5.to_set() == {1, 3}

    def test_equality(self):
        """Test equality comparison."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [1, 2, 3])
        bv3 = BitVectorStateSet(10, [1, 2])
        assert bv1 == bv2
        assert bv1 != bv3
        assert bv1 == {1, 2, 3}

    def test_issubset(self):
        """Test subset check."""
        bv1 = BitVectorStateSet(10, [1, 2])
        bv2 = BitVectorStateSet(10, [1, 2, 3])
        assert bv1.issubset(bv2)
        assert not bv2.issubset(bv1)

    def test_issuperset(self):
        """Test superset check."""
        bv1 = BitVectorStateSet(10, [1, 2, 3])
        bv2 = BitVectorStateSet(10, [1, 2])
        assert bv1.issuperset(bv2)
        assert not bv2.issuperset(bv1)

    def test_isdisjoint(self):
        """Test disjoint check."""
        bv1 = BitVectorStateSet(10, [1, 2])
        bv2 = BitVectorStateSet(10, [3, 4])
        bv3 = BitVectorStateSet(10, [2, 3])
        assert bv1.isdisjoint(bv2)
        assert not bv1.isdisjoint(bv3)

    def test_iteration(self):
        """Test iteration."""
        indices = {1, 3, 5, 7}
        bv = BitVectorStateSet(10, indices)
        assert set(bv) == indices

    def test_boundary_indices(self):
        """Test boundary index handling."""
        bv = BitVectorStateSet(10)
        bv.add(-1)  # Should be ignored
        bv.add(10)  # Should be ignored
        bv.add(0)
        bv.add(9)
        assert len(bv) == 2
        assert 0 in bv
        assert 9 in bv
        assert -1 not in bv
        assert 10 not in bv

    def test_zero_size_bit_vector(self):
        """Test behavior when the universe size is zero."""
        bv = BitVectorStateSet(0)
        assert len(bv) == 0
        assert not list(bv)

    def test_repr(self):
        """Test string representation."""
        bv = BitVectorStateSet(10, [1, 2, 3])
        repr_str = repr(bv)
        assert "BitVectorStateSet" in repr_str

    def test_bit_vector_threshold(self):
        """Test threshold used to choose bit-vector pre-image paths."""
        assert 100 < BIT_VECTOR_THRESHOLD
        assert BIT_VECTOR_THRESHOLD - 1 < BIT_VECTOR_THRESHOLD
        assert BIT_VECTOR_THRESHOLD >= BIT_VECTOR_THRESHOLD
        assert 1000 >= BIT_VECTOR_THRESHOLD


@pytest.mark.unit
class TestBitVectorSetCompatibility:
    """Test that BitVectorStateSet behaves like a set for common operations."""

    def test_update_with_iterable(self):
        """Test update with regular iterable."""
        bv = BitVectorStateSet(10, [1, 2])
        bv.update([3, 4])
        assert bv.to_set() == {1, 2, 3, 4}

    def test_intersection_update_with_iterable(self):
        """Test intersection_update with regular iterable."""
        bv = BitVectorStateSet(10, [1, 2, 3])
        bv.intersection_update({2, 3, 4})
        assert bv.to_set() == {2, 3}

    def test_difference_update_with_iterable(self):
        """Test difference_update with regular iterable."""
        bv = BitVectorStateSet(10, [1, 2, 3])
        bv.difference_update([2, 3])
        assert bv.to_set() == {1}

    def test_not_hashable(self):
        """Test that BitVectorStateSet is not hashable (mutable)."""
        bv = BitVectorStateSet(10, [1, 2, 3])
        with pytest.raises(TypeError):
            hash(bv)
