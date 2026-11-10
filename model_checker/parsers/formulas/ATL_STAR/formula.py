"""AST for ATL* formulas.

phi ::= p | not phi | phi1 and phi2 | <<A>> psi                 (state formulas)
psi ::= phi | not psi | psi1 and psi2 | X psi | psi1 U psi2     (path formulas)

- One `Formula` type covers both, since every phi is also a psi; `verifier.py`
  checks where a `Coalition` may appear.
- `True_` is not in the grammar: the parser needs it to write `F` and `G`.
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
