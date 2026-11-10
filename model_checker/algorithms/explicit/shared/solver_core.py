"""Generic bottom-up formula tree solver for ATL-like logics."""

from collections.abc import Callable
from typing import Any


def solve_formula_tree(
    cgs: Any,
    node: Any,
    parser_instance: Any,
    unary_map: dict[str, Callable],
    binary_map: dict[str, Callable],
    unary_key_fn: Callable[[Any, Any], str | None],
    binary_key_fn: Callable[[Any, Any], str | None],
    boolean_keys: set[str],
    extra_args: tuple = (),
    cache: dict | None = None,
) -> None:
    """Evaluate the formula tree bottom-up, storing satisfying states at each node."""
    if cache is not None:
        node_key = (
            str(node.value)
            + (str(node.left) if node.left else "")
            + (str(node.right) if node.right else "")
        )
        if node_key in cache:
            node.value = cache[node_key]
            return

    if node.left is not None:
        solve_formula_tree(
            cgs,
            node.left,
            parser_instance,
            unary_map,
            binary_map,
            unary_key_fn,
            binary_key_fn,
            boolean_keys,
            extra_args,
            cache,
        )
    if node.right is not None:
        solve_formula_tree(
            cgs,
            node.right,
            parser_instance,
            unary_map,
            binary_map,
            unary_key_fn,
            binary_key_fn,
            boolean_keys,
            extra_args,
            cache,
        )

    val = node.value
    if node.right is None:
        key = unary_key_fn(parser_instance, val)
        if key and key in unary_map:
            if key in boolean_keys:
                unary_map[key](cgs, node)
            else:
                unary_map[key](cgs, node, *extra_args)
    elif node.left is not None and node.right is not None:
        key = binary_key_fn(parser_instance, val)
        if key and key in binary_map:
            if key in boolean_keys:
                binary_map[key](cgs, node)
            else:
                binary_map[key](cgs, node, *extra_args)

    if cache is not None:
        cache[node_key] = node.value
