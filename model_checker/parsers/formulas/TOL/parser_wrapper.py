"""Backward-compatible alias; use TOLParser from parser.py."""

from model_checker.parsers.formulas.TOL.parser import TOLParser as TOLParserWrapper

__all__ = ["TOLParserWrapper"]
