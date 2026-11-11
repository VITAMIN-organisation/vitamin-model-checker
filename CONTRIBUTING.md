# Contributing

Setup and tests are in the [README](README.md). This page sets the rules for
using AI tools in a contribution.

## Using AI tools

AI tools are allowed. The person who opens a pull request is its author and is
responsible for every line of it.

- Read, run and test everything the tool wrote before you ask for a review.
  You must be able to explain the change and why it is correct in your own
  words; for a logic, that includes the semantics it implements.
- Keep each PR small and on one topic, with no unrelated reformatting; for a
  large change, open an issue first. A PR should be worth more to the project
  than the time it takes to review.
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
