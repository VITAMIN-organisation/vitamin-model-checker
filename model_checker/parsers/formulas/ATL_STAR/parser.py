"""ATL* parser entry point for `vitamin.parsers`.

- The parsing is in `grammar.py`, a hand-written parser. PLY does not fit, because
  an ATL* coalition can cover any nested path formula, not one temporal operator.
- This file gives it the `.parse(formula, n_agent=...)` and `.errors` interface
  that `FormulaParserFactory` expects.
"""

from typing import Any

from model_checker.parsers.formulas.ATL_STAR.grammar import (
    ATLStarParseError,
    parse,
)


class ATLStarParser:
    """`parse` returns a `Formula`, or None with the reason in `errors`."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def parse(self, formula: str, n_agent: int | None = None, **_: Any):
        """Parse `formula`, returning a `Formula` or None (see `self.errors`)."""
        self.errors = []
        try:
            return parse(formula, num_agents=n_agent)
        except ATLStarParseError as e:
            self.errors.append(str(e))
            return None
