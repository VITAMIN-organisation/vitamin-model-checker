"""Unit tests for ICTL formula lexer and parser."""

import pytest

from model_checker.parsers.formulas.ICTL.ictl_ply_parser import do_parsingICTL


@pytest.mark.unit
class TestIctlParser:
    def test_parses_classic_lowercase_atoms(self):
        assert do_parsingICTL("EX e") is not None
        assert do_parsingICTL("AG (p -> EF q)") is not None

    def test_parses_mixed_case_atoms(self):
        assert do_parsingICTL("AG Goal") is not None
        assert do_parsingICTL("EF safe_1") is not None

    def test_rejects_operator_like_atom_tokens(self):
        assert do_parsingICTL("AG EX") is None

    def test_rejects_invalid_atom_tokens(self):
        assert do_parsingICTL("AG 1goal") is None
