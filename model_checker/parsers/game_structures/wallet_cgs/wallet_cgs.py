import re

from model_checker.parsers.game_structures.cgs import cgs_actions
from model_checker.parsers.game_structures.cgs.cgs import CGS
from model_checker.parsers.game_structures.cgs.cgs_utils import proposition_index


class WalletCGS(CGS):
    def __init__(self):
        super().__init__()
        self.wallets = {}  # Dictionary mapping states to wallet tuples

        # set of consumption actions (Act↓) - reduce wallet
        self.consumption_actions = {
            "D",  # deposit(v)
            "B",  # bid(v)
            "S",  # stake(v)
            "T",  # transfer(v, recipient)
            "N",  # donate(v)
        }

        # set of income actions (Act↑) - increase wallet
        self.income_actions = {
            "W",  # withdraw(v)
            "R",  # reclaim(v)
            "E",  # redeem(v)
            "F",  # refund(v)
            "U",  # unstake(v)
        }

    def _reset_state(self):
        super()._reset_state()
        self.wallets = {}

    def _parse_lines(self, lines: list[str]) -> None:
        super()._parse_lines(lines)

        current_section = None

        for line in lines:
            line = line.strip()

            if line == "Wallets":
                current_section = "Wallets"
                continue
            elif line == "" or line.startswith("Transition"):
                current_section = None
                continue

            if current_section == "Wallets":
                if ":" in line:
                    parts = line.split(":")
                    state = parts[0].strip()
                    wallet_values = [
                        int(x.strip()) for x in parts[1:] if x.strip().isdigit()
                    ]
                    expected_length = self.get_number_of_agents()
                    if len(wallet_values) != expected_length:
                        raise ValueError(
                            f"Error in {state}: expected {expected_length} wallets, found {len(wallet_values)}."
                        )
                    self.wallets[state] = tuple(wallet_values)

        # AAMAS26b Def. 3.1: W : Q x Ag -> Q+ gives a balance in every state.
        # Not in validate_model_structure: read_from_model_object loads no wallets.
        missing = [str(s) for s in self.states if str(s) not in self.wallets]
        if missing:
            raise ValueError(
                f"Wallets has no row for state(s) {', '.join(missing)}; "
                "every state needs one balance per agent."
            )

    def parse_parameterized_action(self, action_string):
        """(name, value, is_consumption, is_income) of an action token; numbers,
        `I` and any token without a letter-and-amount shape are neutral."""
        action_string = str(action_string).strip()

        # Parse pattern like "D20", "B50", "W30", etc.
        match = re.match(r"^([A-Z])(\d+)$", action_string)
        if match:
            action_char = match.group(1)
            parameter = int(match.group(2))

            if action_char in self.consumption_actions:
                return action_char, parameter, True, False
            elif action_char in self.income_actions:
                return action_char, parameter, False, True
            else:  # Other actions (neutral)
                return action_char, parameter, False, False
        else:
            return action_string, 0, False, False

    def check_action_feasibility(self, state, agent, action_string):
        """(feasible, reason) for one agent's action, per AAMAS26b Def. 3.1 and 4.1:
        a consumption action of value v needs W(state, agent) >= v; income and
        neutral actions are always permitted (p. 3)."""
        action_name, parameter, is_consumption, _ = self.parse_parameterized_action(
            action_string
        )
        if not is_consumption:
            return True, "Income or neutral action - always feasible"

        wallet = self.wallets[state][agent - 1]
        if wallet >= parameter:
            return True, "Sufficient funds"
        action_desc = self.get_action_description(action_name)
        return (
            False,
            f"Insufficient funds for {action_desc}{parameter}: need {parameter}, have {wallet}",
        )

    def is_profile_feasible(self, state, profile):
        """True when every agent of a `|`-joined joint profile can take its action in
        `state`; the contract is checked like any agent (Def. 4.1 has no exemption)."""
        return all(
            self.check_action_feasibility(state, agent, action)[0]
            for agent, action in enumerate(
                profile.split(cgs_actions.AGENT_ACTION_SEPARATOR), start=1
            )
        )

    def get_action_description(self, action_char):
        """Get human-readable action description"""
        descriptions = {
            "D": "deposit",
            "B": "bid",
            "S": "stake",
            "T": "transfer",
            "N": "donate",
            "W": "withdraw",
            "R": "reclaim",
            "E": "redeem",
            "F": "refund",
            "U": "unstake",
            "I": "idle",
        }
        return descriptions.get(action_char, f"action_{action_char}")

    def _contract_agent(self):
        """The last agent is the contract/system pool only when there is more than one agent."""
        num_agents = self.get_number_of_agents()
        return num_agents if num_agents > 1 else None

    def get_valid_actions(self, state, agent, wallet_constraint=None):
        """Get valid actions for an agent in a state with wallet feasibility checks"""
        state_index = self.get_index_by_state_name(state)
        valid_actions = set()
        contract_agent = self._contract_agent()

        for transition in self.graph[state_index]:
            if transition == 0:
                continue

            actions = transition.split(":")
            if len(actions) <= agent - 1:
                continue

            action = actions[agent - 1].strip()

            # Contract agent actions are always feasible; all other agents are checked.
            if agent != contract_agent:
                feasible, _ = self.check_action_feasibility(state, agent, action)
                if not feasible:
                    continue

            # For all agents: check additional wallet constraint if provided
            if wallet_constraint:
                if not self.check_wallet_constraint(state, agent, wallet_constraint):
                    continue

            valid_actions.add(action)

        return list(valid_actions)

    def get_next_states(self, current_state, actions):
        """Return all next states reachable under the given joint actions."""
        state_index = self.get_index_by_state_name(current_state)
        possible_transitions = self.graph[state_index]

        next_states = []
        contract_agent = self._contract_agent()

        for i, transition in enumerate(possible_transitions):
            if transition == 0:
                continue

            transition_actions = transition.split(":")
            match = True

            # 1. Check if actions match the transition pattern
            for agent, action in actions.items():
                agent_index = agent - 1

                if agent_index >= len(transition_actions):
                    match = False
                    break

                if transition_actions[agent_index].strip() != str(action):
                    match = False
                    break

            if match:
                # 2. Check wallet feasibility for all user agents
                all_feasible = True

                for agent, action in actions.items():
                    if agent == contract_agent:
                        # Contract actions are always feasible
                        continue

                    feasible, _ = self.check_action_feasibility(
                        current_state, agent, action
                    )
                    if not feasible:
                        all_feasible = False
                        break

                if all_feasible:
                    next_states.append(self.get_state_name_by_index(i))

        return next_states

    def check_wallet_constraint(self, state, agent, constraint):
        """Check if wallet satisfies a constraint"""
        wallets = self.wallets[state]
        agent_index = agent - 1

        if agent_index < 0 or agent_index >= len(wallets):
            raise IndexError("Agent index out of range")

        value = wallets[agent_index]
        op, target = constraint

        if op == ">=":
            return value >= target
        elif op == "<=":
            return value <= target
        elif op == "==":
            return value == target
        elif op == ">":
            return value > target
        elif op == "<":
            return value < target
        else:
            raise ValueError(f"Unsupported operator: {op}")

    def get_atom_index(self, element):
        """Returns the index of the given atom in the array of atomic propositions."""
        if isinstance(element, (list, tuple)):
            element = " ".join(map(str, element))
        return proposition_index(self.atomic_propositions, element)

    def simulate_transition(self, current_state, actions):
        """Simulate a transition and return the new wallets, keeping the total balance.
        For external callers; Wallet_ATL itself does not use it."""
        current_wallets = list(self.wallets[current_state])
        contract_agent = self._contract_agent()
        system_index = contract_agent - 1 if contract_agent else None

        for agent, action_str in actions.items():
            action_name, parameter, is_consumption, is_income = (
                self.parse_parameterized_action(action_str)
            )
            agent_index = agent - 1

            if is_consumption:
                current_wallets[agent_index] -= parameter

                # The last agent is the system pool, which receives what is consumed.
                if system_index is not None and system_index != agent_index:
                    current_wallets[system_index] += parameter

            elif is_income:
                # Income: agent gains funds only when system pool can cover it.
                if system_index is not None:
                    if (
                        system_index != agent_index
                        and current_wallets[system_index] >= parameter
                    ):
                        current_wallets[system_index] -= parameter
                        current_wallets[agent_index] += parameter
                else:
                    current_wallets[agent_index] += parameter

        return tuple(current_wallets)
