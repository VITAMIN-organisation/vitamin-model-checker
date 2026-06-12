"""Model checking engine for VITAMIN.

Provides the shared execution pipeline and entry-point factory for
logic-specific model checking interfaces.
"""

from model_checker.engine.execution import (
    create_model_checking_entry,
    execute_model_checking_with_parser,
)

__all__ = [
    "create_model_checking_entry",
    "execute_model_checking_with_parser",
]
