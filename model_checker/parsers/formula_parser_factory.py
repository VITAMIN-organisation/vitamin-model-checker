"""Factory for creating formula parsers.

Creates and manages formula parser instances for temporal logics (CTL, ATL, LTL, etc.).
"""

import logging
from threading import Lock
from typing import Any, List

from model_checker.discovery import (
    discover_logic_resource,
    get_entry_points,
    is_integrated_logic,
)

logger = logging.getLogger(__name__)


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

    @staticmethod
    def parse_formula(logic_name: str, formula: str, **kwargs: Any) -> Any:
        """Parse a formula using the specified logic."""
        parser = FormulaParserFactory.get_parser_instance(logic_name)
        if hasattr(parser, "parse"):
            return parser.parse(formula, **kwargs)

        raise AttributeError(f"Parser for {logic_name} does not have a parse method.")

    @staticmethod
    def verify_token(logic_name: str, token_name: str, string: str) -> bool:
        """Verify if a token exists in the string for the specified logic."""
        parser = FormulaParserFactory.get_parser_instance(logic_name)

        if hasattr(parser, "verify"):
            return parser.verify(token_name, string)

        raise AttributeError(
            f"Parser for {logic_name} does not have a verification function."
        )

    @classmethod
    def warmup(cls, parser_names: List[str] = None) -> None:
        """Pre-initialize parsers to generate tables at startup."""
        if parser_names is None:
            # Discover all available parsers via entry points
            eps = get_entry_points("vitamin.parsers")
            parser_names = list({ep.name for ep in eps})

            # Also check the formulas directory for integrated logics
            try:
                from pathlib import Path

                import model_checker.parsers.formulas as formulas_pkg

                pkg_path = Path(formulas_pkg.__file__).parent
                for item in pkg_path.iterdir():
                    if item.is_dir() and (item / "parser.py").is_file():
                        # Only include if it's either in entry points OR in the integration registry
                        if item.name not in parser_names and is_integrated_logic(
                            item.name
                        ):
                            parser_names.append(item.name)
            except Exception as e:
                logger.warning(f"Failed to scan formulas directory during warmup: {e}")

        logger.info(f"Warming up {len(parser_names)} formula parsers...")

        for parser_name in parser_names:
            try:
                cls.get_parser_instance(parser_name)
                logger.debug(f"[OK] Warmed up {parser_name} parser")
            except Exception as e:
                logger.warning(f"[WARNING] Failed to warm up {parser_name} parser: {e}")

        logger.info(f"Parser warmup complete. {len(cls._instances)} parsers ready.")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached parser instances."""
        with cls._lock:
            cls._instances.clear()
        logger.debug("Parser cache cleared")
