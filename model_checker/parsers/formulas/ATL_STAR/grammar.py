"""Parses ATL* formula text into the AST defined in formula.py.

Hand-written recursive-descent, not PLY: a coalition here can scope over an
arbitrarily nested path formula (unlike ATL, where it's always immediately
followed by exactly one temporal operator), so there's no single production
to special-case the way `ATL/parser.py` does.

Grammar (lowest to highest precedence; parentheses always disambiguate):

    formula     := implication
    implication := disjunction ('->' implication)?     (sugar, right-assoc)
    disjunction := conjunction ('|' conjunction)*       (sugar, left-assoc)
    conjunction := until ('&' until)*                   (left-assoc)
    until       := unary ('U' unary)?                   (parenthesize to chain)
    unary       := '!' unary | 'X' unary | 'F' unary | 'G' unary
                 | '<<' agents '>>' unary
                 | atom
    atom        := PROP | 'true' | 'false' | '(' formula ')'
    agents      := INT (',' INT)*

Each keyword also accepts its word form (`not`/`!`, `and`/`&`/`&&`,
`or`/`|`/`||`, `implies`/`->`, `next`/`X`, `eventually`/`F`, `globally`/`G`,
`until`/`U`), case-insensitive. Only uppercase `X`/`F`/`G`/`U` are reserved as
single-letter operators, so lowercase single-letter propositions stay free.

A coalition binds like a prefix operator over the tightest following
`unary`, parenthesize the operand for anything beyond a bare
atom/negation/next (e.g. `<<1,2>>(p1 U p2)`, `<<1>>(F p & G q)`). `F`, `G`,
`|`, and `->` are sugar, desugared here into the six primitive constructors
(`Prop`, `True_`, `Not`, `And`, `Coalition`, `Next`, `Until`) so
`verifier.py` only has to handle those.

A keyword needs a non-identifier boundary to be recognized as itself:
identifiers are matched greedily, so `Xp` tokenizes as one proposition named
`Xp`, not `X` followed by `p`, write `X p` for the operator.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .formula import And, Coalition, Formula, Next, Not, Prop, True_, Until


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
    "until": "UNTIL",
    "true": "TRUE",
    "false": "FALSE",
}

_SINGLE_LETTER_KEYWORDS = {"X": "NEXT", "F": "EVENTUALLY", "G": "GLOBALLY", "U": "UNTIL"}
# Case-sensitive (uppercase only) so lowercase single-letter props like "p"/"g"
# stay available, unlike the multi-word keywords below, which are matched
# case-insensitively since a real proposition named e.g. "until" is unlikely.

_TOKEN_RE = re.compile(
    r"""
      (?P<WS>\s+)
    | (?P<COALITION_OPEN><<)
    | (?P<COALITION_CLOSE>>>)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<COMMA>,)
    | (?P<IMPLIES>->)
    | (?P<AND>&&?)
    | (?P<OR>\|\|?)
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
        if match is None:
            raise ATLStarParseError(f"Unexpected character {text[pos]!r}", pos)
        kind = match.lastgroup
        value = match.group()
        if kind != "WS":
            if kind == "IDENT":
                if value in _SINGLE_LETTER_KEYWORDS:
                    kind = _SINGLE_LETTER_KEYWORDS[value]
                elif value.lower() in _KEYWORDS:
                    kind = _KEYWORDS[value.lower()]
                else:
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
            raise ATLStarParseError(f"Expected {kind}, found {token.kind}", token.position)
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
        left = self._unary()
        if self._peek().kind == "UNTIL":
            self._advance()
            right = self._unary()
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
        self._expect("COALITION_OPEN")
        agents = self._agents()
        self._expect("COALITION_CLOSE")
        return Coalition(agents=agents, path_formula=self._unary())

    def _agents(self) -> frozenset[int]:
        seen: dict[int, int] = {}  # agent id -> the position of its first occurrence

        def add(token: _Token) -> int:
            agent = self._agent_id(token)
            if agent in seen:
                raise ATLStarParseError(f"Duplicate agent id {agent} in coalition", token.position)
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
            raise ATLStarParseError(f"Agent {agent} out of range [1, {self._num_agents}]", token.position)
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
    """Parse ATL* formula text into a `Formula`.

    Args:
        text: the formula text.
        num_agents: if given, every coalition's agent ids must fall in
            `[1, num_agents]`.

    Raises:
        ATLStarParseError: on malformed text, an out-of-range agent id
            (reported at that agent's own position in `text`), or trailing
            input after a complete formula.
    """
    tokens = _tokenize(text)
    return _Parser(tokens, num_agents=num_agents).parse_formula()
