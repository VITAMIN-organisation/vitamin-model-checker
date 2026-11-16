"""CapATL model checker for capacity CGS models."""

import itertools
import re
from typing import Any

from model_checker.algorithms.explicit.CapATL.game import (
    CapModel,
    CoalitionGame,
    next_states,
    release_states,
    until_states,
)
from model_checker.algorithms.explicit.shared.atom_utils import (
    formula_leaves,
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


def _knowledge_operator(node) -> str | None:
    """The first knowledge operator (`K1`) in the parse tree, or None."""
    if isinstance(node, str):
        return node if KCAP_OPERATOR_PATTERN.match(node) else None
    if isinstance(node, tuple):
        for child in node:
            found = _knowledge_operator(child)
            if found:
                return found
    return None


class _Evaluator:
    """States where each subformula holds; a strategic formula restarts at its state."""

    def __init__(self, cgs: Any, atoms: dict[str, set[str]]):
        self.model = CapModel(cgs)
        self.states = [str(s) for s in cgs.states]
        self.all_states = set(self.states)
        self.atoms = atoms
        self._memo: dict[Any, set[str]] = {}

    def states_of(self, node: Any) -> set[str]:
        if node not in self._memo:
            self._memo[node] = self._compute(node)
        return self._memo[node]

    def _compute(self, node: Any) -> set[str]:
        if isinstance(node, str):
            return self.atoms[node]
        op = CONNECTIVES.get(node[0])
        if op == "!":
            return self.all_states - self.states_of(node[1])
        if op is not None:
            left, right = self.states_of(node[1]), self.states_of(node[2])
            if op == "&&":
                return left & right
            if op == "||":
                return left | right
            return (self.all_states - left) | right
        match = STRATEGIC_PATTERN.match(node[0])
        if match is None:
            raise ValueError(f"CapATL operator {node[0]!r} is not supported")
        coalition = sorted(int(a) for a in match.group(1).split(","))
        return self._strategic(coalition, match.group(2), node)

    def _strategic(self, coalition: list[int], temporal: str, node: Any) -> set[str]:
        solve, constant = SOLVERS[temporal]
        tests = [self.states_of(child).__contains__ for child in node[1:]]
        if constant is not None:
            tests.insert(0, lambda _s: constant)
        result: set[str] = set()
        for capacities in itertools.product(
            *(self.model.capacities[a] for a in coalition)
        ):
            game = CoalitionGame(self.model, coalition, capacities)
            result |= solve(game, [s for s in self.states if s not in result], *tests)
        return result


def _core_capatl_checking(cgs, formula):
    """Run CapATL model checking on a loaded model."""
    parser = FormulaParserFactory.get_parser_instance("CapATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_error_response("syntax", error_msg)

    knowledge_op = _knowledge_operator(res_parsing)
    if knowledge_op:
        return create_error_response(
            "validation",
            f"The knowledge operator {knowledge_op}(...) is parsed but not "
            "evaluated by the CapATL solver yet",
        )

    leaves = formula_leaves(res_parsing)
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
    winning_states = evaluator.states_of(res_parsing)
    initial_state = cgs.initial_state
    is_satisfied = verify_initial_state(initial_state, winning_states)
    return format_model_checking_result(winning_states, initial_state, is_satisfied)


model_checking = create_model_checking_entry("CapATL", _core_capatl_checking)
