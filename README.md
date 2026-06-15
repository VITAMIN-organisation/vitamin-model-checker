# VITAMIN Model Checker

Core Python library for model checking multi-agent systems. It provides formula
parsers, game-structure parsers, and explicit-state algorithms for CTL, ATL, LTL,
and many extensions.

**Requirements:** Python 3.11+

## Install

```bash
pip install vitamin-model-checker
```

Development install from a checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
```

## Quick start

```python
from model_checker.algorithms.explicit.CTL.CTL import model_checking

result = model_checking("AG p", "path/to/model.txt")
print(result)
```

Most logics expose the same `model_checking(formula, filename)` entry point and
return a plain dict suitable for serialization.

Higher-level helpers are available from the public API:

```python
from model_checker import FormulaParserFactory, execute_model_checking_with_parser

parser = FormulaParserFactory.get_parser("CTL")
# execute_model_checking_with_parser(...) for integrated workflows
```

### Supported logics

Built-in formula logics include ATL, ATLF, CapATL, CTL, IATL, ICTL, LTL, NatATL,
NatATLF, NatSL, OATL, OL, RABATL, RBATL, TCTL, TOL, and Wallet_ATL. Model
structures include CGS, BCGS, CostCGS, CapCGS, WalletCGS, and timedCGS. See
`pyproject.toml` entry points (`vitamin.parsers`, `vitamin.models`,
`vitamin.benchmarks`) for the full registry.

## Documentation

- Repository docs: [docs/index.md](docs/index.md)
- Architecture, file formats, and logic guides live under `docs/`
- API reference pages are generated with MkDocs (`pip install -e ".[docs]"` then
  `mkdocs serve`)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

## Repository role

| Project | Role |
|---|---|
| `vitamin-model-checker` | Core Python library. |
| `vitamin-benchmark-model-checker` | pyperf benchmark tool for this package. |
| `vitamin-module-integrator` | Validates logic bundles and applies them to this repo. |
| `vitamin-workbench` | User-facing web/API application that calls the model checker. |

For the cross-project view, see [docs/vitamin-stack.md](docs/vitamin-stack.md).

Links:

- Homepage: https://github.com/VITAMIN-organisation/vitamin-model-checker
- PyPI: https://pypi.org/project/vitamin-model-checker/
- Issues: https://github.com/VITAMIN-organisation/vitamin-model-checker/issues

## Run tests

```bash
pytest model_checker/tests/unit/
pytest model_checker/tests/integration/
pytest model_checker/tests/

make test          # unit + integration style suite, excluding slow tests
make test-models   # full model_checker/tests suite
```

Test-suite details live in `model_checker/tests/README.md`.

## Build docs

```bash
pip install -e ".[docs]"
mkdocs serve
mkdocs build --strict
```

## Benchmarks

Benchmark this package with `vitamin-benchmark-model-checker`, a separate pip
package that times `model_checking()` across logics via the `vitamin.benchmarks`
entry points declared here.

```bash
pip install vitamin-benchmark-model-checker
vitamin-benchmark --logic CTL --output ctl.json
```

For local development with a checkout of both repos:

```bash
pip install -e .
pip install -e ../vitamin-benchmark-model-checker
```

See the `vitamin-benchmark-model-checker` README for compare mode, plots, and
the full benchmark matrix.

## Docker

Docker is mainly for isolated build/test checks:

```bash
cd docker
make build
make test
```

See `docker/README.md` for the Docker workflow.

## Adding logic

The recommended path is to package a new logic as a VMI bundle, validate it with
`vitamin-module-integrator`, and let the integrator apply the files and entry
points to this repository.

Manual in-repo changes are still useful for maintainers working directly on the
core package. See `docs/adding_a_new_logic.md` for both workflows.

## License

Distributed under the SOURCE-AVAILABLE NON-COMMERCIAL LICENSE. See [LICENSE](LICENSE)
for the full text. Commercial use requires prior written permission from the
copyright holder.
