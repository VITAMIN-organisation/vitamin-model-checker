"""Generated BaseLogicParser wrapper for TOL.

AUTOMATICALLY GENERATED - DO NOT EDIT MANUALLY
This file is managed by the VITAMIN Module Integrator.
"""

from typing import Any
from model_checker.parsers.formulas.shared_parser import BaseLogicParser
from model_checker.parsers.formulas.TOL.parser import TOLParser

class TOLParserWrapper(BaseLogicParser):
    """Bridge for TOLParser to VMC BaseLogicParser."""

    def __init__(self, **kwargs: Any):
        super().__init__()
        self.original_parser = TOLParser(**kwargs)

    def parse(self, formula: str, **kwargs: Any) -> Any:
        """Delegate parsing to the original parser and capture errors."""
        self.errors = []
        try:
            # Most existing parser implementations take formula as first argument
            result = self.original_parser.parse(formula, **kwargs)

            # If the original parser has its own errors attribute, sync it
            if hasattr(self.original_parser, "errors") and self.original_parser.errors:
                self.errors.extend(self.original_parser.errors)

            return result
        except Exception as e:
            self.logger.debug(f"Wrapped parser failed: {e}")
            self.errors.append(str(e))
            return None

    def verify(self, name: str, string: str) -> bool:
        """Delegate verification if supported by the original parser."""
        if hasattr(self.original_parser, "verify"):
            return self.original_parser.verify(name, string)
        return super().verify(name, string)
