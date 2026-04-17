"""CGS (Concurrent Game Structure) model parser.

Main CGS class for loading and querying CGS model files; heavy work is done
in cgs_parser, cgs_validation, cgs_actions, and cgs_utils.
"""

from typing import Optional

import numpy as np

from model_checker.parsers.game_structures.cgs import (
    cgs_actions,
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
        self.unknown_transition_matrix = getattr(model, "unknown_transition_matrix", [])
        self.invalidate_caches()
        self._cached_edges = None
        self._cached_graph_id = None
        self._cached_reverse_index = None
        self._cached_reverse_index_graph_id = None

    def _get_num_states(self):
        """Number of states (0 if empty). Used internally for validation."""
        return cgs_validation.get_num_states(self.states)

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

    # --- State Accessors ---

    def get_states(self):
        """Return the array of state names."""
        return self.states

    def get_initial_state(self):
        """Return the name of the initial state."""
        return self.initial_state

    def get_index_by_state_name(self, state):
        """Return the index of the state with the given name. Raises IndexError if not found."""
        state_str = str(state)
        if state_str in self.state_to_index:
            return self.state_to_index[state_str]
        raise IndexError(f"State '{state}' not found in model")

    def get_state_name_by_index(self, index):
        """Return the state name at the given index. Raises IndexError if index is out of range."""
        return cgs_utils.get_state_name_by_index(self.states, index)

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

    def get_agents_from_coalition(self, coalition):
        """Parse a comma-separated coalition string (e.g. "1,2,3") into a set of agent ids."""
        return cgs_actions.get_agents_from_coalition(coalition)

    # --- Action Methods ---

    def get_actions(self, agents):
        """Return a dict of agent name -> list of actions for the given 1-based agent numbers.

        Actions are read from the transition matrix as per-agent action tokens (strings).

        Supported cell formats in the Transition matrix:
        - Compact character format (recommended, used in examples):
          each non-zero cell is a string like "AC,AD". Joint choices are
          comma-separated; within each joint, the first character is the action
          of agent 1, the second character is the action of agent 2, and so on.
        - Explicit token format (optional): each non-zero cell uses "|" between
          per-agent tokens, for example "IDLE|MOVE,ATTACK|BLOCK" for 2 agents.

        The helper always decodes cells into per-agent tokens; both "I" and
        "IDLE" are accepted as idle actions and normalized internally.

        Raises ValueError if any agent number is out of range.
        """
        num_agents = self.get_number_of_agents()
        cgs_actions.validate_agent_numbers(agents, num_agents)
        return cgs_actions.extract_actions_for_agents(self.graph, agents)

    def get_coalition_action(self, actions, agents):
        """Return the coalition’s action strings for the given set of actions and agent list."""
        formatted_agents = cgs_actions.format_agents(agents)
        return cgs_actions.get_coalition_actions(
            set(actions), formatted_agents, self.get_number_of_agents()
        )

    def get_base_action(self, action, agents):
        """Same as get_coalition_action for a single action; returns the one resulting string."""
        return self.get_coalition_action({action}, agents).pop()

    def get_opponent_moves(self, actions, agents):
        """Return the moves that are not from the given coalition (opponents’ part of the action)."""
        formatted_agents = cgs_actions.format_agents(agents)
        return cgs_actions.get_opponent_actions(
            set(actions), formatted_agents, self.get_number_of_agents()
        )

    def build_action_list(self, action_string):
        """Turn an action string (e.g. with '*' or commas) into a list of action strings; result is cached."""
        if action_string in self._action_list_cache:
            return self._action_list_cache[action_string]
        result = cgs_utils.build_action_list(action_string, self.get_number_of_agents())
        self._action_list_cache[action_string] = result
        return result

    def translate_action_and_state_to_key(self, action_string, state):
        """Build a single key string from an action string and a state name."""
        return cgs_utils.translate_action_and_state_to_key(action_string, state)

    # --- Atomic Propositions and Labelling ---

    def get_atomic_prop(self):
        """Return the array of atomic proposition names."""
        return self.atomic_propositions

    def get_atom_index(self, element):
        """Return the index of the given atomic proposition, or None if it is not in the model."""
        return cgs_utils.get_atom_index(self.atomic_propositions, element)

    def get_matrix_proposition(self):
        """Return the labelling matrix (which state has which propositions)."""
        return self.matrix_prop

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

    @property
    def transition_matrix(self):
        """The transition matrix (graph) of the model."""
        return self.graph

    # --- NatATL-Specific Methods ---

    def get_label(self, index):
        """Return the NatATL-style label for a state index (e.g. s0, s1)."""
        return f"s{index}"

    def create_label_matrix(self, graph):
        """Build a label matrix from the given graph for NatATL (labels like s0, s1; non-string cells become None)."""
        return [
            [
                self.get_label(i) if isinstance(elem, str) and elem != "*" else None
                for j, elem in enumerate(row)
            ]
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
