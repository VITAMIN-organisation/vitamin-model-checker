"""Factory for creating formula parsers.

Creates and manages formula parser instances for temporal logics (CTL, ATL, LTL, etc.).
"""

from threading import Lock
from typing import Any

from model_checker.discovery import (
    discover_logic_resource,
)


import threading


class FormulaParserFactory:
    """Retrieves parsers for temporal logics, caching instances per-thread for efficiency and thread-safety."""

    _parser_classes = {}
    _lock: Lock = Lock()
    _local = threading.local()

    @staticmethod
    def get_parser_instance(logic_name: str) -> Any:
        """Get a thread-local parser instance for the specified logic.

        Args:
            logic_name: Name of the logic (e.g., "CTL", "ATL").

        Returns:
            A thread-local Parser instance (e.g. CTLParser, ATLParser) to ensure thread-safety.

        Raises:
            ImportError: If the parser module or class cannot be found.
        """
        # Initialize thread-local storage for instances if not present
        if not hasattr(FormulaParserFactory._local, "instances"):
            FormulaParserFactory._local.instances = {}

        if logic_name in FormulaParserFactory._local.instances:
            return FormulaParserFactory._local.instances[logic_name]

        with FormulaParserFactory._lock:
            if logic_name in FormulaParserFactory._parser_classes:
                parser_class = FormulaParserFactory._parser_classes[logic_name]
            else:
                try:
                    parser_class = discover_logic_resource(
                        logic_name=logic_name,
                        group="vitamin.parsers",
                        resource_type_label="Parser",
                    )
                    FormulaParserFactory._parser_classes[logic_name] = parser_class
                except (ImportError, LookupError) as e:
                    raise ImportError(
                        f"Could not load parser for logic '{logic_name}': {e}"
                    ) from e

        # Instantiate and cache in thread-local storage
        instance = parser_class()
        FormulaParserFactory._local.instances[logic_name] = instance
        return instance
