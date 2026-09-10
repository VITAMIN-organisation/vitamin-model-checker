"""Parser and conservative translation helpers for the restricted NatSL prototype.

Concrete syntax accepted by the prototype::

    E{2}xA{2}y:(x,1)(y,2)Fa

The implementation deliberately preserves the quantifier order. Earlier versions
split existential and universal quantifiers into unrelated NatATL formulae; that is
not semantics preserving for mixed prefixes and is no longer used by model checking.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


class NatSLParseError(ValueError):
    """Raised when a formula is outside the supported concrete syntax."""


class UnsupportedTranslationError(ValueError):
    """Raised when no semantics-preserving NatATL translation is implemented."""


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


_QUANTIFIER_RE = re.compile(r"\s*([EA])(?:\{(\d+)\})?([A-Za-z_][A-Za-z0-9_]*?)(?=\s*(?:[EA](?:\{\d+\})?[A-Za-z_]|$))")
_BINDING_RE = re.compile(r"\s*\(([A-Za-z_][A-Za-z0-9_]*),\s*(\d+)\)")
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

    quantifiers: list[Quantifier] = []
    position = 0
    while position < len(prefix):
        match = _QUANTIFIER_RE.match(prefix, position)
        if not match:
            raise NatSLParseError(
                f"Invalid quantifier near {prefix[position:]!r}; expected E{{k}}x or A{{k}}x"
            )
        kind, bound, variable = match.groups()
        parsed_bound = int(bound) if bound is not None else 1
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
        raise NatSLParseError("Every quantified variable must occur in exactly one binding")
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


def do_parsingNatSL(text: str):
    """Return the tuple representation expected by older callers."""
    try:
        formula = parse_formula(text)
    except NatSLParseError:
        return None
    quantifiers = [(q.kind, q.variable, q.bound) for q in formula.quantifiers]
    bindings = [(variable, str(agent)) for variable, agent in formula.bindings]
    goal = (
        ("!", formula.goal.operator, formula.goal.proposition)
        if formula.goal.negated
        else (formula.goal.operator, formula.goal.proposition)
    )
    return quantifiers, bindings, goal


def validate_bindings(parsed_formula) -> None:
    quantifiers, bindings, _ = parsed_formula
    variables = [item[1] for item in quantifiers]
    bound_variables = [item[0] for item in bindings]
    if sorted(variables) != sorted(bound_variables):
        raise ValueError("Every quantified variable must have exactly one binding")


def count_agents(parsed_formula) -> int:
    return len({int(agent) for _, agent in parsed_formula[1]})


def _agents_by_quantifier(parsed_formula, kind: str) -> list[int]:
    quantifiers, bindings, _ = parsed_formula
    mapping = {variable: int(agent) for variable, agent in bindings}
    return [mapping[variable] for qkind, variable, _ in quantifiers if qkind == kind]


def extract_existential_agents(parsed_formula) -> list[int]:
    return _agents_by_quantifier(parsed_formula, "E")


def extract_universal_agents(parsed_formula) -> list[int]:
    return _agents_by_quantifier(parsed_formula, "A")


def count_universal_agents(universal_agents) -> int:
    return len(universal_agents)


def count_existential_agents(existential_agents) -> int:
    return len(existential_agents)


def extract_formula(parsed_formula) -> str:
    return "".join(parsed_formula[2])


def normalize_formula(text: str) -> tuple[bool, str]:
    outer_negated, _ = _strip_outer_negation(text)
    return outer_negated, format_formula(parse_formula(text))


def skolemize_formula(parsed_formula):
    """Preserve the prefix: blindly moving existentials is not logically valid."""
    return parsed_formula


def goal_to_ctl(goal: TemporalGoal) -> str:
    proposition = goal.proposition
    if goal.operator == "F":
        return f"AG !{proposition}" if goal.negated else f"AF {proposition}"
    if goal.operator == "G":
        return f"AF !{proposition}" if goal.negated else f"AG {proposition}"
    if goal.operator == "X":
        return f"AX !{proposition}" if goal.negated else f"AX {proposition}"
    raise NatSLParseError(f"Unsupported temporal operator: {goal.operator}")


def convert_natsl_to_ctl(parsed_formula, flag=False) -> str:
    raw_goal = parsed_formula[2]
    if len(raw_goal) == 3:
        goal = TemporalGoal(raw_goal[1], raw_goal[2], True)
    else:
        goal = TemporalGoal(raw_goal[0], raw_goal[1], bool(flag))
    return goal_to_ctl(goal)


def convert_natsl_to_natatl(text: str) -> list[str]:
    """Translate only the exact homogeneous existential subcase.

    This is exact only when the bindings cover all agents of the input CGS and all
    quantified strategies use the same bound. Mixed or universal prefixes are
    rejected rather than silently changing their semantics.
    """
    formula = parse_formula(text)
    if any(q.kind != "E" for q in formula.quantifiers):
        raise UnsupportedTranslationError(
            "Mixed/universal NatSL prefixes do not have the old separated NatATL translation"
        )
    bounds = {q.bound for q in formula.quantifiers}
    if len(bounds) != 1:
        raise UnsupportedTranslationError(
            "One NatATL coalition bound cannot preserve different per-variable NatSL bounds"
        )
    agents = ",".join(str(agent) for _, agent in formula.bindings)
    bound = next(iter(bounds))
    negation = "!" if formula.goal.negated else ""
    return [
        f"{negation}<{{{agents}}}, {bound}>{formula.goal.operator}{formula.goal.proposition}"
    ]


def convert_natsl_to_natatl_separated(text: str) -> tuple[list[str], list[str]]:
    return convert_natsl_to_natatl(text), []


class NatSLParser:
    """Backward-compatible wrapper for legacy NatSL parser callers."""

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

        # Backward compatibility: legacy NatSL syntax allowed omitted bounds,
        # e.g. `E x:` and `A y:`. Interpret omitted bounds as 1.
        text = re.sub(
            r"(?<![A-Za-z0-9_])([EA])\s+([A-Za-z_][A-Za-z0-9_]*)",
            r"\1{1}\2",
            text,
        )

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

        quantifiers = [
            (q.kind, q.variable, q.bound)
            for q in formula.quantifiers
        ]

        bindings = [
            (variable, str(agent))
            for variable, agent in formula.bindings
        ]

        temporal = (
            ("!", formula.goal.operator, formula.goal.proposition)
            if formula.goal.negated
            else (formula.goal.operator, formula.goal.proposition)
        )

        return quantifiers, bindings, temporal
