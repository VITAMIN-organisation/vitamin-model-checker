from .parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    FreezeExpr,
    SimpleTimeExpr,
    Unary,
    verifyTOL,
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
    "verifyTOL",
]
