"""ATL* parser entry point (`vitamin.parsers`).

Not PLY-based, unlike every other VITAMIN parser: in ATL* a coalition can
scope over an arbitrarily nested path formula (unlike ATL, where it is
always immediately followed by exactly one temporal operator), so there is
no single grammar production to special-case the way ATL's parser does.
`grammar.py` is a hand-written recursive-descent parser instead; this file
only adapts its `parse`/`ATLStarParseError` to the `.parse(formula,
n_agent=...)` / `.errors` interface `FormulaParserFactory` expects.
"""

from typing import Any

from model_checker.parsers.formulas.ATL_STAR.grammar import (
    ATLStarParseError,
    parse,
)


class ATLStarParser:
    """Parser for ATL* formulas.

    Use parse(formula) to get a `Formula` AST or None on invalid input.
    Pass n_agent to validate coalitions' agent ids against the model.
    """

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
