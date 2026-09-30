"""Parser for the restricted NatSL fragment.

Concrete syntax::

    E{2}x A{2}y: (x, 1)(y, 2) F a

Optional whitespace is allowed around ``:``, bindings, goals, and between
quantifiers. Bounds remain required in ``{k}`` form. Goals are limited to
F/G/X and their negations. Quantifier order is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


class NatSLParseError(ValueError):
    """Raised when a formula is outside the supported concrete syntax."""


@dataclass(frozen=True)
class Quantifier:
    kind: str
    variable: str
    bound: int


@dataclass(frozen=True)
class TemporalGoal:
    operator: str
    proposition: str
    negated: bool = False


@dataclass(frozen=True)
class NatSLFormula:
    quantifiers: tuple[Quantifier, ...]
    bindings: tuple[tuple[str, int], ...]
    goal: TemporalGoal


# Allow spaces around braces/variables and between adjacent quantifiers.
_QUANTIFIER_RE = re.compile(
    r"\s*([EA])\s*\{\s*(\d+)\s*\}\s*([A-Za-z_][A-Za-z0-9_]*?)"
    r"(?=\s*(?:[EA]\s*\{\s*\d+\s*\}\s*[A-Za-z_]|$))"
)
_BINDING_RE = re.compile(r"\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d+)\s*\)")
_GOAL_RE = re.compile(
    r"\s*(!|not\s+)?\s*([FGX])\s*([A-Za-z_][A-Za-z0-9_.]*)\s*$",
    re.IGNORECASE,
)


def _strip_outer_negation(text: str) -> tuple[bool, str]:
    text = text.strip()
    if text.startswith("!(") and text.endswith(")"):
        depth = 0
        for index, char in enumerate(text[1:], start=1):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(text) - 1:
                    return False, text
        if depth == 0:
            return True, text[2:-1]
    return False, text


def parse_formula(text: str) -> NatSLFormula:
    if not isinstance(text, str) or not text.strip():
        raise NatSLParseError("NatSL formula must be a non-empty string")

    outer_negated, text = _strip_outer_negation(text)
    if ":" not in text:
        raise NatSLParseError("Missing ':' between quantifier prefix and bindings")
    prefix, suffix = text.split(":", 1)
    prefix = prefix.strip()
    suffix = suffix.strip()

    quantifiers: list[Quantifier] = []
    position = 0
    while position < len(prefix):
        match = _QUANTIFIER_RE.match(prefix, position)
        if not match:
            raise NatSLParseError(
                f"Invalid quantifier near {prefix[position:]!r}; expected E{{k}}x or A{{k}}x"
            )
        kind, bound, variable = match.groups()
        parsed_bound = int(bound)
        if parsed_bound < 1:
            raise NatSLParseError("Strategy-complexity bounds must be positive")
        quantifiers.append(Quantifier(kind, variable, parsed_bound))
        position = match.end()

    if not quantifiers:
        raise NatSLParseError("At least one strategy quantifier is required")

    bindings: list[tuple[str, int]] = []
    position = 0
    while True:
        match = _BINDING_RE.match(suffix, position)
        if not match:
            break
        variable, agent = match.groups()
        bindings.append((variable, int(agent)))
        position = match.end()

    goal_match = _GOAL_RE.match(suffix, position)
    if not goal_match:
        raise NatSLParseError(
            "Unsupported goal; this prototype accepts F p, G p, X p and their negations"
        )
    negation, operator, proposition = goal_match.groups()

    variables = [quantifier.variable for quantifier in quantifiers]
    bound_variables = [variable for variable, _ in bindings]
    agents = [agent for _, agent in bindings]
    if len(set(variables)) != len(variables):
        raise NatSLParseError("Each strategy variable must be quantified exactly once")
    if sorted(variables) != sorted(bound_variables):
        raise NatSLParseError(
            "Every quantified variable must occur in exactly one binding"
        )
    if len(set(agents)) != len(agents):
        raise NatSLParseError("Each agent may occur in only one binding")

    goal_negated = bool(negation)
    if outer_negated:
        quantifiers = [
            Quantifier("A" if q.kind == "E" else "E", q.variable, q.bound)
            for q in quantifiers
        ]
        goal_negated = not goal_negated

    return NatSLFormula(
        tuple(quantifiers),
        tuple(bindings),
        TemporalGoal(operator.upper(), proposition, goal_negated),
    )


def format_formula(formula: NatSLFormula) -> str:
    prefix = "".join(
        f"{quantifier.kind}{{{quantifier.bound}}}{quantifier.variable}"
        for quantifier in formula.quantifiers
    )
    bindings = "".join(f"({variable},{agent})" for variable, agent in formula.bindings)
    negation = "!" if formula.goal.negated else ""
    return f"{prefix}:{bindings}{negation}{formula.goal.operator}{formula.goal.proposition}"


def goal_to_ctl(goal: TemporalGoal) -> str:
    proposition = goal.proposition
    if goal.operator == "F":
        return f"AG !{proposition}" if goal.negated else f"AF {proposition}"
    if goal.operator == "G":
        return f"AF !{proposition}" if goal.negated else f"AG {proposition}"
    if goal.operator == "X":
        return f"AX !{proposition}" if goal.negated else f"AX {proposition}"
    raise NatSLParseError(f"Unsupported temporal operator: {goal.operator}")


class NatSLParser:
    """Entry-point wrapper used by FormulaParserFactory."""

    _RESERVED_TEMPORAL_ATOMS = {
        "exist",
        "forall",
        "and",
        "eventually",
        "not",
        "E",
        "A",
    }

    def __init__(self):
        self.errors = []

    def parse(self, text):
        self.errors = []

        try:
            formula = parse_formula(text)
        except NatSLParseError as exc:
            self.errors.append(str(exc))
            return None

        atom = formula.goal.proposition

        if atom in self._RESERVED_TEMPORAL_ATOMS:
            self.errors.append(
                f"Reserved keyword {atom!r} cannot be used as a temporal atom"
            )
            return None

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", atom):
            self.errors.append(f"Invalid temporal atom {atom!r}")
            return None

        return formula
