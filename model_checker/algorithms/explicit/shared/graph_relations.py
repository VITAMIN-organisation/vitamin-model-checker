"""Graph relation extraction helpers."""


def labeled_pairs(relations, states_list, predicate):
    """(row state, column state) for each matrix cell that satisfies predicate."""
    return [
        (str(states_list[i]), str(states_list[j]))
        for i, row in enumerate(relations)
        for j, element in enumerate(row)
        if predicate(element)
    ]
