from model_checker.parsers.formulas.TOL import *
from model_checker.parsers.formulas.TOL.parser import (
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
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import *
from model_checker.parsers.game_structures.timed_cgs.ZoneGraph import ZoneGraph

from model_checker.models.model_factory import CostCGS

# =============================================================================
# NEW AST-BASED APPROACH (similar to TCTL)
# =============================================================================


def extract_closest_constraint(node: Expr) -> tuple[str]:
    """
    Extracts the closest time constraint from an AST node.
    """
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
    """
    Returns states that satisfy time constraints using zone graph.
    """
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
    """
    Recursively resolves the formula AST according to the operator.
    The result is stored in `node.satisfying_states`.
    """
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

    # Solve subtrees recursively
    if hasattr(node, "operand"):
        solve_tree_ast(timedCostCGS, zone_graph, node.operand)
    if hasattr(node, "left"):
        solve_tree_ast(timedCostCGS, zone_graph, node.left)
    if hasattr(node, "right"):
        solve_tree_ast(timedCostCGS, zone_graph, node.right)
    if hasattr(node, "subject"):
        solve_tree_ast(timedCostCGS, zone_graph, node.subject)

    # Apply operators based on node type
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
            # <Jn>Gφ = <Jn>false R φ
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
            # <Jn>Fφ = <Jn>true U φ
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
            # φ U ψ
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
            # φ R ψ
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
            # φ W ψ = ψ R (φ ∨ ψ)
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
        # Clock constraint will be applied when needed


def model_checking_ast(formula: str, filename: str):
    """
    New model checking function using AST approach.
    """
    global timedCostCGS

    if not formula.strip():
        result = {"res": "Error: formula not entered"}
        return result

    # Parse formula using new AST parser
    ast = do_parsing(formula.strip())
    if ast is None:
        result = {"res": "Syntax Error"}
        return result

    # Parse model
    timedCostCGS = TimedCGS()
    timedCostCGS.read_file(filename)
    build_pre_set_array()

    # Execute model checking
    zone_graph = ZoneGraph(timedCostCGS)
    solve_tree_ast(timedCostCGS, zone_graph, ast)

    # Result: check whether the initial state satisfies the formula
    bool_res = timedCostCGS.initial_state in ast.satisfying_states
    result = {
        "res": "Result set: " + str(ast.satisfying_states),
        "initial_state": "Initial state "
        + str(timedCostCGS.initial_state)
        + ": "
        + str(bool_res),
    }
    return result


# =============================================================================
# ORIGINAL TUPLE-BASED APPROACH (preserved for reference)
# =============================================================================

# Global variables for the original approach
last_filename = ""
pre_set_array = []


class Vertex:
    """Each node in the AST"""

    def __init__(
        self, value: Expr, left=None, right=None, time_constraints: tuple[str] = None
    ):
        self.value = value
        self.left = left
        self.right = right
        self.time_constraints = time_constraints

    def __str__(self):
        return str(self.value)


def _print_tree(node, level=0):
    if isinstance(node, Vertex):
        _print_tree(node.left, level + 1)
        value = f" " * 4 * level + "-> " + str(node.value)
        if node.time_constraints != None:
            value += "".join(node.time_constraints)
        _print_tree(node.right, level + 1)


# returns the states where the proposition holds
def get_states_prop_holds(prop):
    states = set()
    prop_matrix = timedCostCGS.get_matrix_proposition()

    index = timedCostCGS.get_atom_index(prop)
    if index is None:
        return None
    for state, source in enumerate(prop_matrix):
        if source[int(index)] == 1:
            states.add(state)
    return states


# set of states (ex. s1, s2) as input and returns a set of indices to identify them
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


# converts a string into a set
def string_to_set(string):
    if string == "set()":
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)


#  function that builds a formula tree, used by the model checker
def build_tree(tpl):
    if isinstance(tpl, tuple):
        root = Vertex(tpl[0])
        if len(tpl) > 1:
            left_child = build_tree(tpl[1])
            if left_child is None:
                return None
            root.left = left_child
            if len(tpl) > 2:
                right_child = build_tree(tpl[2])
                if right_child is None:
                    return None
                root.right = right_child
    elif isinstance(tpl, ClockExpr):
        states_prop_holds = set()
        if isinstance(tpl.subject, tuple):
            tree = build_tree(tpl.subject)
            if verify("AND", tree.value):
                states_prop_holds = string_to_set(tree.left.value).intersection(
                    tree.right.value
                )
            elif verify("OR", tree.value):
                states_prop_holds = string_to_set(tree.left.value).union(
                    tree.right.value
                )
            elif verify("NOT", tree.value):
                states_prop_holds = set(timedCostCGS.states) - string_to_set(
                    tree.left.value
                )
            tpl.satisfying_states.update(states_prop_holds)
        else:
            states_prop_holds = get_states_prop_holds(tpl.subject)
            for element in states_prop_holds:
                state_name = str(timedCostCGS.get_state_name_by_index(element))
                tpl.satisfying_states.add(str(state_name))

        root = Vertex(
            value=str(tpl.satisfying_states), time_constraints=tpl.constraints
        )
    else:
        states = set()
        if verify("FALSE", str(tpl)):
            return Vertex(str(states))
        elif verify("TRUE", str(tpl)):
            return Vertex(str(set(timedCostCGS.get_states())))
        states_proposition = get_states_prop_holds(str(tpl))
        if states_proposition is None:
            return None
        else:
            for element in states_proposition:
                states.add(timedCostCGS.get_state_name_by_index(element))
            root = Vertex(str(states))
    return root


def complement(state_set):
    result = set()
    graph = timedCostCGS.get_graph()
    if len(graph) - len(state_set) <= 0:
        return result
    for i in range(0, len(graph)):
        if i not in state_set:
            result.add(i)
    return result


# pre with standard matrix
def pre(state_set, constraints: tuple[str] = None):
    result = set()
    graph = timedCostCGS.get_graph()
    for i, source in enumerate(
        graph
    ):  # take states that have at least one transition to one of the states in the set
        for j in state_set:
            if graph[i][j] != 0:
                result.add(i)
                break  # optimization

    return result


def pre_timed(state_set, zone_graph: ZoneGraph, constraints: tuple[str]):
    result = set()
    graph = timedCostCGS.get_graph()
    transitions = timedCostCGS.get_edges()

    # Convert state names to indices if needed (ensure consistency)
    # state_indices = convert_state_set(state_set)

    for i, source_row in enumerate(graph):  # For each potential predecessor state 'i'
        for source_name, target_name in transitions:
            source_idx = timedCostCGS.get_index_by_state_name(source_name)
            target_idx = timedCostCGS.get_index_by_state_name(target_name)

            if source_idx == i and target_idx in state_set:
                # Use ZoneGraph to find if a valid timed path exists
                cc, _ = DBMAdapter.parse_constraints(
                    [constraints], timedCostCGS.clocks_dict
                )
                paths = zone_graph.find_path_from(target_name, cc)
                if len(paths) > 0:
                    result.add(i)
                    break  # Found a path, move to next predecessor

    return result


# builds an array where the j-th element is a set with all the predecessors of the j-th state
def build_pre_set_array():
    global pre_set_array
    graph = timedCostCGS.get_graph()
    graph_len = len(graph)
    result = [set() for _ in range(graph_len)]
    for i in range(0, graph_len):
        for j in range(0, graph_len):
            if graph[i][j] != 0:
                result[j].add(i)
    pre_set_array = result


# pre that uses the array of predecessors instead of the graph matrix
def pre_set_variant(state_set, constraints: tuple[str] = None):
    result = set()
    for i in state_set:
        for j in pre_set_array[i]:
            if constraints:
                zone_predecessors = DBMAdapter.compute_predecessors(
                    tcgs=timedCostCGS, source=i, target=j, formulas=constraints
                )
                non_empty_zones = [
                    zone for zone in zone_predecessors if not (zone.is_empty())
                ]
                if len(non_empty_zones) >= 1:
                    result.add(i)
            else:
                result.add(i)
    return result


# triangle "right" operator
def triangle(s, n, state_set):
    cost = 0
    tCost = 0
    graph = timedCostCGS.get_graph()
    isLoopPresent = False
    for r in state_set:
        if graph[s][r] != "*":
            value = graph[s][r]
            if isinstance(value, str) and ":" in value:
                cost += sum(int(part) for part in value.split(":") if part)
            else:
                cost += int(value)
        else:
            isLoopPresent = True
    # return ((cost <= n and (cost != 0 or isLoopPresent)))
    return cost <= n


# triangle "down" operator
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


# triangle "down" operator
def triangle_down_variant(n, state_set, constraints: tuple[str] = None):
    result = set()
    state_set = convert_state_set(state_set)
    state_set_complement = complement(state_set)
    predecessors = pre_set_variant(state_set, constraints)
    for s in predecessors:
        if triangle(s, n, state_set_complement):
            result.add(s)
    return convert_indices_state_set(result)


# function that solves the formula tree. The result is the model checking result.
# It solves every node depending on the operator.
def solve_tree(node, zone_graph: ZoneGraph):
    if node.left is not None:
        solve_tree(node.left, zone_graph)
    if node.right is not None:
        solve_tree(node.right, zone_graph)
    i = 0
    if node.right is None:  # UNARY OPERATORS: not, globally, next, eventually
        if verify("NOT", node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            all_states = set(timedCostCGS.get_states())
            ris = all_states - states
            node.value = str(ris)

        elif verify("DEMONIC", node.value) and verify(
            "GLOBALLY", node.value
        ):  # e.g. <Jn>Gφ
            # <Jn>falseRφ
            n = int(node.value[2:-2])
            states1 = set()
            states2 = string_to_set(node.left.value)
            p = set(timedCostCGS.states)
            t = states2
            while t != p:
                p = t
                t = states2 & (
                    states1
                    | triangle_down(n, p, zone_graph, node.left.time_constraints)
                )
            node.value = str(p)

        elif verify("DEMONIC", node.value) and verify(
            "NEXT", node.value
        ):  # e.g. <Jn>Xφ
            n = int(node.value[2:-2])
            states = string_to_set(node.left.value)
            ris = triangle_down(n, states, zone_graph, node.left.time_constraints)
            node.value = str(ris)

        elif verify("DEMONIC", node.value) and verify(
            "EVENTUALLY", node.value
        ):  # e.g. <Jn>Fφ
            # <Jn>trueUϕ.
            n = int(node.value[2:-2])
            states1 = set(timedCostCGS.get_states())
            states2 = string_to_set(node.left.value)
            p = set()
            t = states2
            while t != p:
                p = t
                t = states2 | (
                    states1
                    & triangle_down(n, p, zone_graph, node.left.time_constraints)
                )
            node.value = str(p)

    if (
        node.left is not None and node.right is not None
    ):  # BINARY OPERATORS: or, and, until, implies
        if verify("OR", node.value):  # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify("DEMONIC", node.value) and verify(
            "UNTIL", node.value
        ):  # e.g. <Jn>φUθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set()
            t = states2
            while t != p:
                p = t
                t = states2 | (
                    states1
                    & triangle_down(n, p, zone_graph, node.left.time_constraints)
                )
            node.value = str(p)
        elif verify("DEMONIC", node.value) and verify(
            "RELEASE", node.value
        ):  # e.g. <Jn>φRθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set(timedCostCGS.get_states())
            t = states2
            while t != p:
                p = t
                t = states2 & (
                    states1
                    | triangle_down(n, p, zone_graph, node.right.time_constraints)
                )
            node.value = str(p)
        elif verify("DEMONIC", node.value) and verify(
            "WEAK", node.value
        ):  # e.g. <Jn>φWθ
            # <Jn>(θ R (φ ∨ θ))
            n = int(node.value[2:-2])
            states1 = string_to_set(node.right.value)
            states2 = string_to_set(node.left.value) | states1
            p = set(timedCostCGS.get_states())
            t = states2
            while t != p:
                p = t
                t = states2 & (
                    states1
                    | triangle_down(n, p, zone_graph, node.left.time_constraints)
                )
            node.value = str(p)

        elif verify("AND", node.value):  # e.g. φ && θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verify("IMPLIES", node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(timedCostCGS.states).difference(states1)
            ris = not_states1.union(states2)
            node.value = str(ris)


def solve_tree_adjacency_list(node):
    if node.left is not None:
        solve_tree(node.left)
    if node.right is not None:
        solve_tree(node.right)
    if node.right is None:  # UNARY OPERATORS: not, globally, next, eventually
        if verify("NOT", node.value):  # e.g. ¬φ
            states = string_to_set(node.left.value)
            all_states = set(timedCostCGS.get_states())
            ris = all_states - states
            node.value = str(ris)

        elif verify("DEMONIC", node.value) and verify(
            "GLOBALLY", node.value
        ):  # e.g. <Jn>Gφ
            # <Jn>falseRφ
            n = int(node.value[2:-2])
            states1 = set()
            states2 = string_to_set(node.left.value)
            p = set(timedCostCGS.get_states())
            t = states2
            while t != p:
                p = t
                t = states2 & (states1 | triangle_down_variant(n, p))
                i += 1
            node.value = str(p)

        elif verify("DEMONIC", node.value) and verify(
            "NEXT", node.value
        ):  # e.g. <Jn>Xφ
            n = int(node.value[2:-2])
            states = string_to_set(node.left.value)
            ris = triangle_down_variant(n, states)
            node.value = str(ris)

        elif verify("DEMONIC", node.value) and verify(
            "EVENTUALLY", node.value
        ):  # e.g. <Jn>Fφ
            # <Jn>trueUϕ.
            n = int(node.value[2:-2])
            states1 = set(timedCostCGS.get_states())
            states2 = string_to_set(node.left.value)
            p = set()
            t = states2
            while t != p:
                p = t
                t = states2 | (states1 & triangle_down_variant(n, p))
            node.value = str(p)

    if (
        node.left is not None and node.right is not None
    ):  # BINARY OPERATORS: or, and, until, implies
        if verify("OR", node.value):  # e.g. φ || θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verify("DEMONIC", node.value) and verify(
            "UNTIL", node.value
        ):  # e.g. <Jn>φUθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set()
            t = states2
            while t != p:
                p = t
                t = states2 | (states1 & triangle_down_variant(n, p))
            node.value = str(p)
        elif verify("DEMONIC", node.value) and verify(
            "RELEASE", node.value
        ):  # e.g. <Jn>φRθ
            n = int(node.value[2:-2])
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            p = set(timedCostCGS.get_states())
            t = states2
            while t != p:
                p = t
                t = states2 & (states1 | triangle_down_variant(n, p))
            node.value = str(p)
        elif verify("DEMONIC", node.value) and verify(
            "WEAK", node.value
        ):  # e.g. <Jn>φWθ
            # <Jn>(θ R (φ ∨ θ))
            n = int(node.value[2:-2])
            states1 = string_to_set(node.right.value)
            states2 = string_to_set(node.left.value) | states1
            p = set(timedCostCGS.get_states())
            t = states2
            while t != p:
                p = t
                t = states2 & (states1 | triangle_down_variant(n, p))
            node.value = str(p)

        elif verify("AND", node.value):  # e.g. φ && θ
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verify("IMPLIES", node.value):  # e.g. φ -> θ
            # p -> q ≡ ¬p ∨ q
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(timedCostCGS.get_states()).difference(states1)
            ris = not_states1.union(states2)
            node.value = str(ris)


# does the parsing of the model, the formula, builds a tree and then it returns the result of model checking
# function called by front_end_CS
# ORIGINAL VERSION - uses tuple-based parsing
def model_checking(formula: str, filename: str):
    global timedCostCGS
    # early returns before expensive computations
    if not formula.strip():
        result = {"res": "Error: formula not entered"}
        return result

    # formula parsing
    res_parsing = do_parsing(formula)
    if res_parsing is None:
        result = {"res": "Syntax Error"}
        return result

    # parsing of the model
    timedCostCGS = TimedCGS()
    timedCostCGS.read_file(filename)
    build_pre_set_array()

    root = build_tree(res_parsing)
    if root is None:
        result = {"res": "Syntax Error: the atom does not exist"}
        return result

    # model checking
    zone_graph = ZoneGraph(timedCostCGS)
    solve_tree(root, zone_graph)

    # solution
    result = {"res": "Result: " + str(root.value)}
    return result


# NEW VERSION - uses AST-based parsing
def model_checking_new(formula: str, filename: str):
    """
    Wrapper function that uses the new AST approach.
    Can be called to test the new implementation.
    """
    return model_checking_ast(formula, filename)
