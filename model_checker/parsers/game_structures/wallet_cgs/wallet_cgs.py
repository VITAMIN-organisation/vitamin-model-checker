import re

from model_checker.parsers.game_structures.cgs import cgs_actions, cgs_parser
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

        in_wallets = False
        headers = cgs_parser.SECTION_HEADERS | cgs_parser.EXTENSION_SECTION_HEADERS

        for line in lines:
            line = line.strip()

            if cgs_parser.is_blank_or_comment(line):
                continue
            if line in headers:
                in_wallets = line == "Wallets"
            elif in_wallets and ":" in line:
                self._parse_wallet_row(line)

        # AAMAS26b Def. 3.1: W : Q x Ag -> Q+ gives a balance in every state.
        missing = [str(s) for s in self.states if str(s) not in self.wallets]
        if missing:
            raise ValueError(
                f"Wallets has no row for state(s) {', '.join(missing)}; "
                "every state needs one balance per agent."
            )

    def _parse_wallet_row(self, line: str) -> None:
        """One `state: v1 : v2 ...` row: a declared state, once, with a natural
        number (Q+, AAMAS26b Def. 3.1) per agent."""
        state, *texts = (part.strip() for part in line.split(":"))
        if state not in self.all_states_set:
            raise ValueError(f"Wallets row for undeclared state '{state}': '{line}'.")
        if state in self.wallets:
            raise ValueError(
                f"Wallets has a repeated row for state '{state}': '{line}'."
            )
        for text in texts:
            if not (text.isascii() and text.isdigit()):
                raise ValueError(
                    f"Wallet value '{text}' is not a natural number in '{line}'."
                )
        expected_length = self.get_number_of_agents()
        if len(texts) != expected_length:
            raise ValueError(
                f"Error in {state}: expected {expected_length} wallets, found {len(texts)}."
            )
        self.wallets[state] = tuple(int(text) for text in texts)

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
