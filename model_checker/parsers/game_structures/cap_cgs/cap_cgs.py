"""Capability-based Concurrent Game Structure (capCGS) parser.

Extends CGS with capacity assignments and action capacities; used by CapATL
and other capacity-based logics.
"""

from typing import List

import numpy as np

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS


class capCGS(CGS):
    """Parser and in-memory representation for a capCGS model file.

    Adds capacity sections (Capacities, Capacities_assignment,
    Actions_for_capacities) on top of the base CGS. Use read_file(path) to load
    a file; then use get_capacities(), get_capacities_assignment(), and
    get_action_capacities() for capacity data.
    """

    def __init__(self):
        """Initialize an empty capCGS; load data with read_file or read_from_model_object."""
        super().__init__()
        self.capacities_assignment = []
        self.action_capacities = []
        self.capacities = np.array([])

    def _reset_state(self):
        """Clear base CGS state and cap-specific fields."""
        super()._reset_state()
        self.capacities_assignment = []
        self.action_capacities = []
        self.capacities = np.array([])

    def read_file(self, filename: str) -> None:
        """Read and parse a capCGS model file from disk.

        Args:
            filename: Path to the capCGS model file.

        Raises:
            ValueError: If section structure or dimensions are invalid.
        """
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()

        self._reset_state()
        self._parse_capacity_sections(lines)
        self._parse_common_sections(lines)
        self._parse_transitions(lines)

    # --- Private Parsing Methods - Capacity Sections ---

    def _parse_capacity_sections(self, lines):
        """Parse capacity-specific sections: Capacities, Capacities_assignment, Actions_for_capacities.

        Args:
            lines: List of file lines (list of str).
        """
        current_section = None
        capacities_list = []

        capacity_section_headers = {
            "Capacities": "Capacities",
            "Capacities_assignment": "Capacities_assignment",
            "Actions_for_capacities": "Actions_for_capacities",
        }

        def process_capacities(line):
            if line:

                values = line.split()
                if values:
                    capacities_list.extend(values)

        def process_capacities_assignment(line):
            if line:
                values = line.split()
                if values:
                    self.capacities_assignment.append(values)

        def process_actions_for_capacities(line):
            if line:
                values = line.split()
                if values:
                    self.action_capacities.append(values)

        section_processors = {
            "Capacities": process_capacities,
            "Capacities_assignment": process_capacities_assignment,
            "Actions_for_capacities": process_actions_for_capacities,
        }

        for line in lines:
            line = line.strip()

            if not line or line.startswith("#") or line.startswith("//"):
                continue

            if line in capacity_section_headers:
                current_section = capacity_section_headers[line]
                if current_section == "Capacities":
                    capacities_list = []
            elif line in cgs_parser.SECTION_HEADERS:
                current_section = None
            elif current_section and current_section in section_processors:
                section_processors[current_section](line)

        if self.capacities_assignment:
            cgs_parser._check_rectangular_rows(
                self.capacities_assignment, "Capacities_assignment"
            )
        if capacities_list:
            self.capacities = np.array(capacities_list)

    # --- Private Parsing Methods - Common Sections ---

    def _parse_common_sections(self, lines):
        """Parse common CGS sections (states, labelling, agents, etc.), skipping transitions and capacity sections.

        Args:
            lines: List of file lines (list of str).
        """
        sections_to_skip = {
            "Transition",  # Skip transitions - will be parsed separately
            "Capacities",
            "Capacities_assignment",
            "Actions_for_capacities",
        }
        filtered_lines = cgs_parser.filter_lines_for_common_sections(
            lines, sections_to_skip
        )
        cgs_parser.parse_cgs_file(filtered_lines, self)

    # --- Private Parsing Methods - Transitions ---

    def _parse_transitions(self, lines):
        """Parse the Transition section and fill the graph and actions list.

        Args:
            lines: List of file lines (list of str).
        """
        rows_graph = cgs_parser.extract_transition_rows(lines)
        if not rows_graph:
            return

        cgs_parser._check_rectangular_rows(rows_graph, "Transition")
        actions = []
        for row in rows_graph:
            processed_row = cgs_parser.process_transition_row(row, actions)
            self.graph.append(processed_row)

        self.actions = list(set(actions))

    def read_from_model_object(self, model):
        """Initialize from a model object (alternative to read_file)."""
        super().read_from_model_object(model)
        self.capacities_assignment = model.capacities_assignment
        self.action_capacities = model.action_capacities
        self.capacities = np.array(model.capacities)

    # --- Capacity Accessor Methods ---

    def get_capacities_assignment(self) -> List[List[str]]:
        """Return capacities assignment formatted by agent.

        Returns:
            List of lists; each inner list is [agent_id, cap1, cap2, ...]
            for that agent's assigned capacities (e.g. [['1', 'cap1', 'cap2'], ['2', 'cap3']]).
        """
        cap_ass = self.capacities_assignment
        result = []
        num_agents = self.get_number_of_agents()
        capacities_list = self.get_capacities()

        for i in range(1, num_agents + 1):
            interm = [str(i)]
            cap_ag = cap_ass[i - 1]
            for count, value in enumerate(cap_ag):
                if value == "1":
                    interm.append(capacities_list[count])
            result.append(interm)

        return result

    def get_action_capacities(self) -> List[List[str]]:
        """Return the action-capacity mapping (one list per row from Actions_for_capacities).

        Returns:
            List of lists; each inner list is one row from the Actions_for_capacities section.
        """
        return self.action_capacities

    def get_capacities(self) -> List[str]:
        """Return the list of capacity names from the Capacities section.

        Returns:
            List of capacity name strings.
        """
        return self.capacities.tolist() if len(self.capacities) > 0 else []
