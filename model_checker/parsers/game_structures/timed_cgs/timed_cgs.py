import re
from enum import Enum

from model_checker.models.model_factory import CostCGS


class TimedCGS(CostCGS):
    def __init__(self):
        super().__init__()
        self.clock_constraints_dict = {}
        self.clocks_dict = {}

    def read_file(self, filename):
        """
        Parses the definition file for the CGS with real-time constraints.
        First the file is parsed ignoring every timed section.
        Then, we parse the timed aspects.
        """
        with open(filename, "r") as f:
            lines = f.readlines()

        timed_sections = {"Clocks", "Clock_constraints", "Invariants"}
        base_sections = {
            "Transition",
            "Transition_With_Costs",
            "Name_State",
            "Initial_State",
            "Atomic_propositions",
            "Labelling",
            "Number_of_agents",
            "Costs_for_actions",
            "Costs_for_actions_split",
        }
        filtered_lines: list[str] = []
        skip_timed_section = False
        for line in lines:
            stripped = line.strip()
            if stripped in timed_sections:
                skip_timed_section = True
                continue
            if skip_timed_section and stripped in base_sections:
                skip_timed_section = False
            if not skip_timed_section:
                filtered_lines.append(line)

        self._reset_state()
        from model_checker.parsers.game_structures.cost_cgs import (
            cost_cgs_parser,
        )

        cost_cgs_parser.parse_cost_sections(filtered_lines, self)
        cost_cgs_parser.parse_common_sections(filtered_lines, self)
        cost_cgs_parser.parse_transitions(filtered_lines, self)

        current_section = Sections.UNKNOWN
        # Initialize 2d array to hold clock constraints.
        self.clock_constraint_struct = [
            [""] * len(self.states) for _ in range(len(self.states))
        ]
        self.invariants_arr = [[] for _ in range(len(self.states))]

        row_index = 0
        for line in lines:
            line = line.strip()
            if row_index >= len(self.states):
                row_index = 0
            # Section header
            if line == "Clocks":
                current_section = Sections.CLOCKS
            elif line == "Clock_constraints":
                current_section = Sections.CLOCK_CONSTRAINTS
            elif line == "Invariants":
                current_section = Sections.INVARIANTS
            else:
                match current_section.name:
                    case Sections.CLOCKS.name:
                        self.clocks = line.strip().split()
                        self.clock_constraints_dict = {
                            clock: [] for clock in self.clocks
                        }
                        self.clocks_dict = {
                            value: index for index, value in enumerate(self.clocks)
                        }
                    case Sections.CLOCK_CONSTRAINTS.name:
                        values = line.strip().split()
                        self._parse_clock_constraints(values, row_index)
                        row_index += 1
                    case Sections.INVARIANTS.name:
                        values = line.strip().split()
                        self._parse_invariants(values, row_index)
                        row_index += 1

    def get_clocks(self):
        return self.clocks

    def get_clock_constraints(self):
        return self.clock_constraint_struct

    def get_graph(self):
        return self.graph

    def get_contraints_dict(self):
        return self.clock_constraints_dict

    def get_invariants(self):
        return self.invariants_arr

    def _parse_clock_constraints(self, line: list[str], row: int):
        for col, constraint in enumerate(line):
            parts = constraint.split(",")
            for part in parts:
                if re.search(r"(\w+)(=|>|>=|==|<|<=)(\d+)", part):
                    if len(self.clock_constraint_struct[row][col]) > 1:
                        self.clock_constraint_struct[row][col] += f",{part}"
                    else:
                        self.clock_constraint_struct[row][col] = str(part)
                    # if matched.group(2) != '=':
                    # self.clock_constraints_dict[matched.group(1)].append(int(matched.group(3)))

    def _parse_invariants(self, line: list[str], location: int):
        """
        Receives a row of the invariants matrix (location x clock) and a reference
        to the current line being parsed (the location).
        Computes
        invariants_arr: A 2d array indexed by location, where each element in the array is a list of
        invariants for the ith location of the form ['x', 2] to signal x<=2 for ith-location.
        """
        for index, value in enumerate(line):
            invariants = value.split(",")
            for invariant in invariants:
                if matched := re.match(r"(\w+)(?:<=|<)(\d+)", invariant):
                    self.invariants_arr[location] += [
                        matched.group(1),
                        float(matched.group(2)),
                    ]


class Sections(Enum):
    CLOCKS = ("Clocks",)
    CLOCK_CONSTRAINTS = ("Clock_constraints",)
    INVARIANTS = ("Invariants",)
    UNKNOWN = "Unknown"
