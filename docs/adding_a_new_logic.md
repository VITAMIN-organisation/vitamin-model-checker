# Adding a New Logic

The recommended way to add a new logic is to build a
`vitamin-module-integrator` bundle, validate it there, and let VMI apply the
files and entry points to this repository.

Manual changes in this repo are still useful for maintainers changing built-in
logics or core contracts. Keep those changes small and test them directly in
`model_checker/tests/`.

## Recommended Path: VMI Bundle

```mermaid
flowchart LR
    source["New logic source"]
    bundle["VMI bundle"]
    validate["VMI validation"]
    integrate["VMI integration"]
    target["vitamin-model-checker"]
    tests["VMC tests and benchmarks"]

    source --> bundle --> validate --> integrate --> target --> tests
```

Use this path when the logic is meant to be packaged and integrated as a module.
VMI checks the manifest, folder layout, parser/checker contracts, dependencies,
collisions, example execution, and post-integration runtime behavior.

At a high level, the bundle provides:

- a parser package under `parsers/formulas/<LogicName>/`, unless it reuses an
  existing parser,
- an algorithm package under `algorithms/explicit/<LogicName>/`,
- optional game-structure code under `parsers/game_structures/<name>/`,
- examples and tests,
- `vitamin_module.yaml` describing the logic, parser, checker, model type,
  dependencies, examples, tests, and optional extra paths.

After integration, VMI patches this repository's `pyproject.toml` entry points,
copies files into the right package locations, updates managed metadata, and
runs post-integration verification.

## What The Checker Must Return

Every public checker function should return a plain dict.

Success responses should include:

- `res`: the satisfying state set as a string,
- `initial_state`: whether the initial state satisfies the formula.

Error responses should include:

- `error`: a clear message or structured error payload.

Use the existing helpers instead of inventing a result shape:

- `format_model_checking_result`
- `verify_initial_state`
- `model_checker.utils.error_handler`

Good references are the ATL, OATL, CTL, and COTL implementations.

## Parser Choices

### New Formula Parser

Add a parser package under:

```text
model_checker/parsers/formulas/<LogicName>/
```

The parser class should follow the shape of existing parser classes and be
registered through `pyproject.toml` entry points after integration:

```toml
[project.entry-points."vitamin.parsers"]
MyLogic = "model_checker.parsers.formulas.MyLogic.parser:MyLogicParser"
```

### Reuse An Existing Parser

If your logic uses the same formula syntax as another logic, reuse that parser.
For example, COTL uses the OATL parser:

```toml
[project.entry-points."vitamin.parsers"]
COTL = "model_checker.parsers.formulas.OATL.parser:OATLParser"
```

This is the preferred approach when syntax is genuinely shared. Do not copy a
parser only to change the logic name.

## Algorithm Shape

Add the algorithm under:

```text
model_checker/algorithms/explicit/<LogicName>/
```

Expose:

```python
def model_checking(formula: str, filename: str) -> dict:
    ...
```

Inside the public function, call:

```python
execute_model_checking_with_parser(
    formula,
    filename,
    "<LogicName>",
    _core_my_logic_checking,
)
```

The core function receives the parsed model object and the formula. It should:

1. get the parser through `FormulaParserFactory`,
2. parse the formula,
3. evaluate the formula over the model,
4. format the result through shared helpers,
5. return error dicts through `model_checker.utils.error_handler` helpers.

Avoid global model state. The model for each run is the object passed by the
engine runner.

## Model Type Mapping

If your logic uses an existing model type, map it to the right parser behavior:

- `CGS`
- `costCGS`
- `capCGS`

For built-in manual changes, update `model_checker/parsers/model_parser_factory.py`
where the existing logic-to-model-type sets are maintained.

If the logic needs a new game structure, add the parser package under:

```text
model_checker/parsers/game_structures/<name>/
```

Then register the model type through entry points:

```toml
[project.entry-points."vitamin.models"]
MyModelType = "model_checker.parsers.game_structures.my_model.my_model:MyModel"
```

VMI can copy and register custom game-structure files when the bundle manifest
declares them.

## Entry Points

This repository uses Python entry points as the package-level integration
contract.

| Group | Required when |
|---|---|
| `vitamin.parsers` | The logic has or reuses a formula parser. |
| `vitamin.benchmarks` | The logic should be callable by benchmark tooling. |
| `vitamin.metadata` | The logic exposes parser/package metadata. |
| `vitamin.models` | A new game-structure model type is added. |

For VMI bundles, the integrator updates these entries during integration. For
manual maintainer changes, update `pyproject.toml` directly and run the tests.

## Tests And Examples

Add tests under `model_checker/tests/`:

- parser unit tests for new syntax,
- algorithm unit tests for tricky helper behavior,
- integration tests under `integration/algorithms/<logic>/`,
- interface tests if the public cross-logic behavior changes,
- performance tests only when runtime behavior needs a guard.

Add examples under the repo-root `examples/` directory when the logic should be
visible to demo flows:

```text
examples/<model_type>/<LogicName>/
├── my_model.txt
└── my_model_formula.txt
```

The formula file can contain multiple semicolon-terminated formulas.

## COTL Example

COTL is a useful example because it reuses OATL syntax and runs over `costCGS`.

What it needs:

1. no new parser, because `COTL` maps to `OATLParser`,
2. `COTL` listed as cost-based in `model_parser_factory.py`,
3. an algorithm module under `algorithms/explicit/COTL/`,
4. entry points for parser, benchmark callable, and metadata,
5. integration tests and example costCGS models.

The important lesson is that parser reuse should be explicit. If syntax is the
same, register the existing parser and keep algorithm behavior separate.

## Advanced Manual Checklist

Use this checklist when you are maintaining this repository directly:

- [ ] Add or reuse a parser under `model_checker/parsers/formulas/`.
- [ ] Add the algorithm under `model_checker/algorithms/explicit/`.
- [ ] Expose `model_checking(formula, filename) -> dict`.
- [ ] Use `execute_model_checking_with_parser(...)`.
- [ ] Update model type mapping if needed.
- [ ] Add or update `pyproject.toml` entry points.
- [ ] Add tests under `model_checker/tests/`.
- [ ] Add examples if the logic should appear in demo flows.
- [ ] Run `pytest model_checker/tests/`.
- [ ] Run benchmarks if the change can affect performance.

## Workbench Notes

Workbench-specific logic descriptions, HTTP request schemas, prompts, and UI
behavior live in the sibling `vitamin-workbench` repository. Do not document
Workbench paths as if they live in this repo.

If a logic needs Workbench support, update this repository first, then make the
corresponding Workbench change in that project.
