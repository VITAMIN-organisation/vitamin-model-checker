"""Actions and coalitions for CGS models.

Extract actions from the transition matrix, format coalition/opponent moves.
"""


def validate_agent_numbers(agents: list[int], num_agents: int):
    """Check that every agent number is between 1 and num_agents. Raises ValueError if not."""
    for agent in agents:
        if not isinstance(agent, int) or agent < 1 or agent > num_agents:
            raise ValueError(
                f"Invalid agent number: {agent}. "
                f"Agent numbers must be between 1 and {num_agents} (inclusive)."
            )


def format_agents(agents: list[int]) -> set[int]:
    """Drop 0 from the list and convert 1-based agent numbers to 0-based indices."""
    return {int(x) - 1 for x in agents if x != 0}


def get_agents_from_coalition(coalition: str) -> set[str]:
    """Split a comma-separated coalition string (e.g. "1,2,3") into a set of agent ids."""
    if not coalition or not coalition.strip():
        return set()
    return {value for value in coalition.split(",") if value}


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


def wildcard_joint_profile(num_agents: int) -> str:
    """Return the pipe-separated wildcard profile for ``num_agents`` positions."""
    if num_agents <= 0:
        return "*"
    return AGENT_ACTION_SEPARATOR.join("*" for _ in range(num_agents))


def build_action_list(action_string: str, num_agents: int) -> list[str]:
    """Expand one transition cell into pipe-normalized joint profiles.

    Compact joints such as ``AC`` and explicit joints such as ``A|C`` both become
    per-agent token lists joined with ``|``. The cell wildcard ``*`` becomes one
    profile with ``*`` in every agent position.
    """
    raw = str(action_string).strip() if action_string is not None else ""
    if not raw:
        return []
    if raw == "*":
        return [wildcard_joint_profile(num_agents)]
    return [
        AGENT_ACTION_SEPARATOR.join(tokens)
        for tokens in parse_joint_action_cell(raw, num_agents)
    ]


def parse_joint_action_cell(
    cell: str, num_agents: int, *, strict_arity: bool = False
) -> list[list[str]]:
    """Parse positional joint actions in a CGS transition cell.

    Examples for two agents (position 1 belongs to agent 1):
      ``AB,CD``                         legacy one-character notation
      ``MOVE_FORWARD|BLOCK_PATH``       nominal per-agent action names
      ``IDLE|BLOCK_PATH,MOVE_FORWARD|IDLE`` two transitions in one cell

    For a *single* agent, the entire unsplit token is its action name:
    ``MOVE_FORWARD`` no longer becomes ``M``. ``I`` and ``IDLE`` normalize
    to ``IDLE`` in either syntax.

    Legacy callers still tolerate and truncate surplus positional components.
    Strict verifiers may request ``strict_arity=True`` to reject incorrect
    component counts, empty action names, and empty comma-separated entries.
    The literal cell wildcard ``*`` remains handled by build_action_list().
    """
    if not isinstance(cell, str):
        return []
    if not isinstance(num_agents, int) or num_agents < 1:
        raise ValueError("Number of agents must be positive")

    raw = cell.strip()
    if not raw or raw == "*":
        return []

    joint_strings = raw.split(JOINT_CHOICE_SEPARATOR)
    joint_actions: list[list[str]] = []
    for part in joint_strings:
        joint = part.strip()
        if not joint:
            if strict_arity:
                raise ValueError(f"Empty joint-action entry in cell {cell!r}")
            continue

        if AGENT_ACTION_SEPARATOR in joint:
            tokens = [
                normalize_action_token(t) for t in joint.split(AGENT_ACTION_SEPARATOR)
            ]
        elif num_agents == 1:
            # Crucial for one-agent CGSs: multi-character names are indivisible.
            tokens = [normalize_action_token(joint)]
        else:
            # Backward-compatible compact encoding: one character per agent.
            tokens = [normalize_action_token(ch) for ch in joint]

        if strict_arity and (
            len(tokens) != num_agents or any(not token for token in tokens)
        ):
            raise ValueError(
                f"Invalid joint-action arity or empty action in {joint!r}: "
                f"expected exactly {num_agents} nonempty agent action(s), "
                f"got {len(tokens)}"
            )
        if len(tokens) < num_agents:
            raise ValueError(
                f"Action joint {joint!r} in cell {cell!r} has "
                f"{len(tokens)} agent action(s); expected at least {num_agents}"
            )

        # In permissive mode, retain VITAMIN's historical truncation behavior.
        joint_actions.append(tokens[:num_agents])

    return joint_actions


def extract_actions_for_agents(
    graph: list[list], agents: list[int], *, num_agents: int
) -> dict[str, list[str]]:
    """Return ``agent{n}`` -> action tokens from graph cells for 1-based agent ids.

    Call ``validate_agent_numbers`` first. Cell encoding is defined by
    ``parse_joint_action_cell``.
    """
    agent_indices = {agent: agent - 1 for agent in agents}
    actions_per_agent = {f"agent{agent}": set() for agent in agents}

    valid_elements = (
        str(elem) for row in graph for elem in row if elem not in (0, "0", "", None, "*")
    )

    # A coalition may omit agents. In that case its maximum index is NOT
    # the arity of a joint action. Callers with the CGS must supply its full
    # number of agents to distinguish legacy "AB" from a single-agent name.
    if type(num_agents) is not int or num_agents < 1:
        raise ValueError("[MODEL] Number of agents must be positive")
    validate_agent_numbers(agents, num_agents)
    if num_agents < max(agents, default=0):
        raise ValueError("Selected agent index exceeds total number of agents")

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
        agent_key: sorted(actions) for agent_key, actions in actions_per_agent.items()
    }


def process_action_string(
    action_string: str, agents: set[int], include_agents: bool = True
) -> str:
    """Keep or drop agent positions in a pipe-separated profile; others become "-".

    ``action_string`` must already be a per-agent profile (``A|C``), as produced by
    ``build_action_list``. include_agents=True keeps the given agents;
    False keeps the others (opponents).
    """
    tokens = [
        normalize_action_token(t) for t in action_string.split(AGENT_ACTION_SEPARATOR)
    ]
    masked_tokens = []
    for idx, token in enumerate(tokens):
        keep = (idx in agents) if include_agents else (idx not in agents)
        masked_tokens.append(token if keep else "-")
    return AGENT_ACTION_SEPARATOR.join(masked_tokens)


def _expand_action_wildcards(actions: set[str], num_agents: int) -> set[str]:
    """Expand a bare "*" profile to one wildcard token per agent position."""
    if num_agents <= 0:
        return {s for s in actions if s != "*"}
    wildcard_joint = wildcard_joint_profile(num_agents)
    return {s if s != "*" else wildcard_joint for s in actions}


def _process_actions_for_agents(
    actions: set[str], agents: set[int], num_agents: int, include_agents: bool
) -> set[str]:
    """Expand wildcards then mask each action by coalition (include_agents=True) or opponents (False)."""
    expanded = _expand_action_wildcards(actions, num_agents)
    return {
        process_action_string(s, agents, include_agents=include_agents)
        for s in expanded
    }


def get_coalition_actions(
    actions: set[str], agents: set[int], num_agents: int
) -> set[str]:
    """Return the coalition's part of each profile (other positions become "-")."""
    if not agents:
        if num_agents <= 0:
            return {"-"}
        return {AGENT_ACTION_SEPARATOR.join("-" for _ in range(num_agents))}
    return _process_actions_for_agents(actions, agents, num_agents, include_agents=True)
