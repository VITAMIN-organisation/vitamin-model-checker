"""Node class for NatATL Recall execution traces and basic tree operations."""

from model_checker.parsers.game_structures.cgs import CGS


class Node:
    """Recall tree node. ``state`` is the pruned-model name; ``old_state`` is the CGS location."""

    def __init__(
        self,
        name: str,
        cgs: CGS,
        action: str | None = None,
        predecessors: list[str] | None = None,
    ):
        self.cgs = cgs
        self.state = str(name)
        self.action = action
        self.children: list[Node] = []
        self.predecessors = (
            [str(p) for p in predecessors] if predecessors is not None else []
        )
        self.label_row = self.get_label_row_list(cgs.states, cgs.matrix_prop)
        self.actions: list[str] = []
        self.old_state = name
        self.pruned = False

    def add_child(self, child: "Node", action: str | None = None) -> None:
        """Add a child node with an optional action label."""
        self.children.append(child)
        if action:
            self.actions.append(action)

    def __repr__(self, level: int = 0) -> str:
        """Return indented representation for debugging."""
        ret = "\t" * level + repr(self.state)
        if self.action:
            ret += f" ({self.action})"
        ret += "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret

    def __str__(self, level: int = 0) -> str:
        """Return detailed string representation with all attributes."""
        ret = (
            " " * level
            + f"Name: {self.state}, Original: {self.old_state}, "
            + f"Action: {self.action}, Predecessors: {self.predecessors}, "
            + f"Labels: {self.label_row}, Pruned: {self.pruned}\n"
        )
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

    def get_label_row_list(
        self, states: list[str], label_matrix: list[list]
    ) -> list | None:
        """Get proposition values for this state from the label matrix."""
        for i, state in enumerate(states):
            if self.state == state:
                return label_matrix[i]
        return None


def rename_nodes(tree: Node) -> None:
    """After pruning, rename children to s1, s2, ... (root stays s0)."""

    def rename(node: Node, counter: int) -> int:
        for child in node.children:
            child.state = f"s{counter}"
            counter += 1
            counter = rename(child, counter)
        return counter

    rename(tree, 1)


def get_states_from_tree(root: Node) -> list[str]:
    """Unique state names in DFS order."""
    states: list[str] = []

    def traverse(node: Node) -> None:
        if node.state not in states:
            states.append(node.state)
        for child in node.children:
            traverse(child)

    traverse(root)
    return states


def reset_pruned_flag(node: Node) -> None:
    """Clear ``pruned`` on all nodes (between agent pruning passes)."""
    node.pruned = False
    for child in node.children:
        reset_pruned_flag(child)


def are_all_nodes_pruned(tree: Node) -> bool:
    """Whether every node has ``pruned=True``."""
    if tree.pruned is False:
        return False
    for child in tree.children:
        if not are_all_nodes_pruned(child):
            return False
    return True
