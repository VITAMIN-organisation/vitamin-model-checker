"""Boolean guards over a fixed declared vocabulary; no temporal operators.

T/true and false are constants. Knowledge operators are NOT accepted by this
perfect-information evaluator. Caches must belong to a single verification run.
"""
import re

_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_BOOL_TOKEN = re.compile(r"\s*(&&|\|\||!|\(|\)|[A-Za-z_][A-Za-z_0-9]*)")


class BooleanGuard:
    def __init__(self, text: str, propositions: set[str]):
        self.tokens = []
        pos = 0
        text = text.strip()
        while pos < len(text):
            match = _BOOL_TOKEN.match(text, pos)
            if not match:
                raise ValueError(f"Invalid boolean guard near {text[pos:]!r}")
            self.tokens.append(match.group(1))
            pos = match.end()
        self.pos = 0
        self.props = propositions
        self.tree = self._or()
        if self.pos != len(self.tokens):
            raise ValueError(f"Unexpected boolean token: {self.tokens[self.pos]}")

    def _accept(self, value: str) -> bool:
        if self.pos < len(self.tokens) and self.tokens[self.pos] == value:
            self.pos += 1
            return True
        return False

    def _or(self):
        left = self._and()
        while self._accept("||"):
            left = ("or", left, self._and())
        return left

    def _and(self):
        left = self._not()
        while self._accept("&&"):
            left = ("and", left, self._not())
        return left

    def _not(self):
        if self._accept("!"):
            return ("not", self._not())
        if self._accept("("):
            node = self._or()
            if not self._accept(")"):
                raise ValueError("Unclosed boolean parentheses")
            return node
        if self.pos == len(self.tokens):
            raise ValueError("Missing boolean operand")
        tok = self.tokens[self.pos]
        self.pos += 1
        if not _IDENT.fullmatch(tok):
            raise ValueError(f"Invalid boolean operand: {tok}")
        if tok in {"T", "true"}:
            return ("true",)
        if tok == "false":
            return ("false",)
        if tok not in self.props:
            raise ValueError(f"Unknown atomic proposition: {tok}")
        return ("atom", tok)

    def __call__(self, label: frozenset[str]) -> bool:
        def evaluate(node):
            kind = node[0]
            if kind == "true":
                return True
            if kind == "false":
                return False
            if kind == "atom":
                return node[1] in label
            if kind == "not":
                return not evaluate(node[1])
            if kind == "and":
                return evaluate(node[1]) and evaluate(node[2])
            if kind == "or":
                return evaluate(node[1]) or evaluate(node[2])
            raise AssertionError(kind)
        return evaluate(self.tree)
