from model_checker.models.model_factory import CostCGS
from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.timed_cgs import timed_cgs_parser


class TimedCGS(CostCGS):
    def __init__(self):
        super().__init__()
        self.clock_constraints_dict = {}
        self.clocks_dict = {}

    def read_file(self, filename: str) -> None:
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()

        self._reset_state()
        self.clock_constraints_dict = {}
        self.clocks_dict = {}

        base_lines = cgs_parser.filter_lines_for_common_sections(
            lines,
            timed_cgs_parser.TIMED_SECTION_HEADERS,
            exit_skip_on=(
                cgs_parser.SECTION_HEADERS | cgs_parser.EXTENSION_SECTION_HEADERS
            ),
        )
        timed_cgs_parser.parse_base_sections(base_lines, self)
        timed_cgs_parser.parse_timed_sections(lines, self)
