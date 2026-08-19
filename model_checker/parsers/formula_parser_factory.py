"""Factory for creating formula parsers.

Creates and manages formula parser instances for temporal logics (CTL, ATL, LTL, etc.).
"""

from threading import Lock
from typing import Any

from model_checker.discovery import (
    discover_logic_resource,
)


class FormulaParserFactory:
    """Retrieves parsers for temporal logics, caching instances for efficiency."""

    _instances = {}
    _lock: Lock = Lock()

    @staticmethod
    def get_parser_instance(logic_name: str) -> Any:
        """Get or create a parser instance for the specified logic.

        Args:
            logic_name: Name of the logic (e.g., "CTL", "ATL").

        Returns:
            Parser instance (e.g. CTLParser, ATLParser).

        Raises:
            ImportError: If the parser module or class cannot be found.
        """
        with FormulaParserFactory._lock:
            if logic_name in FormulaParserFactory._instances:
                return FormulaParserFactory._instances[logic_name]

        try:
            parser_class = discover_logic_resource(
                logic_name=logic_name,
                group="vitamin.parsers",
                resource_type_label="Parser",
            )

            instance = parser_class()
            with FormulaParserFactory._lock:
                FormulaParserFactory._instances[logic_name] = instance
            return instance

        except (ImportError, LookupError) as e:
            raise ImportError(
                f"Could not load parser for logic '{logic_name}': {e}"
            ) from e
