"""Drop the resource bounds of a formula to get plain ATL.

The ATL prefilter uses it: if the formula is false at the initial state even with
no bounds, no resource allocation can make it true, so the bounded check is skipped.
"""

import re


def resource_bounded_atl_to_atl(formula: str) -> str:
    """Remove bound or cost brackets, e.g. ``<1><5>F p`` becomes ``<1>F p``."""
    pattern = r"(<\d+(?:,\d+)*>)<\d+(?:,\d+)*>"
    return re.sub(pattern, r"\1", formula)


def wallet_atl_to_atl(formula: str) -> str:
    """Drop the wallet constraints to get ATL: ``<< 1, 2 : wallet(1, >= 10) >> F p``
    becomes ``<1,2> F p``."""

    def replacer(match):
        agents_part = match.group(1)
        agents = "".join(agents_part.split())
        return f"<{agents}>"

    pattern = r"<<\s*([\d\s,]+)(?:\s*:.*?)?>>"
    return re.sub(pattern, replacer, formula)
