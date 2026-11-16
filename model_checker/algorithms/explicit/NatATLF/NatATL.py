"""NatATLF model checking: the NatATL memoryless check, kept at this path for the
NatATLF entry point."""

from model_checker.algorithms.explicit.NatATL.Memoryless.NatATL import (
    model_checking,
)

__all__ = ["model_checking"]
