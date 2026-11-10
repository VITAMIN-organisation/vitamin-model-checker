"""Without Spot (no win-64 build exists), every Spot-backed entry point raises ImportError instead of failing later."""

import importlib

import pytest

spot = pytest.importorskip("spot")

from model_checker.automata.automaton import Automaton
from model_checker.automata.games.game import Game
from model_checker.automata.games.solver import solve
from model_checker.automata.product import product
from model_checker.automata.transition_system import TransitionSystem


def _loop():
    ts = TransitionSystem()
    ts.add_transition("s0", "a", "s0")
    ts.add_state("s0", initial=True)
    return ts


# importlib, because `model_checker.automata.product` as an attribute is the function, not the module.
@pytest.mark.parametrize(
    ("module", "call"),
    [
        (
            "model_checker.automata.automaton",
            lambda: Automaton(graph=object()).acceptance_condition(),
        ),
        ("model_checker.automata.automaton", lambda: Automaton.from_ltl("GFa")),
        (
            "model_checker.automata.product",
            lambda: product(Automaton(graph=object()), _loop()),
        ),
        (
            "model_checker.automata.games.solver",
            lambda: solve(Game(arena=_loop(), player_states={0: {"s0"}, 1: set()})),
        ),
    ],
    ids=["acceptance_condition", "from_ltl", "product", "solve"],
)
def test_entry_point_without_spot_raises_import_error(monkeypatch, module, call):
    """The module's `spot` handle is None when the import failed at load time."""
    monkeypatch.setattr(importlib.import_module(module), "spot", None)
    with pytest.raises(ImportError):
        call()
