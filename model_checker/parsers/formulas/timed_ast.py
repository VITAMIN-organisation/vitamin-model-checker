"""Formula tree nodes shared by the TCTL and TOL parsers; each node keeps the regions
where it holds once a solver has run."""


class Expr:
    def __init__(self) -> None:
        self.satisfying_regions: set = set()
        self.constraints = None


class Unary(Expr):
    def __init__(self, op: str, operand: Expr) -> None:
        super().__init__()
        self.op = op
        self.operand = operand

    def __repr__(self) -> str:
        return f"{self.op}({self.operand})"


class Binary(Expr):
    def __init__(self, op: str, left: Expr, right: Expr) -> None:
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"{self.op} {self.left},{self.right}"


class AtomicProp(Expr):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class FreezeExpr(Expr):
    def __init__(self, clock: str, operand: Expr) -> None:
        super().__init__()
        self.clock = clock
        self.operand = operand

    def __repr__(self) -> str:
        return f"{self.clock}.({self.operand})"


class ClockExpr(Expr):
    def __init__(self, subject: Expr, constraints: Expr) -> None:
        super().__init__()
        self.subject = subject
        self.constraints = str(constraints)

    def __repr__(self) -> str:
        return f"{self.subject}: {self.constraints}"

    def __str__(self) -> str:
        return f"{self.subject}: {self.constraints}"


class SimpleTimeExpr(Expr):
    def __init__(self, constraints: str) -> None:
        super().__init__()
        self.constraints = constraints

    def __repr__(self) -> str:
        return self.constraints

    def __str__(self) -> str:
        return self.constraints


class BooleanConst(Expr):
    def __init__(self, value: bool) -> None:
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return "true" if self.value else "false"
