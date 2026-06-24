from .tctl_ply_parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    Expr,
    FreezeExpr,
    QuantifiedPath,
    SimpleTimeExpr,
    Unary,
    do_parsingTCTL,
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
    "do_parsingTCTL",
    "verifyTCTL",
]
