"""NatATL to CTL conversion and coalition extraction (parser-backed)."""

import logging
import re

from model_checker.algorithms.explicit.NatATL.natatl_ast import (
    analyze_natatl_formula,
    get_agents_from_ast,
    get_k_value_from_ast,
    natatl_ast_to_ctl,
    parse_natatl_formula,
)

logger = logging.getLogger(__name__)

_NATATL_AGENTS_IN_MODAL_RE = re.compile(r"<\{([\d,]+)\},\s*\d+>")


def _n_agent_for_conversion(natatl_formula: str, n_agent: int) -> int:
    """Use model agent count when set; otherwise allow agents present in the formula.

    Parser range checks are fail-closed. Conversion helpers historically defaulted
    to n_agent=0 for syntax-only transforms, so when no model size is supplied we
    take the max agent id appearing in capacity modals as the ceiling.
    """
    if n_agent > 0:
        return n_agent
    found: list[int] = []
    for match in _NATATL_AGENTS_IN_MODAL_RE.finditer(natatl_formula):
        found.extend(int(part) for part in match.group(1).split(",") if part.strip())
    return max(found) if found else 0


def natatl_to_ctl(natatl_formula: str, n_agent: int = 0) -> str:
    """
    Transform a NatATL formula into a CTL formula (FORALL path quantifier).

    When n_agent > 0, coalition agents must lie in [1, n_agent]. When n_agent is 0
    (syntax-only conversion), the ceiling is the largest agent id in the formula.
    """
    ast = parse_natatl_formula(
        natatl_formula, n_agent=_n_agent_for_conversion(natatl_formula, n_agent)
    )
    return natatl_ast_to_ctl(ast)


def get_agents_from_natatl(natatl_formula: str, n_agent: int = 0) -> list[int]:
    """Extract agent indices from coalition modalities in a NatATL formula."""
    ast = parse_natatl_formula(
        natatl_formula, n_agent=_n_agent_for_conversion(natatl_formula, n_agent)
    )
    return get_agents_from_ast(ast)


def get_k_value(natatl_formula: str, n_agent: int = 0) -> int:
    """Return strategy-complexity bound k from a NatATL formula."""
    ast = parse_natatl_formula(
        natatl_formula, n_agent=_n_agent_for_conversion(natatl_formula, n_agent)
    )
    return get_k_value_from_ast(ast)


def prepare_natatl_formula(natatl_formula: str, n_agent: int):
    """Parse NatATL once and return CTL string, agents, and k."""
    _, ctl_formula, agents, k = analyze_natatl_formula(natatl_formula, n_agent)
    logger.debug("NatATL formula: %s", natatl_formula)
    logger.debug("Converted CTL formula: %s", ctl_formula)
    return ctl_formula, agents, k
