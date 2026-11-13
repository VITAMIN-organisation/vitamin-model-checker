# NatATLF algorithm

The NatATLF checker accepts the [NatATL](natatl.md) formulas, `<{A}, k> phi`, on
a `CGS` model, and runs the memoryless NatATL algorithm unchanged: the same
strategies, search, pruning and CTL check, with Boolean results. Its result has
the same fields as NatATL's. Formula syntax is in the
[knowledge base](../reference/logic_knowledge_base.md#syntax-cards).

NatATLF has no semantics over labels between 0 and 1: it reads a `CGS`, whose
labels are 0 or 1, and not the [fuzzyCGS](../reference/file_formats.md#fuzzycgs-sections)
that [ATLF](atlf.md) reads. A label such as `0.7` is an error when the model is
loaded.
