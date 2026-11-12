# ATL* algorithm

The ATL* checker decides `<<A>> psi` where `psi` is any path formula, such as
`<<1>> (F p && G q)`, on a `CGS` model. Unlike the other checkers it does not
iterate a pre-image: it turns each coalition formula into a two-player game and
solves the game with the Spot automata library. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#atl-star), the model file in
[CGS sections](../reference/file_formats.md#cgs-sections).

## Overview

The formula is evaluated from the innermost subformula outward into sets of
states. Atoms, `true`, `!` and `&&` are the usual set operations; a temporal
operator outside a coalition is an error ("a bare ... is not a state formula;
temporal operators need a <<...>> coalition around them"). Each coalition
formula `<<A>> psi` is solved for all states at once in four steps:

1. Every coalition nested inside `psi` is solved first, and replaced by a fresh
   atom that labels the states where it holds. What is left of `psi` uses only
   atoms, `!`, `&&`, `X` and `U`.
2. `psi` is translated into a deterministic parity automaton.
3. The automaton is combined with the model into a turn-based game: from each
   state, the coalition first picks its part of the joint action, then the other
   agents pick theirs, and the automaton follows the state reached.
4. The parity game is solved. A state satisfies `<<A>> psi` when the coalition
   wins the game that starts there with the automaton in its initial state.

A cell `*` in the model becomes a self-loop on every action the model uses
elsewhere and the state does not already list. The result has the usual `res` and
`initial_state` fields (see the
[shared steps](index.md#steps-shared-by-the-set-based-checkers)).

## Strategy synthesis

A separate entry point returns the coalition's winning strategy for a formula
whose outermost part is one coalition with no coalition nested inside. When the
formula fails at the chosen state, it returns `Result: the formula does not hold
at state s0, no strategy to synthesize` and no strategy.

## Requires Spot

The Spot team publishes no official PyPI wheel. On Linux, the community
[`spottl`](https://pypi.org/project/spottl/) package gives one (it imports as
`spot`) and is installed as a regular dependency of `vitamin-model-checker`:

```bash
pip install vitamin-model-checker
```

On macOS, or to pin an exact Spot version, use conda-forge instead:

```bash
conda install -c conda-forge spot
```

Neither has a Windows build; use WSL there. The other checkers work without
Spot; ATL* then returns an error of type `environment` instead of a result.
