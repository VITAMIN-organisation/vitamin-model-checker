import numpy as np

from .bound import Bound


class DBM:
    """Barebones API to work with DBMs (Difference Bound Matrices)"""

    def __init__(self, number_of_clocks: int, elements=None):
        self.size = number_of_clocks + 1
        if elements is not None:
            self.elements = np.empty((self.size, self.size), dtype=Bound)
            for i in range(self.size):
                for j in range(self.size):
                    bound = elements[i][j]
                    self.elements[i][j] = Bound(bound.constant, bound.operator)
            return

        self.elements = np.empty((self.size, self.size), dtype=Bound)
        zero = Bound(0, "<=")
        inf = Bound(np.inf, "<=")
        for i in range(self.size):
            for j in range(self.size):
                self.elements[i][j] = zero if i == j else inf
        for j in range(self.size):
            self.elements[0][j] = zero

    def close(self):
        """
        Applies the Floyd-Warshall algorithm to compute the all-pairs shortest paths
        (or tightest bounds) in the DBM
        """
        result = self.copy()
        result._close_in_place()
        return result

    def _close_in_place(self):
        elems = self.elements
        size = self.size
        for k in range(size):
            for i in range(size):
                row_i_k = elems[i][k]
                for j in range(size):
                    value = row_i_k.add(elems[k][j])
                    if value.less_than(elems[i][j]):
                        elems[i][j] = value
        if self.is_empty():
            raise ValueError("DBM is not consistent")

    def includes(self, other) -> bool:
        if self.size != other.size:
            raise ValueError(f"DBM sizes are not equal {self.size} vs {other.size}")

        for i in range(self.size):
            for j in range(self.size):
                left = self.elements[i][j]
                right = other.elements[i][j]
                if left.constant > right.constant:
                    return False
                if (
                    left.constant == right.constant
                    and left.operator == "<="
                    and right.operator == "<"
                ):
                    return False
        return True

    def is_empty(self) -> bool:
        sentinel = self.elements[0][0]
        return sentinel.constant < 0 or sentinel.operator == "<"

    def add_initial_constraint(self, i, j, constant: int, operator="<="):
        self.elements[i][j] = Bound(constant, operator)

    def intersect(self, other):
        if self.size != other.size:
            raise ValueError(
                f"Cannot intersect two DBMs of different size {self.size} vs {other.size}"
            )

        for i in range(self.size):
            for j in range(self.size):
                other_bound = other.elements[i][j]
                if other_bound.constant == np.inf:
                    continue
                self.add_constraint(i, j, other_bound.constant, other_bound.operator)

    def add_constraint(
        self, first_clock_idx, second_clock_idx, constant, operator="<="
    ):
        if self.is_empty():
            return

        new_bound = Bound(constant, operator)
        current = self.elements[first_clock_idx][second_clock_idx]
        reverse = self.elements[second_clock_idx][first_clock_idx]
        combined = reverse.add(new_bound)
        if combined.constant < 0 or (
            combined.constant == 0 and (reverse.operator == "<" or operator == "<")
        ):
            self.elements[0][0].constant = -1
            return

        if not new_bound.less_than(current):
            return

        self.elements[first_clock_idx][second_clock_idx] = new_bound
        elems = self.elements
        size = self.size
        for i in range(size):
            via_first = elems[i][first_clock_idx]
            via_second = elems[i][second_clock_idx]
            for j in range(size):
                path = via_first.add(elems[first_clock_idx][j])
                if path.less_than(elems[i][j]):
                    elems[i][j] = path
                path = via_second.add(elems[second_clock_idx][j])
                if path.less_than(elems[i][j]):
                    elems[i][j] = path

    def k_normalize(self, max_constants: list):
        """
        Args:
        max_constants: a list of the maximum constant each clock is compared to in the automaton.
        """
        final_max_constants = [0] + max_constants
        elems = self.elements
        size = self.size
        inf = Bound(np.inf, "<=")
        for i in range(size):
            max_i = final_max_constants[i]
            for j in range(size):
                bound = elems[i][j]
                if bound.constant == np.inf:
                    continue
                if Bound(max_i).less_than(bound):
                    elems[i][j] = inf
                elif bound.less_than(Bound(-final_max_constants[j], "<")):
                    elems[i][j] = Bound(-final_max_constants[j], "<")

        self._close_in_place()

    def reset(self, clock_index: int, constant: int = 0):
        elems = self.elements
        size = self.size
        pos = Bound(constant)
        neg = Bound(-constant)
        for j in range(size):
            elems[clock_index][j] = pos.add(elems[0][j])
            elems[j][clock_index] = neg.add(elems[j][0])

    def get_reset(self, clock_index: int, constant: int):
        result = self.copy()
        result.reset(clock_index, constant)
        return result

    def down(self):
        # computes the time pre-decessor
        elems = self.elements
        size = self.size
        zero = Bound(0, "<=")
        for i in range(1, size):
            min_bound = zero
            for j in range(1, size):
                candidate = elems[j][i]
                if candidate.less_than(min_bound):
                    min_bound = candidate
            elems[0][i] = min_bound
        self._close_in_place()

    def up(self):
        # computes the time successor
        inf = Bound(np.inf, "<=")
        for i in range(1, self.size):
            self.elements[i][0] = inf

    def free(self, clock_index: int):
        inf = Bound(np.inf, "<=")
        elems = self.elements
        for i in range(self.size):
            if i != clock_index:
                elems[clock_index][i] = inf
                elems[i][clock_index] = elems[i][0]

    def get_free(self, clock_index: int):
        result = self.copy()
        result.free(clock_index)
        return result

    def copy(self):
        return DBM(self.size - 1, elements=self.elements)

    def __eq__(self, other):
        """
        Determines if two DBMs are exactly the same, entry by entry.
        """
        if isinstance(other, DBM):
            if other.size != self.size:
                return False

            return np.array_equal(self.elements, other.elements)
        return NotImplemented

    def __hash__(self):
        return hash(tuple(tuple(row) for row in self.elements))
