import re

from model_checker.parsers.formulas.TOL.tol_ply_parser import (
    AtomicProp,
    Binary,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    SimpleTimeExpr,
    Unary,
    do_parsing,
    verify,
)
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.ZoneGraph import ZoneGraph


def get_states_prop_holds(prop):
    states = set()
    prop_matrix = timedCostCGS.matrix_prop
    index = proposition_index(timedCostCGS.atomic_propositions, prop)
    if index is None:
        return None
    for state, source in enumerate(prop_matrix):
        if source[int(index)] == 1:
            states.add(state)
    return states


def convert_state_set(state_set):
    states = set()
    for elem in state_set:
        position = timedCostCGS.get_index_by_state_name(elem)
        states.add(int(position))
    return states


def convert_indices_state_set(indices_state_set):
    states = set()
    for elem in indices_state_set:
        states.add(timedCostCGS.get_state_name_by_index(elem))
    return states


def complement(state_set):
    result = set()
    graph = timedCostCGS.get_graph()
    if len(graph) - len(state_set) <= 0:
        return result
    for i in range(0, len(graph)):
        if i not in state_set:
            result.add(i)
    return result


def pre(state_set, constraints: tuple[str] = None):
    result = set()
    graph = timedCostCGS.get_graph()
    for i, _source in enumerate(graph):
        for j in state_set:
            if graph[i][j] != 0:
                result.add(i)
                break
    return result


def pre_timed(state_set, zone_graph: ZoneGraph, constraints: tuple[str]):
    result = set()
    graph = timedCostCGS.get_graph()
    transitions = timedCostCGS.get_edges()

    for i, _ in enumerate(graph):
        for source_name, target_name in transitions:
            source_idx = timedCostCGS.get_index_by_state_name(source_name)
            target_idx = timedCostCGS.get_index_by_state_name(target_name)

            if source_idx == i and target_idx in state_set:
                cc, _ = DBMAdapter.parse_constraints(
                    [constraints], timedCostCGS.clocks_dict
                )
                paths = zone_graph.find_path_from(target_name, cc)
                if len(paths) > 0:
                    result.add(i)
                    break

    return result


def triangle(s, n, state_set):
    cost = 0
    graph = timedCostCGS.get_graph()
    for r in state_set:
        if graph[s][r] == "*":
            continue
        value = graph[s][r]
        if isinstance(value, str) and ":" in value:
            cost += sum(int(part) for part in value.split(":") if part)
        else:
            cost += int(value)
    return cost <= n


def triangle_down(n, state_set, zone_graph: ZoneGraph, constraints: tuple[str] = None):
    result = set()
    state_set = convert_state_set(state_set)
    state_set_complement = complement(state_set)
    if constraints:
        predecessors = pre_timed(state_set, zone_graph, constraints)
    else:
        predecessors = pre(state_set)
    for s in predecessors:
        if triangle(s, n, state_set_complement):
            result.add(s)
    return convert_indices_state_set(result)


def extract_closest_constraint(node: Expr) -> tuple[str]:
    """Extract the closest time constraint from an AST node."""
    c = getattr(node, "constraints", None)
    if c:
        return c

    for attr_name in ("operand", "left", "right", "subject"):
        child = getattr(node, attr_name, None)
        if child:
            res = extract_closest_constraint(child)
            if res:
                return res

    return None


def states_with_time_constraints(
    timedCostCGS, zone_graph: ZoneGraph, constraints: tuple[str]
):
    """Return states that satisfy time constraints using the zone graph."""
    result = set()
    guards, resets = DBMAdapter.parse_constraints(
        [constraints], timedCostCGS.clocks_dict
    )
    for state in sorted(zone_graph.states, key=lambda s: s.location):
        copy_state = state.copy()
        copy_state.apply_constraint(guards, resets)
        if not copy_state.zone.is_empty():
            result.add(copy_state.location)
    return result


def solve_tree_ast(timedCostCGS, zone_graph: ZoneGraph, node: Expr):
    """Recursively evaluate the formula AST; results go in node.satisfying_states."""
    if isinstance(node, AtomicProp):
        prop_states = get_states_prop_holds(node.name)
        for element in prop_states:
            state_name = str(timedCostCGS.get_state_name_by_index(element))
            node.satisfying_states.add(state_name)
        return

    if isinstance(node, SimpleTimeExpr):
        node.satisfying_states = states_with_time_constraints(
            timedCostCGS, zone_graph, node.constraints
        )
        return

    if hasattr(node, "operand"):
        solve_tree_ast(timedCostCGS, zone_graph, node.operand)
    if hasattr(node, "left"):
        solve_tree_ast(timedCostCGS, zone_graph, node.left)
    if hasattr(node, "right"):
        solve_tree_ast(timedCostCGS, zone_graph, node.right)
    if hasattr(node, "subject"):
        solve_tree_ast(timedCostCGS, zone_graph, node.subject)

    if isinstance(node, Unary):
        if verify("NOT", node.op):
            node.satisfying_states = (
                set(timedCostCGS.states) - node.operand.satisfying_states
            )

    elif isinstance(node, Binary):
        if verify("OR", node.op):
            node.satisfying_states = node.left.satisfying_states.union(
                node.right.satisfying_states
            )
        elif verify("AND", node.op):
            node.satisfying_states = node.left.satisfying_states.intersection(
                node.right.satisfying_states
            )
        elif verify("IMPLIES", node.op):
            not_states1 = set(timedCostCGS.states) - node.left.satisfying_states
            node.satisfying_states = not_states1.union(node.right.satisfying_states)

    elif isinstance(node, DemonicOp):
        n = int(re.findall(r"\d+", node.demonic_cost)[0])
        if verify("GLOBALLY", node.op):
            states1 = set()
            states2 = node.operand.satisfying_states
            p = set(timedCostCGS.states)
            t = states2
            constraint = extract_closest_constraint(node.operand)
            while t != p:
                p = t
                t = states2 & (states1 | triangle_down(n, p, zone_graph, constraint))
            node.satisfying_states = p

        elif verify("NEXT", node.op):
            constraint = extract_closest_constraint(node.operand)
            node.satisfying_states = triangle_down(
                n, node.operand.satisfying_states, zone_graph, constraint
            )

        elif verify("EVENTUALLY", node.op):
            states1 = set(timedCostCGS.states)
            states2 = node.operand.satisfying_states
            p = set()
            t = states2
            constraint = extract_closest_constraint(node.operand)
            while t != p:
                p = t
                t = states2 | (states1 & triangle_down(n, p, zone_graph, constraint))
            node.satisfying_states = t

    elif isinstance(node, DemonicBinary):
        n = int(re.findall(r"\d+", node.demonic_cost)[0])
        if verify("UNTIL", node.op):
            states1 = node.left.satisfying_states
            states2 = node.right.satisfying_states
            p = set()
            t = states2
            constraint = extract_closest_constraint(node.right)
            while t != p:
                p = t
                t = states2 | (states1 & triangle_down(n, p, zone_graph, constraint))
            node.satisfying_states = t

        elif verify("RELEASE", node.op):
            states1 = node.left.satisfying_states
            states2 = node.right.satisfying_states
            p = set(timedCostCGS.states)
            t = states2
            constraint = extract_closest_constraint(node.right)
            while t != p:
                p = t
                t = states2 & (states1 | triangle_down(n, p, zone_graph, constraint))
            node.satisfying_states = p

        elif verify("WEAK", node.op):
            states1 = node.right.satisfying_states
            states2 = node.left.satisfying_states | states1
            p = set(timedCostCGS.states)
            t = states2
            constraint = extract_closest_constraint(node.left)
            while t != p:
                p = t
                t = states2 & (states1 | triangle_down(n, p, zone_graph, constraint))
            node.satisfying_states = p

    elif isinstance(node, ClockExpr):
        node.satisfying_states = node.subject.satisfying_states


def model_checking_ast(formula: str, filename: str):
    """Model checking using the formula AST and zone-graph semantics."""
    global timedCostCGS

    if not formula.strip():
        return {"res": "Error: formula not entered"}

    ast = do_parsing(formula.strip())
    if ast is None:
        return {"res": "Syntax Error"}

    timedCostCGS = TimedCGS()
    timedCostCGS.read_file(filename)

    zone_graph = ZoneGraph(timedCostCGS)
    solve_tree_ast(timedCostCGS, zone_graph, ast)

    bool_res = timedCostCGS.initial_state in ast.satisfying_states
    return {
        "res": "Result set: " + str(ast.satisfying_states),
        "initial_state": "Initial state "
        + str(timedCostCGS.initial_state)
        + ": "
        + str(bool_res),
    }
