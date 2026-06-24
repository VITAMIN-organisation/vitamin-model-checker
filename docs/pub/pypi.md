# Publishing to PyPI

Manual upload steps for maintainers. PyPI does not accept uploads through the
website UI; use `twine` or a GitHub Actions workflow with trusted publishing.

## Before you upload

1. Bump `version` in `pyproject.toml` (versions on PyPI are immutable).
2. Update `CHANGELOG.md`.
3. Commit, tag (`vX.Y.Z`), and push the tag.
4. Create a GitHub release for the tag (optional but recommended).

Run tests and packaging checks:

```bash
make test
make lint
python -m build
twine check dist/*
```

## 1. Create a PyPI API token

1. Log in at https://pypi.org
2. Open **Account settings** -> **API tokens** -> **Add API token**
3. Scope: **Project: vitamin-model-checker** (or entire account)
4. Copy the token (`pypi-...`). It is shown only once.

## 2. Configure credentials

Create or edit `~/.pypirc` (mode `600`):

```ini
[distutils]
index-servers =
    pypi

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-PASTE_YOUR_TOKEN_HERE
```

- **Username** must be `__token__`, not your PyPI login email.
- **Password** is the full token, including the `pypi-` prefix.
- Do not commit this file or put tokens in the repository.

Alternative for a one-off upload:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-PASTE_YOUR_TOKEN_HERE
```

## 3. Build and upload

From the repository root (replace `1.6.0` with your release version):

```bash
cd vitamin-model-checker
python -m pip install --upgrade build twine
python -m build
twine check dist/vitamin_model_checker-1.6.0*
twine upload dist/vitamin_model_checker-1.6.0*
```

`twine upload` reads `~/.pypirc` when `TWINE_*` variables are not set.

## 4. Verify

```bash
pip install --upgrade vitamin-model-checker==1.6.0
python -c "import model_checker; print(model_checker.__version__)"
```

Check the project page: https://pypi.org/project/vitamin-model-checker/

## Trusted publishing (optional)

For automated uploads on GitHub release, configure a trusted publisher on the
project **Publishing** settings:

| Field | Value |
|-------|--------|
| PyPI project name | `vitamin-model-checker` |
| Owner | `VITAMIN-organisation` |
| Repository | `vitamin-model-checker` |
| Workflow name | `publish.yml` |
| Environment | `pypi` (optional) |

The workflow file must exist at `.github/workflows/publish.yml` on `main`, and a
GitHub environment named `pypi` must be created if you set the environment
field. Publishing a GitHub release then triggers the upload.

Manual `twine upload` (above) does not require trusted publishing.

## Common errors

| Error | What to do |
|-------|------------|
| `403 Invalid or non-existent authentication` | Username is `__token__`; password is the full API token |
| `403 ... not allowed to upload` | Token scope must include `vitamin-model-checker`; account must be a maintainer |
| `File already exists` | That version is already on PyPI; bump the version in `pyproject.toml` |
| Trusted publish fails | Ensure `publish.yml` exists and matches the PyPI publisher settings |

## Security

- Revoke leaked tokens on PyPI immediately.
- Never commit API tokens, `.pypirc`, or secrets to git.
