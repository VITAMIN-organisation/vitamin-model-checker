"""Shared atomic proposition identifier validation."""

import pytest

from model_checker.parsers.formulas.parser_utils import (
    validate_natsl_temporal_atom,
    validate_proposition_identifier,
)


@pytest.mark.unit
@pytest.mark.parametrize("name", ["p", "Goal", "safe_1", "win"])
def test_validate_proposition_identifier_accepts_standard_names(name):
    valid, err = validate_proposition_identifier(name)
    assert valid is True
    assert err is None


@pytest.mark.unit
@pytest.mark.parametrize("name", ["1goal", "forall", "exist"])
def test_validate_proposition_identifier_rejects_invalid_names(name):
    valid, err = validate_proposition_identifier(name)
    assert valid is False
    assert err is not None


@pytest.mark.unit
def test_validate_natsl_temporal_atom_rejects_quantifier_tokens():
    for atom in ("E", "A"):
        valid, err = validate_natsl_temporal_atom(atom)
        assert valid is False
        assert "quantifier token" in err


@pytest.mark.unit
def test_validate_natsl_temporal_atom_accepts_model_names():
    valid, err = validate_natsl_temporal_atom("Goal")
    assert valid is True
    assert err is None
