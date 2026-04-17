"""
Knowledge structures for CapATL model checker.

This module defines data structures for representing epistemic states in CapATL:
- Pointed knowledge (state-knowledge pairs)
- Coalition knowledge with actions
- Formula tree nodes

These structures are essential for knowledge-based reasoning about agent capacities.
"""

import numpy as np


class p_knowledge_for_Y:
    """Represents a state-knowledge-action tuple for a specific coalition Y.

    Attributes:
        state: The current state name or tuple.
        knowledge: A tuple of capacity sets for each agent.
        action: The joint action performed by coalition Y.
        coalition: The coalition string identifier.
        agents: The set of all agents in the model.
    """

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

    def not_in(self, ens: list) -> bool:
        """Check if this element is already present in the given list."""
        for elem in ens:
            if (
                elem.state == self.state
                and elem.knowledge == self.knowledge
                and elem.coalition == self.coalition
                and elem.action == self.action
            ):
                return False
        return True

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
    """Represents a state-knowledge pair (Sigma, Delta).

    Attributes:
        state: The current state name or tuple.
        knowledge: A tuple of capacity sets for each agent.
        agents: The set of all agents in the model.
    """

    def __init__(self, state, knowledge, agents):
        self.state = tuple(state) if isinstance(state, (list, np.ndarray)) else state
        self.knowledge = tuple(
            tuple(k) if isinstance(k, (list, set)) else k for k in knowledge
        )
        self.agents = tuple(agents) if isinstance(agents, (list, set)) else agents

    def __repr__(self) -> str:
        return f"pk({self.state}, {self.knowledge})"

    def not_in(self, ens: list) -> bool:
        """Check if this element is already present in the given list."""
        for elem in ens:
            if elem.state == self.state and elem.knowledge == self.knowledge:
                return False
        return True

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
