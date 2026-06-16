"""Graph relation extraction helpers."""


def labeled_pairs(relations, states_list, predicate):
    """Collect state pairs for matrix cells that satisfy predicate."""
    pairs = []
    for i, row in enumerate(relations):
        for j, element in enumerate(row):
            if not predicate(element):
                continue
            if element == "*":
                pairs.append((states_list[i], states_list[i]))
            else:
                pairs.append((states_list[i], states_list[j]))
    return pairs
