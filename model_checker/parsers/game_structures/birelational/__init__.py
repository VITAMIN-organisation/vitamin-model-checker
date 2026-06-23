"""Birelational model loading for ICTL.

ICTL models use a preorder/transition matrix format loaded by
``model_checker.algorithms.explicit.ICTL.util.graph.read_file``.
This package is the shared registration point for that model family.
"""

from model_checker.algorithms.explicit.ICTL.util.graph import read_file

__all__ = ["read_file"]
