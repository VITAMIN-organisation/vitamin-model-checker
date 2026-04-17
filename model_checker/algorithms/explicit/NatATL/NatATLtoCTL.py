import logging
import re
from typing import List, Set

from model_checker.parsers.formula_parser_factory import FormulaParserFactory

logger = logging.getLogger(__name__)


_CAPACITY_PATTERN = r"(!?|not)?<\{((?:\d+,)*\d+)\},\s*(\d+)>"


def natatl_to_ctl(natatl_formula: str) -> str:
    """
    Transform a NatATL formula into a CTL formula (using "FORALL" path quantifier).

    Accepts canonical NatATL syntax only: <{1,2}, k> Op phi.
    """
    pattern = _CAPACITY_PATTERN

    match = re.search(pattern, natatl_formula)
    if not match:
        raise ValueError(f"Invalid NatATL formula format: {natatl_formula}")

    negation = match.group(1)
    ctl_formula = re.sub(pattern, "A", natatl_formula)

    if negation:
        ctl_formula = f"!({ctl_formula})"

    # Early validation: ensure resulting CTL is syntactically correct
    ctl_parser = FormulaParserFactory.get_parser_instance("CTL")
    if ctl_parser.parse(ctl_formula) is None:
        err_detail = (
            ctl_parser.errors[0] if ctl_parser.errors else "syntactically invalid"
        )
        raise ValueError(f"Resulting CTL formula '{ctl_formula}' is {err_detail}")

    return ctl_formula


def get_agents_from_natatl(natatl_formula: str) -> List[int]:
    """
    Extract all unique agents involved in NatATL coalitions from the formula.

    Uses canonical <{agents}, k> syntax only.
    """
    pattern = _CAPACITY_PATTERN
    index = 2  # coalition group in capacity pattern

    matches = re.findall(pattern, natatl_formula)

    agents: Set[int] = set()
    for match in matches:
        agents_str = match[index - 1] if len(match) >= index else ""
        if not agents_str:
            continue
        agents.update(int(agent) for agent in agents_str.split(",") if agent)

    return sorted(agents)


def get_k_value(natatl_formula: str) -> int:
    """
    Return the complexity bound 'k' from canonical <{A}, k> NatATL syntax.
    """
    match = re.search(_CAPACITY_PATTERN, natatl_formula)
    if match:
        try:
            return int(match.group(3))
        except (TypeError, ValueError):
            logger.debug(
                "Failed to parse NatATL capacity bound from %r", natatl_formula
            )
            return 1
    raise ValueError(
        f"NatATL formula must use <{{agents}}, k> syntax: {natatl_formula!r}"
    )
