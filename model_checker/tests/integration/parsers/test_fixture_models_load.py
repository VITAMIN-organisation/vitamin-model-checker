"""Every valid model file in the test fixtures loads with the parser the factory picks.

A parser change that breaks a fixture would otherwise show up only as an odd
failure in some logic's test; this names the file.
"""

import warnings
from pathlib import Path

import pytest

from model_checker.models.model_factory import create_model_parser

_TESTS = Path(__file__).resolve().parents[2]
# fixtures/tests/ holds the deliberately broken files.
_BROKEN = _TESTS / "fixtures" / "tests"
_FIXTURES = sorted(
    [p for p in (_TESTS / "fixtures").rglob("*.txt") if not p.is_relative_to(_BROKEN)]
    + list((_TESTS / "integration").rglob("fixtures/*.txt"))
)


@pytest.mark.integration
def test_fixture_folder_is_not_empty():
    """Guards the glob: an empty list would make the next test pass vacuously."""
    assert len(_FIXTURES) >= 20


@pytest.mark.integration
@pytest.mark.parametrize("path", _FIXTURES, ids=lambda p: str(p.relative_to(_TESTS)))
def test_fixture_loads_and_its_initial_state_is_a_state(path):
    """The file parses, passes structure validation, and its initial state is listed."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = create_model_parser(str(path))
        model.read_file(str(path))
    assert model.initial_state in list(model.states)
