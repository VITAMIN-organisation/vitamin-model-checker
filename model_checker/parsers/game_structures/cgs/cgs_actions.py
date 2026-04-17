"""Actions and coalitions for CGS models.

Extract actions from the transition matrix, format coalition/opponent moves.
"""

from typing import Dict, List, Set


def validate_agent_numbers(agents: List[int], num_agents: int):
    """Check that every agent number is between 1 and num_agents. Raises ValueError if not."""
    for agent in agents:
        if not isinstance(agent, int) or agent < 1 or agent > num_agents:
            raise ValueError(
                f"Invalid agent number: {agent}. "
                f"Agent numbers must be between 1 and {num_agents} (inclusive)."
            )


def format_agents(agents: List[int]) -> Set[int]:
    """Drop 0 from the list and convert 1-based agent numbers to 0-based indices."""
    return {int(x) - 1 for x in agents if x != 0}


def get_agents_from_coalition(coalition: str) -> Set[str]:
    """Split a comma-separated coalition string (e.g. "1,2,3") into a set of agent ids."""
    return set(coalition.split(","))


JOINT_CHOICE_SEPARATOR = ","
AGENT_ACTION_SEPARATOR = "|"
IDLE_TOKENS = {"I", "IDLE"}
CANONICAL_IDLE_TOKEN = "IDLE"


def normalize_action_token(token: str) -> str:
    """Normalize a per-agent action token (map idle tokens to a canonical form)."""
    stripped = str(token).strip()
    if stripped in IDLE_TOKENS:
        return CANONICAL_IDLE_TOKEN
    return stripped


def parse_joint_action_cell(cell: str, num_agents: int) -> List[List[str]]:
    """Parse one transition-matrix cell into per-agent action tokens for each joint choice.

    Supported formats for each non-zero cell in the Transition matrix:
    - Compact character format (recommended, current examples):
      * Joint choices separated by JOINT_CHOICE_SEPARATOR (",")
      * Each joint is a string of characters, one character per agent position
        (for example, "AC" with 2 agents means agent 1 does "A", agent 2 does "C").
      * A joint without any AGENT_ACTION_SEPARATOR is treated as a sequence of characters;
        the first num_agents characters are taken as the per-agent tokens and any extra
        characters beyond num_agents are ignored.
    - Explicit token format (optional, for longer names):
      * Joint choices separated by JOINT_CHOICE_SEPARATOR (",")
      * Within each joint, per-agent tokens separated by AGENT_ACTION_SEPARATOR ("|"),
        for example "IDLE|MOVE" for 2 agents.

    Idle tokens can be "I" or "IDLE" and are normalized to CANONICAL_IDLE_TOKEN.
    """
    if not isinstance(cell, str):
        return []

    raw = cell.strip()
    if not raw or raw == "*":
        return []

    joint_strings = [
        part.strip() for part in raw.split(JOINT_CHOICE_SEPARATOR) if part.strip()
    ]
    joint_actions: List[List[str]] = []

    for joint in joint_strings:
        if AGENT_ACTION_SEPARATOR in joint:
            # Explicit token format: a|b|c
            tokens = [
                normalize_action_token(t) for t in joint.split(AGENT_ACTION_SEPARATOR)
            ]
            if len(tokens) < num_agents:
                raise ValueError(
                    f"Action joint '{joint}' in cell '{cell}' has {len(tokens)} token(s); "
                    f"expected at least {num_agents} token(s) (one per agent)."
                )
        else:
            # Compact character format: treat as sequence of characters
            chars = [normalize_action_token(ch) for ch in joint]
            if len(chars) < num_agents:
                raise ValueError(
                    f"Action joint '{joint}' in cell '{cell}' has length {len(chars)}; "
                    f"expected at least {num_agents} character(s) (one per agent)."
                )
            tokens = chars

        # Use only the first num_agents tokens for per-agent actions
        tokens = tokens[:num_agents]
        joint_actions.append(tokens)

    return joint_actions


def extract_actions_for_agents(
    graph: List[List], agents: List[int]
) -> Dict[str, List[str]]:
    """Build a dict agent_name -> list of actions from the transition matrix for the given 1-based agents.

    Each matrix cell encodes one or more joint choices as strings; for each joint choice we
    collect the per-agent action tokens for the requested agents. Idle tokens are included.
    """
    agent_indices = {agent: agent - 1 for agent in agents}
    actions_per_agent = {f"agent{agent}": set() for agent in agents}

    valid_elements = (
        str(elem) for row in graph for elem in row if elem != 0 and elem != "*"
    )

    # Infer number of agents from the largest agent index we care about
    num_agents = max(agent_indices.values()) + 1 if agent_indices else 0

    for elem_str in valid_elements:
        if not num_agents:
            continue

        joint_actions = parse_joint_action_cell(elem_str, num_agents)
        for joint in joint_actions:
            for agent, agent_index in agent_indices.items():
                if 0 <= agent_index < len(joint):
                    token = joint[agent_index]
                    actions_per_agent[f"agent{agent}"].add(token)

    return {
        agent_key: list(actions) for agent_key, actions in actions_per_agent.items()
    }


def process_action_string(
    action_string: str, agents: Set[int], include_agents: bool = True
) -> str:
    """Keep or drop agent positions in an action string; replaced positions become "-".

    include_agents=True keeps the given agents; False keeps the others (opponents).
    """
    tokens = [
        normalize_action_token(t) for t in action_string.split(AGENT_ACTION_SEPARATOR)
    ]
    masked_tokens = []
    for idx, token in enumerate(tokens):
        keep = (idx in agents) if include_agents else (idx not in agents)
        masked_tokens.append(token if keep else "-")
    return AGENT_ACTION_SEPARATOR.join(masked_tokens)


def _expand_action_wildcards(actions: Set[str], num_agents: int) -> Set[str]:
    """Expand "*" to a wildcard token for each agent in the joint choice."""
    if num_agents <= 0:
        return {s for s in actions if s != "*"}
    wildcard_joint = AGENT_ACTION_SEPARATOR.join("*" for _ in range(num_agents))
    return {s if s != "*" else wildcard_joint for s in actions}


def _process_actions_for_agents(
    actions: Set[str], agents: Set[int], num_agents: int, include_agents: bool
) -> Set[str]:
    """Expand wildcards then mask each action by coalition (include_agents=True) or opponents (False)."""
    expanded = _expand_action_wildcards(actions, num_agents)
    return {
        process_action_string(s, agents, include_agents=include_agents)
        for s in expanded
    }


def get_coalition_actions(
    actions: Set[str], agents: Set[int], num_agents: int
) -> Set[str]:
    """Return the coalition’s part of each action string (other positions become "-")."""
    if not agents:
        return {"-" * num_agents}
    return _process_actions_for_agents(actions, agents, num_agents, include_agents=True)


def get_opponent_actions(
    actions: Set[str], agents: Set[int], num_agents: int
) -> Set[str]:
    """Return the opponents’ part of each action string (coalition positions become "-")."""
    return _process_actions_for_agents(
        actions, agents, num_agents, include_agents=False
    )
