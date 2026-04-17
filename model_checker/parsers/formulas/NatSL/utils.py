"""Utility functions for NatSL formula processing."""

import re


def validate_bindings(parsed_formula):
    """Verify that all quantifier variables are associated with an agent."""
    quantifiers, binding_pairs, _ = parsed_formula
    bound_variables = {var for var, _ in binding_pairs}
    quantified_variables = {binding_var for _, binding_var, _ in quantifiers}
    for _, binding_var, _ in quantifiers:
        if binding_var not in bound_variables:
            raise ValueError(
                f"Error: Binding variable '{binding_var}' not associated with any agent."
            )
    for bound_var in bound_variables:
        if bound_var not in quantified_variables:
            raise ValueError(
                f"Error: Binding variable '{bound_var}' has no corresponding quantifier."
            )


def count_agents(parsed_formula):
    """Count the number of unique agents present in the formula."""
    _, binding_pairs, _ = parsed_formula
    agents = {int(agent) for _, agent in binding_pairs}
    return len(agents)


def _extract_agents_by_quantifier(parsed_formula, quantifier_char):
    """Extract agent numbers for variables bound to the given quantifier (E or A)."""
    quantifiers, binding_pairs, _ = parsed_formula
    variables = [var for q, var, _ in quantifiers if q == quantifier_char]
    map_vars_to_agents = dict(binding_pairs)
    return [
        int(map_vars_to_agents[var]) for var in variables if var in map_vars_to_agents
    ]


def extract_existential_agents(parsed_formula):
    """Extract existential agents from the NatSL formula."""
    return _extract_agents_by_quantifier(parsed_formula, "E")


def extract_universal_agents(parsed_formula):
    """Extract universal agents from the NatSL formula."""
    return _extract_agents_by_quantifier(parsed_formula, "A")


def count_universal_agents(universal_agents):
    """Count the number of universal agents."""
    return len(universal_agents)


def count_existential_agents(existential_agents):
    """Count the number of existential agents."""
    return len(existential_agents)


def extract_formula(parsed_formula):
    """Extract the temporal operator and proposition from the NatSL formula."""
    _, _, temporal_expr = parsed_formula
    if isinstance(temporal_expr, tuple):
        if len(temporal_expr) == 2:
            operator, proposition = temporal_expr
            return operator + proposition
        if len(temporal_expr) == 3 and temporal_expr[0] == "!":
            _, operator, proposition = temporal_expr
            return "!" + operator + proposition
    raise ValueError("Unexpected temporal expression format")


def convert_natsl_to_ctl(parsed_formula, negate: bool):
    """Convert a parsed NatSL formula to the corresponding CTL formula using the universal quantifier 'A'."""
    _, _, temporal_expr = parsed_formula
    temporal_operator, proposition = temporal_expr
    ctl_formula = (
        f"!A{temporal_operator}{proposition}"
        if negate
        else f"A{temporal_operator}{proposition}"
    )
    return ctl_formula


def normalize_formula(formula):
    """Normalize formula by handling outer negation."""
    fully_negated = False

    if formula.startswith("!(") and formula.endswith(")"):
        fully_negated = True
        formula = formula[2:-1]

    quantifiers_part, rest = formula.split(":", 1)

    if fully_negated:
        pattern = r"\b(E|A)(\{\d+\})?\s*[a-zA-Z_][a-zA-Z0-9_]*"

        def swap_quantifier(match):
            s = match.group(0)
            if s.startswith("E"):
                return "A" + s[1:]
            elif s.startswith("A"):
                return "E" + s[1:]
            return s

        normalized_quantifiers = re.sub(pattern, swap_quantifier, quantifiers_part)
    else:
        normalized_quantifiers = quantifiers_part

    normalized_formula = normalized_quantifiers + ":" + rest
    return fully_negated, normalized_formula


def skolemize_formula(parsed_formula):
    """Reorder quantifiers so existentials come first, then universals. Does not perform skolemization."""
    quantifiers, binding_pairs, temporal_expr = parsed_formula

    existentials = [(q, var, bound) for q, var, bound in quantifiers if q == "E"]
    universals = [(q, var, bound) for q, var, bound in quantifiers if q == "A"]

    skolemized_quantifiers = existentials + universals
    return (skolemized_quantifiers, binding_pairs, temporal_expr)
