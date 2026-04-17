"""
NatSL (Strategy Logic) model checker - Sequential semantics.

NatSL extends NatATL with both existential and universal strategy quantifiers.
This module implements Sequential semantics where existential strategies are
evaluated completely before universal strategies are checked.

The verification process:
1. Parse NatSL formula into separate existential and universal NatATL formulas
2. Run existential NatATL to find candidate strategies (collect all pruned trees)
3. If direct solution found, return immediately
4. Otherwise, check collected trees against all universal counter-strategies
"""

import logging
import time
from typing import Any, Dict

from model_checker.algorithms.explicit.NatSL.shared_recall import (
    existential_natatl_sequential as existentialNatATL,
)
from model_checker.algorithms.explicit.NatSL.shared_recall import (
    universal_natatl_recall as universalNatATL,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.NatSL.conversion import (
    convert_parsed_natsl_to_natatl_separated,
)
from model_checker.parsers.formulas.NatSL.utils import (
    count_universal_agents,
    extract_existential_agents,
    extract_universal_agents,
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
    Execute model checking for NatSL with Sequential semantics.

    Example formula: E{1}xA{1}y:(x,1)(y,2)Fa
        - E{1}x: Existential quantifier for agent 1 with variable x
        - A{1}y: Universal quantifier for agent 1 with variable y
        - (x,1)(y,2)Fa: Path formula with strategy bindings

    Sequential semantics differs from Alternated:
    - Existential strategies are fully enumerated first
    - Pruned trees are collected during existential phase
    - Universal strategies are then checked against all collected trees

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
        result: Dict[str, Any] = {}
        start_time = time.time()

        logger.info("Starting NatSL verification (Sequential)")
        logger.debug("Formula: %s", natsl_formula)

        # Parse and validate formula structure
        try:
            fully_negated, normalized_formula = normalize_formula(natsl_formula)
        except ValueError:
            return create_syntax_error("Error parsing the formula")

        parser = FormulaParserFactory.get_parser_instance("NatSL")
        parsed = parser.parse(normalized_formula)

        if parsed:
            try:
                validate_bindings(parsed)
                existential_agents = extract_existential_agents(parsed)
                universal_agents = extract_universal_agents(parsed)
                n_universal = count_universal_agents(universal_agents)

                logger.debug("Existential agents: %s", existential_agents)
                logger.debug("Universal agents: %s", universal_agents)
                logger.debug("Number of universal agents: %d", n_universal)

            except ValueError as e:
                return create_syntax_error(f"Formula validation error: {str(e)}")
        else:
            error_msg = (
                parser.errors[0] if parser.errors else "Error parsing the formula"
            )
            return create_syntax_error(error_msg)

        existential_natatl, universal_natatl = convert_parsed_natsl_to_natatl_separated(
            parsed, fully_negated=fully_negated, original_formula=natsl_formula
        )
        logger.debug("Existential NatATL formula: %s", existential_natatl)
        logger.debug("Universal NatATL formula: %s", universal_natatl)

        solution, trees, height, cgs = existentialNatATL(
            model_path, existential_natatl[0]
        )

        if solution:
            elapsed = time.time() - start_time
            logger.info("Direct existential solution found in %.3f seconds", elapsed)
            result["Satisfiability"] = solution
            return result

        logger.info(
            "No direct solution. Checking %d candidate trees against universal strategies",
            len(trees),
        )

        result["Satisfiability"] = universalNatATL(
            trees,
            model_path,
            universal_natatl[0],
            n_universal,
            height,
            start_time,
            cgs,
        )

        elapsed = time.time() - start_time
        logger.info("NatSL verification completed in %.3f seconds", elapsed)

        return result

    except FileNotFoundError:
        return create_system_error(f"Model file not found: {model_path}")
    except ValueError:
        # Standard classification by runner.py
        raise
    except Exception as e:
        logger.exception("Unexpected error during NatSL Sequential verification")
        return create_system_error(
            f"Error during NatSL Sequential verification: {str(e)}"
        )
