"""
Convert resource- or cost-bounded ATL formulas (RABATL, RBATL, OATL) to ATL by stripping bounds.

RABATL/RBATL use <J><b>Op (e.g. <1,2><3,4>X phi); OATL uses <J><n>Op (e.g. <1><5>F p).
The unbounded ATL semantics corresponds to <J>Op. With any finite bound or cost,
the logic is more restrictive than ATL, so if ATL does not hold then the
bounded logic does not hold. This enables an ATL prefilter for early rejection.
"""

import re


def resource_bounded_atl_to_atl(formula: str) -> str:
    """
    Strip bounds or costs from RABATL/RBATL/OATL formula to obtain an ATL formula.

    Replaces each <J><b> or <J><n> with <J>: J is a coalition, b a bound vector,
    n a cost. E.g. <1,2><3,4>X p -> <1,2>X p, <1><5>F q -> <1>F q.

    Args:
        formula: RABATL, RBATL, or OATL formula string

    Returns:
        ATL formula string (bounds/costs removed)
    """
    pattern = r"(<\d+(?:,\d+)*>)<\d+(?:,\d+)*>"
    return re.sub(pattern, r"\1", formula)
