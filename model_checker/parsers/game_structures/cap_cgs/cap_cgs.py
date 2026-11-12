"""Capability-based Concurrent Game Structure (CapCGS) parser.

Extends CGS with capacity assignments and action capacities; read by CapATL
only, so its names follow CapATL's reserved words.
"""

import numpy as np

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.syntax_patterns import (
    CAPATL_KNOWLEDGE_NAME_RE,
    CAPATL_RESERVED_WORDS,
)


class CapCGS(CGS):
    """A CapCGS model: a CGS plus the Capacities, Capacities_assignment and
    Actions_for_capacities sections."""

    RESERVED_WORDS = CAPATL_RESERVED_WORDS

    def validate_name(self, name: str, kind: str) -> None:
        """Also reject `kcap1`, `kcap42`: CapATL reads them as its knowledge
        operator, so no formula could name them."""
        super().validate_name(name, kind)
        if CAPATL_KNOWLEDGE_NAME_RE.fullmatch(name):
            raise ValueError(
                f"{kind} {name!r} spells the CapATL knowledge operator "
                f"({name}(...)), so no formula could name it."
            )

    def __init__(self):
        """Initialize an empty CapCGS; load data with read_file."""
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

    def _parse_lines(self, lines: list[str]) -> None:
        self._reset_state()
        self._parse_capacity_sections(lines)
        self._parse_common_sections(lines)
        self._parse_transitions(lines)

    # --- Private Parsing Methods - Capacity Sections ---

    def _parse_capacity_sections(self, lines):
        """Read the Capacities, Capacities_assignment and Actions_for_capacities
        sections."""
        current_section = None
        capacities_list = []

        capacity_section_headers = {
            "Capacities": "Capacities",
            "Capacities_assignment": "Capacities_assignment",
            "Actions_for_capacities": "Actions_for_capacities",
        }

        def process_capacities(line):
            values = line.split()
            for value in values:
                self.validate_name(value, kind="Capacity")
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

            if cgs_parser.is_blank_or_comment(line):
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
        """Read the plain CGS sections; transitions and capacities come later."""
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
        """Read the Transition section into the graph and the actions list."""
        rows_graph = cgs_parser.extract_transition_rows(lines)
        if not rows_graph:
            return

        cgs_parser._check_rectangular_rows(rows_graph, "Transition")
        actions = []
        for row in rows_graph:
            processed_row = cgs_parser.process_transition_row(row, actions)
            self.graph.append(processed_row)

        self.actions = list(set(actions))

    # --- Capacity Accessor Methods ---

    def get_capacities_assignment(self) -> list[list[str]]:
        """Each agent's capacities, as `[['1', 'cap1', 'cap2'], ['2', 'cap3']]`."""
        cap_ass = self.capacities_assignment
        result = []
        num_agents = self.get_number_of_agents()
        capacities_list = self.capacities_list

        for i in range(1, num_agents + 1):
            interm = [str(i)]
            cap_ag = cap_ass[i - 1]
            for count, value in enumerate(cap_ag):
                if value == "1":
                    interm.append(capacities_list[count])
            result.append(interm)

        return result

    @property
    def capacities_list(self) -> list[str]:
        """The capacity names of the Capacities section."""
        return self.capacities.tolist() if len(self.capacities) > 0 else []
