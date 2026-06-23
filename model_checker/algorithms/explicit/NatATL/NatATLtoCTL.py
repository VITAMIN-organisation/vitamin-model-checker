"""NatATL to CTL conversion and coalition extraction (parser-backed)."""

import logging
from typing import List

from model_checker.algorithms.explicit.NatATL.natatl_ast import (
    analyze_natatl_formula,
    get_agents_from_ast,
    get_k_value_from_ast,
    natatl_ast_to_ctl,
    parse_natatl_formula,
)

logger = logging.getLogger(__name__)


def natatl_to_ctl(natatl_formula: str, n_agent: int = 0) -> str:
    """
    Transform a NatATL formula into a CTL formula (FORALL path quantifier).

    Uses NatATLParser AST when n_agent > 0; otherwise parses with n_agent=0
    (coalition range checks apply only when n_agent is set).
    """
    ast = parse_natatl_formula(natatl_formula, n_agent=n_agent)
    return natatl_ast_to_ctl(ast)


def get_agents_from_natatl(natatl_formula: str, n_agent: int = 0) -> List[int]:
    """Extract agent indices from coalition modalities in a NatATL formula."""
    ast = parse_natatl_formula(natatl_formula, n_agent=n_agent)
    return get_agents_from_ast(ast)


def get_k_value(natatl_formula: str, n_agent: int = 0) -> int:
    """Return strategy-complexity bound k from a NatATL formula."""
    ast = parse_natatl_formula(natatl_formula, n_agent=n_agent)
    return get_k_value_from_ast(ast)


def prepare_natatl_formula(natatl_formula: str, n_agent: int):
    """Parse NatATL once and return CTL string, agents, and k."""
    _, ctl_formula, agents, k = analyze_natatl_formula(natatl_formula, n_agent)
    logger.debug("NatATL formula: %s", natatl_formula)
    logger.debug("Converted CTL formula: %s", ctl_formula)
    return ctl_formula, agents, k
