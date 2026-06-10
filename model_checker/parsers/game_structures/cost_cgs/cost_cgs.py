"""Cost-based Concurrent Game Structure (CostCGS) parser.

Extends CGS with action-state costs; used by OATL, OL and other cost-bounded logics.
"""

from typing import Any

from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cost_cgs import cost_cgs_parser


class CostCGS(CGS):
    """Parser and in-memory representation for a CostCGS model file.

    Adds cost sections (e.g. Costs_for_actions, Transition_With_Costs) on top
    of the base CGS. Use read_file(path) to load a file; then use
    get_cost_for_action(action, state) or cost_for_action for cost data.
    """

    # --- Initialization and File Reading ---

    def __init__(self):
        """Create an empty CostCGS; load data with read_file or read_from_model_object."""
        super().__init__()
        self.costs = []
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False

    def read_file(self, filename: str) -> None:
        """Load a CostCGS model from a file. Raises ValueError on bad structure."""
        with open(filename, encoding="utf-8") as f:
            lines = f.readlines()

        self._reset_state()
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False

        cost_cgs_parser.parse_cost_sections(lines, self)
        cost_cgs_parser.parse_common_sections(lines, self)
        cost_cgs_parser.parse_transitions(lines, self)

    def read_from_model_object(self, model: Any) -> None:
        """Copy fields from an existing model object, including cost_for_action."""
        super().read_from_model_object(model)
        self.cost_for_action = model.cost_for_action

    # --- Cost Accessor Methods ---

    def get_cost_for_action(self, action: str, state: str) -> Any:
        """Look up cost for action at state; all-wildcard actions use the '*' key."""
        key = f"{action};{state}"
        if key in self.cost_for_action:
            return self.cost_for_action[key]
        if action == "*" * self.get_number_of_agents():
            key = f"*;{state}"
        return self.cost_for_action[key]
