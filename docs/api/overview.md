# Model Checker API

These pages describe the **model_checker** Python package: the library that parses models and formulas and runs the model-checking algorithms. It is the core verification engine.

If you are looking for HTTP routes, request/response shapes, or AI endpoints, refer to the Workbench backend documentation in the `workbench` project.

## Package layout

- **Root**: [model_checker](model_checker.md)
- **Parsers**: [parsers](model_checker.parsers.md), [game_structures](model_checker.parsers.game_structures.md) (CGS, capCGS, costCGS), [formulas](model_checker.parsers.formulas.md) and the per-logic formula parsers (ATL, CTL, LTL, etc.)
- **Engine**: [engine](model_checker.engine.md) - runner and shared boilerplate for running model checks (validation, parser setup, file I/O, error handling)
- **Utils**: [utils](model_checker.utils.md) - error handling and shared helpers used by parsers and algorithms
- **Algorithms**: [algorithms](model_checker.algorithms.md), [algorithms.explicit](model_checker.algorithms.explicit.md) and the per-logic checkers (ATL, CTL, LTL, etc.)

The sidebar under **model checker API** lists all modules.
