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
