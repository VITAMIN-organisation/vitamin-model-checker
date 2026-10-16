"""Finite automata for regular guards over sequences of CGS state labels.

A history s0...st is consumed as L(s0), ..., L(st), including the
current state's labelling. Acceptance means a FULL regex match.

Canonical grammar:
    R ::= g | (R) | R.R | R|R | R*
    g ::= p | !p | T | [Boolean expression]
Boolean expressions support !, &&, ||, parentheses and T/false.
"""

import re
from collections.abc import Iterable

from model_checker.algorithms.explicit.NatATL.boolean_guards import (
    BooleanGuard as _Boolean,
)

_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


class HistoryRegex:
    """An epsilon-NFA that can be stepped incrementally over CGS labels."""

    def __init__(self, pattern: str, propositions: Iterable[str]):
        self.props = set(propositions)
        self.tokens = self._lex(pattern)
        self.pos = 0
        self.edges: dict[int, list[tuple[_Boolean | None, int]]] = {}
        self.start, self.accept = self._union()
        if self.pos != len(self.tokens):
            raise ValueError(f"Unexpected regex token: {self.tokens[self.pos]!r}")
        self.initial = self._closure(frozenset({self.start}))

    @staticmethod
    def _lex(pattern: str) -> list[tuple[str, str]]:
        result = []
        pos = 0
        while pos < len(pattern):
            if pattern[pos].isspace():
                pos += 1
                continue
            ch = pattern[pos]
            if ch == "[":
                end = pattern.find("]", pos + 1)
                if end == -1:
                    raise ValueError("Unclosed [Boolean guard]")
                result.append(("guard", pattern[pos + 1:end]))
                pos = end + 1
            elif ch in "().|*":
                result.append((ch, ch))
                pos += 1
            else:
                match = re.match(r"!?[A-Za-z_][A-Za-z_0-9]*", pattern[pos:])
                if not match:
                    raise ValueError(f"Invalid history regex near {pattern[pos:]!r}")
                result.append(("guard", match.group()))
                pos += len(match.group())
        if not result:
            raise ValueError("Empty history regex")
        return result

    def _node(self) -> int:
        index = len(self.edges)
        self.edges[index] = []
        return index

    def _edge(self, src: int, dst: int, guard: _Boolean | None = None):
        self.edges[src].append((guard, dst))

    def _accept(self, tok: str) -> bool:
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == tok:
            self.pos += 1
            return True
        return False

    def _union(self):
        left = self._concat()
        while self._accept("|"):
            right = self._concat()
            start, end = self._node(), self._node()
            self._edge(start, left[0])
            self._edge(start, right[0])
            self._edge(left[1], end)
            self._edge(right[1], end)
            left = (start, end)
        return left

    def _concat(self):
        left = self._star()
        while self._accept("."):
            right = self._star()
            self._edge(left[1], right[0])
            left = (left[0], right[1])
        return left

    def _star(self):
        if self._accept("("):
            start, end = self._union()
            if not self._accept(")"):
                raise ValueError("Unclosed regex parentheses")
        elif self.pos < len(self.tokens) and self.tokens[self.pos][0] == "guard":
            guard = _Boolean(self.tokens[self.pos][1], self.props)
            self.pos += 1
            start, end = self._node(), self._node()
            self._edge(start, end, guard)
        else:
            raise ValueError("Missing regex operand")
        while self._accept("*"):
            new_start, new_end = self._node(), self._node()
            self._edge(new_start, start)
            self._edge(new_start, new_end)
            self._edge(end, start)
            self._edge(end, new_end)
            start, end = new_start, new_end
        return start, end

    def _closure(self, active: frozenset[int]) -> frozenset[int]:
        seen = set(active)
        stack = list(active)
        while stack:
            for guard, dst in self.edges[stack.pop()]:
                if guard is None and dst not in seen:
                    seen.add(dst)
                    stack.append(dst)
        return frozenset(seen)

    def step(self, active: frozenset[int], label: Iterable[str]) -> frozenset[int]:
        valuation = frozenset(label)
        if not valuation <= self.props:
            raise ValueError(f"Unknown labels: {valuation - self.props}")
        destinations = {
            dst
            for src in active
            for guard, dst in self.edges[src]
            if guard is not None and guard(valuation)
        }
        return self._closure(frozenset(destinations))

    def is_accepting(self, active: frozenset[int]) -> bool:
        return self.accept in active

    def matches(self, history: Iterable[Iterable[str]]) -> bool:
        current = self.initial
        for label in history:
            current = self.step(current, label)
        return self.is_accepting(current)
