"""Real-valued state list utilities for ATLF (state, value) tuples in [0, 1]."""


def set_value_tuple_list(cgs, value):
    """Assign a value to all tuples (state, value) in the list."""
    return [(state, value) for state in cgs.states]


def _to_dict(states_list):
    """Convert list of (state, value) tuples to dictionary for O(1) lookup."""
    return dict(states_list)


def intersection_values(states1, states2):
    """Returns the minimum between matching values: min(states1[i], states2[i])."""
    dict2 = _to_dict(states2)
    return [(state, min(val, dict2.get(state, val))) for state, val in states1]


def union_values(states1, states2):
    """Returns the max between matching values: max(states1[i], states2[i])."""
    dict2 = _to_dict(states2)
    return [(state, max(val, dict2.get(state, val))) for state, val in states1]


def difference_values(states1, states2):
    """Returns the difference between matching values: states1[i] - states2[i],
    rounded to 12 decimals because float subtraction leaves noise (1 - 0.7 is
    0.30000000000000004), the only arithmetic ATLF does besides min and max."""
    dict2 = _to_dict(states2)
    return [(state, round(val - dict2.get(state, 0), 12)) for state, val in states1]


def update_values(p, t):
    """`p` with each state's value raised to its value in `t` when that is larger."""
    dict_t = _to_dict(t)
    return [(state, max(val_p, dict_t.get(state, val_p))) for state, val_p in p]


def first_included_in_second(p, t):
    """Whether `p` is included in `t`: value_p <= value_t in every state."""
    dict_t = _to_dict(t)
    return all(val_p <= dict_t.get(state, val_p) for state, val_p in p)
