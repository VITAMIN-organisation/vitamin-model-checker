"""
COTL model checker.

Uses costCGS and the same formula syntax as OATL (<1><5>F p, etc.).
The model (cgs) is passed in by the engine execution layer instead of a global.
"""

from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    state_names_to_indices,
)
from model_checker.algorithms.explicit.shared import (
    verify_initial_state as _verify_initial_state,
)
from model_checker.algorithms.explicit.shared.cost_utils import (
    extract_coalition_and_cost,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
    build_pre_by_index,
    cross_indices,
)
from model_checker.algorithms.explicit.shared.state_utils import state_indices_to_names
from model_checker.engine.execution import create_model_checking_entry
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.utils.error_handler import (
    create_semantic_error,
    create_syntax_error,
)
from model_checker.utils.formula_tree import build_formula_tree
from model_checker.utils.literals import parse_state_set_literal


def _get_states_prop_holds(cgs, prop):
    prop_matrix = cgs.matrix_prop
    index = proposition_index(cgs.atomic_propositions, prop)
    if index is None:
        return None
    states = set()
    for state, source in enumerate(prop_matrix):
        if int(source[int(index)]) == 1:
            states.add(state)
    return states


def _resolve_atom_cotl(cgs, atom):
    """Resolve an atom or constant to state names, or None if it is not in the model."""
    tpl_str = str(atom)
    parser = FormulaParserFactory.get_parser_instance("OATL")
    if parser.verify("FALSE", tpl_str):
        return set()
    if parser.verify("TRUE", tpl_str):
        return {str(s) for s in cgs.states}
    states_proposition = _get_states_prop_holds(cgs, tpl_str)
    if states_proposition is None:
        return None
    return {cgs.get_state_name_by_index(i) for i in states_proposition}


def _get_cached_cost(cgs, action, state, agents_set):
    """Return cost for (action, state, agents_set), using cache."""
    if not hasattr(cgs, "_cost_cache"):
        cgs._cost_cache = {}
    key = (action, state, tuple(agents_set))
    if key in cgs._cost_cache:
        return cgs._cost_cache[key]
    try:
        costs = cgs.get_cost_for_action(action, state)
        if isinstance(costs[0], list):
            aux = sum(costs[0][int(i) - 1] for i in agents_set)
        else:
            aux = sum(costs[int(i) - 1] for i in agents_set)
    except (KeyError, IndexError, AttributeError, TypeError):
        aux = None
    cgs._cost_cache[key] = aux
    return aux


def _Cost(cgs, action_set, state, agents, agents_set=None):
    if agents_set is None:
        agents_set = cgs_actions.get_agents_from_coalition(agents)
    total = None
    for action in action_set:
        aux = _get_cached_cost(cgs, action, state, agents_set)
        if aux is not None and (total is None or aux < total):
            total = aux
    return total


def _cross_index(
    cgs,
    max_cost,
    coalition,
    state_indices,
    solve_context,
    agents_set,
    base_action_cache,
):
    """Cost-bounded pre-image in index space using coalition-specific costs."""

    def affordable(cgs, actions, state_name, bound):
        cost = _Cost(cgs, actions, state_name, coalition, agents_set=agents_set)
        return cost is not None and cost <= bound

    return cross_indices(
        cgs,
        max_cost,
        coalition,
        state_indices,
        solve_context,
        base_action_cache,
        affordable,
    )


def _solve_unary_globally(cgs, node, solve_context):
    coalition, n = extract_coalition_and_cost(node.value)
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    agents_set = cgs_actions.get_agents_from_coalition(coalition)

    def update(p):
        return states2_index & _cross_index(
            cgs,
            n,
            coalition,
            p,
            solve_context,
            agents_set,
            cgs._base_action_cache,
        )

    t_index = greatest_fixpoint(states2_index, update)
    node.value = str(
        tuple(sorted({str(s) for s in state_indices_to_names(cgs, t_index)}))
    )


def _solve_unary_next(cgs, node, solve_context):
    coalition, n = extract_coalition_and_cost(node.value)
    states_index = state_names_to_indices(cgs, parse_state_set_literal(node.left.value))
    agents_set = cgs_actions.get_agents_from_coalition(coalition)
    res_index = _cross_index(
        cgs,
        n,
        coalition,
        states_index,
        solve_context,
        agents_set,
        cgs._base_action_cache,
    )
    node.value = str(
        tuple(sorted({str(s) for s in state_indices_to_names(cgs, res_index)}))
    )


def _solve_unary_eventually(cgs, node, solve_context, all_states_index):
    coalition, n = extract_coalition_and_cost(node.value)
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    agents_set = cgs_actions.get_agents_from_coalition(coalition)

    def update(p):
        cross_result = _cross_index(
            cgs,
            n,
            coalition,
            p,
            solve_context,
            agents_set,
            cgs._base_action_cache,
        )
        return states2_index | (all_states_index & cross_result)

    t_index = least_fixpoint(states2_index, update)
    node.value = str(
        tuple(sorted({str(s) for s in state_indices_to_names(cgs, t_index)}))
    )


def _solve_binary_or(node):
    node.value = str(
        tuple(
            sorted(
                {
                    str(s)
                    for s in parse_state_set_literal(node.left.value).union(
                        parse_state_set_literal(node.right.value)
                    )
                }
            )
        )
    )


def _solve_binary_until(cgs, node, solve_context):
    coalition, n = extract_coalition_and_cost(node.value)
    states1_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )
    agents_set = cgs_actions.get_agents_from_coalition(coalition)

    def update(p):
        cross_result = _cross_index(
            cgs,
            n,
            coalition,
            p,
            solve_context,
            agents_set,
            cgs._base_action_cache,
        )
        return states2_index | (states1_index & cross_result)

    t_index = least_fixpoint(states2_index, update)
    node.value = str(
        tuple(sorted({str(s) for s in state_indices_to_names(cgs, t_index)}))
    )


def _solve_binary_release(cgs, node, solve_context, all_states_index):
    coalition, n = extract_coalition_and_cost(node.value)
    states1_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )
    agents_set = cgs_actions.get_agents_from_coalition(coalition)

    def update(p):
        cross_result = _cross_index(
            cgs,
            n,
            coalition,
            p,
            solve_context,
            agents_set,
            cgs._base_action_cache,
        )
        return states2_index & (states1_index | cross_result)

    t_index = greatest_fixpoint(states2_index, update)
    node.value = str(
        tuple(sorted({str(s) for s in state_indices_to_names(cgs, t_index)}))
    )


def _solve_binary_weak(cgs, node, solve_context, all_states_index):
    coalition, n = extract_coalition_and_cost(node.value)
    states1 = parse_state_set_literal(node.right.value)
    states2 = parse_state_set_literal(node.left.value) | states1
    states1_index = state_names_to_indices(cgs, states1)
    states2_index = state_names_to_indices(cgs, states2)
    agents_set = cgs_actions.get_agents_from_coalition(coalition)

    def update(p):
        cross_result = _cross_index(
            cgs,
            n,
            coalition,
            p,
            solve_context,
            agents_set,
            cgs._base_action_cache,
        )
        return states2_index & (states1_index | cross_result)

    t_index = greatest_fixpoint(states2_index, update)
    node.value = str(
        tuple(sorted({str(s) for s in state_indices_to_names(cgs, t_index)}))
    )


def _solve_binary_and(node):
    node.value = str(
        tuple(
            sorted(
                {
                    str(s)
                    for s in parse_state_set_literal(node.left.value).intersection(
                        parse_state_set_literal(node.right.value)
                    )
                }
            )
        )
    )


def _solve_binary_implies(node, all_states):
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = str(
        tuple(sorted({str(s) for s in all_states.difference(states1).union(states2)}))
    )


def _get_node_operator(node, parser):
    """Return operator key for this node, or None if not an operator we handle."""
    if node.right is None:
        if parser.verify("NOT", node.value):
            return "NOT"
        if parser.verify("COALITION_DEMONIC", node.value):
            if parser.verify("GLOBALLY", node.value):
                return "GLOBALLY"
            if parser.verify("NEXT", node.value):
                return "NEXT"
            if parser.verify("EVENTUALLY", node.value):
                return "EVENTUALLY"
        return None
    if node.left is None or node.right is None:
        return None
    if parser.verify("OR", node.value):
        return "OR"
    if parser.verify("AND", node.value):
        return "AND"
    if parser.verify("IMPLIES", node.value):
        return "IMPLIES"
    if parser.verify("COALITION_DEMONIC", node.value):
        if parser.verify("UNTIL", node.value):
            return "UNTIL"
        if parser.verify("RELEASE", node.value):
            return "RELEASE"
        if parser.verify("WEAK", node.value):
            return "WEAK"
    return None


def _make_solve_handlers():
    """Build dispatch map: operator key -> handler(context)."""

    def run_not(ctx):
        node = ctx["node"]
        node.value = str(
            tuple(
                sorted(
                    {
                        str(s)
                        for s in ctx["all_states"]
                        - parse_state_set_literal(node.left.value)
                    }
                )
            )
        )

    def run_globally(ctx):
        _solve_unary_globally(ctx["cgs"], ctx["node"], ctx["solve_context"])

    def run_next(ctx):
        _solve_unary_next(ctx["cgs"], ctx["node"], ctx["solve_context"])

    def run_eventually(ctx):
        _solve_unary_eventually(
            ctx["cgs"],
            ctx["node"],
            ctx["solve_context"],
            ctx["all_states_index"],
        )

    def run_or(ctx):
        _solve_binary_or(ctx["node"])

    def run_until(ctx):
        _solve_binary_until(ctx["cgs"], ctx["node"], ctx["solve_context"])

    def run_release(ctx):
        _solve_binary_release(
            ctx["cgs"],
            ctx["node"],
            ctx["solve_context"],
            ctx["all_states_index"],
        )

    def run_weak(ctx):
        _solve_binary_weak(
            ctx["cgs"],
            ctx["node"],
            ctx["solve_context"],
            ctx["all_states_index"],
        )

    def run_and(ctx):
        _solve_binary_and(ctx["node"])

    def run_implies(ctx):
        _solve_binary_implies(ctx["node"], ctx["all_states"])

    return {
        "NOT": run_not,
        "GLOBALLY": run_globally,
        "NEXT": run_next,
        "EVENTUALLY": run_eventually,
        "OR": run_or,
        "UNTIL": run_until,
        "RELEASE": run_release,
        "WEAK": run_weak,
        "AND": run_and,
        "IMPLIES": run_implies,
    }


_SOLVE_HANDLERS = _make_solve_handlers()


def _solve_tree(cgs, node, solve_context):
    if node.left is not None:
        _solve_tree(cgs, node.left, solve_context)
    if node.right is not None:
        _solve_tree(cgs, node.right, solve_context)

    parser = FormulaParserFactory.get_parser_instance("OATL")
    op = _get_node_operator(node, parser)
    if op is None:
        return

    num_states = len(solve_context["graph"])
    context = {
        "cgs": cgs,
        "node": node,
        "solve_context": solve_context,
        "all_states": {str(s) for s in cgs.states},
        "all_states_index": set(range(num_states)),
    }
    _SOLVE_HANDLERS[op](context)


def _core_cotl_checking(cgs, formula):
    if not hasattr(cgs, "_cost_cache"):
        cgs._cost_cache = {}
    else:
        cgs._cost_cache.clear()
    if not hasattr(cgs, "_base_action_cache"):
        cgs._base_action_cache = {}
    else:
        cgs._base_action_cache.clear()
    parser = FormulaParserFactory.get_parser_instance("OATL")
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = build_formula_tree(res_parsing, lambda atom: _resolve_atom_cotl(cgs, atom))
    if root is None:
        return create_semantic_error("The atom does not exist in the model")

    solve_context = {
        "graph": cgs.graph,
        "pre_by_index": build_pre_by_index(cgs.graph),
    }
    _solve_tree(cgs, root, solve_context)

    initial_state = cgs.initial_state
    is_satisfied = _verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


model_checking = create_model_checking_entry("COTL", _core_cotl_checking)
