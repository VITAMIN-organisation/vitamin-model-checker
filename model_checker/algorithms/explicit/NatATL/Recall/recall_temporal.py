"""Universal temporal model checking on a finite recall-product graph.

This checks a FIXED recall strategy profile, not the existential search for
strategies. The product graph already contains every possible opponent move.
All paths are infinite: every reachable product node must have successors.
"""

from collections.abc import Set

from model_checker.algorithms.explicit.NatATL.Recall.recall_product import (
    ProductState,
    RecallProduct,
)


def states_with_atom(product: RecallProduct, proposition: str) -> set[ProductState]:
    """Product states labelled with the given atomic proposition."""
    return {
        node for node, labels in product.labels.items()
        if proposition in labels
    }


def universal_temporal_states(
    product: RecallProduct,
    operator: str,
    left: Set[ProductState],
    right: Set[ProductState] | None = None,
) -> set[ProductState]:
    """State-set semantics of AX, AF, AG, A[U], A[W] on the product.

    ``left`` is the operand of X/F/G, or the left operand of U/W.
    ``right`` is mandatory for U/W and forbidden for X/F/G.

    Only REACHABLE product nodes are represented. Because the graph records
    all opponent choices, AX uses universal quantification over successors.
    """
    if not isinstance(operator, str):
        raise ValueError("Temporal operator must be a string")
    op = operator.upper()
    if op not in {"X", "F", "G", "U", "W"}:
        raise ValueError(f"Unsupported temporal operator: {operator!r}")
    if (op in {"U", "W"}) != (right is not None):
        raise ValueError(f"Incorrect operands for temporal operator {op}")

    successors = product.successors
    universe = set(successors)
    if not universe or product.initial not in universe:
        raise ValueError("Recall product is empty or lacks its initial state")
    if set(product.labels) != universe or set(product.edges) != universe:
        raise ValueError("Recall product has inconsistent node sets")
    if any(not succ or not set(succ) <= universe for succ in successors.values()):
        raise ValueError("Temporal checking requires a total, closed product")

    phi = set(left)
    psi = set(right) if right is not None else None
    if not phi <= universe or (psi is not None and not psi <= universe):
        raise ValueError("Temporal operand contains an unknown product state")

    def ax(target: set[ProductState]) -> set[ProductState]:
        return {
            node for node, children in successors.items()
            if children <= target
        }

    if op == "X":
        return ax(phi)

    # Least fixpoint for AF and AU, greatest fixpoint for AG and AW.
    if op == "F":
        current: set[ProductState] = set()
        def step(z: set[ProductState]) -> set[ProductState]:
            return phi | ax(z)
    elif op == "G":
        current = universe.copy()
        def step(z: set[ProductState]) -> set[ProductState]:
            return phi & ax(z)
    elif op == "U":
        current = set()
        assert psi is not None
        def step(z: set[ProductState]) -> set[ProductState]:
            return psi | (phi & ax(z))
    else:  # W
        current = universe.copy()
        assert psi is not None
        def step(z: set[ProductState]) -> set[ProductState]:
            return psi | (phi & ax(z))

    while True:
        updated = step(current)
        if updated == current:
            return updated
        current = updated


def check_initial(
    product: RecallProduct,
    operator: str,
    left: Set[ProductState],
    right: Set[ProductState] | None = None,
) -> bool:
    """Verdict of a temporal objective for the FIXED recall strategy profile."""
    return product.initial in universal_temporal_states(
        product, operator, left, right
    )
