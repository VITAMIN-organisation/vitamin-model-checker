from model_checker.parsers.game_structures.cost_cgs.cost_cgs import CostCGS
from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.timed_cgs import timed_cgs_parser


class TimedCGS(CostCGS):
    def __init__(self):
        super().__init__()

    def _reset_state(self):
        super()._reset_state()
        self.clock_constraints_dict = {}
        self.clocks_dict = {}
        self.clock_constraint_struct = []
        self.invariants_arr = []

    def _parse_lines(self, lines: list[str]) -> None:
        self._reset_state()

        base_lines = cgs_parser.filter_lines_for_common_sections(
            lines,
            timed_cgs_parser.TIMED_SECTION_HEADERS,
            exit_skip_on=(
                cgs_parser.SECTION_HEADERS | cgs_parser.EXTENSION_SECTION_HEADERS
            ),
        )
        timed_cgs_parser.parse_base_sections(base_lines, self)
        timed_cgs_parser.parse_timed_sections(lines, self)
