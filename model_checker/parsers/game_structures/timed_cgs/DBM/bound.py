import numpy as np


class Bound:
    def __init__(self, constant: float = np.inf, operator: str = "<="):
        self.constant = constant
        self.operator = operator

    def add(self, other):
        if other.constant == np.inf or self.constant == np.inf:
            return Bound(np.inf, "<=")
        c = float(other.constant) + float(self.constant)
        op = "<" if self.operator == "<" or other.operator == "<" else "<="
        return Bound(c, op)

    def less_than(self, other) -> bool:
        if float(self.constant) < float(other.constant):
            return True

        if other.constant == np.inf and self.constant != np.inf:
            return True

        if (
            self.constant == other.constant
            and self.operator == "<"
            and other.operator == "<="
        ):
            return True

        return False

    def __eq__(self, value):
        return self.constant == value.constant and self.operator == value.operator

    def __hash__(self):
        return hash((float(self.constant), self.operator))
