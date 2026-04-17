"""
COTL model checker.

Uses costCGS and the same formula syntax as OATL (<1><5>F p, etc.).
The model (cgs) is passed in by the engine runner instead of a global.
"""

from model_checker.algorithms.explicit.shared import (
    format_model_checking_result,
    resolve_atom_with_constants,
    state_names_to_indices,
    state_set_to_str,
)
from model_checker.algorithms.explicit.shared import (
    verify_initial_state as _verify_initial_state,
)
from model_checker.algorithms.explicit.shared.bit_vector import (
    BitVectorStateSet,
    should_use_bit_vectors,
)
from model_checker.algorithms.explicit.shared.fixpoint_iter import (
    greatest_fixpoint,
    least_fixpoint,
)
from model_checker.engine.runner import (
    build_formula_tree,
    indices_to_state_names,
    parse_state_set_literal,
)
from model_checker.parsers.formula_parser_factory import FormulaParserFactory
from model_checker.utils.error_handler import (
    create_semantic_error,
    create_syntax_error,
)


def _get_parser():
    return FormulaParserFactory.get_parser_instance("OATL")


def _get_states_prop_holds(cgs, prop):
    """Return indices of states where prop holds."""
    parser = _get_parser()
    states = resolve_atom_with_constants(cgs, prop, parser)
    if states is None:
        return None
    return state_names_to_indices(cgs, states)


def build_tree(cgs, tpl):
    """Build formula tree with atom resolution for COTL."""
    parser = _get_parser()
    return build_formula_tree(
        tpl,
        lambda atom: resolve_atom_with_constants(cgs, atom, parser),
    )


def _cell_has_edge(cell):
    """True if the graph cell represents an edge (non-zero transition)."""
    return cell != 0 and cell != "0"


def _get_cached_base_action(cgs, action, agents_set):
    """Return base action for (action, agents_set), using cache."""
    if not hasattr(cgs, "_base_action_cache"):
        cgs._base_action_cache = {}
    key = (action, tuple(sorted(agents_set)))
    if key not in cgs._base_action_cache:
        cgs._base_action_cache[key] = cgs.get_base_action(action, agents_set)
    return cgs._base_action_cache[key]


def _build_pre_by_index(graph):
    """Build target index -> set of source indices from the graph. O(|S|^2) once."""
    n = len(graph)
    pre_by_index = [set() for _ in range(n)]
    for src in range(n):
        for tgt in range(n):
            if _cell_has_edge(graph[src][tgt]):
                pre_by_index[tgt].add(src)
    return pre_by_index


def _pre_index(state_set_index, pre_by_index):
    """Return predecessor state indices in one step. Uses pre_by_index, no name conversion."""
    result = set()
    for tgt in state_set_index:
        result.update(pre_by_index[tgt])
    return result


def _get_states_prop_holds(cgs, prop):
    prop_matrix = cgs.get_matrix_proposition()
    index = cgs.get_atom_index(prop)
    if index is None:
        return None
    states = set()
    for state, source in enumerate(prop_matrix):
        if int(source[int(index)]) == 1:
            states.add(state)
    return states


def _resolve_atom_cotl(cgs, atom):
    """
    Resolve atom or constant (FALSE, TRUE, proposition) to a set of state names.
    Returns None if the atom does not exist in the model.
    """
    tpl_str = str(atom)
    if _get_parser().verify("FALSE", tpl_str):
        return set()
    if _get_parser().verify("TRUE", tpl_str):
        return {str(s) for s in cgs.get_states()}
    states_proposition = _get_states_prop_holds(cgs, tpl_str)
    if states_proposition is None:
        return None
    return {cgs.get_state_name_by_index(i) for i in states_proposition}


def _build_tree(cgs, tpl):
    """Build formula tree using shared build_formula_tree with COTL atom resolution."""
    return build_formula_tree(tpl, lambda atom: _resolve_atom_cotl(cgs, atom))


def _check_if_action_is_extension(action, extension_action):
    for idx, letter in enumerate(action):
        if letter == "-":
            continue
        if letter != extension_action[idx]:
            return False
    return True


def _next(cgs, action, state):
    """Return the set of next state indices reachable when the coalition plays this action."""
    graph = cgs.graph
    row = graph[state]
    result = set()
    for index, cell in enumerate(row):
        if _cell_has_edge(cell):
            for elem_action in cgs.build_action_list(cell):
                if action == elem_action or _check_if_action_is_extension(
                    action, elem_action
                ):
                    result.add(index)
                    break
    return result


def _D_index(cgs, src_index, state_set_index, agents_set, graph):
    """Dominant actions from src_index that keep next state in state_set_index. Index-space only."""
    num_states = len(graph)
    row = graph[src_index]
    use_bit_vector = should_use_bit_vectors(num_states)
    if use_bit_vector:
        safe_bits = BitVectorStateSet(num_states, state_set_index)
    else:
        state_set_complement = set(range(num_states)) - state_set_index
    result = set()
    for _tgt_index, cell in enumerate(row):
        if not _cell_has_edge(cell):
            continue
        for action in cgs.build_action_list(cell):
            base_action = _get_cached_base_action(cgs, action, agents_set)
            next_states = _next(cgs, base_action, src_index)
            if use_bit_vector:
                all_safe = all(i in safe_bits for i in next_states)
            else:
                all_safe = len(next_states & state_set_complement) == 0
            if all_safe:
                result.add(action)
    return result


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
        agents_set = cgs.get_agents_from_coalition(agents)
    total = None
    for action in action_set:
        aux = _get_cached_cost(cgs, action, state, agents_set)
        if aux is not None and (total is None or aux < total):
            total = aux
    return total


def _cross_index(cgs, n, agents, state_indices, graph, pre_by_index, agents_set):
    """Cost-bounded pre-image in index space. Returns set of predecessor indices."""
    pre_indices = _pre_index(state_indices, pre_by_index)
    result = set()
    for src in pre_indices:
        actions = _D_index(cgs, src, state_indices, agents_set, graph)
        if actions:
            state_name = cgs.get_state_name_by_index(src)
            if _Cost(cgs, actions, state_name, agents, agents_set=agents_set) <= n:
                result.add(src)
    return result


def _extract_coalition_and_cost(string):
    tmp = string[1:].split(">")
    coalition = tmp[0]
    cost = tmp[1][1:]
    return (coalition, cost)


def _solve_unary_not(node, all_states):
    node.value = state_set_to_str(all_states - parse_state_set_literal(node.left.value))


def _solve_unary_globally(cgs, node, graph, pre_by_index, num_states, all_states_index):
    coalition, cost = _extract_coalition_and_cost(node.value)
    n = int(cost)
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    agents_set = cgs.get_agents_from_coalition(coalition)

    def update(p):
        return states2_index & _cross_index(
            cgs, n, coalition, p, graph, pre_by_index, agents_set
        )

    t_index = greatest_fixpoint(states2_index, update)
    node.value = state_set_to_str(indices_to_state_names(cgs, t_index))


def _solve_unary_next(cgs, node, graph, pre_by_index):
    coalition, cost = _extract_coalition_and_cost(node.value)
    n = int(cost)
    states_index = state_names_to_indices(cgs, parse_state_set_literal(node.left.value))
    agents_set = cgs.get_agents_from_coalition(coalition)
    res_index = _cross_index(
        cgs, n, coalition, states_index, graph, pre_by_index, agents_set
    )
    node.value = state_set_to_str(indices_to_state_names(cgs, res_index))


def _solve_unary_eventually(cgs, node, graph, pre_by_index, all_states_index):
    coalition, cost = _extract_coalition_and_cost(node.value)
    n = int(cost)
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    agents_set = cgs.get_agents_from_coalition(coalition)

    def update(p):
        cross_index = _cross_index(
            cgs, n, coalition, p, graph, pre_by_index, agents_set
        )
        return states2_index | (all_states_index & cross_index)

    t_index = least_fixpoint(states2_index, update)
    node.value = state_set_to_str(indices_to_state_names(cgs, t_index))


def _solve_binary_or(node):
    node.value = state_set_to_str(
        parse_state_set_literal(node.left.value).union(
            parse_state_set_literal(node.right.value)
        )
    )


def _solve_binary_until(cgs, node, graph, pre_by_index):
    coalition, cost = _extract_coalition_and_cost(node.value)
    n = int(cost)
    states1_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )
    agents_set = cgs.get_agents_from_coalition(coalition)

    def update(p):
        cross_index = _cross_index(
            cgs, n, coalition, p, graph, pre_by_index, agents_set
        )
        return states2_index | (states1_index & cross_index)

    t_index = least_fixpoint(states2_index, update)
    node.value = state_set_to_str(indices_to_state_names(cgs, t_index))


def _solve_binary_release(cgs, node, graph, pre_by_index, all_states_index):
    coalition, cost = _extract_coalition_and_cost(node.value)
    n = int(cost)
    states1_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.left.value)
    )
    states2_index = state_names_to_indices(
        cgs, parse_state_set_literal(node.right.value)
    )
    agents_set = cgs.get_agents_from_coalition(coalition)

    def update(p):
        cross_index = _cross_index(
            cgs, n, coalition, p, graph, pre_by_index, agents_set
        )
        return states2_index & (states1_index | cross_index)

    t_index = greatest_fixpoint(states2_index, update)
    node.value = state_set_to_str(indices_to_state_names(cgs, t_index))


def _solve_binary_weak(cgs, node, graph, pre_by_index, all_states_index):
    coalition, cost = _extract_coalition_and_cost(node.value)
    n = int(cost)
    states1 = parse_state_set_literal(node.right.value)
    states2 = parse_state_set_literal(node.left.value) | states1
    states1_index = state_names_to_indices(cgs, states1)
    states2_index = state_names_to_indices(cgs, states2)
    agents_set = cgs.get_agents_from_coalition(coalition)

    def update(p):
        cross_index = _cross_index(
            cgs, n, coalition, p, graph, pre_by_index, agents_set
        )
        return states2_index & (states1_index | cross_index)

    t_index = greatest_fixpoint(states2_index, update)
    node.value = state_set_to_str(indices_to_state_names(cgs, t_index))


def _solve_binary_and(node):
    node.value = state_set_to_str(
        parse_state_set_literal(node.left.value).intersection(
            parse_state_set_literal(node.right.value)
        )
    )


def _solve_binary_implies(node, all_states):
    states1 = parse_state_set_literal(node.left.value)
    states2 = parse_state_set_literal(node.right.value)
    node.value = state_set_to_str(all_states.difference(states1).union(states2))


def _get_node_operator(node):
    """Return operator key for this node, or None if not an operator we handle."""
    if node.right is None:
        if _get_parser().verify("NOT", node.value):
            return "NOT"
        if _get_parser().verify("COALITION_DEMONIC", node.value):
            if _get_parser().verify("GLOBALLY", node.value):
                return "GLOBALLY"
            if _get_parser().verify("NEXT", node.value):
                return "NEXT"
            if _get_parser().verify("EVENTUALLY", node.value):
                return "EVENTUALLY"
        return None
    if node.left is None or node.right is None:
        return None
    if _get_parser().verify("OR", node.value):
        return "OR"
    if _get_parser().verify("AND", node.value):
        return "AND"
    if _get_parser().verify("IMPLIES", node.value):
        return "IMPLIES"
    if _get_parser().verify("COALITION_DEMONIC", node.value):
        if _get_parser().verify("UNTIL", node.value):
            return "UNTIL"
        if _get_parser().verify("RELEASE", node.value):
            return "RELEASE"
        if _get_parser().verify("WEAK", node.value):
            return "WEAK"
    return None


def _make_solve_handlers():
    """Build dispatch map: operator key -> handler(context)."""

    def run_not(ctx):
        _solve_unary_not(ctx["node"], ctx["all_states"])

    def run_globally(ctx):
        _solve_unary_globally(
            ctx["cgs"],
            ctx["node"],
            ctx["graph"],
            ctx["pre_by_index"],
            ctx["num_states"],
            ctx["all_states_index"],
        )

    def run_next(ctx):
        _solve_unary_next(ctx["cgs"], ctx["node"], ctx["graph"], ctx["pre_by_index"])

    def run_eventually(ctx):
        _solve_unary_eventually(
            ctx["cgs"],
            ctx["node"],
            ctx["graph"],
            ctx["pre_by_index"],
            ctx["all_states_index"],
        )

    def run_or(ctx):
        _solve_binary_or(ctx["node"])

    def run_until(ctx):
        _solve_binary_until(ctx["cgs"], ctx["node"], ctx["graph"], ctx["pre_by_index"])

    def run_release(ctx):
        _solve_binary_release(
            ctx["cgs"],
            ctx["node"],
            ctx["graph"],
            ctx["pre_by_index"],
            ctx["all_states_index"],
        )

    def run_weak(ctx):
        _solve_binary_weak(
            ctx["cgs"],
            ctx["node"],
            ctx["graph"],
            ctx["pre_by_index"],
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


def _solve_tree(cgs, node, graph, pre_by_index, num_states):
    if node.left is not None:
        _solve_tree(cgs, node.left, graph, pre_by_index, num_states)
    if node.right is not None:
        _solve_tree(cgs, node.right, graph, pre_by_index, num_states)

    op = _get_node_operator(node)
    if op is None:
        return

    context = {
        "cgs": cgs,
        "node": node,
        "graph": graph,
        "pre_by_index": pre_by_index,
        "num_states": num_states,
        "all_states": {str(s) for s in cgs.get_states()},
        "all_states_index": set(range(num_states)),
    }
    _SOLVE_HANDLERS[op](context)


def _core_cotl_checking(cgs, formula):
    if hasattr(cgs, "_cost_cache"):
        cgs._cost_cache.clear()
    if hasattr(cgs, "_base_action_cache"):
        cgs._base_action_cache.clear()
    parser = _get_parser()
    res_parsing = parser.parse(formula, n_agent=cgs.get_number_of_agents())
    if res_parsing is None:
        error_msg = parser.errors[0] if parser.errors else "Syntax error in formula"
        return create_syntax_error(error_msg)

    root = _build_tree(cgs, res_parsing)
    if root is None:
        return create_semantic_error("The atom does not exist in the model")

    graph = cgs.graph
    num_states = len(graph)
    pre_by_index = _build_pre_by_index(graph)
    _solve_tree(cgs, root, graph, pre_by_index, num_states)

    initial_state = cgs.get_initial_state()
    is_satisfied = _verify_initial_state(initial_state, root.value)

    return format_model_checking_result(root.value, initial_state, is_satisfied)


def model_checking(formula: str, filename: str):
    from model_checker.engine.runner import execute_model_checking_with_parser

    return execute_model_checking_with_parser(
        formula, filename, "COTL", _core_cotl_checking
    )
