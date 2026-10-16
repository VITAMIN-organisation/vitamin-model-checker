"""Run-local Recall snapshot and caches; no state is attached to the mutable CGS."""
from model_checker.algorithms.explicit.NatATL.Recall.history_automaton import (
    HistoryRegex,
)
from model_checker.parsers.game_structures.cgs.semantic_snapshot import prepare_cgs


class RecallContext:
    def __init__(self, cgs):
        self.snapshot = prepare_cgs(cgs)
        self.monitors = {}
        self.rule_results = {}
        self.stats = {"Regex Compilations": 0, "Appropriateness Checks": 0,
                      "Appropriateness Cache Hits": 0}

    def monitor(self, pattern):
        if pattern not in self.monitors:
            self.monitors[pattern] = HistoryRegex(pattern, self.snapshot.propositions)
            self.stats["Regex Compilations"] += 1
        return self.monitors[pattern]

    def require_idle(self, agents):
        """Supported Recall input contract: fallback IDLE is enabled at every state.

        Validate only the agents quantified by the modality, not its opponents.
        Missing IDLE is an unsupported model, never exhaustive negative evidence.
        """
        for agent in agents:
            if type(agent) is not int or not 1 <= agent <= self.snapshot.number_of_agents:
                raise ValueError("[MODEL] Invalid coalition agent")
            missing = [s for s in self.snapshot.states
                       if "IDLE" not in self.snapshot.enabled[s][agent]]
            if missing:
                raise ValueError(f"[MODEL] Mandatory recall IDLE unavailable for agent {agent} "
                                 f"in states {missing!r}")
