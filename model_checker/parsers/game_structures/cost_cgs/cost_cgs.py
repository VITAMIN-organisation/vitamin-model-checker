"""Cost-based Concurrent Game Structure (CostCGS) parser.

Extends CGS with action-state costs; used by OATL, OL and other cost-bounded logics.
"""

from typing import Any

from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_actions import (
    AGENT_ACTION_SEPARATOR,
    build_action_list,
    wildcard_joint_profile,
)
from model_checker.parsers.game_structures.cost_cgs import cost_cgs_parser


class CostCGS(CGS):
    """A CostCGS model: a CGS plus cost sections such as Costs_for_actions."""

    def _reset_state(self):
        super()._reset_state()
        self.costs = []
        self.cost_for_action = {}
        self.usesCostsInsteadOfActions = False

    def _parse_lines(self, lines: list[str]) -> None:
        self._reset_state()

        cost_cgs_parser.parse_cost_sections(lines, self)
        cost_cgs_parser.parse_common_sections(lines, self)
        cost_cgs_parser.normalize_cost_action_keys(self)
        cost_cgs_parser.parse_transitions(lines, self)

    # --- Cost Accessor Methods ---

    def get_cost_for_action(self, action: str, state: str) -> Any:
        """The cost of `action` at `state`; an all-wildcard action uses the '*' key.
        Both ``A|C`` and compact ``AC`` profiles are accepted."""
        action = str(action)
        num_agents = self.get_number_of_agents()
        candidates = [action]
        if AGENT_ACTION_SEPARATOR in action:
            candidates.append("".join(action.split(AGENT_ACTION_SEPARATOR)))
        else:
            profiles = build_action_list(action, num_agents)
            if profiles:
                candidates.append(profiles[0])

        compact = (
            "".join(action.split(AGENT_ACTION_SEPARATOR))
            if AGENT_ACTION_SEPARATOR in action
            else action
        )
        if action == wildcard_joint_profile(num_agents) or compact == "*" * num_agents:
            candidates.extend(
                ["*", "*" * num_agents, wildcard_joint_profile(num_agents)]
            )

        seen: set[str] = set()
        for act in candidates:
            if act in seen:
                continue
            seen.add(act)
            key = f"{act};{state}"
            if key in self.cost_for_action:
                return self.cost_for_action[key]
        raise KeyError(f"{action};{state}")
