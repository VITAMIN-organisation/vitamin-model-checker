"""Independent AST enumeration/cost oracle, with exact all-word language checks.

CI exhausts small AST sizes, not all ASTs of size 8 (combinatorially expensive).
Explicit raw-size 8 cases test the free-prefix normalization. No bounded word
signature is treated as regular-language equivalence.
"""

from collections import deque
from functools import lru_cache

import pytest

from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import (
    HistoryRegex,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_full_regex_generation import (
    history_guards_full_exact_cost,
)
from model_checker.algorithms.explicit.NatATL.Recall.recall_lazy_generation import (
    regex_complexity,
)

# Independent grammar ASTs, not production parser/generator/cost functions.
T = ("T",)
P = ("p",)
F = ("false",)


@lru_cache(None)
def bool_asts(n):
    if n == 1:
        return (T, P, F)
    out = [("not", b) for b in bool_asts(n - 1)]
    for i in range(1, n - 1):
        for a in bool_asts(i):
            for b in bool_asts(n - i - 1):
                out.extend((("and", a, b), ("or", a, b)))
    return tuple(out)


@lru_cache(None)
def regex_asts(n):
    out = [("test", b) for b in bool_asts(n)]
    if n > 1:
        out += [("star", r) for r in regex_asts(n - 1)]
    for i in range(1, n - 1):
        for a in regex_asts(i):
            for b in regex_asts(n - i - 1):
                out.extend((("cat", a, b), ("union", a, b)))
    return tuple(out)


def bsize(b):
    return 1 + sum(bsize(x) for x in b[1:])


def raw_size(r):
    return bsize(r[1]) if r[0] == "test" else 1 + sum(raw_size(x) for x in r[1:])


TS = ("star", ("test", T))


def factors(r):
    return factors(r[1]) + factors(r[2]) if r[0] == "cat" else [r]


def normalize(r):
    parts = factors(r)
    prefix = False
    while len(parts) > 1 and parts[0] == TS:
        parts.pop(0)
        prefix = True
    if parts == [TS]:
        return "T*", 1
    suffix = parts[-1]
    for x in reversed(parts[:-1]):
        suffix = ("cat", x, suffix)
    return ("T*." if prefix else "") + render(suffix), sum(
        raw_size(x) for x in parts
    ) + len(parts) - 1


def brender(b):
    if len(b) == 1:
        return b[0]
    if b[0] == "not":
        return f"!({brender(b[1])})"
    return f"({brender(b[1])} {'&&' if b[0] == 'and' else '||'} {brender(b[2])})"


def render(r):
    if r[0] == "test":
        return brender(r[1]) if len(r[1]) == 1 else f"[{brender(r[1])}]"
    if r == TS:
        return "T*"
    if r[0] == "star":
        return f"({render(r[1])})*"
    return f"({render(r[1])}{'.' if r[0] == 'cat' else '|'}{render(r[2])})"


# Brzozowski derivatives form an independent exact automata oracle.
ZERO = ("0",)
EPS = ("e",)


def union(*xs):
    flat = set()
    for x in xs:
        if x == ZERO:
            continue
        flat.update(x[1:] if x[0] == "u" else [x])
    ys = tuple(sorted(flat, key=repr))
    return ZERO if not ys else ys[0] if len(ys) == 1 else ("u",) + ys


def concat(*xs):
    out = []
    for x in xs:
        if x == ZERO:
            return ZERO
        if x == EPS:
            continue
        out.extend(x[1:] if x[0] == "c" else [x])
    return EPS if not out else out[0] if len(out) == 1 else ("c",) + tuple(out)


def star(x):
    return EPS if x in (ZERO, EPS) else x if x[0] == "s" else ("s", x)


def mask(b):
    if b == T:
        return 3
    if b == F:
        return 0
    if b == P:
        return 2
    if b[0] == "not":
        return 3 ^ mask(b[1])
    if b[0] == "and":
        return mask(b[1]) & mask(b[2])
    if b[0] == "or":
        return mask(b[1]) | mask(b[2])
    raise AssertionError(b)


def semantic(r):
    if r[0] == "test":
        return ("l", mask(r[1]))
    if r[0] == "star":
        return star(semantic(r[1]))
    f = concat if r[0] == "cat" else union
    return f(semantic(r[1]), semantic(r[2]))


@lru_cache(None)
def nullable(r):
    if r == EPS or r[0] == "s":
        return True
    if r == ZERO or r[0] == "l":
        return False
    return (all if r[0] == "c" else any)(nullable(x) for x in r[1:])


@lru_cache(None)
def derivative(r, a):
    if r in (ZERO, EPS):
        return ZERO
    if r[0] == "l":
        return EPS if r[1] & (1 << a) else ZERO
    if r[0] == "u":
        return union(*(derivative(x, a) for x in r[1:]))
    if r[0] == "s":
        return concat(derivative(r[1], a), r)
    terms = []
    for i, x in enumerate(r[1:], 1):
        terms.append(concat(derivative(x, a), *r[i + 1 :]))
        if not nullable(x):
            break
    return union(*terms)


def equivalent_to_monitor(ast, pattern):
    machine = HistoryRegex(pattern, ["p"])
    init = (semantic(ast), machine.initial)
    pending = deque([init])
    seen = {init}
    while pending:
        r, active = pending.popleft()
        assert nullable(r) == machine.is_accepting(active), (ast, pattern, r, active)
        for bit, label in enumerate((frozenset(), frozenset({"p"}))):
            target = (derivative(r, bit), machine.step(active, label))
            if target not in seen:
                seen.add(target)
                pending.append(target)
    return True


def test_independent_small_ast_enumeration_and_exact_languages():
    # Set membership checks canonical syntax produced by an independent AST
    # renderer; the derivative product checks its language on ALL finite words.
    actual = {
        cost: set(history_guards_full_exact_cost(cost, ["p"])) for cost in range(1, 5)
    }
    for size in range(1, 5):
        for ast in regex_asts(size):
            assert raw_size(ast) == size
            normalized, cost = normalize(ast)
            assert normalized in actual[cost], (ast, normalized, cost)
            assert regex_complexity(render(ast)) == cost
            assert equivalent_to_monitor(ast, normalized)


@pytest.mark.parametrize(
    "ast",
    [
        ("cat", TS, ("cat", TS, ("test", ("not", P)))),  # raw 8, significant 2
        ("cat", ("cat", TS, ("test", P)), ("test", P)),  # associative prefix
        ("cat", TS, TS),  # repeated universal prefixes
        ("union", TS, ("test", P)),  # prefix under union is NOT free
    ],
)
def test_explicit_prefix_normal_forms(ast):
    normalized, cost = normalize(ast)
    assert regex_complexity(render(ast)) == cost
    assert normalized in set(history_guards_full_exact_cost(cost, ["p"]))
    assert equivalent_to_monitor(ast, normalized)


def test_raw_size_eight_is_actually_exercised():
    ast = ("cat", TS, ("cat", TS, ("test", ("not", P))))
    assert raw_size(ast) == 8
    assert normalize(ast) == ("T*.[!(p)]", 2)


def test_no_prefix_discount_under_star():
    ast = ("star", ("cat", TS, ("test", P)))
    assert raw_size(ast) == 5
    assert regex_complexity(render(ast)) == 5
    assert equivalent_to_monitor(ast, render(ast))
