"""Strip resource or cost bounds from a formula to get plain ATL (for prefiltering)."""

import re


def resource_bounded_atl_to_atl(formula: str) -> str:
    """Remove bound or cost brackets, e.g. ``<1><5>F p`` becomes ``<1>F p``."""
    pattern = r"(<\d+(?:,\d+)*>)<\d+(?:,\d+)*>"
    return re.sub(pattern, r"\1", formula)
