import numpy as np

from .Bound import Bound


class DBM:
    """Barebones API to work with DBMs (Difference Bound Matrices)"""

    def __init__(self, number_of_clocks: int, elements=None):
        self.size = number_of_clocks + 1
        self.elements = np.empty((self.size, self.size), dtype=Bound)

        if elements is not None:
            self.elements = np.empty_like(elements, dtype=Bound)
            self.elements[:] = elements
        else:
            # Initialize the DBM entries with size = num of clocks + 1.
            self.elements = np.empty((self.size, self.size), dtype=Bound)
            for i in range(self.size):
                for j in range(self.size):
                    if i == j:
                        self.elements[i][j] = Bound(
                            0, "<="
                        )  # every clock is at most itself
                    else:
                        self.elements[i][j] = Bound(np.inf, "<=")
                    self.elements[0][j] = Bound(
                        0, "<="
                    )  # all clocks are positive, 0 - xi ≤ 0

    def close(self):
        """
        Applies the Floyd-Warshall algorithm to compute the all-pairs shortest paths
        (or tightest bounds) in the DBM
        """
        temp_matrix = self.copy()

        for k in range(self.size):
            for i in range(self.size):
                for j in range(self.size):
                    # Calculate the path sum from i -> k -> j
                    value = temp_matrix.elements[i][k].add(temp_matrix.elements[k][j])
                    if value.less_than(temp_matrix.elements[i][j]):
                        temp_matrix.elements[i][j] = value

        if temp_matrix.is_empty():
            raise ValueError("DBM is not consistent")
        return temp_matrix

    def _close_in_place(self):
        self.elements = self.close().elements.copy()

    def includes(self, other) -> bool:
        if self.size != other.size:
            raise ValueError(f"DBM sizes are not equal {self.size} vs {other.size}")

        for i in range(self.size):
            for j in range(self.size):
                if self.elements[i][j].constant > other.elements[i][j].constant:
                    return False
                elif (
                    self.elements[i][j].constant == other.elements[i][j].constant
                    and self.elements[i][j].operator == "<="
                    and other.elements[i][j].operator == "<"
                ):
                    return False
        return True

    def is_empty(self) -> bool:
        return self.elements[0][0].constant < 0 or self.elements[0][0].operator == "<"

    def add_initial_constraint(self, i, j, constant: int, operator="<="):
        self.elements[i][j] = Bound(constant, operator)

    def intersect(self, other):
        if self.size != other.size:
            raise ValueError(
                f"Cannot intersect two DBMs of different size {self.size} vs {other.size}"
            )

        for i in range(self.size):
            for j in range(self.size):
                self.add_constraint(
                    i, j, other.elements[i][j].constant, other.elements[i][j].operator
                )

    def add_constraint(
        self, first_clock_idx, second_clock_idx, constant, operator="<="
    ):
        new_bound = Bound(constant, operator)
        sum = self.elements[second_clock_idx][first_clock_idx].add(new_bound)

        if sum.constant < 0 or (
            sum.constant == 0
            and (
                self.elements[second_clock_idx][first_clock_idx].operator == "<"
                or operator == "<"
            )
        ):
            # raise RuntimeError(f"Inconsistent DBM sum is {sum} for i:{first_clock_idx}, j:{second_clock_idx}")
            self.elements[0][0].constant = -1
        elif new_bound.less_than(self.elements[first_clock_idx][second_clock_idx]):
            self.elements[first_clock_idx][second_clock_idx] = new_bound
            for i in range(self.size):
                for j in range(self.size):
                    _sum = self.elements[i][first_clock_idx].add(
                        self.elements[first_clock_idx][j]
                    )
                    if _sum.less_than(self.elements[i][j]):
                        self.elements[i][j] = _sum
                    _sum = self.elements[i][second_clock_idx].add(
                        self.elements[second_clock_idx][j]
                    )
                    if _sum.less_than(self.elements[i][j]):
                        self.elements[i][j] = _sum
        # self._close_in_place()

    def k_normalize(self, max_constants: list):
        """
        Args:
        max_constants: a list of the maximum constant each clock is compared to in the automaton.
        """
        # max_constants.insert(0, 999) # max constant for clock x0 is zero
        final_max_constants = [0] + max_constants
        for i in range(self.size):
            for j in range(self.size):
                bound = self.elements[i][j]
                if bound.constant != np.inf:
                    if Bound(final_max_constants[i]).less_than(
                        bound
                    ):  # (max_constants[i], <=) < (m, op) ?
                        self.elements[i][j] = Bound(np.inf, "<=")
                    elif bound.less_than(
                        Bound(-final_max_constants[j], "<")
                    ):  # (-max_constants[j], <) < (m, op) ? == (m, op) > (-max_constants[j], <)
                        self.elements[i][j] = Bound(-final_max_constants[j], "<")

        self._close_in_place()

    def reset(self, clock_index: int, constant: int = 0):
        for j in range(self.size):
            self.elements[clock_index][j] = Bound(constant).add(self.elements[0][j])
            self.elements[j][clock_index] = Bound(-constant).add(self.elements[j][0])

    def get_reset(self, clock_index: int, constant: int):
        _foo = self.copy()
        _foo.reset(clock_index, constant)
        return _foo

    def down(self):
        # computes the time pre-decessor
        for i in range(1, self.size):
            self.elements[0][i] = Bound(0, "<=")
            for j in range(1, self.size):
                if self.elements[j][i].less_than(self.elements[0][i]):
                    self.elements[0][i] = self.elements[j][i]
        self._close_in_place()

    def up(self):
        # computes the time successor
        for i in range(1, self.size):
            self.elements[i][0] = Bound(np.inf, "<=")

    def free(self, clock_index: int):
        for i in range(self.size):
            if i != clock_index:
                self.elements[clock_index][i] = Bound(np.inf, "<=")
                self.elements[i][clock_index] = self.elements[i][0]

    def get_free(self, clock_index: int):
        _dbm = self.copy()
        for i in range(self.size):
            if i != clock_index:
                _dbm.elements[clock_index][i] = Bound(np.inf, "<=")
                _dbm.elements[i][clock_index] = self.elements[i][0]
        return _dbm

    def copy(self):
        return DBM(self.size - 1, elements=np.array(self.elements))

    def __str__(self) -> str:
        to_return = "    " + " ".join([f"x{k: <3}" for k in range(self.size)])
        to_return += "\n     " + "----" * self.size
        for i in range(self.size):
            row_str = f"x{i}: "
            for j in range(self.size):
                row_str += str(self.elements[i][j])
            to_return += f"\n {row_str}"
        to_return += "\n--------------------"
        return to_return

    def __eq__(self, other):
        """
        Determines if two DBMs are exactly the same, entry by entry.
        """
        if isinstance(other, DBM):
            if other.size != self.size:
                return False

            return np.array_equal(self.elements, other.elements)
        return NotImplemented

    def to_canonical_tuple(self):
        return tuple(tuple(row) for row in self.elements)

    def __hash__(self):
        return hash(self.to_canonical_tuple())
