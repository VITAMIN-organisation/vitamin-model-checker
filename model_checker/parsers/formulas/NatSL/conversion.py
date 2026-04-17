"""NatSL to NatATL conversion helpers.

This module converts already-parsed NatSL formulas to NatATL strings expected
by downstream model checkers.
"""


def _build_existential_natatl_formula(
    existential_vars, var_to_agent, temporal_operator, proposition
):
    """Build the single merged existential NatATL formula in canonical NatATL format."""
    if not existential_vars:
        return None
    coalition = [
        var_to_agent[var] for _, var, _ in existential_vars if var in var_to_agent
    ]
    coalition_str = ",".join(map(str, coalition))
    bounds = [bound for _, var, bound in existential_vars if var in var_to_agent]
    k = max(bounds) if bounds else 1
    return f"<{{{coalition_str}}}, {k}>{temporal_operator}{proposition}"


def _build_universal_natatl_formulas(
    universal_vars, var_to_agent, temporal_operator, proposition
):
    """Build list of NatATL formulas, one per universal variable."""
    formulas = []
    for _, var, bound in universal_vars:
        if var not in var_to_agent:
            raise ValueError(
                f"Universal variable '{var}' not associated with any agent."
            )
        agent = var_to_agent[var]
        formulas.append(f"<{{{agent}}}, {bound}>{temporal_operator}{proposition}")
    return formulas


def _convert_structures_to_natatl_separated(
    temporal_operator,
    proposition,
    var_to_agent,
    existential_vars,
    universal_vars,
    negate_prefix,
):
    """Convert NatSL parse structures into separated existential/universal NatATL formulas."""
    existential_formulas = []
    existential_formula = _build_existential_natatl_formula(
        existential_vars, var_to_agent, temporal_operator, proposition
    )
    if existential_formula is not None:
        existential_formulas.append(existential_formula)

    universal_formulas = _build_universal_natatl_formulas(
        universal_vars, var_to_agent, temporal_operator, proposition
    )

    if negate_prefix:
        existential_formulas = [f"!{f}" for f in existential_formulas]
        universal_formulas = [f"!{f}" for f in universal_formulas]

    return existential_formulas, universal_formulas


def convert_parsed_natsl_to_natatl_separated(
    parsed_formula, fully_negated=False, original_formula=""
):
    """Convert an already parsed NatSL formula to separated NatATL formulas."""
    negate_prefix = fully_negated or original_formula.startswith("!")
    quantifiers, binding_pairs, temporal_expr = parsed_formula
    temporal_operator, proposition = temporal_expr
    var_to_agent = {var: int(agent) for var, agent in binding_pairs}
    existential_vars = [(q, var, bound) for q, var, bound in quantifiers if q == "E"]
    universal_vars = [(q, var, bound) for q, var, bound in quantifiers if q == "A"]
    return _convert_structures_to_natatl_separated(
        temporal_operator,
        proposition,
        var_to_agent,
        existential_vars,
        universal_vars,
        negate_prefix,
    )
