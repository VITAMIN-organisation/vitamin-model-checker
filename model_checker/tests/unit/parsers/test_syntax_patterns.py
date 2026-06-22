"""Central syntax pattern definitions."""

import pytest

from model_checker.parsers.syntax_patterns import (
    NATATL_CAPACITY_RE,
    PROPOSITION_FULL_RE,
    PROPOSITION_TOKEN,
)


@pytest.mark.unit
def test_proposition_pattern_accepts_mixed_case():
    assert PROPOSITION_FULL_RE.match("Goal")
    assert PROPOSITION_FULL_RE.match("safe_1")
    assert not PROPOSITION_FULL_RE.match("1goal")


@pytest.mark.unit
def test_natatl_capacity_pattern_matches_canonical_form():
    match = NATATL_CAPACITY_RE.match("<{1,2}, 5>")
    assert match
    assert match.group(1) == "1,2"
    assert match.group(2) == "5"

