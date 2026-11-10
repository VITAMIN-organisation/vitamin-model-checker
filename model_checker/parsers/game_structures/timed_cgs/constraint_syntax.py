"""Clock-constraint token syntax for timedCGS files, DBM parsing, and formula guards.

Operators are longest-first so ``>=`` is never split as ``>``.
``=`` is a reset; ``==`` is equality. Invariants are upper bounds only.
"""

import re

from model_checker.parsers.syntax_patterns import (
    COMPARISON_OPERATORS,
    COMPARISON_OPS_ALT,
)

# File-cell tokens that mean "no guard / no invariant on this cell".
NO_CONSTRAINT_TOKENS = frozenset({"0", "-", "*"})

BOUND_OPERATORS = COMPARISON_OPERATORS
INVARIANT_OPERATORS = ("<=", "<")
RESET_OPERATOR = "="
# A formula clock prefix does not treat ``==`` as a bound.
FORMULA_PREFIX_OPERATORS = ("<=", ">=", "<", ">")

_CLOCK = r"(\w+)"
_FORMULA_CLOCK = r"([a-zA-Z][a-zA-Z0-9_]*)"
_INVARIANT_OPS = "|".join(INVARIANT_OPERATORS)
_FORMULA_PREFIX_OPS = "|".join(FORMULA_PREFIX_OPERATORS)
_RESET = re.escape(RESET_OPERATOR)

# Clock_constraints cell: bound or reset, whole token.
CELL_CONSTRAINT_RE = re.compile(rf"^{_CLOCK}({COMPARISON_OPS_ALT}|{_RESET})(\d+)$")
INVARIANT_RE = re.compile(rf"^{_CLOCK}({_INVARIANT_OPS})(\d+)$")

# DBM: bound vs reset are separate so ``x=0`` is not read as a bound.
BOUND_RE = re.compile(rf"{_CLOCK}({COMPARISON_OPS_ALT})(\d+)")
RESET_RE = re.compile(rf"{_CLOCK}{_RESET}(\d+)")
MAX_CONSTRAINT_RE = re.compile(rf"{_CLOCK}\s*(?:{COMPARISON_OPS_ALT})\s*(\d+)")

CLOCK_BOUND_PREFIX_RE = re.compile(rf"^{_FORMULA_CLOCK}(?:{_FORMULA_PREFIX_OPS})")
BOUND_CONSTANT_RE = re.compile(rf"{_FORMULA_CLOCK}\s*(?:{COMPARISON_OPS_ALT})\s*(\d+)")
