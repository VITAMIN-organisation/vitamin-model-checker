import re

from model_checker.parsers.game_structures.cgs.cgs import CGS


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

    def read_file(self, filename):
        """Read and parse the WATL model file"""
        super().read_file(filename)

        with open(filename) as f:
            lines = f.readlines()

        current_section = None
        self.wallets = {}

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

    def parse_parameterized_action(self, action_string):
        """Parse parameterized actions - handle both action codes and contract numbers"""
        action_string = str(action_string).strip()

        # Contract actions (numbers) are always neutral
        if action_string.isdigit():
            return action_string, 0, False, False

        if action_string == "I":  # Idle action
            return "I", 0, False, False

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
        """Check if an action is feasible according to WCGS rules - returns (bool, reason)"""
        action_name, parameter, is_consumption, is_income = (
            self.parse_parameterized_action(action_string)
        )

        # Contract actions (numbers) are always feasible - they're system triggers
        if str(action_string).isdigit():
            return True, "Contract action - always feasible"

        wallet = self.wallets.get(state, (0,) * self.get_number_of_agents())[agent - 1]

        # CONSUMPTION ACTIONS (Act↓): Require sufficient wallet balance
        if is_consumption:
            if wallet >= parameter:
                return True, "Sufficient funds"
            else:
                action_desc = self.get_action_description(action_name)
                return (
                    False,
                    f"Insufficient funds for {action_desc}{parameter}: need {parameter}, have {wallet}",
                )

        # INCOME ACTIONS (Act↑): Require external preconditions
        elif is_income:
            available_funds = self.get_available_system_funds(state, agent, action_name)
            if available_funds >= parameter:
                return True, "Sufficient system funds"
            else:
                action_desc = self.get_action_description(action_name)
                return (
                    False,
                    f"Insufficient system funds for {action_desc}{parameter}: need {parameter}, system has {available_funds}",
                )

        # Neutral actions (Idle and others) are always feasible
        else:
            return True, "Neutral action - always feasible"

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

    def get_available_system_funds(self, state, agent, action_name):
        """Get available funds in the system for this income action.
        Always use the last agent as the system/contract pool.
        """
        num_agents = self.get_number_of_agents()
        if num_agents >= 1:
            contract_index = num_agents - 1
            return self.wallets.get(state, (0,) * self.get_number_of_agents())[
                contract_index
            ]
        return 0

    def get_valid_actions(self, state, agent, wallet_constraint=None):
        """Get valid actions for an agent in a state with wallet feasibility checks"""
        state_index = self.get_index_by_state_name(state)
        valid_actions = set()

        for transition in self.graph[state_index]:
            if transition == 0:
                continue

            actions = transition.split(":")
            if len(actions) <= agent - 1:
                continue

            action = actions[agent - 1].strip()

            # For agents 1 and 2: check wallet feasibility
            if agent in [1, 2]:
                if not self.check_action_feasibility(state, agent, action):
                    continue

            # For all agents: check additional wallet constraint if provided
            if wallet_constraint:
                if not self.check_wallet_constraint(state, agent, wallet_constraint):
                    continue

            valid_actions.add(action)

        return list(valid_actions)

    def get_next_states(self, current_state, actions):
        """
        Get possible next states given current state and actions
        """
        state_index = self.get_index_by_state_name(current_state)
        possible_transitions = self.graph[state_index]

        next_states = []

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
                num_agents = self.get_number_of_agents()
                contract_agent = num_agents  # last agent is the contract

                for agent, action in actions.items():
                    if agent == contract_agent:
                        # Contract actions are always feasible
                        continue

                    if not self.check_action_feasibility(current_state, agent, action):
                        all_feasible = False
                        break

                if all_feasible:
                    next_state = self.get_state_name_by_index(i)
                    next_states.append(next_state)

                    return next_states

    def check_wallet_constraint(self, state, agent, constraint):
        """Check if wallet satisfies a constraint"""
        wallets = self.wallets.get(state, (0,) * self.get_number_of_agents())
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
        from model_checker.parsers.game_structures.cgs.cgs_utils import (
            proposition_index,
        )

        if isinstance(element, (list, tuple)):
            element = " ".join(map(str, element))
        return proposition_index(self.atomic_propositions, element)

    def simulate_transition(self, current_state, actions):
        """Simulate a transition and return the new wallet state"""
        current_wallets = list(
            self.wallets.get(current_state, (0,) * self.get_number_of_agents())
        )
        total_agents = self.get_number_of_agents()

        for agent, action_str in actions.items():

            action_name, parameter, is_consumption, is_income = (
                self.parse_parameterized_action(action_str)
            )
            agent_index = agent - 1

            if is_consumption:
                # Consumption: agent loses funds
                current_wallets[agent_index] -= parameter

                # Funds go to system (typically the last agent)
                if total_agents > 1:  # Ensure there's at least one other agent
                    system_index = total_agents - 1  # Last agent is typically system
                    if system_index != agent_index:  # Don't transfer to self
                        current_wallets[system_index] += parameter

            elif is_income:
                # Income: agent gains funds
                current_wallets[agent_index] += parameter

                # Funds come from system (typically the last agent)
                if total_agents > 1:
                    system_index = total_agents - 1
                    if (
                        system_index != agent_index
                        and current_wallets[system_index] >= parameter
                    ):
                        current_wallets[system_index] -= parameter

        return tuple(current_wallets)
