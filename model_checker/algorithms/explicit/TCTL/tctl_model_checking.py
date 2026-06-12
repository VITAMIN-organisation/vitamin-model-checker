from model_checker.parsers.formulas.TCTL import (
    AtomicProp,
    Binary,
    ClockExpr,
    Expr,
    QuantifiedPath,
    SimpleTimeExpr,
    Unary,
    do_parsingTCTL,
    verifyTCTL,
)
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index
from model_checker.parsers.game_structures.timed_cgs.DBM import DBMAdapter
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS
from model_checker.parsers.game_structures.timed_cgs.ZoneGraph import ZoneGraph


class Vertex:
    """Each node in the AST"""

    def __init__(
        self, value: Expr, left=None, right=None, timing_constraints: tuple[str] = None
    ):
        self.value = value
        self.left = left
        self.right = right
        self.time_constraints = timing_constraints


def _print_tree(node, level=0):
    if isinstance(node, Vertex):
        _print_tree(node.left, level + 1)
        value = " " * 4 * level + "-> " + str(node.value)
        if node.time_constraints is not None:
            value += "".join(node.time_constraints)
        _print_tree(node.right, level + 1)


def get_states_prop_holds(tcgs: TimedCGS, prop):
    """
    Returns the set of states in which the proposition `prop` is true.
    """
    states = set()
    prop_matrix = tcgs.matrix_prop
    index = proposition_index(tcgs.atomic_propositions, prop)
    if index is None:
        return None
    for state, row in enumerate(prop_matrix):
        if row[int(index)] == 1:
            states.add(state)
    return states


def convert_state_set(tcgs, state_set):
    """
    Converts a set of state names (e.g. {"s1", "s2"}) into the corresponding set of indices.
    """
    states = set()
    for elem in state_set:
        position = tcgs.get_index_by_state_name(elem)
        states.add(int(position))
    return states


def string_to_set(string: str):
    """
    Converts a string representing a set (e.g. "{s1, s2}") into a Python set object.
    """
    parts = string.split(":")
    if len(parts) > 1:
        return {parts[0].strip()}
    else:
        if string == "set()":
            return set()
        set_list = string.strip("{}").split(", ")
        new_string = "{" + ", ".join(set_list) + "}"
        return eval(new_string)


def build_tree(tcgs: TimedCGS, tpl):
    if isinstance(tpl, tuple):
        root = Vertex(tpl[0])
        if len(tpl) > 1:
            left_child = build_tree(tcgs, tpl[1])
            if left_child is None:
                return None
            root.left = left_child
            if len(tpl) > 2:
                right_child = build_tree(tcgs, tpl[2])
                if right_child is None:
                    return None
                root.right = right_child
    elif isinstance(tpl, ClockExpr):
        states_prop_holds = set()
        if isinstance(tpl.subject, tuple):
            tree = build_tree(tcgs, tpl.subject)
            if verifyTCTL("AND", tree.value):
                states_prop_holds = string_to_set(tree.left.value).intersection(
                    string_to_set(tree.right.value)
                )
            elif verifyTCTL("OR", tree.value):
                states_prop_holds = string_to_set(tree.left.value).union(
                    string_to_set(tree.right.value)
                )
            elif verifyTCTL("NOT", tree.value):
                states_prop_holds = set(tcgs.states) - string_to_set(tree.left.value)
            tpl.satisfying_states.update(states_prop_holds)
        else:
            states_prop_holds = get_states_prop_holds(tcgs, tpl.subject)
            for element in states_prop_holds:
                state_name = str(tcgs.get_state_name_by_index(element))
                tpl.satisfying_states.add(str(state_name))

        root = Vertex(
            value=str(tpl.satisfying_states), timing_constraints=tpl.constraints
        )
    elif isinstance(tpl, SimpleTimeExpr):
        root = Vertex(value=str(set(tcgs.states)), timing_constraints=tpl.constraints)

    else:  # Atomic node: build the set of states where the proposition is true.
        states = set()
        states_proposition = get_states_prop_holds(tcgs, str(tpl))
        if states_proposition is None:
            return None
        else:
            for element in states_proposition:
                # always convert to Python str
                state_name = str(tcgs.get_state_name_by_index(element))
                states.add(state_name)
            root = Vertex(str(states))
    return root


def pre_image_exist(tcgs: TimedCGS, list_holds_p, constraints: tuple):
    """
    Computes the pre-image algorithm of a real-time system using backwards zone reachability.
    """
    pre_list = set()
    transitions = tcgs.get_edges()
    for state in list(list_holds_p):
        for source, target in transitions:
            if target == state:
                zone_predecessors = DBMAdapter.compute_predecessors(
                    tcgs, source, target, constraints
                )
                non_empty_zones = [
                    zone for zone in zone_predecessors if not (zone.is_empty())
                ]
                if len(non_empty_zones) > 0:
                    pre_list.add(source)
    return pre_list


def pre_image_exist_time(
    tcgs: TimedCGS, zone_graph: ZoneGraph, list_holds_p: list[str], constraints: tuple
):
    """
    Computes the pre-image algorithm of a real-time system using backwards zone reachability.
    """
    pre_list = set()
    transitions = tcgs.get_edges()
    for state in sorted(list_holds_p):
        for source, target in transitions:
            if target == state:
                cc, _ = DBMAdapter.parse_constraints([constraints], tcgs.clocks_dict)
                paths = zone_graph.find_path_from(target, cc)
                if len(paths) > 0:
                    pre_list.add(source)
    return pre_list


def pre_image_all(transitions, states_set, holds_p):
    """
    Compute the universal pre-image (AX):
    Returns the states in `states_set` for which, if the state has successors,
    all successors belong to `holds_p`.
    (For deadlocks, AX is assumed to be true.)
    """
    pre_states = set()
    for state in states_set:
        # Collect successors of 'state'
        successors = {t for (s, t) in transitions if s == state}
        if not successors or successors.issubset(holds_p):
            pre_states.add(state)
    return pre_states


def pre_release_A(tcgs, holds_phi, holds_psi):
    """
    Compute A(φ R ψ) using the greatest fixpoint.
    Returns the set of states where A(φ R ψ) holds, i.e. states s such that:
      - s satisfies ψ, and
      - if s does not satisfy φ, then every successor of s belongs to the fixpoint.
    """
    all_states = set(tcgs.states)
    # Initially, the result (fixpoint) is given by the states satisfying ψ.
    result = holds_psi.copy()
    transitions = tcgs.get_edges()
    while True:
        new_result = set()
        for s in all_states:
            if s in holds_psi:
                # Check: if s satisfies φ or all successors of s (if any)
                # are already in result, then s is added to new_result.
                successors = {t for (s_, t) in transitions if s_ == s}
                if (
                    (s in holds_phi)
                    or (not successors)
                    or (successors.issubset(result))
                ):
                    new_result.add(s)
        if new_result == result:
            break
        result = new_result
    return result


def extract_closest_constraint(node: Expr) -> str:
    """
    Because time constraints can be applied at multiple levels of the formulae.
    """
    c = getattr(node, "constraints", None)
    if c:
        return node.constraints

    for attr_name in ("operand", "left", "right", "formula", "subject"):
        child = getattr(node, attr_name, None)
        if child:
            res = extract_closest_constraint(child)
            if res:
                return res

    return None


def states_with_time_constraints(
    tcgs: TimedCGS, zone_graph: ZoneGraph, constraints: tuple[str]
):
    result = set()
    guards, resets = DBMAdapter.parse_constraints([constraints], tcgs.clocks_dict)
    for state in sorted(zone_graph.states, key=lambda s: s.location):
        copy_state = state.copy()
        copy_state.apply_constraint(guards, resets)
        if not copy_state.zone.is_empty():
            result.add(copy_state.location)
        # z = DBMAdapter.add_constraints(tcgs, state.zone, constraints)
        # if not z.is_empty():
        #    result.add(state.location)

    return result


def solve_tree(tcgs: TimedCGS, zone_graph: ZoneGraph, node: Expr):
    """
    Recursively resolves the formula tree according to the operator.
    The result is stored in `node.satisfying_states`, which contains the set
    of states in which the formula holds.
    """
    if isinstance(node, AtomicProp):
        prop_states = get_states_prop_holds(tcgs, node.name)
        for element in prop_states:
            state_name = str(tcgs.get_state_name_by_index(element))
            node.satisfying_states.add(state_name)
        return

    if isinstance(node, SimpleTimeExpr):
        node.satisfying_states = states_with_time_constraints(
            tcgs, zone_graph, node.constraints
        )
        return

    if hasattr(node, "operand"):
        solve_tree(tcgs, zone_graph, node.operand)
    if hasattr(node, "left"):
        solve_tree(tcgs, zone_graph, node.left)
    if hasattr(node, "right"):
        solve_tree(tcgs, zone_graph, node.right)
    if hasattr(node, "formula"):
        solve_tree(tcgs, zone_graph, node.formula)
    if hasattr(node, "subject"):
        solve_tree(tcgs, zone_graph, node.subject)

    if isinstance(node, Unary):
        node.satisfying_states = set(tcgs.states) - node.operand.satisfying_states
    elif isinstance(node, ClockExpr):
        node.satisfying_states = (
            node.subject.satisfying_states
        )  # the clock constraint is applied later when resolving the quantified path.
    elif isinstance(node, Binary):
        if verifyTCTL("OR", node.op):
            node.satisfying_states = node.left.satisfying_states.union(
                node.right.satisfying_states
            )
        elif verifyTCTL("AND", node.op):
            node.satisfying_states = node.left.satisfying_states.intersection(
                node.right.satisfying_states
            )
        elif verifyTCTL("IMPLIES", node.op):  #  φ -> θ  ≡ ¬φ ∨ θ,
            states1 = node.left.satisfying_states
            states2 = node.right.satisfying_states
            not_states1 = set(tcgs.states) - states1
            rest = not_states1.union(states2)
            node.satisfying_states = rest

    elif isinstance(node, QuantifiedPath):
        if verifyTCTL("EXIST", node.quantifier) and verifyTCTL(
            "EVENTUALLY", node.quantifier
        ):
            target_obj = node.formula.satisfying_states
            T = target_obj.copy()
            constraint = extract_closest_constraint(node.formula)
            while True:
                new_T = T.union(pre_image_exist_time(tcgs, zone_graph, T, constraint))
                if new_T == T:
                    break
                T = new_T
            node.satisfying_states = T
        elif verifyTCTL("FORALL", node.quantifier) and verifyTCTL(
            "EVENTUALLY", node.quantifier
        ):
            target = set(tcgs.states) - node.formula.satisfying_states
            T = target.copy()
            while True:
                new_T = T.union(
                    pre_image_exist(
                        tcgs,
                        T,
                        constraints=extract_closest_constraint(node.formula),
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.satisfying_states = set(tcgs.states) - T
        elif verifyTCTL("EXIST", node.quantifier) and verifyTCTL(
            "GLOBALLY", node.quantifier
        ):
            target = node.formula.satisfying_states
            T = set(tcgs.states)
            while True:
                new_T = target.intersection(
                    pre_image_exist(
                        tcgs,
                        T,
                        constraints=extract_closest_constraint(node.formula),
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.satisfying_states = T
        elif verifyTCTL("FORALL", node.quantifier) and verifyTCTL(
            "GLOBALLY", node.quantifier
        ):
            target = set(tcgs.states) - node.formula.satisfying_states
            T = target.copy()
            while True:
                new_T = T.union(
                    pre_image_exist_time(
                        tcgs,
                        zone_graph,
                        T,
                        constraints=extract_closest_constraint(node.formula),
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.satisfying_states = set(tcgs.states) - T
        elif verifyTCTL("EXIST", node.quantifier) and verifyTCTL(
            "UNTIL", node.quantifier
        ):
            states_phi = node.formula.left.satisfying_states
            states_psi = node.formula.right.satisfying_states
            T = states_psi.copy()
            while True:
                new_T = T.union(
                    states_phi.intersection(
                        pre_image_exist(
                            tcgs,
                            T,
                            constraints=extract_closest_constraint(node.formula),
                        )
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.satisfying_states = T
        elif verifyTCTL("FORALL", node.value) and verifyTCTL("UNTIL", node.value):
            not_states_phi = set(tcgs.states) - node.formula.left.satisfying_states
            not_states_psi = set(tcgs.states) - node.formula.right.satisfying_states
            T = not_states_psi.copy()
            while True:
                new_T = T.union(
                    (not_states_phi.intersection(not_states_psi)).intersection(
                        pre_image_exist(
                            tcgs.get_edges(),
                            T,
                            clock_constraints=tcgs.get_clock_constraints(),
                        )
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.satisfying_states = set(tcgs.states) - T

    return

    # Solve the subtrees (recursion)
    if node.left is not None:
        solve_tree(tcgs, node.left)
    if node.right is not None:
        solve_tree(tcgs, node.right)

    # UNARY OPERATOR
    if node.right is None:
        if verifyTCTL("NOT", node.value):  # ¬φ, local (negation)
            states = string_to_set(node.left.value)
            ris = set(tcgs.states) - states
            node.value = str(ris)

        elif verifyTCTL("EXIST", node.value) and verifyTCTL(
            "NEXT", node.value
        ):  # EX φ, next doesn't exist on TCTL
            states = string_to_set(node.left.value)
            ris = pre_image_exist(
                tcgs.get_edges(), states, clock_constraints=tcgs.get_clock_constraints()
            )
            node.value = str(ris)

        elif verifyTCTL("FORALL", node.value) and verifyTCTL(
            "NEXT", node.value
        ):  # AX φ, next doesn't exist on TCTL
            states = string_to_set(node.left.value)
            ris = pre_image_all(tcgs.get_edges(), tcgs.states, states)
            node.value = str(ris)

        elif verifyTCTL("EXIST", node.value) and verifyTCTL(
            "EVENTUALLY", node.value
        ):  # EF φ
            # EF φ = least fixpoint: T = φ ∪ (EX φ) iterated
            target_obj = node.left
            target = string_to_set(target_obj.value)
            T = target.copy()
            while True:
                new_T = T.union(
                    pre_image_exist(
                        tcgs, list_holds_p=T, constraints=node.left.time_constraints
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.value = str(T)

        elif verifyTCTL("FORALL", node.value) and verifyTCTL(
            "EVENTUALLY", node.value
        ):  # AF φ
            # AF φ = ¬EG(¬φ). Compute EF on the complement and then take its complement
            target = set(tcgs.states) - string_to_set(node.left.value)
            T = target.copy()
            while True:
                new_T = T.union(
                    pre_image_exist(tcgs, T, constraints=node.left.time_constraints)
                )
                if new_T == T:
                    break
                T = new_T
            # Complement with respect to the full set of states
            node.value = str(set(tcgs.states) - T)

        elif verifyTCTL("EXIST", node.value) and verifyTCTL(
            "GLOBALLY", node.value
        ):  # EG φ
            # EG φ = greatest fixpoint: T = φ ∩ EX T
            target = string_to_set(node.left.value)
            T = set(tcgs.states)
            while True:
                new_T = target.intersection(
                    pre_image_exist(tcgs, T, constraints=node.left.time_constraints)
                )
                if new_T == T:
                    break
                T = new_T
            node.value = str(T)

        elif verifyTCTL("FORALL", node.value) and verifyTCTL(
            "GLOBALLY", node.value
        ):  # AG φ
            # AG φ = ¬EF(¬φ)
            target = set(tcgs.states) - string_to_set(node.left.value)
            T = target.copy()
            while True:
                new_T = T.union(
                    pre_image_exist(tcgs, T, constraints=node.left.time_constraints)
                )
                if new_T == T:
                    break
                T = new_T
            node.value = str(set(tcgs.states) - T)

        # RELEASE operator (universal version, AR)
        elif verifyTCTL("FORALL", node.value) and verifyTCTL(
            "RELEASE", node.value
        ):  # A(φ R ψ)
            # We assume the binary tree is: left -> φ, right -> ψ (or vice versa)
            # A(φ R ψ) requires: ψ ∧ (φ ∨ AX (φ R ψ))
            # We use the fixpoint characterization:
            holds_phi = string_to_set(node.left.value)
            holds_psi = string_to_set(node.right.value)
            ris = pre_release_A(tcgs, holds_phi, holds_psi)
            node.value = str(ris)

    # BINARY OPERATOR
    if node.left is not None and node.right is not None:
        if verifyTCTL("OR", node.value):  # φ ∨ θ, local
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.union(states2)
            node.value = str(ris)

        elif verifyTCTL("AND", node.value):  # φ ∧ θ, local
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            ris = states1.intersection(states2)
            node.value = str(ris)

        elif verifyTCTL("IMPLIES", node.value):  # φ -> θ  ≡ ¬φ ∨ θ, local
            states1 = string_to_set(node.left.value)
            states2 = string_to_set(node.right.value)
            not_states1 = set(tcgs.states) - states1
            ris = not_states1.union(states2)
            node.value = str(ris)

        elif verifyTCTL("EXIST", node.value) and verifyTCTL(
            "UNTIL", node.value
        ):  # E(φ U ψ)
            # Calcolo del least fixpoint: T = ψ ∪ (φ ∩ EX T)
            states_phi = string_to_set(node.left.value)
            states_psi = string_to_set(node.right.value)
            T = states_psi.copy()
            while True:
                new_T = T.union(
                    states_phi.intersection(
                        pre_image_exist(
                            tcgs, T, constraints=node.right.time_constraints
                        )
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.value = str(T)

        elif verifyTCTL("FORALL", node.value) and verifyTCTL(
            "UNTIL", node.value
        ):  # A(φ U ψ)
            # A(φ U ψ) = ¬E(¬ψ U (¬φ ∧ ¬ψ)) (formula duale)
            # Possiamo calcolarla tramite una trasformazione:
            not_states_phi = set(tcgs.states) - string_to_set(node.left.value)
            not_states_psi = set(tcgs.states) - string_to_set(node.right.value)
            # Calcoliamo E(not ψ U (not φ ∧ not ψ))
            T = not_states_psi.copy()
            while True:
                new_T = T.union(
                    (not_states_phi.intersection(not_states_psi)).intersection(
                        pre_image_exist(
                            tcgs.get_edges(),
                            T,
                            clock_constraints=tcgs.get_clock_constraints(),
                        )
                    )
                )
                if new_T == T:
                    break
                T = new_T
            # Complemento: A(φ U ψ) = ¬T
            node.value = str(set(tcgs.states) - T)

        # For the existential RELEASE operator (if needed) it can be defined dually,
        # e.g.: E(φ R ψ) = ¬A(¬φ U ¬ψ)
        elif verifyTCTL("EXIST", node.value) and verifyTCTL(
            "RELEASE", node.value
        ):  # E(φ R ψ)
            not_states_phi = set(tcgs.states) - string_to_set(node.left.value)
            not_states_psi = set(tcgs.states) - string_to_set(node.right.value)
            # Compute A(not φ U not ψ)
            T = not_states_psi.copy()
            while True:
                new_T = T.union(
                    not_states_phi.intersection(not_states_psi).intersection(
                        pre_image_all(tcgs.get_edges(), tcgs.states, T)
                    )
                )
                if new_T == T:
                    break
                T = new_T
            node.value = str(set(tcgs.states) - T)


def timed_model_checking(formula, filename):
    if not formula.strip():
        result = {"res": "Error: no formula specified", "initial_state": ""}
        return result

    # Parse the model
    tcgs = TimedCGS()
    tcgs.read_file(filename)
    # Parse the CTL formula
    ast = do_parsingTCTL(formula.strip())
    if ast is None:
        result = {
            "res": "Syntax error in formula or the atom doesn't exist",
            "initial_state": "",
        }
        return result
    # root = build_tree(tcgs, res_parsing)
    # if root is None:
    #    result = {'res': "Syntax error: the atom doesn't exist", 'initial_state': ''}
    #    return result

    # Execute model checking
    zone_graph = ZoneGraph(tcgs)  # instantiate and build zone graph.
    solve_tree(tcgs, zone_graph, ast)
    # Result: check whether the initial state satisfies the formula
    bool_res = tcgs.initial_state in ast.satisfying_states
    result = {
        "res": "Result set: " + str(ast.satisfying_states),
        "initial_state": "Initial state "
        + str(tcgs.initial_state)
        + ": "
        + str(bool_res),
    }
    return result
