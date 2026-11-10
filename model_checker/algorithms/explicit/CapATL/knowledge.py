"""Data structures for CapATL: pointed knowledge (`p_knowledge`, a state-knowledge
pair), its coalition form with actions (`p_knowledge_for_Y`), and formula tree nodes
(`Node_PK`)."""

import numpy as np


class p_knowledge_for_Y:
    """A state, each agent's capacity knowledge, and the joint action of coalition Y."""

    def __init__(self, state, knowledge, beta, agents, agents_tot):
        self.state = tuple(state) if isinstance(state, (list, np.ndarray)) else state
        self.knowledge = tuple(
            tuple(k) if isinstance(k, (list, set)) else k for k in knowledge
        )
        self.action = tuple(beta) if isinstance(beta, (list, np.ndarray)) else beta
        self.coalition = agents
        self.agents = (
            tuple(agents_tot) if isinstance(agents_tot, (list, set)) else agents_tot
        )

    def __repr__(self) -> str:
        return f"pkY({self.state}, {self.knowledge}, {self.action}, {self.coalition})"

    def __eq__(self, other):
        if isinstance(other, p_knowledge_for_Y):
            return (
                self.state == other.state
                and self.knowledge == other.knowledge
                and self.action == other.action
                and self.coalition == other.coalition
                and self.agents == other.agents
            )
        return False

    def __hash__(self):
        return hash(
            (self.state, self.knowledge, self.action, self.coalition, self.agents)
        )


class p_knowledge:
    """A state with each agent's capacity knowledge, the pair (Sigma, Delta)."""

    def __init__(self, state, knowledge, agents):
        self.state = tuple(state) if isinstance(state, (list, np.ndarray)) else state
        self.knowledge = tuple(
            tuple(k) if isinstance(k, (list, set)) else k for k in knowledge
        )
        self.agents = tuple(agents) if isinstance(agents, (list, set)) else agents

    def __repr__(self) -> str:
        return f"pk({self.state}, {self.knowledge})"

    def __eq__(self, other):
        if isinstance(other, p_knowledge):
            return (
                self.state == other.state
                and self.knowledge == other.knowledge
                and self.agents == other.agents
            )
        return False

    def __hash__(self):
        return hash((self.state, self.knowledge, self.agents))


class Node_PK:
    """Represents a node in the formula tree for CapATL."""

    def __init__(self, data):
        self.left = None
        self.right = None
        self.value = data
