"""Parsing helpers for coalition-constrained operators."""


def parse_coalition_constraint(formula_node_value: str) -> tuple[str, str]:
    """Parse ``<coalition><constraint>...`` into raw coalition and constraint text."""
    raw = formula_node_value.strip()
    if not raw.startswith("<"):
        raise ValueError(
            f"Invalid coalition constraint '{formula_node_value}': expected string starting with '<'."
        )

    parts = raw[1:].split(">")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Invalid coalition constraint '{formula_node_value}': expected '<J><constraint>'."
        )

    if not parts[1].startswith("<"):
        raise ValueError(
            f"Invalid coalition constraint '{formula_node_value}': constraint must start with '<'."
        )

    constraint = parts[1][1:].strip(">").strip()

    if not constraint:
        raise ValueError(
            f"Invalid coalition constraint '{formula_node_value}': constraint cannot be empty."
        )

    return parts[0], constraint


def parse_coalition_and_bound_vector(formula_node_value: str) -> tuple[str, list[int]]:
    """Parse ``<J><b1,b2,...>`` into coalition and integer vector."""
    coalition, constraint = parse_coalition_constraint(formula_node_value)
    bounds: list[int] = []
    for token in constraint.split(","):
        stripped = token.strip()
        if not stripped:
            raise ValueError(
                f"Invalid coalition-bound format '{formula_node_value}': empty bound value in list."
            )
        try:
            bounds.append(int(stripped))
        except ValueError as exc:
            raise ValueError(
                f"Invalid coalition-bound format '{formula_node_value}': {exc}"
            ) from exc

    return coalition, bounds


def parse_coalition_and_scalar_constraint(
    formula_node_value: str,
) -> tuple[str, int | float]:
    """Parse ``<J><n>`` into coalition and scalar numeric constraint."""
    coalition, constraint = parse_coalition_constraint(formula_node_value)
    last_error = None
    for parser in (int, float):
        try:
            return coalition, parser(constraint)
        except ValueError as error:
            last_error = error

    raise ValueError(
        f"Invalid coalition-cost format '{formula_node_value}': {last_error}"
    )
