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

Built-in formula logics include ATL, ATLF, ATL_STAR, CapATL, COTL, CTL, IATL,
ICTL, LTL, NatATL, NatATLF, NatSL, OATL, OL, RABATL, RBATL, TCTL, TOL, and
Wallet_ATL. Model
structures include CGS, BCGS, CostCGS, CapCGS, WalletCGS, and timedCGS. See
`pyproject.toml` entry points (`vitamin.parsers`, `vitamin.models`,
`vitamin.benchmarks`) for the full registry.

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
```

Test-suite details live in `model_checker/tests/README.md`.

## Docker

Docker is mainly for isolated build/test checks:

```bash
cd docker
make build
make test
```

See `docker/README.md` for the Docker workflow.

## License

Distributed under the SOURCE-AVAILABLE NON-COMMERCIAL LICENSE. See LICENSE for
the full text. Commercial use requires prior written permission from the
copyright holder.
