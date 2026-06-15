# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.6.0] - 2026-06-15

### Changed

- **Packaging:** Runtime dependencies are declared only in `pyproject.toml`.
  1.6.0 installs only the libraries required by `model_checker`.
- **Python:** Supported versions are Python 3.11 and 3.12 (`requires-python =
  >=3.11`). Earlier metadata claimed broader support than the pinned
  dependencies allow.
- **Metadata:** Added license, Trove classifiers, keywords, and project URLs for
  the PyPI project page.
- **Version reporting:** `model_checker.__version__` reads the installed
  distribution version from package metadata.

### Added

- Logics and entry points for ICTL, IATL, TOL, and TCTL (parsers, metadata, and
  model-checking modules).
- CI checks for wheel/sdist builds, `twine check`, and `mkdocs build --strict`.

### Removed

- `setuptools` as a runtime dependency (it remains a build-time requirement
  only).
