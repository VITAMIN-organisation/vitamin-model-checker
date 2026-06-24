from .tol_ply_parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    FreezeExpr,
    SimpleTimeExpr,
    Unary,
    do_parsing,
    verify,
)

METADATA = {"model_type": "timedCGS"}

__all__ = [
    "METADATA",
    "AtomicProp",
    "Binary",
    "ClockExpr",
    "DemonicBinary",
    "DemonicOp",
    "Expr",
    "FreezeExpr",
    "SimpleTimeExpr",
    "Unary",
    "do_parsing",
    "verify",
]
