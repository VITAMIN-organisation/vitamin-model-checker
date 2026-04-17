"""
Efficient state set implementation using bit vectors.

This module provides a bit vector implementation for storing sets of state indices,
optimized for dense sets and frequent membership checks in large models.
"""

from typing import Iterable, Iterator, Optional, Set, Union

import numpy as np

# Use bit vectors when the number of states is at least this size.
# Tuned to balance numpy overhead vs. Python set performance on typical models.
BIT_VECTOR_THRESHOLD = 300


class BitVectorStateSet:
    """Bit vector implementation for storing sets of integer state indices.

    Uses a numpy boolean array (_bits) where _bits[i] == 1 indicates presence.
    Best suited for models larger than BIT_VECTOR_THRESHOLD.
    """

    __slots__ = ("_bits", "_num_states")

    def __init__(
        self, num_states: int, initial_indices: Optional[Iterable[int]] = None
    ):
        self._num_states = num_states
        self._bits = np.zeros(num_states, dtype=np.uint8)
        if initial_indices is not None:
            for idx in initial_indices:
                if 0 <= idx < num_states:
                    self._bits[idx] = 1

    @classmethod
    def from_set(cls, num_states: int, indices: Iterable[int]) -> "BitVectorStateSet":
        return cls(num_states, indices)

    @classmethod
    def full(cls, num_states: int) -> "BitVectorStateSet":
        out = cls(num_states)
        out._bits.fill(1)
        return out

    @classmethod
    def empty(cls, num_states: int) -> "BitVectorStateSet":
        return cls(num_states)

    def add(self, state_idx: int) -> None:
        if 0 <= state_idx < self._num_states:
            self._bits[state_idx] = 1

    def remove(self, state_idx: int) -> None:
        if 0 <= state_idx < self._num_states:
            self._bits[state_idx] = 0

    def discard(self, state_idx: int) -> None:
        self.remove(state_idx)

    def __contains__(self, state_idx: int) -> bool:
        if 0 <= state_idx < self._num_states:
            return bool(self._bits[state_idx])
        return False

    def __len__(self) -> int:
        return int(np.sum(self._bits))

    def __bool__(self) -> bool:
        return bool(np.any(self._bits))

    def __iter__(self) -> Iterator[int]:
        return iter(np.nonzero(self._bits)[0])

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BitVectorStateSet):
            return self._num_states == other._num_states and np.array_equal(
                self._bits, other._bits
            )
        if isinstance(other, (set, frozenset)):
            return self.to_set() == other
        return NotImplemented

    def __hash__(self):
        raise TypeError("BitVectorStateSet is mutable and cannot be hashed")

    def copy(self) -> "BitVectorStateSet":
        out = BitVectorStateSet(self._num_states)
        out._bits = self._bits.copy()
        return out

    def clear(self) -> None:
        self._bits.fill(0)

    def to_set(self) -> Set[int]:
        return set(np.nonzero(self._bits)[0])

    def update(self, other: Union["BitVectorStateSet", Iterable[int]]) -> None:
        if isinstance(other, BitVectorStateSet):
            np.maximum(self._bits, other._bits, out=self._bits)
        else:
            for idx in other:
                self.add(idx)

    def intersection_update(
        self, other: Union["BitVectorStateSet", Iterable[int]]
    ) -> None:
        if isinstance(other, BitVectorStateSet):
            np.minimum(self._bits, other._bits, out=self._bits)
        else:
            o = set(other)
            for i in range(self._num_states):
                if self._bits[i] and i not in o:
                    self._bits[i] = 0

    def difference_update(
        self, other: Union["BitVectorStateSet", Iterable[int]]
    ) -> None:
        if isinstance(other, BitVectorStateSet):
            self._bits = self._bits & ~other._bits
        else:
            for idx in other:
                self.remove(idx)

    def __or__(self, other: "BitVectorStateSet") -> "BitVectorStateSet":
        if not isinstance(other, BitVectorStateSet):
            return NotImplemented
        out = BitVectorStateSet(self._num_states)
        np.maximum(self._bits, other._bits, out=out._bits)
        return out

    def __and__(self, other: "BitVectorStateSet") -> "BitVectorStateSet":
        if not isinstance(other, BitVectorStateSet):
            return NotImplemented
        out = BitVectorStateSet(self._num_states)
        np.minimum(self._bits, other._bits, out=out._bits)
        return out

    def __sub__(self, other: "BitVectorStateSet") -> "BitVectorStateSet":
        if not isinstance(other, BitVectorStateSet):
            return NotImplemented
        out = BitVectorStateSet(self._num_states)
        out._bits = self._bits & ~other._bits
        return out

    def __ior__(self, other: "BitVectorStateSet") -> "BitVectorStateSet":
        self.update(other)
        return self

    def __iand__(self, other: "BitVectorStateSet") -> "BitVectorStateSet":
        self.intersection_update(other)
        return self

    def __isub__(self, other: "BitVectorStateSet") -> "BitVectorStateSet":
        self.difference_update(other)
        return self

    def issubset(self, other: "BitVectorStateSet") -> bool:
        if isinstance(other, BitVectorStateSet):
            return not np.any(self._bits & ~other._bits)
        return self.to_set().issubset(other)

    def issuperset(self, other: "BitVectorStateSet") -> bool:
        if isinstance(other, BitVectorStateSet):
            return not np.any(other._bits & ~self._bits)
        return self.to_set().issuperset(other)

    def isdisjoint(self, other: "BitVectorStateSet") -> bool:
        if isinstance(other, BitVectorStateSet):
            return not np.any(self._bits & other._bits)
        return self.to_set().isdisjoint(other)

    def __repr__(self) -> str:
        idxs = list(self)[:10]
        return f"BitVectorStateSet({idxs}{'...' if len(self) > 10 else ''})"


def should_use_bit_vectors(num_states: int) -> bool:
    return num_states >= BIT_VECTOR_THRESHOLD


def indices_to_bit_vector(num_states: int, indices: Iterable[int]) -> BitVectorStateSet:
    return BitVectorStateSet.from_set(num_states, indices)


def bit_vector_to_indices(bv: BitVectorStateSet) -> Set[int]:
    return bv.to_set()
