from binarytree import Node
from model_checker.parsers.formulas.ICTL.ictl_ply_parser import do_parsingICTL, verifyICTL

from .util.process_input import *


# returns the states where the proposition holds
def get_states_prop_holds(prop, prop_matrix, propositions):
    stati = set()
    index = get_atom_index(prop, propositions)
    if index is None:
        return None
    for state, source in enumerate(prop_matrix):
        if source[int(index)] == 1:
            stati.add(state)
    return stati


# converts a string into a set
def string_to_set(string):
    if string == "set()":
        return set()
    set_list = string.strip("{}").split(", ")
    new_string = "{" + ", ".join(set_list) + "}"
    return eval(new_string)


# It returns the states predecessors of those held in input
def pre_image_exist(transitions, list_holds_p):
    pre_list = set()
    pre_list.update({s for s, t in transitions if t in list_holds_p})
    return pre_list


def pre_image_all(transitions, list_holds_p):
    pre_list = set()
    for state in list(list_holds_p):
        predecessors = {s for s, t in transitions if t == state}
        for predecessor in predecessors:
            successor_states = {t for s, t in transitions if s == predecessor}
            if successor_states.issubset(list_holds_p):
                pre_list.add(predecessor)
    return pre_list


class ICTL_Model_Checker:
    def __init__(self, model):
        self.data = model
        self.edges = get_edges(self.data["graph"], self.data["states"])
        self.preorder_edges = get_preorder_edges(
            self.data["graph"], self.data["states"]
        )
        self.upward_closure = get_preorder(
            self.preorder_edges, self.data["states_counter"]
        )

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
            states_proposition = get_states_prop_holds(
                str(tpl), self.data["matrix_prop"], self.data["atomic_propositions"]
            )
            if states_proposition is None:
                return None
            else:
                stati = {
                    get_state_name_by_index(self.data["states"], element)
                    for element in states_proposition
                }
                root = Node(str(stati))
        return root

    def get_states(self):
        return self.data["states"]

    def get_relations(self):
        return self.data["graph"]

    def get_initial_state(self):
        return self.data["initial_state"]

    def get_edges(self):
        return self.edges

    def get_preorder_edges(self):
        return self.preorder_edges

    def get_upward_closure(self):
        return self.upward_closure

    # This function solves formula tree returning a result for model checking. It analyzes tree recursively,
    # solving nodes depending on the associated operator. Eg: Same build tree formula: !AXa -> this function starts to
    # solve AXa node as first, and then applies NOT at the result. To solve AXa node, it uses pre-image function to
    # define the states set where a proposition is satisfied. The result will be assigned to AXa node. At the end,
    # the algorithm applies NOT operator at the result for AXa. To do so, it computes the complementary states set for
    # those that satisfy AXa. The final result is stored in NOT operator root.
    def solve_tree(self, node):
        if node.left is not None:
            
            
            self.solve_tree(node.left)

        if node.right is not None:
            
            self.solve_tree(node.right)

        if node.right is None:  # UNARY OPERATORS: not, globally, next, eventually
            if verifyICTL("NOT", node.value):  # e.g. ¬φ
                y = set(self.get_states()) - string_to_set(node.left.value)
                ris = calculate_subset_states_hat(
                    set(self.get_states()), self.get_upward_closure(), y
                )
                node.value = str(ris)

            elif verifyICTL("FORALL", node.value) and verifyICTL(
                "NEXT", node.value
            ):  # e.g. EXφ
                states_sat = string_to_set(node.left.value)
                negated_states = set(self.get_states()) - states_sat
                ris = pre_image_all(self.get_edges(), negated_states)
                complement = set(self.get_states()) - ris
                node.value = str(complement)

            elif verifyICTL("EXIST", node.value) and verifyICTL("NEXT", node.value):
                states_sat = string_to_set(node.left.value)
                ris = pre_image_exist(self.get_edges(), states_sat)
                node.value = str(ris)

            elif verifyICTL("EXIST", node.value) and verifyICTL(
                "GLOBALLY", node.value
            ):  # e.g. EGφ
                states_sat = string_to_set(node.left.value)
                p = set(self.get_states())
                t = states_sat
                while p - t:  # p not in t
                    p = t
                    t = pre_image_exist(self.get_edges(), p) & states_sat
                node.value = str(p)

            elif verifyICTL("FORALL", node.value) and verifyICTL(
                "GLOBALLY", node.value
            ):
                states_sat = string_to_set(node.left.value)
                compl_states = set(self.get_states()) - states_sat
                p = set()
                t = compl_states
                while t - p:  # t not in p
                    p.update(t)
                    t = pre_image_all(self.get_edges(), p)
                out = set(self.get_states()) - p
                node.value = str(out)

            elif verifyICTL("EXIST", node.value) and verifyICTL(
                "EVENTUALLY", node.value
            ):  # trueUϕ.
                states_sat = string_to_set(node.left.value)
                p = set()
                t = states_sat
                while t - p:  # t not in p
                    p.update(t)
                    t = pre_image_exist(self.get_edges(), p)
                node.value = str(p)

            elif verifyICTL("FORALL", node.value) and verifyICTL(
                "EVENTUALLY", node.value
            ):  # not (EG(not p))
                states_sat = string_to_set(node.left.value)
                compl_states = set(self.get_states()) - states_sat
                p = set(self.get_states())
                t = compl_states
                while p - t:  # p not in t
                    p = t
                    t = pre_image_all(self.get_edges(), p) & compl_states
                ris = set(self.get_states()) - p
                node.value = str(ris)

        if (
            node.left is not None and node.right is not None
        ):  # BINARY OPERATORS: or, and, until, implies
            if verifyICTL("OR", node.value):  # e.g. φ || θ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                ris = states1.union(states2)
                node.value = str(ris)

            elif verifyICTL("AND", node.value):  # e.g. φ && θ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                ris = states1.intersection(states2)
                node.value = str(ris)

            elif verifyICTL("EXIST", node.value) and verifyICTL(
                "UNTIL", node.value
            ):  # e.g. AφUθ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                p = set()
                t = states2
                while t - p:  # t not in p
                    p.update(t)
                    t = pre_image_exist(self.get_edges(), p) & states1
                node.value = str(p)

            elif verifyICTL("FORALL", node.value) and verifyICTL(
                "UNTIL", node.value
            ):  # e.g. AφUθ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                p = set()
                t = states2
                while t - p:  # t not in p
                    p.update(t)
                    t = pre_image_all(self.get_edges(), p) & states1
                node.value = str(p)

            elif verifyICTL("EXIST", node.value) and verifyICTL(
                "RELEASE", node.value
            ):  # e.g. AφUθ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                p = set(self.get_states())
                t = states2
                while p - t:  # p not in t
                    p & t
                    t.update(pre_image_exist(self.get_edges(), p), states1)
                node.value = str(p)

            elif verifyICTL("FORALL", node.value) and verifyICTL(
                "RELEASE", node.value
            ):  # e.g. AφUθ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                p = set(self.get_states())
                t = states2
                while p - t:  # p not in t
                    p & t
                    t.update(pre_image_all(self.get_edges(), p), states1)
                node.value = str(p)

            elif verifyICTL("IMPLIES", node.value):  # e.g. φ -> θ
                states1 = string_to_set(node.left.value)
                states2 = string_to_set(node.right.value)
                not_states1 = set(self.get_states()).difference(states1)
                y = not_states1.union(states2)
                ris = calculate_subset_states_hat(
                    set(self.get_states()), self.get_upward_closure(), y
                )
                node.value = str(ris)


# returns whether the result of model checking is true or false in the initial state
def verify_initial_state(init_state, string):
    return init_state in string


# does the parsing of the model, the formula, builds a tree, and then it returns the result of model checking
# function called by front_end_CS
def model_checking(formula, model_checker):
    if not formula.strip():
        result = {"res": "Error: formula not entered", "initial_state": ""}
        return result

    # formula parsing
    
    res_parsing = do_parsingICTL(formula)
    
    if res_parsing is None:
        result = {"res": "Syntax Error", "initial_state": ""}
        return result
    root = model_checker.build_tree(res_parsing)
    if root is None:
        result = {"res": "Syntax Error: the atom does not exist", "initial_state": ""}
        return result
    
    # model checking
    model_checker.solve_tree(root)

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
    return result


def process_modelCheckingICTL_model_from_file(filename, formula):
    data = read_file(filename)
    
    model_checker = ICTL_Model_Checker(data)
    result = model_checking(formula, model_checker)
    
    return result


def process_modelCheckingICTL_model_generated(states_row, states_col, formula):
    data = generate_experiment_model(states_row, states_col)
    
    model_checker = ICTL_Model_Checker(data)
    result = model_checking(formula, model_checker)
    
    return result


def do_test_process_modelCheckingICTL_model_generated(formula):
    i = 240
    with open(f"results{i}x{i}.txt", "a") as f:
        
        f.write(f"Matrix {i} x {i}, Tot states:{i * i}\n")
        for execs in range(10):
            
            f.write(f"exec:{execs}\n")
            t0 = time.time()
            data = generate_experiment_model(i, i)
            tot_num_rel = np.count_nonzero(data["graph"] != "0")
            t1 = time.time()
            
            
            f.write(f"Relations:{tot_num_rel}\n")
            f.write(f"Generation_Time:{t1 - t0}\n")
            t2 = time.time()
            
            model_checker = ICTL_Model_Checker(data)
            t3 = time.time()
            
            f.write(f"Processing_preorder_time:{t3 - t2}\n")
            
            result = model_checking(formula, model_checker)
            t4 = time.time()
            
            f.write(f"MC_Time:{t4 - t3}\n")
            
            
            
        f.close()


def do_test_process_modelCheckingICTL_3k_model_generated():
    n = [200]
    with open(f"results_k_model.txt", "a") as f:
        f.write(f"n°agents,n°states,T_MC (sec)\n")
        for i in n:
            formula = f"{' & '.join(f'p{k}' for k in range(i))} -> (EF an0 & (an{i - 1} -> know) & (know -> an{i - 1}))"
            
            data = generate_3n_model(i)
            
            tot_states_n = data["states_counter"]
            
            model_checker = ICTL_Model_Checker(data)
            
            t_execs = 0
            for execs in range(10):
                
                t1 = time.time()
                model_checking(formula, model_checker)
                t_execs += time.time() - t1
            t_execs /= 10
            f.write(f"{i},{tot_states_n},{t_execs}\n")
    f.close()
