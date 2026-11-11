"""Recursive-descent parser from ATL* formula text to the AST of formula.py.

Grammar, lowest to highest precedence:

    formula     := implication
    implication := disjunction ('->' implication)?     (sugar, right-assoc)
    disjunction := conjunction ('||' conjunction)*      (sugar, left-assoc)
    conjunction := until ('&&' until)*                  (left-assoc)
    until       := unary ('U' unary)?                   (parenthesize to chain)
    unary       := '!' unary | 'X' unary | 'F' unary | 'G' unary
                 | '<<' agents '>>' until
                 | atom
    atom        := PROP | 'true' | 'false' | '(' formula ')'
    agents      := INT (',' INT)*

- Word forms (`not`, `and`, `until`, ...) are lowercase only. `X`, `F`, `G`, `U` are
  uppercase only, so lowercase one-letter propositions stay free.
- A name follows the rule of every logic (`validate_proposition_identifier`): it
  starts with a letter and is no reserved word in any case, so `Always`, `True`
  and `exist` are errors.
- `<<1>> p U q` is `<<1>>(p U q)`, as in ATL (JACM 2002, p. 689).
- `F`, `G`, `||` and `->` become the seven constructors of formula.py, so the
  verifier handles only those.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..parser_utils import (
    ambiguous_prefix_message,
    validate_proposition_identifier,
)
from .formula import And, Coalition, Formula, Next, Not, Prop, True_, Until

_CONNECTIVES = frozenset({"AND", "OR", "IMPLIES"})


class ATLStarParseError(ValueError):
    """Raised on malformed ATL* formula text; `position` is 0-based."""

    def __init__(self, message: str, position: int):
        super().__init__(f"{message} (position {position})")
        self.position = position


_KEYWORDS = {
    "not": "NOT",
    "and": "AND",
    "or": "OR",
    "implies": "IMPLIES",
    "next": "NEXT",
    "eventually": "EVENTUALLY",
    "globally": "GLOBALLY",
    "always": "GLOBALLY",
    "until": "UNTIL",
    "true": "TRUE",
    "false": "FALSE",
}

# Uppercase only, so one-letter props like `p` stay free.
_SINGLE_LETTER_KEYWORDS = {
    "X": "NEXT",
    "F": "EVENTUALLY",
    "G": "GLOBALLY",
    "U": "UNTIL",
}

# IDENT takes a leading `_` so that `_goal` fails with the name rule's message
# rather than "Unexpected character".
_TOKEN_RE = re.compile(
    r"""
      (?P<WS>\s+)
    | (?P<COALITION_OPEN><<)
    | (?P<COALITION_CLOSE>>>)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<COMMA>,)
    | (?P<IMPLIES>->)
    | (?P<AND>&&)
    | (?P<OR>\|\|)
    | (?P<NOT>!)
    | (?P<INT>\d+)
    | (?P<IDENT>[a-zA-Z_][a-zA-Z0-9_]*)
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    position: int


def _tokenize(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        kind = match.lastgroup if match else None
        if match is None or kind is None:
            raise ATLStarParseError(f"Unexpected character {text[pos]!r}", pos)
        value = match.group()
        if kind != "WS":
            if kind == "IDENT":
                if value in _SINGLE_LETTER_KEYWORDS:
                    kind = _SINGLE_LETTER_KEYWORDS[value]
                elif value in _KEYWORDS:
                    kind = _KEYWORDS[value]
                else:
                    _, err = validate_proposition_identifier(value)
                    if err is not None:
                        raise ATLStarParseError(err, pos)
                    kind = "PROP"
            tokens.append(_Token(kind, value, pos))
        pos = match.end()
    tokens.append(_Token("EOF", "", len(text)))
    return tokens


class _Parser:
    def __init__(self, tokens: list[_Token], num_agents: int | None = None):
        self._tokens = tokens
        self._index = 0
        self._num_agents = num_agents

    def _peek(self) -> _Token:
        return self._tokens[self._index]

    def _advance(self) -> _Token:
        token = self._tokens[self._index]
        self._index += 1
        return token

    def _expect(self, kind: str) -> _Token:
        token = self._peek()
        if token.kind != kind:
            raise ATLStarParseError(
                f"Expected {kind}, found {token.kind}", token.position
            )
        return self._advance()

    def parse_formula(self) -> Formula:
        formula = self._implication()
        self._expect("EOF")
        return formula

    def _implication(self) -> Formula:
        left = self._disjunction()
        if self._peek().kind == "IMPLIES":
            self._advance()
            right = self._implication()
            return Not(And(left, Not(right)))
        return left

    def _disjunction(self) -> Formula:
        left = self._conjunction()
        while self._peek().kind == "OR":
            self._advance()
            right = self._conjunction()
            left = Not(And(Not(left), Not(right)))
        return left

    def _conjunction(self) -> Formula:
        left = self._until()
        while self._peek().kind == "AND":
            self._advance()
            right = self._until()
            left = And(left, right)
        return left

    def _until(self) -> Formula:
        start = self._index
        left = self._unary()
        if self._peek().kind == "UNTIL":
            until = self._advance()
            right = self._unary()
            token = self._peek()
            if token.kind == "UNTIL":
                raise ATLStarParseError(
                    "U does not chain: write (x U y) U z or x U (y U z)",
                    token.position,
                )
            # The paper states no precedence between U and the connectives.
            before = self._tokens[start - 1] if start else None
            if before is not None and before.kind in _CONNECTIVES:
                c = before.value
                raise ATLStarParseError(
                    f"'x {c} y U z' is ambiguous: write (x {c} y) U z or x {c} (y U z)",
                    until.position,
                )
            if token.kind in _CONNECTIVES:
                c = token.value
                raise ATLStarParseError(
                    f"'x U y {c} z' is ambiguous: write (x U y) {c} z or x U (y {c} z)",
                    until.position,
                )
            return Until(left, right)
        return left

    def _unary(self) -> Formula:
        token = self._peek()
        if token.kind == "NOT":
            self._advance()
            return Not(self._unary())
        if token.kind == "NEXT":
            self._advance()
            return Next(self._unary())
        if token.kind == "EVENTUALLY":
            self._advance()
            return Until(True_(), self._unary())
        if token.kind == "GLOBALLY":
            self._advance()
            return Not(Until(True_(), Not(self._unary())))
        if token.kind == "COALITION_OPEN":
            return self._coalition()
        return self._atom()

    def _coalition(self) -> Formula:
        open_token = self._expect("COALITION_OPEN")
        agents = self._agents()
        self._expect("COALITION_CLOSE")
        # <<A>> phi1 U phi2 is the coalition over the Until, as in ATL (JACM 2002,
        # p. 689).
        coalition = Coalition(agents=agents, path_formula=self._until())
        token = self._peek()
        if token.kind in _CONNECTIVES:
            # <<A>> x & y is (<<A>> x) & y or <<A>> (x & y), and both are ATL*.
            prefix = f"<<{','.join(str(agent) for agent in sorted(agents))}>>"
            raise ATLStarParseError(
                ambiguous_prefix_message(prefix, token.value), open_token.position
            )
        return coalition

    def _agents(self) -> frozenset[int]:
        seen: dict[int, int] = {}  # agent id -> the position of its first occurrence

        def add(token: _Token) -> int:
            agent = self._agent_id(token)
            if agent in seen:
                raise ATLStarParseError(
                    f"Duplicate agent id {agent} in coalition", token.position
                )
            seen[agent] = token.position
            return agent

        agents = [add(self._expect("INT"))]
        while self._peek().kind == "COMMA":
            self._advance()
            agents.append(add(self._expect("INT")))
        return frozenset(agents)

    def _agent_id(self, token: _Token) -> int:
        agent = int(token.value)
        if self._num_agents is not None and not (1 <= agent <= self._num_agents):
            raise ATLStarParseError(
                f"Agent {agent} out of range [1, {self._num_agents}]", token.position
            )
        return agent

    def _atom(self) -> Formula:
        token = self._peek()
        if token.kind == "TRUE":
            self._advance()
            return True_()
        if token.kind == "FALSE":
            self._advance()
            return Not(True_())
        if token.kind == "PROP":
            self._advance()
            return Prop(token.value)
        if token.kind == "LPAREN":
            self._advance()
            inner = self._implication()
            self._expect("RPAREN")
            return inner
        raise ATLStarParseError(f"Unexpected token {token.kind}", token.position)


def parse(text: str, num_agents: int | None = None) -> Formula:
    """Parse ATL* text into a `Formula`, with agent ids up to `num_agents` when given;
    ATLStarParseError names the position of a mistake."""
    tokens = _tokenize(text)
    return _Parser(tokens, num_agents=num_agents).parse_formula()
