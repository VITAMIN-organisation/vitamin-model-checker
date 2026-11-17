from .parser import (
    AtomicProp,
    Binary,
    BooleanConst,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    FreezeExpr,
    SimpleTimeExpr,
    Unary,
)

# TOL is OL with clocks, so its transition function is partial like OATL's.
METADATA = {"model_type": "timedCGS", "partial_transitions": True}

__all__ = [
    "METADATA",
    "AtomicProp",
    "Binary",
    "BooleanConst",
    "ClockExpr",
    "DemonicBinary",
    "DemonicOp",
    "Expr",
    "FreezeExpr",
    "SimpleTimeExpr",
    "Unary",
]
