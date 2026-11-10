"""Bottom-up evaluation of OL formula trees.

OL `<Jn> theta` is OATL `[[Ag]]^n theta` with the coalition of all agents (AAMAS
2024, section 6), so the OATL operators do the work: at each step the Demon
erases joint actions costing at most n in total, never all of them, and every
remaining path must satisfy theta (ECAI 2023, Definitions 3-4). `W` is ECAI
2023's abbreviation `<n>(phi W psi) := <n>(psi R (phi or psi))`.
"""

from model_checker.algorithms.explicit.OATL.solver import solve_demonic_tree
from model_checker.parsers.syntax_patterns import OL_DEMONIC_BOUND_PREFIX_RE


def _all_agents_prefix_reader(cgs):
    """Read `<Jn>` as the coalition of every agent with Demon budget n."""
    all_agents = ",".join(str(i) for i in range(1, cgs.get_number_of_agents() + 1))

    def read_prefix(token: str) -> tuple[str, int]:
        match = OL_DEMONIC_BOUND_PREFIX_RE.match(token)
        if match is None:
            raise ValueError(f"OL operator '{token}' has no <Jn> prefix")
        return all_agents, int(match.group(1))

    return read_prefix


def solve_tree(cgs, root) -> None:
    """Replace each node value with the set of states satisfying its subformula."""
    solve_demonic_tree(cgs, root, "OL", "DEMONIC", _all_agents_prefix_reader(cgs))
