# NatATLF algorithm

The NatATLF checker accepts the [NatATL](natatl.md) formulas, `<{A}, k> phi`, on
a `CGS` model, and runs the memoryless NatATL algorithm unchanged: the same
strategies, search, pruning and CTL check, with Boolean results. Its result has
the same fields as NatATL's. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#syntax-cards).

NatATLF has no semantics over labels between 0 and 1: it reads a `CGS`, whose
labels are 0 or 1, and not the [fuzzyCGS](../reference/file_formats.md#fuzzycgs-sections)
that [ATLF](atlf.md) reads. A label such as `0.7` is an error when the model is
loaded, with a message that names the value, row and column and ends "Labels
between 0 and 1 need a fuzzyCGS model." The Boolean checkers test a label for
equality with 1, so without this check a fractional label would read as false
with no message. That is what the CGS loader and NatATL of the original VITAMIN
repository (commit e8ea8773) did; NatATLF itself was not reachable there.

## Relation to HumanATL[F]

NatATLF is NatATL on labels 0 and 1. It is not the HumanATL[F] logic of Aruta,
Improta, Malvone and Murano, "When Natural Strategies Meet Fuzziness and
Resource-Bounded Actions" (AAAI 2026). That logic gives each proposition a
weight between 0 and 1 in each state (Def. 1, p. 3), and in its words "each
action carries a real-valued cost drawn from a non-refillable budget" and "atomic
conditions and goals have degrees in [0,1]" (abstract, p. 1). This checker has no
weights, costs or budgets. The paper's own code is the separate repository
[HumanATLFTool](https://github.com/MarcoAruta/HumanATLFTool) (p. 1).
