"""Executable restricted NatSL[1G] model checker.

The supported prefix is ``E* A*`` followed by a complete binding and one Boolean
temporal goal. For each existential profile, the current NatATL pruning and CTL
backend first checks the stronger case in which opponents are unrestricted. A
positive answer is a sound shortcut. A negative answer is inconclusive, so all
bounded universal natural strategies are then enumerated explicitly.

The time-oriented implementation materializes strategy domains and stores failed
existentially-pruned models for a second universal phase. The space-oriented
implementation generates domains lazily and checks the universal profiles before
moving to the next existential profile.
"""

from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
import io
import itertools
from pathlib import Path
import tempfile
from typing import Iterable, Iterator, Sequence

from model_checker.parsers.formulas.NatSL.parser import (
    NatSLFormula,
    Quantifier,
    format_formula,
    goal_to_ctl,
    parse_formula,
)
from model_checker.algorithms.explicit.CTL.CTL import (
    model_checking as ctl_model_checking,
)
from model_checker.utils.literals import parse_state_set_literal
from model_checker.parsers.game_structures.cgs.cgs import CGS


Strategy = dict[str, list[tuple[str, str]]]


def _hard_prune_agent_action(
    graph: list,
    states: set[str],
    action: str,
    agent_position: int,
    agents: list[int],
    state_to_index: dict[str, int],
) -> tuple[list, set[str]]:
    """Keep only joint actions where the selected agent plays exactly action."""
    new_graph = [row.copy() for row in graph]
    tuple_index = agents[agent_position - 1] - 1

    for state in states:
        row_index = state_to_index.get(str(state))
        if row_index is None:
            continue

        row = new_graph[row_index]
        for column, cell in enumerate(row):
            if not isinstance(cell, str) or cell == "*":
                continue

            kept = []
            for joint_action in cell.split(","):
                joint_action = joint_action.strip()
                if not joint_action:
                    continue

                # Current fixtures use compact one-character-per-agent profiles.
                if len(joint_action) > tuple_index and joint_action[tuple_index] == action:
                    kept.append(joint_action)

            row[column] = ",".join(kept) if kept else 0

    invalid_states = set()
    for state in states:
        row_index = state_to_index.get(str(state))
        if row_index is None:
            continue
        if all(cell == 0 for cell in new_graph[row_index]):
            invalid_states.add(str(state))

    return new_graph, invalid_states


def _process_transition_matrix_data_hard(
    cgs: CGS,
    model_path: str,
    agents: list[int],
    *strategies: Strategy,
) -> tuple[list | None, str]:
    """Apply exact NatSL action pruning; reject inadmissible strategies."""
    graph = [row.copy() for row in cgs.graph]
    all_states = {str(state) for state in cgs.states}
    state_to_index = cgs.state_to_index

    for strategy_index, strategy in enumerate(strategies, start=1):
        covered: set[str] = set()

        for condition, action in strategy["condition_action_pairs"]:
            condition = str(condition).strip()
            action = str(action).strip()

            if condition.upper() == "T":
                target_states = all_states - covered
            else:
                ctl_result = ctl_model_checking(
                    condition,
                    model_path,
                    preloaded_model=cgs,
                )
                result_string = (ctl_result or {}).get("res", "")
                state_set: set[str] = set()

                if ": " in result_string:
                    state_set = {
                        str(state)
                        for state in parse_state_set_literal(
                            result_string.split(": ", 1)[1]
                        )
                    }

                target_states = state_set - covered

            if not target_states:
                continue

            covered |= target_states

            graph, invalid_states = _hard_prune_agent_action(
                graph,
                target_states,
                action,
                strategy_index,
                agents,
                state_to_index,
            )

            if invalid_states:
                return None, (
                    f"Inadmissible strategy: action {action!r} is not enabled "
                    f"in states {sorted(invalid_states)}"
                )

    return graph, ""


@dataclass
class EvaluationStats:
    existential_candidates: int = 0
    universal_profiles_checked: int = 0
    unrestricted_opponent_checks: int = 0
    unrestricted_opponent_shortcuts: int = 0
    complete_profile_checks: int = 0
    inadmissible_existential_profiles: int = 0
    incompatible_universal_profiles: int = 0


def _condition_cost(condition: str) -> int:
    """Count condition symbols without parentheses (the compl_Sigma metric)."""
    return len(condition.replace("!", " ! ").split())


def _conditions(atomic_propositions: list[str], max_cost: int) -> tuple[tuple[str, int], ...]:
    """Generate a deterministic propositional guard vocabulary."""
    generated: set[str] = set()
    output: list[tuple[str, int]] = []
    propositions = sorted(set(atomic_propositions))
    max_literals = min(len(propositions), (max_cost + 1) // 2)

    for size in range(1, max_literals + 1):
        for chosen in itertools.combinations(propositions, size):
            for signs in itertools.product((False, True), repeat=size):
                literals = [f"!{p}" if negated else p for p, negated in zip(chosen, signs)]
                connectors = (None,) if size == 1 else ("and", "or")
                for connector in connectors:
                    condition = literals[0] if connector is None else f" {connector} ".join(literals)
                    cost = _condition_cost(condition)
                    if cost <= max_cost and condition not in generated:
                        generated.add(condition)
                        output.append((condition, cost))

    output.sort(key=lambda item: (item[1], item[0]))
    return tuple(output)


def generate_agent_strategies(
    actions: Iterable[str], atomic_propositions: list[str], bound: int
) -> Iterator[Strategy]:
    """Enumerate complete memoryless decision lists with complexity at most bound."""
    sorted_actions = tuple(sorted(set(str(action) for action in actions)))
    if not sorted_actions or bound < 1:
        return

    guards = _conditions(atomic_propositions, bound - 1)

    def prefixes(
        remaining: int,
        used: frozenset[str],
        current: tuple[tuple[str, str], ...],
    ) -> Iterator[tuple[tuple[str, str], ...]]:
        yield current
        for condition, cost in guards:
            if cost > remaining or condition in used:
                continue
            for action in sorted_actions:
                yield from prefixes(
                    remaining - cost,
                    used | {condition},
                    current + ((condition, action),),
                )

    seen: set[tuple[tuple[str, str], ...]] = set()
    for prefix in prefixes(bound - 1, frozenset(), tuple()):
        for default_action in sorted_actions:
            pairs = prefix + (("T", default_action),)
            if pairs not in seen:
                seen.add(pairs)
                yield {"condition_action_pairs": list(pairs)}


def _serialize_assignment(assignment: dict[str, Strategy]) -> dict[str, list[dict[str, str]]]:
    return {
        variable: [
            {"condition": condition, "action": action}
            for condition, action in strategy["condition_action_pairs"]
        ]
        for variable, strategy in assignment.items()
    }


class RestrictedNatSL1GEvaluator:
    def __init__(self, formula: NatSLFormula, model_path: str | Path, mode: str):
        if mode not in {"time", "space"}:
            raise ValueError("mode must be 'time' or 'space'")
        self.formula = formula
        self.model_path = Path(model_path).resolve()
        self.mode = mode
        self.stats = EvaluationStats()

        kinds = "".join(quantifier.kind for quantifier in formula.quantifiers)
        if "AE" in kinds:
            raise ValueError(
                "This restricted NatSL[1G] prototype accepts only a two-block E* A* "
                "prefix; universal-then-existential or repeated alternation is unsupported"
            )

        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        self.cgs = CGS()
        self.cgs.read_file(str(self.model_path))
        self.atomic_propositions = list(map(str, self.cgs.atomic_propositions))
        if formula.goal.proposition not in self.atomic_propositions:
            raise ValueError(
                f"Unknown proposition {formula.goal.proposition!r}; "
                f"model propositions are {self.atomic_propositions}"
            )

        expected_agents = set(range(1, self.cgs.get_number_of_agents() + 1))
        bound_agents = {agent for _, agent in formula.bindings}
        if bound_agents != expected_agents:
            raise ValueError(
                "The executable fragment requires a closed binding prefix covering every "
                f"model agent exactly once; expected {sorted(expected_agents)}, "
                f"got {sorted(bound_agents)}"
            )
        if any(cell == "*" for row in self.cgs.graph for cell in row):
            raise ValueError("Wildcard '*' transitions are not supported by this prototype")

        self.variable_to_agent = dict(formula.bindings)
        self.actions_by_agent = self._validate_and_extract_actions()
        if any(not actions for actions in self.actions_by_agent.values()):
            raise ValueError("Every bound agent must have at least one action in the model")

        self.existential_quantifiers = tuple(q for q in formula.quantifiers if q.kind == "E")
        self.universal_quantifiers = tuple(q for q in formula.quantifiers if q.kind == "A")
        self.materialized_domains: dict[str, tuple[Strategy, ...]] = {}
        if mode == "time":
            for quantifier in formula.quantifiers:
                domain = tuple(self._filtered_domain(quantifier))
                if not domain:
                    raise ValueError(f"Empty admissible strategy domain for {quantifier.variable}")
                self.materialized_domains[quantifier.variable] = domain

    def _validate_and_extract_actions(self) -> dict[int, tuple[str, ...]]:
        number_of_agents = self.cgs.get_number_of_agents()
        action_sets = {agent: set() for agent in range(1, number_of_agents + 1)}
        for row_index, row in enumerate(self.cgs.graph):
            destination_by_joint_action: dict[str, int] = {}
            for destination, cell in enumerate(row):
                if cell == 0:
                    continue
                for joint_action in str(cell).split(","):
                    joint_action = joint_action.strip()
                    if len(joint_action) != number_of_agents:
                        raise ValueError(
                            f"Joint action {joint_action!r} in row {row_index} must contain "
                            "exactly one action symbol per agent"
                        )
                    # A joint action may have multiple successors in a CGS.
                    # NatSL pruning retains every successor compatible with
                    # the selected action, so determinism is not required here.
                    destination_by_joint_action.setdefault(joint_action, destination)
                    for agent, action in enumerate(joint_action, start=1):
                        action_sets[agent].add(action)

            row_joint_actions = set(destination_by_joint_action)
            local_actions = [
                sorted({joint_action[index] for joint_action in row_joint_actions})
                for index in range(number_of_agents)
            ]
            expected_joint_actions = {
                "".join(profile) for profile in itertools.product(*local_actions)
            }
            if row_joint_actions != expected_joint_actions:
                missing = sorted(expected_joint_actions - row_joint_actions)
                raise ValueError(
                    f"Non-total local joint-action table in state "
                    f"{self.cgs.states[row_index]!r}; missing profiles: {missing}"
                )
        return {agent: tuple(sorted(actions)) for agent, actions in action_sets.items()}

    def _raw_domain(self, quantifier: Quantifier) -> Iterator[Strategy]:
        agent = self.variable_to_agent[quantifier.variable]
        return generate_agent_strategies(
            self.actions_by_agent[agent], self.atomic_propositions, quantifier.bound
        )

    def _filtered_domain(self, quantifier: Quantifier) -> Iterator[Strategy]:
        for strategy in self._raw_domain(quantifier):
            if self._apply_assignment({quantifier.variable: strategy}) is not None:
                yield strategy

    def _domain(self, quantifier: Quantifier) -> Iterable[Strategy]:
        if self.mode == "time":
            return self.materialized_domains[quantifier.variable]
        return self._filtered_domain(quantifier)

    def _assignment_product(
        self, quantifiers: Sequence[Quantifier], index: int = 0
    ) -> Iterator[dict[str, Strategy]]:
        if index == len(quantifiers):
            yield {}
            return
        quantifier = quantifiers[index]
        saw_strategy = False
        for strategy in self._domain(quantifier):
            saw_strategy = True
            for suffix in self._assignment_product(quantifiers, index + 1):
                yield {quantifier.variable: strategy, **suffix}
        if not saw_strategy:
            raise ValueError(f"Empty admissible strategy domain for {quantifier.variable}")

    def _apply_assignment(
        self, assignment: dict[str, Strategy], base_graph: list | None = None
    ) -> list | None:
        if not assignment:
            graph = base_graph if base_graph is not None else self.cgs.graph
            return [row.copy() for row in graph]

        cgs_base = CGS()
        cgs_base.read_file(str(self.model_path))
        if base_graph is not None:
            cgs_base.graph = [row.copy() for row in base_graph]

        ordered = sorted(
            (
                (agent, variable)
                for variable, agent in self.formula.bindings
                if variable in assignment
            ),
            key=lambda item: item[0],
        )
        agents = [agent for agent, _ in ordered]
        strategies = [assignment[variable] for _, variable in ordered]
        with redirect_stdout(io.StringIO()):
            graph, _reason = _process_transition_matrix_data_hard(
                cgs_base, str(self.model_path), agents, *strategies
            )
        return graph

    def _check_graph(self, graph: list, unrestricted_opponents: bool) -> bool:
        cgs_work = CGS()
        cgs_work.read_file(str(self.model_path))
        cgs_work.graph = [row.copy() for row in graph]
        cgs_work.invalidate_caches()

        with redirect_stdout(io.StringIO()):
            ctl_result = ctl_model_checking(
                goal_to_ctl(self.formula.goal),
                str(self.model_path),
                preloaded_model=cgs_work,
            )

        if unrestricted_opponents:
            self.stats.unrestricted_opponent_checks += 1
        else:
            self.stats.complete_profile_checks += 1

        return str(
            (ctl_result or {}).get("initial_state", "")
        ).rstrip().endswith("True")

    def _check_bounded_universals(
        self, existential_assignment: dict[str, Strategy], existential_graph: list
    ) -> tuple[bool, dict[str, Strategy]]:
        last_trace = dict(existential_assignment)
        saw_compatible_profile = False
        for universal_assignment in self._assignment_product(self.universal_quantifiers):
            full_graph = self._apply_assignment(universal_assignment, existential_graph)
            if full_graph is None:
                self.stats.incompatible_universal_profiles += 1
                continue
            saw_compatible_profile = True
            self.stats.universal_profiles_checked += 1
            last_trace = {**existential_assignment, **universal_assignment}
            if not self._check_graph(full_graph, unrestricted_opponents=False):
                return False, last_trace
        if not saw_compatible_profile:
            raise ValueError("No compatible bounded universal strategy profile was generated")
        return True, last_trace

    def _space_run(self) -> tuple[bool, dict[str, Strategy]]:
        last_trace: dict[str, Strategy] = {}
        for existential_assignment in self._assignment_product(self.existential_quantifiers):
            self.stats.existential_candidates += 1
            existential_graph = self._apply_assignment(existential_assignment)
            if existential_graph is None:
                self.stats.inadmissible_existential_profiles += 1
                continue
            last_trace = dict(existential_assignment)

            if not self.universal_quantifiers:
                if self._check_graph(existential_graph, unrestricted_opponents=False):
                    return True, last_trace
                continue

            if self._check_graph(existential_graph, unrestricted_opponents=True):
                self.stats.unrestricted_opponent_shortcuts += 1
                return True, last_trace

            all_hold, last_trace = self._check_bounded_universals(
                existential_assignment, existential_graph
            )
            if all_hold:
                return True, last_trace
        return False, last_trace

    def _time_run(self) -> tuple[bool, dict[str, Strategy]]:
        failed_candidates: list[tuple[dict[str, Strategy], list]] = []
        last_trace: dict[str, Strategy] = {}

        # Phase 1: materialized existential generation and unrestricted checks.
        for existential_assignment in self._assignment_product(self.existential_quantifiers):
            self.stats.existential_candidates += 1
            existential_graph = self._apply_assignment(existential_assignment)
            if existential_graph is None:
                self.stats.inadmissible_existential_profiles += 1
                continue
            last_trace = dict(existential_assignment)

            if not self.universal_quantifiers:
                if self._check_graph(existential_graph, unrestricted_opponents=False):
                    return True, last_trace
                continue

            if self._check_graph(existential_graph, unrestricted_opponents=True):
                self.stats.unrestricted_opponent_shortcuts += 1
                return True, last_trace
            failed_candidates.append((dict(existential_assignment), existential_graph))

        # Phase 2: reuse stored existentially-pruned models for bounded opponents.
        for existential_assignment, existential_graph in failed_candidates:
            all_hold, last_trace = self._check_bounded_universals(
                existential_assignment, existential_graph
            )
            if all_hold:
                return True, last_trace
        return False, last_trace

    def run(self) -> dict:
        satisfiable, trace = self._time_run() if self.mode == "time" else self._space_run()
        result = {
            "Satisfiability": satisfiable,
            "Mode": "time-efficient" if self.mode == "time" else "space-efficient",
            "Algorithm": (
                "materialized sequential two-phase evaluation"
                if self.mode == "time"
                else "space-efficient alternating depth-first evaluation"
            ),
            "Supported fragment": "closed Boolean memoryless restricted NatSL[1G], E* A*",
            "Backend reduction": (
                "unrestricted-opponent NatATL/CTL shortcut, followed when necessary "
                "by bounded universal enumeration"
            ),
            "Normalized formula": format_formula(self.formula),
            "CTL goal": goal_to_ctl(self.formula.goal),
            "Existential candidates": self.stats.existential_candidates,
            "Universal profiles checked": self.stats.universal_profiles_checked,
            "Unrestricted-opponent checks": self.stats.unrestricted_opponent_checks,
            "Unrestricted-opponent shortcuts": self.stats.unrestricted_opponent_shortcuts,
            "Complete-profile checks": self.stats.complete_profile_checks,
            "Inadmissible existential profiles": self.stats.inadmissible_existential_profiles,
            "Incompatible universal profiles": self.stats.incompatible_universal_profiles,
            "Decisive assignment": _serialize_assignment(trace),
        }
        if self.mode == "time":
            result["Materialized domain sizes"] = {
                variable: len(domain) for variable, domain in self.materialized_domains.items()
            }
        return result


def model_checking(formula: str, model: str | Path, mode: str = "space") -> dict:
    return RestrictedNatSL1GEvaluator(parse_formula(formula), model, mode).run()
