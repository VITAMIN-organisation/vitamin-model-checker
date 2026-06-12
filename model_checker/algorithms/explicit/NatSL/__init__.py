"""NatSL package: Sequential and Alternated semantics variants."""

from model_checker.algorithms.explicit.NatSL.Alternated.natSL import (
    model_checking as model_checking_alternated,
)
from model_checker.algorithms.explicit.NatSL.Sequential.natSL import (
    model_checking as model_checking_sequential,
)

__all__ = ["model_checking_sequential", "model_checking_alternated"]
