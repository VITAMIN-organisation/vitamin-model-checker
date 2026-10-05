"""AST for ATL* syntax.

phi ::= p | not phi | phi1 and phi2 | <<A>> psi
psi ::= phi | not psi | psi1 and psi2 | X psi | psi1 U psi2

A single recursive `Formula` type covers both sorts, since every phi is
trivially a psi (`psi ::= phi | ...`); only *where* `Coalition` may appear
well-formed differs, which is a semantic constraint for `verifier.py`, not
a syntactic one.

`True_` isn't in the grammar above, it's a boolean constant `parser.py`
needs to desugar `F`/`G` without inventing a fake atomic proposition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prop:
    name: str


@dataclass(frozen=True)
class True_:
    pass


@dataclass(frozen=True)
class Not:
    operand: Formula


@dataclass(frozen=True)
class And:
    left: Formula
    right: Formula


@dataclass(frozen=True)
class Coalition:
    agents: frozenset[int]
    path_formula: Formula


@dataclass(frozen=True)
class Next:
    operand: Formula


@dataclass(frozen=True)
class Until:
    left: Formula
    right: Formula


Formula = Prop | True_ | Not | And | Coalition | Next | Until
