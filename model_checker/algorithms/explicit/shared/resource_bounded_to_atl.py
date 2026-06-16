"""
Projection from resource-bounded ATL formulas to plain ATL.

Used by the ATL prefilter to quickly reject formulas that are false even without
resource constraints.  If the unbounded ATL check already returns False at the
initial state, no resource allocation can make the formula true, so the expensive
bounded checker is skipped entirely.
"""

import re


def resource_bounded_atl_to_atl(formula: str) -> str:
    """Remove bound or cost brackets, e.g. ``<1><5>F p`` becomes ``<1>F p``."""
    pattern = r"(<\d+(?:,\d+)*>)<\d+(?:,\d+)*>"
    return re.sub(pattern, r"\1", formula)
