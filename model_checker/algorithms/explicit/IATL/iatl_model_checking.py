from collections import defaultdict

import numpy as np
from binarytree import Node

from model_checker.parsers.formulas.IATL.iatl_ply_parser import (
    do_parsingIATL,
    verifyIATL,
)

from .util.process_input import (
    get_agents_from_coalition,
    get_edges,
    get_index_by_state_name,
    get_preorder,
    get_preorder_edges,
    read_file,
)


# returns the states where the proposition holds
def get_states_prop_holdsIATL(prop, prop_matrix, propositions):
    index = get_atom_index(prop, propositions)
    if index is None:
        return None
    return set(np.where(prop_matrix[:, int(index)] == 1)[0])


# converts a string into a set
def string_to_setIATL(string):
    if string == "set()":
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)


# returns whether the result of model checking is true or false in the initial state
def verify_initial_stateIATL(initial_state, string):
    return initial_state in string


# Given a graph entry G[i,j], it returns the list of available action from state i to state j
def build_list(action_string):
    return action_string.split(",")


# returns the state, given an index
def get_state_name_by_index(states_list, index):
    return states_list[index]


def get_state_label(index):
    return f"s{index}"


def calculate_subset_states_hat(stati, closures, subset_states):
    """
    Calcola l'insieme Y^ dato l'insieme S, le upward closure e l'insieme Y.

    Parameters:
    stati (set): L'insieme degli stati del modello
    closures (dict): Dizionario dove le chiavi sono gli elements di S e i valori sono le loro upward closure
    subset_states (set): Sottoinsieme di S

    Returns:
    set: L'insieme Y^
    """
    return {s for s in stati if closures[s].issubset(subset_states)}


def get_atom_index(element, atomic_propositions):
    return np.where(atomic_propositions == element)[0][0]


class IATLModelChecker:
    def __init__(self, model):
        self.graph = model
        self.edges = get_edges(self.graph["graph"], self.graph["states"])
        self.preorder_edges = get_preorder_edges(
            self.graph["preorder"], self.graph["states"]
        )
        self.upward_closure = get_preorder(
            self.preorder_edges, self.graph["states_counter"]
        )
        self.actions = self.graph["actions"]

    # function that builds a formula tree, used by the model checker
    # This function builds a formula tree, creating nodes for operators and atomic propositions
    # Eg: Input: !AXa, Tree Root: NOT operator, Left Child: AXa
    def build_tree(self, tpl):
        if isinstance(tpl, tuple):
            root = Node(tpl[0])
            if len(tpl) > 1:
                left_child = self.build_tree(tpl[1])
                if left_child is None:
                    return None
                root.left = left_child
                if len(tpl) > 2:
                    right_child = self.build_tree(tpl[2])
                    if right_child is None:
                        return None
                    root.right = right_child
        else:
            states_proposition = get_states_prop_holdsIATL(
                str(tpl), self.get_preorder_matrix(), self.get_atomic_propositions()
            )
            if states_proposition is None:
                return None
            else:
                stati = {
                    get_state_name_by_index(self.get_states(), element)
                    for element in states_proposition
                }
                root = Node(str(stati))
        return root

    def get_states(self):
        return self.graph["states"]

    def get_relations(self):
        return self.graph["graph"]

    def get_initial_state(self):
        return self.graph["initial_state"]

    def get_edges(self):
        return self.edges

    def get_preorder_edges(self):
        return self.preorder_edges

    def get_upward_closure(self):
        return self.upward_closure

    def get_atomic_propositions(self):
        return self.graph["atomic_propositions"]

    def get_actions(self):
        return self.actions

    def get_number_of_agents(self):
        return self.graph["number_of_agents"]

    def get_preorder_matrix(self):
        return self.graph["preorder"]

    # np.array states as input and returns a set of indices to identify them
    def convert_state_setIATL(self, states):
        return set(np.where(np.isin(self.get_states(), list(states)))[0])

    def pre_existsIATL(self, coalition, state_set, show_strategy):
        get_agents_from_coalition(coalition)
        state_set = self.convert_state_setIATL(state_set)  # returns a set of indexes

        # take states that have at least one transition to one of the states in the set
        self.get_inner_states_of_state_set(state_set)
        return set(), {}

    def get_inner_states_of_state_set(self, state_set):
        # take states that have at least one transition to one of the states in the set
        np.arange(self.graph["graph"].shape[0])
        col_indices = np.array(list(state_set)).astype(int)
        valid_positions = np.where(self.graph["graph"][:, col_indices] != "0")
        row_valid_indices = valid_positions[0]
        col_valid_indices = col_indices[valid_positions[1]]
        return {
            f"{i},{j}": build_list(self.graph["graph"][i, j])
            for i, j in zip(row_valid_indices, col_valid_indices)
        }

    def pre_forallIATL(self, a, b, c):
        return set(), {}

    def process_globally(self, node, pre_func, strategy, show_strategy):
        coalition = node.value[1:-2]
        states = string_to_setIATL(node.left.value)
        p = set(self.get_states())
        tmp_strat = defaultdict(list)
        t = states
        while p - t:  # p not in t
            p = t
            if show_strategy:
                # save the resulting set into strategy <- intersect them with strat.keys() <- take the states
                # indexes in t
                strategy = {
                    k: tmp_strat[k]
                    for k in (
                        tmp_strat.keys()
                        & [get_index_by_state_name(self.get_states(), a) for a in t]
                    )
                }
            t, tmp_strat = pre_func(coalition, p, show_strategy)
            t = t & states
        node.value = str(p)
        return strategy

    def process_eventually(self, node, pre_func, strategy, show_strategy):
        coalition = node.value[1:-2]
        states = string_to_setIATL(node.left.value)
        tmp_strat = defaultdict(list)
        p = set()
        t = states
        while t - p:  # t not in p
            p.update(t)
            if show_strategy:
                strategy.update(tmp_strat)
            t, tmp_strat = pre_func(coalition, p, show_strategy)
        node.value = str(p)

    def process_next(self, node, pre_func, show_strategy):
        coalition = node.value[1:-2]
        states = string_to_setIATL(node.left.value)
        ris, strategy = pre_func(coalition, states, show_strategy)
        node.value = str(ris)
        return strategy

    def process_until(self, node, pre_func, strategy, show_strategy):
        coalition = node.value[1:-2]
        states1 = string_to_setIATL(node.left.value)
        states2 = string_to_setIATL(node.right.value)
        p = set()
        tmp_strat = res_dict = defaultdict(list)
        t = states2
        while t - p:  # t not in p
            p.update(t)
            if show_strategy:
                # save the resulting set into res_dict <- intersect them with strat.keys() <- take the states
                # indexes in t
                res_dict = {
                    k: tmp_strat[k]
                    for k in (
                        tmp_strat.keys()
                        & [get_index_by_state_name(self.get_states(), a) for a in t]
                    )
                }
                strategy.update(res_dict)
            t, tmp_strat = pre_func(coalition, p, show_strategy)
            t = t & states1
        node.value = str(p)

    def process_release(self, node, pre_func, strategy, show_strategy):
        coalition = node.value[1:-2]
        states1 = string_to_setIATL(node.left.value)
        states2 = string_to_setIATL(node.right.value)
        p = set(self.get_states())
        t = states2
        tmp_strat = res_dict = defaultdict(list)
        while p - t:  # p not in t
            p & t
            if show_strategy:
                res_dict = {
                    k: tmp_strat[k]
                    for k in (
                        tmp_strat.keys()
                        & [get_index_by_state_name(self.get_states(), a) for a in t]
                    )
                }
                strategy.update(res_dict)
        t, tmp_strat = pre_func(coalition, p, show_strategy)
        t.update(states1)
        node.value = str(p)

    # function that solves the formula tree. The result is the model checking result.
    # It solves every node depending on the operator.
    def solve_tree(self, node, show_strategy):
        strategy = defaultdict(list)

        if node.left is not None:
            strategy = self.solve_tree(node.left, show_strategy)
        if node.right is not None:
            strategy = self.solve_tree(node.right, show_strategy)

        if node.right is None:  # UNARY OPERATORS: not, globally, next, eventually
            if verifyIATL("NOT", node.value):
                y = set(self.get_states()) - string_to_setIATL(node.left.value)
                ris = calculate_subset_states_hat(
                    set(self.get_states()), self.get_upward_closure(), y
                )
                node.value = str(ris)

            elif verifyIATL("ECOALITION", node.value) and verifyIATL(
                "GLOBALLY", node.value
            ):  # e.g. <1>Gφ
                strategy = self.process_globally(
                    node, self.pre_existsIATL, strategy, show_strategy
                )

            elif verifyIATL("ECOALITION", node.value) and verifyIATL(
                "NEXT", node.value
            ):  # e.g. <1>Xφ
                strategy = self.process_next(node, self.pre_existsIATL, show_strategy)

            elif verifyIATL("ECOALITION", node.value) and verifyIATL(
                "EVENTUALLY", node.value
            ):  # e.g. <1>Fφ
                self.process_eventually(
                    node, self.pre_existsIATL, strategy, show_strategy
                )

            elif verifyIATL("ACOALITION", node.value) and verifyIATL(
                "GLOBALLY", node.value
            ):  # e.g. [1]Gφ
                strategy = self.process_globally(
                    node, self.pre_forallIATL, strategy, show_strategy
                )

            elif verifyIATL("ACOALITION", node.value) and verifyIATL(
                "NEXT", node.value
            ):  # e.g. [1]Xφ
                strategy = self.process_next(node, self.pre_forallIATL, show_strategy)

            elif verifyIATL("ACOALITION", node.value) and verifyIATL(
                "EVENTUALLY", node.value
            ):  # e.g. [1]Fφ
                self.process_eventually(
                    node, self.pre_forallIATL, strategy, show_strategy
                )

        if (
            node.left is not None and node.right is not None
        ):  # BINARY OPERATORS: or, and, until, implies
            if verifyIATL("OR", node.value):  # e.g. φ || θ
                states1 = string_to_setIATL(node.left.value)
                states2 = string_to_setIATL(node.right.value)
                ris = states1.union(states2)
                node.value = str(ris)

            elif verifyIATL("ECOALITION", node.value) and verifyIATL(
                "UNTIL", node.value
            ):  # e.g. <1>φUθ
                self.process_until(node, strategy, self.pre_existsIATL, show_strategy)

            elif verifyIATL("ACOALITION", node.value) and verifyIATL(
                "UNTIL", node.value
            ):  # e.g. <1>φUθ
                self.process_until(node, strategy, self.pre_forallIATL, show_strategy)

            elif verifyIATL("ECOALITION", node.value) and verifyIATL(
                "RELEASE", node.value
            ):  # e.g. <1>φUθ
                self.process_release(node, strategy, self.pre_existsIATL, show_strategy)

            elif verifyIATL("ACOALITION", node.value) and verifyIATL(
                "RELEASE", node.value
            ):  # e.g. <1>φUθ
                self.process_release(node, strategy, self.pre_forallIATL, show_strategy)

            elif verifyIATL("AND", node.value):  # e.g. φ && θ
                states1 = string_to_setIATL(node.left.value)
                states2 = string_to_setIATL(node.right.value)
                ris = states1.intersection(states2)
                node.value = str(ris)

            elif verifyIATL("IMPLIES", node.value):  # e.g. φ -> θ
                states1 = string_to_setIATL(node.left.value)
                states2 = string_to_setIATL(node.right.value)
                not_states1 = set(self.get_states()).difference(states1)
                y = not_states1.union(states2)
                ris = calculate_subset_states_hat(
                    set(self.get_states()), self.get_upward_closure(), y
                )
                node.value = str(ris)
        return strategy


def verify_initial_state(init_state, string):
    return init_state in string


# does the parsing of the model, the formula, builds a tree, and then it returns the result of model checking
# function called by front_end_CS
def model_checking(formula, model_checker, show_strategy=False):
    if not formula.strip():
        result = {"res": "Error: formula not entered", "initial_state": ""}
        return result

    # formula parsing
    res_parsing = do_parsingIATL(formula, model_checker.get_number_of_agents())
    if res_parsing is None:
        result = {"res": "Syntax Error", "initial_state": ""}
        return result
    root = model_checker.build_tree(res_parsing)
    if root is None:
        result = {"res": "Syntax Error: the atom does not exist", "initial_state": ""}
        return result
    # model checking
    strategy = model_checker.solve_tree(root, show_strategy)

    # solution
    init_state = model_checker.get_initial_state()
    bool_res = verify_initial_state(init_state, root.value)
    res = str(root.value)
    cleaned_res = res.strip("{}").replace(" ", "")
    states = cleaned_res.split(",")
    result = {
        "States_Satisfying_Formula": res,
        "Tot_states": len(states),
        "Res_Initial_state": f"{init_state} : {bool_res}",
    }
    if show_strategy:
        result["Strategy"] = strategy
    return result


def process_modelCheckingIATL_model_from_file(filename, formula):
    data = read_file(filename)
    model_checker = IATLModelChecker(data)
    result = model_checking(formula, model_checker)
    return result
