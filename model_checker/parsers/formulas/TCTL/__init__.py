from .parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    Expr,
    FreezeExpr,
    QuantifiedPath,
    SimpleTimeExpr,
    Unary,
    verifyTCTL,
)

METADATA = {"model_type": "timedCGS"}

__all__ = [
    "METADATA",
    "AtomicProp",
    "Binary",
    "ClockExpr",
    "Expr",
    "FreezeExpr",
    "QuantifiedPath",
    "SimpleTimeExpr",
    "Unary",
    "verifyTCTL",
]
