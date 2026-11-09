"""Reader for COTL model files: a graph whose edges demons can disable at a cost.

Besides Name_State, Initial_State, Atomic_propositions and Labelling, a file has:

Transition        0/1 matrix; row i marks the successors of state i.
                  A state may have no successor.
Number_of_demons  k >= 1.
Demon_actions     one line `demon state action cost` per action a demon can
                  play at a state, other than idle; cost >= 1. The idle action
                  `*` is always available at cost 0.
Curses            one line `state a1,...,ak successor...`: when the demons play
                  this joint action (one action per demon, `*` for idle), the
                  edges from `state` to the listed successors are disabled.
                  A joint action that is not listed disables nothing.
"""

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_validation import (
    collect_state_errors,
    raise_structure_errors,
    validate_labelling_matrix_dimensions,
    validate_transition_matrix_dimensions,
)
from model_checker.parsers.syntax_patterns import PROPOSITION_FULL_RE

IDLE = "*"
_DEMON_SECTIONS = ("Number_of_demons", "Demon_actions", "Curses")


class ObstructionModel(CGS):
    """COTL model: states, edges, labelling, and what each demon can disable at what cost.

    After read_file:
    - `successors[s]`: indices of the states reachable from state index s.
    - `demon_actions[s]`: {demon index: {action: cost}} for the actions declared
      at s; use `actions_of`, which adds idle.
    - `curses[s]`: {curse: disabled successor indices} for the listed curses at s.
    """

    def _reset_state(self):
        super()._reset_state()
        self.number_of_demons = 0
        self.successors: list[frozenset[int]] = []
        self.demon_actions: list[dict[int, dict[str, int]]] = []
        self.curses: list[dict[tuple[str, ...], frozenset[int]]] = []
        self._demon_lines: dict[str, list[tuple[int, str]]] = {
            name: [] for name in _DEMON_SECTIONS
        }

    def _parse_lines(self, lines: list[str]) -> None:
        super()._parse_lines(lines)
        section = None
        for number, raw in enumerate(lines, start=1):
            line = raw.strip()
            if cgs_parser.is_blank_or_comment(line):
                continue
            if line in _DEMON_SECTIONS:
                section = line
            elif (
                line in cgs_parser.SECTION_HEADERS
                or line in cgs_parser.EXTENSION_SECTION_HEADERS
            ):
                section = None
            elif section is not None:
                self._demon_lines[section].append((number, line))

    def read_from_model_object(self, model):
        raise NotImplementedError("ObstructionModel is loaded with read_file")

    def validate_model_structure(self) -> None:
        """Check the graph and labelling, then read and check the demon sections."""
        num_states = len(self.states)
        errors = collect_state_errors(self)
        errors += validate_transition_matrix_dimensions(self.graph, num_states)
        errors += validate_labelling_matrix_dimensions(
            self.matrix_prop, num_states, len(self.atomic_propositions), self.states
        )
        raise_structure_errors(errors)

        # Checked first, so a file of another model type fails with this message.
        self.number_of_demons = self._read_number_of_demons()
        self.successors = [self._row_successors(i) for i in range(num_states)]
        self.demon_actions = self._read_demon_actions()
        self.actions = sorted(
            {
                a
                for per_state in self.demon_actions
                for d in per_state.values()
                for a in d
            }
        )
        self.curses = self._read_curses()

    def actions_of(self, state: int, demon: int) -> dict[str, int]:
        """Actions of a demon (0-based index) at a state with their costs, idle included."""
        return {IDLE: 0, **self.demon_actions[state].get(demon, {})}

    def _row_successors(self, i: int) -> frozenset[int]:
        successors = set()
        for j, cell in enumerate(self.graph[i]):
            if cell not in (0, "0", "1"):
                raise ValueError(
                    f"Transition row of state '{self.states[i]}', column {j}: "
                    f"expected 0 or 1, got '{cell}'"
                )
            if cell == "1":
                successors.add(j)
        return frozenset(successors)

    def _read_number_of_demons(self) -> int:
        lines = self._demon_lines["Number_of_demons"]
        if len(lines) != 1:
            raise ValueError(
                "Number_of_demons must hold exactly one integer >= 1, "
                f"found {len(lines)} line(s)"
            )
        number, text = lines[0]
        if not text.isdigit() or int(text) < 1:
            raise ValueError(
                f"Number_of_demons line {number}: expected an integer >= 1, got '{text}'"
            )
        return int(text)

    def _state_index(self, name: str, where: str) -> int:
        if name not in self.state_to_index:
            raise ValueError(f"{where}: unknown state '{name}'")
        return self.state_to_index[name]

    def _read_demon_actions(self) -> list[dict[int, dict[str, int]]]:
        # Sparse, so memory follows the file and not Number_of_demons.
        table: list[dict[int, dict[str, int]]] = [{} for _ in range(len(self.states))]
        for number, text in self._demon_lines["Demon_actions"]:
            where = f"Demon_actions line {number} '{text}'"
            fields = text.split()
            if len(fields) != 4:
                raise ValueError(f"{where}: expected 'demon state action cost'")
            demon, state, action, cost = fields
            if not demon.isdigit() or not 1 <= int(demon) <= self.number_of_demons:
                raise ValueError(
                    f"{where}: demon must be between 1 and {self.number_of_demons}"
                )
            if not PROPOSITION_FULL_RE.match(action):
                raise ValueError(
                    f"{where}: action must be a name such as 'block_a1' "
                    f"(the idle action '{IDLE}' is implicit)"
                )
            # Only the idle action is free.
            if not cost.isdigit() or int(cost) < 1:
                raise ValueError(f"{where}: cost must be an integer >= 1")
            state_actions = table[self._state_index(state, where)]
            actions = state_actions.setdefault(int(demon) - 1, {})
            if action in actions:
                raise ValueError(f"{where}: action declared twice")
            actions[action] = int(cost)
        return table

    def _read_curses(self) -> list[dict[tuple[str, ...], frozenset[int]]]:
        table: list[dict[tuple[str, ...], frozenset[int]]] = [
            {} for _ in range(len(self.states))
        ]
        for number, text in self._demon_lines["Curses"]:
            where = f"Curses line {number} '{text}'"
            fields = text.split()
            if len(fields) < 2:
                raise ValueError(f"{where}: expected 'state a1,...,ak successor...'")
            state = self._state_index(fields[0], where)
            curse = tuple(fields[1].split(","))
            if len(curse) != self.number_of_demons:
                raise ValueError(
                    f"{where}: a curse has one action per demon, "
                    f"expected {self.number_of_demons}, got {len(curse)}"
                )
            for demon, action in enumerate(curse):
                if action != IDLE and action not in self.demon_actions[state].get(
                    demon, {}
                ):
                    raise ValueError(
                        f"{where}: demon {demon + 1} has no action '{action}' "
                        f"at state '{fields[0]}'"
                    )
            disabled = set()
            for name in fields[2:]:
                target = self._state_index(name, where)
                if target not in self.successors[state]:
                    raise ValueError(
                        f"{where}: there is no edge from '{fields[0]}' to '{name}'"
                    )
                disabled.add(target)
            if curse in table[state]:
                raise ValueError(f"{where}: curse listed twice for this state")
            table[state][curse] = frozenset(disabled)
        return table
