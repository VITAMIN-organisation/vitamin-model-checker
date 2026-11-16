"""CapATL model checker for capacity CGS models."""

import itertools
import re
from collections.abc import Callable
from functools import partial
from typing import Any

from model_checker.algorithms.explicit.CapATL.game import (
    CapModel,
    CoalitionGame,
    Knowledge,
    StateTest,
    next_states,
    release_states,
    until_states,
)
from model_checker.algorithms.explicit.shared.atom_utils import (
    boolean_constant,
    resolve_atom_with_constants,
)
from model_checker.algorithms.explicit.shared.result_formatters import (
    format_model_checking_result,
    verify_initial_state,
)
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.formulas.CapATL.parser import KCAP_OPERATOR_PATTERN
from model_checker.parsers.syntax_patterns import (
    CAPATL_COALITION_TOKEN,
    spelling_to_symbol,
)
from model_checker.utils.error_handler import (
    create_error_response,
    unresolved_leaves_error,
)

STRATEGIC_PATTERN = re.compile(rf"^{CAPATL_COALITION_TOKEN}([XFGUR])$")
CONNECTIVES = spelling_to_symbol("NOT", "AND", "OR", "IMPLIES")
# F and G are U and R with a constant left operand.
SOLVERS = {
    "X": (next_states, None),
    "F": (until_states, True),
    "U": (until_states, None),
    "G": (release_states, False),
    "R": (release_states, None),
}


def _connective(node: Any, value: Callable[[Any], bool]) -> bool:
    """`!`, `&&`, `||` or `->` (any spelling) of the values of the operands."""
    op = CONNECTIVES[node[0]]
    if op == "!":
        return not value(node[1])
    if op == "&&":
        return value(node[1]) and value(node[2])
    if op == "||":
        return value(node[1]) or value(node[2])
    return not value(node[1]) or value(node[2])


def _is_knowledge(node: Any) -> bool:
    return isinstance(node, tuple) and bool(KCAP_OPERATOR_PATTERN.match(node[0]))


def _propositions(node: Any) -> set[str]:
    """Leaves outside knowledge operators: propositions and constants."""
    if isinstance(node, str):
        return {node}
    if _is_knowledge(node):
        return set()
    return set().union(*(_propositions(child) for child in node[1:]))


def _capacities_named(node: Any) -> set[str]:
    """Capacity names in the `a is c` atoms of knowledge operators."""
    if isinstance(node, str):
        return set()
    if node[0] == "is":
        return {node[2]}
    return set().union(*(_capacities_named(child) for child in node[1:]))


def _observed_agents(node: Any) -> frozenset[int]:
    """Agents named by a K, not counting nested strategic operators."""
    # A nested strategic operator starts its own play.
    if isinstance(node, str) or STRATEGIC_PATTERN.match(node[0]):
        return frozenset()
    if _is_knowledge(node):
        return frozenset({int(node[0][1:])})
    return frozenset().union(*(_observed_agents(child) for child in node[1:]))


class _Evaluator:
    """Whether a state formula holds at a state, given what each agent knows."""

    def __init__(self, cgs: Any, atoms: dict[str, set[str]]):
        self.model = CapModel(cgs)
        self.states = [str(s) for s in cgs.states]
        self.atoms = atoms
        self._strategic_states: dict[Any, set[str]] = {}
        self._capacity_masks: dict[Any, int] = {}
        self._holds: dict[tuple[Any, str, Knowledge], bool] = {}

    def satisfying_states(self, formula: Any) -> set[str]:
        """States where the formula holds before any move."""
        knowledge = self.model.initial_knowledge
        return {s for s in self.states if self.holds(formula, s, knowledge)}

    def holds(self, node: Any, state: str, knowledge: Knowledge) -> bool:
        key = (node, state, knowledge)
        if key not in self._holds:
            self._holds[key] = self._compute(node, state, knowledge)
        return self._holds[key]

    def _compute(self, node: Any, state: str, knowledge: Knowledge) -> bool:
        if isinstance(node, str):
            return state in self.atoms[node]
        if node[0] in CONNECTIVES:
            return _connective(node, lambda c: self.holds(c, state, knowledge))
        if _is_knowledge(node):
            known = knowledge[int(node[0][1:]) - 1]
            return known & ~self._capacity_mask(node[1]) == 0
        if node not in self._strategic_states:
            self._strategic_states[node] = self._strategic(node)
        return state in self._strategic_states[node]

    def _capacity_mask(self, node: Any) -> int:
        """Assignments that satisfy a capacity formula (`a is c`, connectives)."""
        if node not in self._capacity_masks:
            mask = 0
            for i, kappa in enumerate(self.model.assignments):
                if self._capacity_formula(node, kappa):
                    mask |= 1 << i
            self._capacity_masks[node] = mask
        return self._capacity_masks[node]

    def _capacity_formula(self, node: Any, kappa: tuple[str, ...]) -> bool:
        if isinstance(node, str):
            constant = boolean_constant(node)
            if constant is None:
                raise ValueError(f"{node!r} is not allowed inside a knowledge operator")
            return constant
        if node[0] == "is":
            return kappa[int(node[1]) - 1] == node[2]
        return _connective(node, lambda c: self._capacity_formula(c, kappa))

    def _strategic(self, node: Any) -> set[str]:
        match = STRATEGIC_PATTERN.match(node[0])
        if match is None:
            raise ValueError(f"CapATL operator {node[0]!r} is not supported")
        coalition = sorted(int(a) for a in match.group(1).split(","))
        solve, constant = SOLVERS[match.group(2)]
        tests: list[StateTest] = [partial(self.holds, child) for child in node[1:]]
        if constant is not None:
            tests.insert(0, lambda _s, _k: constant)
        observed = frozenset().union(*(_observed_agents(c) for c in node[1:]))
        result: set[str] = set()
        for capacities in itertools.product(
            *(self.model.capacities[a] for a in coalition)
        ):
            game = CoalitionGame(self.model, coalition, capacities, observed)
            result |= solve(game, [s for s in self.states if s not in result], *tests)
        return result


def _core_capatl_checking(cgs, formula):
    """Run CapATL model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("CapATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    unknown = sorted(_capacities_named(res_parsing) - set(cgs.capacities_list))
    if unknown:
        return create_error_response(
            "semantic",
            f"Capacity {', '.join(map(repr, unknown))} is not in the model's "
            f"Capacities {cgs.capacities_list}",
        )

    leaves = _propositions(res_parsing)
    atoms: dict[str, set[str]] = {}
    for leaf in leaves:
        states = resolve_atom_with_constants(cgs, leaf, parser)
        if states is None:
            return unresolved_leaves_error(leaves, cgs.atomic_propositions)
        atoms[leaf] = states

    try:
        evaluator = _Evaluator(cgs, atoms)
    except ValueError as error:  # a transition label with the wrong number of actions
        return create_error_response("model", str(error))
    winning_states = evaluator.satisfying_states(res_parsing)
    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, winning_states)
    return format_model_checking_result(winning_states, initial_state, is_satisfied)


model_checking = create_model_checking_entry("CapATL", _core_capatl_checking)
