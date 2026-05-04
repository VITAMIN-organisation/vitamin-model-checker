# Python API Overview

These pages document the `model_checker` Python package: parsers, algorithms,
engine helpers, utilities, and benchmark support.

This is not the Workbench HTTP API and not the VMI backend API.

| API surface | Where it lives | What it is for |
|---|---|---|
| Python package API | `vitamin-model-checker` | Import parsers, run model checking, test algorithms, benchmark logic. |
| Integration API | `vitamin-module-integrator` | Upload, validate, integrate, remove, and verify logic bundles. |
| HTTP/user API | `vitamin-workbench` | User-facing application and backend routes. |

## Package Layout

- [Root](model_checker.md)
- [Algorithms](model_checker.algorithms.md)
- [Explicit algorithms](model_checker.algorithms.explicit.md)
- [Parsers](model_checker.parsers.md)
- [Game structures](model_checker.parsers.game_structures.md)
- [Formula parsers](model_checker.parsers.formulas.md)
- [Engine](model_checker.engine.md)
- [Utils](model_checker.utils.md)

The sidebar lists the main generated API pages. Some deeper per-module pages are
generated for direct linking from search or source references.

## Common Public Shape

Most logic entry modules expose:

```python
model_checking(formula: str, filename: str) -> dict
```

The result is a plain dict so host projects can serialize and display it without
depending on internal Python classes.
