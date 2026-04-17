"""Shared utilities for model checker interfaces.

This module provides common boilerplate reduction for explicit model checking interfaces,
handling validation, parser creation, file reading, and error handling consistently.
"""

import ast
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from model_checker.models.model_factory import (
    create_model_parser_for_logic,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol
from model_checker.utils.error_handler import (
    create_model_error,
    create_semantic_error,
    create_syntax_error,
    create_system_error,
    create_validation_error,
)


def execute_model_checking_with_parser(
    formula: str,
    filename: str,
    logic_type: str,
    core_checking_func: Callable[[Any, str], Dict[str, Any]],
    pre_validation_func: Optional[Callable[[Any], Optional[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """
    Shared wrapper for model checking execution that handles common boilerplate.

    This function handles:
    - Input validation (formula and filename)
    - Parser creation using the factory
    - File reading
    - Error handling (FileNotFoundError, ValueError, Exception)
    - Delegates core checking logic to the provided function

    Args:
        formula: Formula string to check
        filename: Path to model file
        logic_type: Logic type identifier (e.g., "ATL", "CTL", "OATL")
        core_checking_func: Function that performs the actual model checking.
            Signature: (parser, formula) -> Dict[str, Any]
            This function should handle:
            - Formula parsing
            - Tree building
            - Tree solving
            - Result construction
            It should return early with error dictionaries for syntax/semantic errors.
        pre_validation_func: Optional function to validate the model after reading.
            Signature: (parser) -> Optional[Dict[str, Any]]
            If it returns a dict, that dict is returned as an error response.
            If it returns None, execution continues.

    Returns:
        Dictionary with keys: "res" (result string), "initial_state" (verification
        string), and optionally "error" (structured error information).
    """
    # Input validation
    if not formula or not formula.strip():
        return create_validation_error("Formula not entered")

    if not filename:
        return create_validation_error("Model file not specified")

    try:
        parser = create_model_parser_for_logic(filename, logic_type)
        parser.filename = filename  # Attach filename for algorithms that need it
        parser.read_file(filename)

        if pre_validation_func is not None:
            validation_error = pre_validation_func(parser)
            if validation_error is not None:
                return validation_error

        return core_checking_func(parser, formula)

    except FileNotFoundError:
        return create_system_error(f"Model file not found: {filename}")
    except ValueError as e:
        error_msg = str(e)
        if "[SEMANTIC]" in error_msg:
            return create_semantic_error(error_msg.replace("[SEMANTIC]", "").strip())
        if "[SYNTAX]" in error_msg:
            return create_syntax_error(error_msg.replace("[SYNTAX]", "").strip())
        if "[MODEL]" in error_msg:
            return create_model_error(error_msg.replace("[MODEL]", "").strip())

        if "index" in error_msg.lower() or "dimension" in error_msg.lower():
            return create_model_error(error_msg)

        syntax_keywords = (
            "formula",
            "parsing",
            "syntax",
            "unexpected token",
            "syntactically",
            "invalid natatl",
            "could not extract",
        )
        if any(kw in error_msg.lower() for kw in syntax_keywords):
            return create_syntax_error(error_msg)

        semantic_keywords = ("atom", "does not exist", "not found", "unknown")
        if any(kw in error_msg.lower() for kw in semantic_keywords):
            return create_semantic_error(error_msg)

        return create_system_error(error_msg)
    except Exception as e:
        return create_system_error(f"Error during model checking: {str(e)}")


# -----------------------------
# Shared parsing/helper utilities
# -----------------------------


def parse_state_set_literal(value: Optional[Union[str, Set[str]]]) -> Set[str]:
    """
    Return a set of state names from a node value that may be already a set or a string.

    If value is already a set, returns a copy so callers can mutate safely.
    If value is a string (e.g. from tree nodes), parses it with ast.literal_eval.
    Returns an empty set for None, empty string, or invalid inputs.
    """
    if value is None or value == "":
        return set()
    if isinstance(value, set):
        return {str(s) for s in value}
    if value in ("set()", "{}"):
        return set()

    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, set):
            return {str(item).strip("'\"") for item in parsed}
        if isinstance(parsed, (list, tuple)):
            return {str(item).strip("'\"") for item in parsed}
    except (ValueError, SyntaxError, TypeError):
        pass

    return set()


def parse_tuple_list_literal(value: str) -> List[Tuple[str, float]]:
    """
    Safely parse a string representing a list of (state, value) tuples into a list.
    Non-decodable inputs yield an empty list rather than raising.
    """
    if value in ("[]", None, ""):
        return []
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, (list, tuple)):
            result: List[Tuple[str, float]] = []
            for item in parsed:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    state, val = item
                    result.append((str(state), float(val)))
            return result
    except (ValueError, SyntaxError, TypeError):
        return []
    return []


def indices_to_state_names(cgs: CGSProtocol, indices: Iterable[int]) -> Set[str]:
    """
    Convert iterable of state indices into the corresponding state names for the given CGS.
    """
    return {str(cgs.get_state_name_by_index(idx)) for idx in indices}


def states_where_prop_holds(cgs: CGSProtocol, prop: str) -> Optional[Set[str]]:
    """
    Return the set of state names where the given proposition holds.
    Returns None if the proposition is unknown in the CGS.
    """
    idx = cgs.get_atom_index(prop)
    if idx is None:
        return None

    matching: Set[str] = set()
    prop_matrix = cgs.matrix_prop
    for state_idx, row in enumerate(prop_matrix):
        if row[int(idx)] == 1:
            matching.add(str(cgs.get_state_name_by_index(state_idx)))
    return matching


def build_formula_tree(tpl: Any, atom_resolver: Callable[[Any], Optional[str]]):
    """
    Build a binary tree (binarytree.Node) from a parsed formula tuple, resolving atoms
    through the provided callback that returns the leaf node value or None on failure.
    """
    from binarytree import Node

    if isinstance(tpl, tuple):
        root = Node(tpl[0])
        if len(tpl) > 1:
            left_child = build_formula_tree(tpl[1], atom_resolver)
            if left_child is None:
                return None
            root.left = left_child
            if len(tpl) > 2:
                right_child = build_formula_tree(tpl[2], atom_resolver)
                if right_child is None:
                    return None
                root.right = right_child
    else:
        leaf_value = atom_resolver(tpl)
        if leaf_value is None:
            return None
        if isinstance(leaf_value, set):
            leaf_value = str(tuple(sorted(leaf_value)))
        root = Node(leaf_value)

    return root
