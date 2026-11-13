# VITAMIN Model Checker

Core Python library for model checking multi-agent systems: given a model of
agents that act together and a formula, it says whether the formula holds in
the initial state and, for most logics, in which states it holds. It covers CTL, ATL, LTL and the other logics in
[Supported logics](#supported-logics), with algorithms that work on the whole
model in memory and visit its states directly (explicit-state).

The base model type is the concurrent game structure
([CGS](docs/reference/file_formats.md#cgs-sections)): states, agents, the joint
actions that move between states, and the propositions true in each state. Most
other model types add sections to it.

It needs Python 3.11 or later.

## Install

```bash
pip install vitamin-model-checker
```

Development install from a checkout, with [`uv`](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev --extra docs
```

ATL* and the vendored automata library (`model_checker/automata/`) need the
Spot automata library. On Linux, both install commands above also install `spottl`;
on macOS use conda-forge (details in
[Requires Spot](docs/algorithms/atl_star.md#requires-spot)). Other logics do
not require Spot.

## Quick start

From the repository root of a checkout, this checks the CTL formula `EF q` (some
path reaches a state where `q` holds) on a 4-state test model (format in
[file formats](docs/reference/file_formats.md)):

```python
from model_checker.algorithms.explicit.CTL.CTL import model_checking

result = model_checking("EF q", "model_checker/tests/fixtures/CGS/CTL/ctl_1agent_4states.txt")
print(result)
```

It prints a dict: `res` lists the states where the formula holds,
`initial_state` says whether the model's initial state is one of them, and
`formula` and `model` echo the input:

```text
{'res': "Result: ('s0', 's1', 's2', 's3')", 'initial_state': 'Initial state s0: True', 'formula': 'EF q', 'model': 'model_checker/tests/fixtures/CGS/CTL/ctl_1agent_4states.txt'}
```

Most logics expose the same `model_checking(formula, filename)` entry point and
return a plain dict suitable for serialization. The exceptions, and the shared
pipeline `execute_model_checking_with_parser` that the package also exports,
are in [Engine layer](docs/guides/architecture.md#engine-layer).

## Supported logics

The 19 built-in logics are ATL, ATLF, ATL_STAR, CapATL, COTL, CTL, IATL, ICTL,
LTL, NatATL, NatATLF, NatSL, OATL, OL, RABATL, RBATL, TCTL, TOL and Wallet_ATL;
`NatATL_Recall` is a variant of NatATL with its own entry. Each logic has a page
in [docs/algorithms/](docs/algorithms/index.md). The model types, the logics
that use each and their file layout are in
[Supported model types](docs/reference/file_formats.md#supported-model-types).
The `pyproject.toml` entry points (`vitamin.parsers`, `vitamin.models`,
`vitamin.benchmarks`, `vitamin.metadata`) hold the full registry.

## Related projects

Table 1 lists the projects around this library.

**Table 1: The VITAMIN projects.**

| Project | Role |
| :--- | :--- |
| `vitamin-model-checker` | Core Python library. |
| `vitamin-benchmark-model-checker` | pyperf benchmark tool for this package. |
| `vitamin-module-integrator` | Validates logic bundles and applies them to this repo. |
| `vitamin-workbench` | User-facing web/API application that calls the model checker. |

Links:

- Homepage: https://github.com/VITAMIN-organisation/vitamin-model-checker
- PyPI: https://pypi.org/project/vitamin-model-checker/
- Issues: https://github.com/VITAMIN-organisation/vitamin-model-checker/issues

## Run tests

```bash
uv run pytest model_checker/tests/
```

Test-suite details live in
[model_checker/tests/README.md](model_checker/tests/README.md).

## Docker

The Docker setup gives a clean Python 3.11 environment for building and testing
the library:

```bash
cd docker
make build
make test
```

See [docker/README.md](docker/README.md) for the Docker workflow.

## Contributing and AI usage

The rules for using AI tools in a contribution are in
[CONTRIBUTING.md](CONTRIBUTING.md). How the maintainer used AI tools is in
[AIUSE.md](AIUSE.md). The people who have contributed are listed in
[CONTRIBUTORS.md](CONTRIBUTORS.md).

## License

Distributed under the SOURCE-AVAILABLE NON-COMMERCIAL LICENSE. See
[LICENSE](LICENSE) for the full text. Commercial use requires prior written permission from the
copyright holder. The vendored automata library in `model_checker/automata/` is
under the MIT License instead; see
[model_checker/automata/NOTICE.md](model_checker/automata/NOTICE.md).
