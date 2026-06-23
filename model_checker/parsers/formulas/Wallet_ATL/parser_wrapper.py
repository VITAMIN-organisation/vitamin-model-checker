"""Backward-compatible alias; use Wallet_ATLParser from parser.py."""

from model_checker.parsers.formulas.Wallet_ATL.parser import (
    Wallet_ATLParser as Wallet_ATLParserWrapper,
)

__all__ = ["Wallet_ATLParserWrapper"]
