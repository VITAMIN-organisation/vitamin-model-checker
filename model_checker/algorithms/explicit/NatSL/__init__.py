# NatSL has two variants: Sequential and Alternated
# Import both for flexibility
from model_checker.algorithms.explicit.NatSL.Alternated.natSL import (  # noqa: F401
    model_checking as model_checking_alternated,
)
from model_checker.algorithms.explicit.NatSL.Sequential.natSL import (
    model_checking as model_checking_sequential,
)

# Default to Sequential for backward compatibility
model_checking = model_checking_sequential
