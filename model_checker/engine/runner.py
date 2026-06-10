"""Shared helpers for explicit model checking entry points."""

import ast
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from model_checker.models.model_factory import (
    create_model_parser_for_logic,
)
from model_checker.parsers.game_structures.cgs import CGSProtocol
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
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
    """Validate input, load the model, and run core_checking_func(parser, formula)."""
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


def bind_model_checking(
    logic_type: str,
    core_checking_func: Callable[[Any, str], Dict[str, Any]],
    pre_validation_func: Optional[Callable[[Any], Optional[Dict[str, Any]]]] = None,
) -> Callable[[str, str], Dict[str, Any]]:
    """Return a model_checking entry point for the given logic and core checker."""

    def model_checking(formula: str, filename: str) -> Dict[str, Any]:
        return execute_model_checking_with_parser(
            formula,
            filename,
            logic_type,
            core_checking_func,
            pre_validation_func,
        )

    return model_checking


def bind_resource_bounded_model_checking(
    logic_type: str,
    core_checking_func: Callable[[Any, str], Dict[str, Any]],
    pre_validation_func: Optional[Callable[[Any], Optional[Dict[str, Any]]]] = None,
) -> Callable[[str, str], Dict[str, Any]]:
    """Return a model_checking entry point that prefilters with unbounded ATL."""

    full_checking = bind_model_checking(
        logic_type, core_checking_func, pre_validation_func
    )

    def model_checking(formula: str, filename: str) -> Dict[str, Any]:
        from model_checker.algorithms.explicit.ATL import (
            model_checking as atl_model_checking,
        )
        from model_checker.algorithms.explicit.shared.resource_bounded_to_atl import (
            resource_bounded_atl_to_atl,
        )

        atl_result = atl_model_checking(resource_bounded_atl_to_atl(formula), filename)
        if "error" in atl_result:
            return atl_result
        if str(atl_result.get("initial_state", "")).endswith(": False"):
            return atl_result

        return full_checking(formula, filename)

    return model_checking


# -----------------------------
# Shared parsing/helper utilities
# -----------------------------


def parse_state_set_literal(value: Optional[Union[str, Set[str]]]) -> Set[str]:
    """Parse a state set from a set, tuple string, or tree node value."""
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
    """Parse a list of (state, value) pairs from a string; return [] on failure."""
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


def states_where_prop_holds(cgs: CGSProtocol, prop: str) -> Optional[Set[str]]:
    """Return states where prop holds, or None if the proposition is unknown."""
    idx = proposition_index(cgs.atomic_propositions, prop)
    if idx is None:
        return None

    matching: Set[str] = set()
    prop_matrix = cgs.matrix_prop
    for state_idx, row in enumerate(prop_matrix):
        if row[int(idx)] == 1:
            matching.add(str(cgs.get_state_name_by_index(state_idx)))
    return matching


def build_formula_tree(tpl: Any, atom_resolver: Callable[[Any], Optional[str]]):
    """Build a formula tree from a parsed tuple; atom_resolver fills leaf values."""
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
