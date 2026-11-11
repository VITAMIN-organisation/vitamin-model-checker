# Contributing

Use this page when changing `vitamin-model-checker` itself. To add a new logic
as a `vitamin-module-integrator` bundle, start with
[Adding a New Logic](docs/adding_a_new_logic.md). For a large change, open an
[issue](https://github.com/VITAMIN-organisation/vitamin-model-checker/issues)
first.

## Local setup

The project uses [`uv`](https://docs.astral.sh/uv/); `uv.lock` pins the
dependency versions. ATL* needs Spot (see the README).

```bash
uv sync --extra dev --extra docs
```

## Checks

CI runs lint, type check and tests; run the same before opening a PR.

```bash
uv run make lint        # ruff
uv run make typecheck   # basedpyright
uv run pytest model_checker/tests/
```

While working, run a smaller scope such as `uv run pytest
model_checker/tests/unit/` or `model_checker/tests/integration/`.

After a grammar change, run `uv run make generate-parsers` and commit the
regenerated `generated/` files. Add a line under `[Unreleased]` in
`CHANGELOG.md` for each change.

## Docs

```bash
uv run mkdocs serve
uv run mkdocs build --strict
```

When changing docs, check links and keep Mermaid diagrams theme-friendly. Do not
add direct colors with `classDef`, `style`, or `themeVariables`.

## Benchmarks

Benchmarks live in `vitamin-benchmark-model-checker`. Run them when an
algorithm change might affect runtime; they do not replace correctness tests.
From that repository:

```bash
vitamin-benchmark --logic CTL --output before.json
vitamin-benchmark --mode compare --baseline before.json --result after.json
```

## Changes in other VITAMIN repositories

- Update `vitamin-module-integrator` when the bundle format, validation
  contract, or integration behavior changes.
- Update `vitamin-workbench` when HTTP routes, prompts, UI logic, or
  user-facing configuration changes.
- Keep the docs of this repository about Python package behavior and entry
  points.

## Using AI tools

AI tools are allowed. The person who opens a pull request is its author and is
responsible for every line of it.

- Read, run and test everything the tool wrote before you ask for a review.
  You must be able to explain the change and why it is correct in your own
  words; for a logic, that includes the semantics it implements.
- Keep each PR small and on one topic, with no unrelated reformatting. A PR
  should be worth more to the project than the time it takes to review.
- Do not change, skip or delete tests to make them pass.
- Write the PR description yourself: what changed, why, and how you checked
  it.
- State in the PR description which AI tool you used and for what (code,
  tests, docs). Help with grammar, spelling or translation needs no note.
- A person opens every PR and issue and posts every review comment; no agent
  posts on its own. AI may help you review, but post only what you have read
  and agree with.
- Copy no code whose license conflicts with this repository's
  [LICENSE](LICENSE).

PRs that do not follow these rules may be closed without review. These rules
are adapted from the AI policies of
[LLVM](https://llvm.org/docs/AIToolPolicy.html),
[SciPy](https://docs.scipy.org/doc/scipy/dev/conduct/ai_policy.html) and
[CPython](https://devguide.python.org/getting-started/ai-tools/index.html).
How the maintainer uses AI is in [AIUSE.md](AIUSE.md).

## PR checklist

- [ ] Tests cover the changed behavior.
- [ ] `make lint`, `make typecheck` and the tests pass.
- [ ] `CHANGELOG.md` has a line under `[Unreleased]`.
- [ ] Docs are updated when behavior, setup, or public contracts changed.
- [ ] Benchmarks were run for algorithm changes that might affect runtime.
- [ ] Entry points in `pyproject.toml` are updated for new built-in logic.
- [ ] AI use, if any, is stated in the PR description.
