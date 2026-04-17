"""
NatSL (Strategy Logic) model checker - Alternated semantics.

NatSL extends NatATL with both existential and universal strategy quantifiers.
This module implements the Alternated semantics where existential and universal
strategies alternate at each verification step.

The verification process:
1. Parse NatSL formula into separate existential and universal NatATL formulas
2. Call existential NatATL to search for winning strategies
3. Existential strategies are validated against all universal counter-strategies
"""

import logging
import time
from typing import Any, Dict

from model_checker.algorithms.explicit.NatSL.shared_recall import (
    existential_natatl_alternated as existentialNatATL,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.NatSL.conversion import (
    convert_parsed_natsl_to_natatl_separated,
)
from model_checker.parsers.formulas.NatSL.utils import (
    normalize_formula,
    validate_bindings,
)
from model_checker.utils.error_handler import (
    create_syntax_error,
    create_system_error,
    create_validation_error,
)

logger = logging.getLogger(__name__)


def model_checking(natsl_formula: str, model_path: str) -> Dict[str, Any]:
    """
    Execute model checking for NatSL with Alternated semantics.

    Converts the NatSL formula to paired NatATL formulas (existential and
    universal parts) and verifies using alternating strategy search.

    Example formula: E{1}xA{1}y:(x,1)(y,2)Fa
        - E{1}x: Existential quantifier for agent 1 with variable x
        - A{1}y: Universal quantifier for agent 1 with variable y
        - (x,1)(y,2)Fa: Path formula with strategy bindings

    Args:
        natsl_formula: NatSL formula string
        model_path: Path to model file

    Returns:
        Dictionary with:
        - "Satisfiability": True/False result
        - "error"/"error_type": If verification failed
    """
    if not natsl_formula or not natsl_formula.strip():
        return create_validation_error("Formula not entered")

    if not model_path:
        return create_validation_error("Model file not specified")

    try:
        start_time = time.time()
        result: Dict[str, Any] = {}

        logger.info("Starting NatSL verification (Alternated)")
        logger.debug("Formula: %s", natsl_formula)

        try:
            fully_negated, normalized_formula = normalize_formula(natsl_formula)
        except ValueError:
            return create_syntax_error("Error parsing the formula")

        parser = FormulaParserFactory.get_parser_instance("NatSL")
        parsed = parser.parse(normalized_formula)
        if not parsed:
            error_msg = (
                parser.errors[0] if parser.errors else "Error parsing the formula"
            )
            return create_syntax_error(error_msg)

        try:
            validate_bindings(parsed)
        except ValueError as e:
            return create_syntax_error(f"Formula validation error: {str(e)}")

        existential_natatl, universal_natatl = convert_parsed_natsl_to_natatl_separated(
            parsed, fully_negated=fully_negated, original_formula=natsl_formula
        )
        logger.debug("Existential NatATL formula: %s", existential_natatl)
        logger.debug("Universal NatATL formula: %s", universal_natatl)

        solution = existentialNatATL(
            model_path, existential_natatl[0], universal_natatl[0], start_time
        )

        result["Satisfiability"] = solution

        elapsed = time.time() - start_time
        logger.info(
            "NatSL verification (Alternated) completed in %.3f seconds", elapsed
        )

        return result

    except FileNotFoundError:
        return create_system_error(f"Model file not found: {model_path}")
    except ValueError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during NatSL Alternated verification")
        return create_system_error(
            f"Error during NatSL Alternated verification: {str(e)}"
        )
