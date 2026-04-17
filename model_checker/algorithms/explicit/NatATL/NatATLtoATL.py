import re
from typing import Match


def natatl_to_atl(natatl_formula: str) -> str:
    """
    Transform a NatATL formula into an ATL formula by removing the complexity bounds.

    Example:
        "<{1,2},4>Xa" -> "<{1,2}>Xa"
    """
    k_pattern = r"<\{((?:\d+,)*\d+)\},\s*\d+>"

    def replace_match(match: Match) -> str:
        coalition = match.group(1)
        return f"<{coalition}>"

    atl_formula = re.sub(k_pattern, replace_match, natatl_formula)
    return atl_formula
