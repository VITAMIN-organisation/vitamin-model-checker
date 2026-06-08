from . import do_parsing
from . import verify as tol_verify
from .tol_ply_parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    SimpleTimeExpr,
    Unary,
)

# Expose symbols for the checker
verify = tol_verify


class TOLParser:
    def parse(self, formula: str):
        return do_parsing(formula)

    def verify(self, name: str, string: str):
        return tol_verify(name, string)

    def build(self, result):
        return result
