from .parser import (
    AtomicProp,
    Binary,
    BooleanConst,
    ClockExpr,
    Expr,
    FreezeExpr,
    QuantifiedPath,
    SimpleTimeExpr,
    Unary,
)

# TCTL has no agents, so a row need not list every combination of actions.
METADATA = {"model_type": "timedCGS", "partial_transitions": True}

__all__ = [
    "METADATA",
    "AtomicProp",
    "Binary",
    "BooleanConst",
    "ClockExpr",
    "Expr",
    "FreezeExpr",
    "QuantifiedPath",
    "SimpleTimeExpr",
    "Unary",
]
