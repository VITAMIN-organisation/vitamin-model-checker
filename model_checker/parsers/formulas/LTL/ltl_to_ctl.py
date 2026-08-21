import re

_KEYWORD_TO_SYMBOL = (
    (re.compile(r"\buntil\b", re.IGNORECASE), "U"),
    (re.compile(r"\beventually\b", re.IGNORECASE), "F"),
    (re.compile(r"\bglobally\b", re.IGNORECASE), "G"),
    (re.compile(r"\bnext\b", re.IGNORECASE), "X"),
)

# Separate glued temporal operators / single-letter atoms so the CTL lexer
# sees distinct tokens (Xp, FGp). Do not split inside multi-letter names (Goal).
# Also split after an existing path quantifier (AXp -> AX p).
_COMPACT_TEMPORAL = re.compile(
    r"(?:(?<![A-Za-z0-9_])|(?<=[AE]))([XFG])(?=[XFG]|[a-zA-Z_](?![a-zA-Z0-9_]))"
)

# Add a universal path quantifier before each bare temporal operator.
_PREFIX_TEMPORAL = re.compile(r"(?<![AE])(?<![a-zA-Z0-9_])([XFG])(?=\s|[(!]|$)")

# Separate glued quantified temporals: AGAFp -> AG AF p (after compact/prefix).
_ADJACENT_QUANTIFIED = re.compile(r"(A[XFG])(?=A[XFG])")

_UNTIL_PATTERN = re.compile(
    r"(\([^()]*\)|A\([^()]*\)|[a-zA-Z]\w*)\s*U\s*"
    r"(\([^()]*\)|A\([^()]*\)|[a-zA-Z]\w*)"
)


def ltl_to_ctl(ltl_formula: str) -> str:
    """Adapt an LTL formula string for the CTL-backed sure-win checker.

    Turns the user formula into a universally quantified CTL-shaped string that
    the CTL parser accepts after strategy pruning. This is a syntactic bridge
    for VITAMIN's strategic LTL mode, not a classical LTL-to-CTL embedding.
    """
    formula = ltl_formula.strip()
    for pattern, replacement in _KEYWORD_TO_SYMBOL:
        formula = pattern.sub(replacement, formula)

    prev = None
    while prev != formula:
        prev = formula
        formula = _COMPACT_TEMPORAL.sub(r"\1 ", formula)

    prev = None
    while prev != formula:
        prev = formula
        formula = _PREFIX_TEMPORAL.sub(r"A\1 ", formula)

    prev = None
    while prev != formula:
        prev = formula
        formula = _ADJACENT_QUANTIFIED.sub(r"\1 ", formula)

    placeholder = "__U_PLACEHOLDER__"
    while placeholder in formula:
        placeholder = f"{placeholder}_X"

    while True:
        new_formula = _UNTIL_PATTERN.sub(rf"A(\1 {placeholder} \2)", formula)
        if new_formula == formula:
            break
        formula = new_formula

    formula = formula.replace(placeholder, "U")
    return re.sub(r"\s+", " ", formula).strip()
