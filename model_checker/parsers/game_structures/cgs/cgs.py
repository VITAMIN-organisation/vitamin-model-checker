"""CGS (Concurrent Game Structure) model parser.

Main CGS class for loading and querying CGS model files; heavy work is done
in cgs_parser, cgs_validation, cgs_actions, and cgs_utils.
"""

from typing import Optional

import numpy as np

from model_checker.parsers.game_structures.cgs import (
    cgs_parser,
    cgs_utils,
    cgs_validation,
)


class CGS:
    """Parser and in-memory representation for a CGS model file.

    Use read_file(path) to load a file, or read_from_model_object(model) to
    build from an existing model. The rest of the API gives access to states,
    actions, graph, and labelling; validation lives in cgs_validation.
    """

    # --- Initialization and File Reading ---

    def __init__(self):
        """Create an empty CGS; load data with read_file or read_from_model_object."""
        self._reset_state()

    def _reset_state(self):
        """Clear all model data and caches (used by __init__ and read_file)."""
        self.graph = []
        self.unknown_transition_matrix = []
        self.states = np.array([])
        self.atomic_propositions = np.array([])
        self.matrix_prop = []
        self.initial_state = ""
        self.number_of_agents: Optional[int] = None
        self.agent_labels: list = []
        self.actions = []
        self._all_states_set = None
        self._state_to_index = None
        self._action_list_cache = {}
        self._cached_edges = None
        self._cached_graph_id = None
        self._cached_reverse_index = None
        self._cached_reverse_index_graph_id = None

    def read_file(self, filename):
        """Load and parse a CGS model from a file path. Replaces any existing data."""
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()
        self._reset_state()
        cgs_parser.parse_cgs_file(lines, self)

    def read_from_model_object(self, model):
        """Fill this CGS from an existing model object instead of reading a file."""
        self.graph = model.transition_matrix
        self.states = np.array(model.state_names)
        self.atomic_propositions = np.array(model.propositions)
        self.matrix_prop = model.labelling_function
        self.initial_state = model.initial_state
        na = getattr(model, "number_of_agents", None)
        if na is None:
            self.number_of_agents = None
        elif isinstance(na, int):
            self.number_of_agents = na
        else:
            self.number_of_agents = int(str(na).strip()) if str(na).strip() else None
        self.actions = model.actions
        labels = getattr(model, "agent_labels", None)
        self.agent_labels = list(labels) if labels else []
        self.unknown_transition_matrix = getattr(model, "unknown_transition_matrix", [])
        self.invalidate_caches()
        self._cached_edges = None
        self._cached_graph_id = None
        self._cached_reverse_index = None
        self._cached_reverse_index_graph_id = None

    # --- Cached Properties for Performance ---

    @property
    def all_states_set(self):
        """Set of all state names; computed once and then cached."""
        if self._all_states_set is None:
            self._all_states_set = {str(s) for s in self.states}
        return self._all_states_set

    @property
    def state_to_index(self):
        """Map from state name (str) to its index; built once and cached."""
        if self._state_to_index is None:
            self._state_to_index = {
                str(name): idx for idx, name in enumerate(self.states)
            }
        return self._state_to_index

    def invalidate_caches(self):
        """Clear caches; call this after you change states or graph so lookups stay correct."""
        self._all_states_set = None
        self._state_to_index = None
        self._action_list_cache = {}

    def get_index_by_state_name(self, state):
        """Return the index of the state with the given name. Raises IndexError if not found."""
        state_str = str(state)
        if state_str in self.state_to_index:
            return self.state_to_index[state_str]
        raise IndexError(f"State '{state}' not found in model")

    def get_state_name_by_index(self, index):
        """Return the state name at the given index. Raises IndexError if index is out of range."""
        if index < 0:
            raise IndexError(f"State index must be non-negative, got {index}")
        if index >= len(self.states):
            raise IndexError(
                f"State index {index} is out of bounds for {len(self.states)} states"
            )
        return self.states[index]

    # --- Agent and Coalition Methods ---

    def get_number_of_agents(self):
        """Return the number of agents as an int. Raises ValueError if missing or not set."""
        if self.number_of_agents is None:
            raise ValueError(
                "Number_of_agents is missing or empty in the model file. "
                "Please ensure the file contains a 'Number_of_agents' section "
                "followed by a valid integer value."
            )
        return self.number_of_agents

    def get_agent_labels(self):
        """Return display labels for agents 1..n; defaults to '1', '2', ... when omitted."""
        n = self.get_number_of_agents()
        if self.agent_labels:
            return list(self.agent_labels)
        return cgs_utils.default_agent_labels(n)

    def build_action_list(self, action_string):
        """Turn an action string (e.g. with '*' or commas) into a list of action strings; result is cached."""
        if action_string in self._action_list_cache:
            return self._action_list_cache[action_string]
        result = cgs_utils.build_action_list(action_string, self.get_number_of_agents())
        self._action_list_cache[action_string] = result
        return result

    # --- Graph and Edge Methods ---

    def get_edges(self):
        """Return the list of (source_state, target_state) edges; result is cached until the graph changes."""
        current_graph_id = id(self.graph)
        if self._cached_edges is None or self._cached_graph_id != current_graph_id:
            self._cached_edges = cgs_utils.get_edges(self.graph, self.states)
            self._cached_graph_id = current_graph_id
            self._cached_reverse_index = None
            self._cached_reverse_index_graph_id = None
        return self._cached_edges

    def get_reverse_index(self):
        """Return a dict target_state -> set of source states for pre-image; cached until the graph changes."""
        current_graph_id = id(self.graph)
        if (
            self._cached_reverse_index is None
            or self._cached_reverse_index_graph_id != current_graph_id
        ):
            edges = self.get_edges()
            self._cached_reverse_index = cgs_utils.build_reverse_index(edges)
            self._cached_reverse_index_graph_id = current_graph_id
        return self._cached_reverse_index

    def create_label_matrix(self, graph):
        """Build a label matrix from the given graph for NatATL (labels like s0, s1; non-string cells become None)."""
        return [
            [f"s{i}" if isinstance(elem, str) and elem != "*" else None for elem in row]
            for i, row in enumerate(graph)
        ]

    # --- Validation ---

    def validate_model_structure(self):
        """Check that states, agents, initial state, transition matrix, and labelling are consistent.

        Raises ValueError with a list of issues if anything is wrong.
        """
        errors = cgs_validation.collect_model_structure_errors(self)
        if errors:
            raise ValueError(
                "Model structure validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
