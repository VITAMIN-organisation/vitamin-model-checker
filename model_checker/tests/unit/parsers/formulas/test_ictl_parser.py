"""Unit tests for ICTL formula lexer and parser."""

import pytest

from model_checker.parsers.formula_parser_factory import FormulaParserFactory


@pytest.mark.unit
class TestIctlParser:
    def test_parses_classic_lowercase_atoms(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("EX e") == ("EX", "e")
        assert parser.parse("AG (p -> EF q)") == ("AG", ("->", "p", ("EF", "q")))

    def test_parses_mixed_case_atoms(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("AG Goal") == ("AG", "Goal")
        assert parser.parse("EF safe_1") == ("EF", "safe_1")

    def test_rejects_operator_like_atom_tokens(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("AG EX") is None

    def test_rejects_leading_digits_in_atoms(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("AG 1goal") is None

    @pytest.mark.parametrize(
        ("flat", "grouped", "bracketed", "tree"),
        [
            ("A p U q", "A(p U q)", "A[p U q]", ("AU", "p", "q")),
            ("E p U q", "E(p U q)", "E[p U q]", ("EU", "p", "q")),
            ("A p R q", "A(p R q)", "A[p R q]", ("AR", "p", "q")),
            ("E p R q", "E(p R q)", "E[p R q]", ("ER", "p", "q")),
        ],
    )
    def test_path_quantifier_over_until_or_release_has_three_written_forms(
        self, flat, grouped, bracketed, tree
    ):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse(flat) == tree
        assert parser.parse(grouped) == tree
        assert parser.parse(bracketed) == tree

    def test_grouped_until_keeps_a_parenthesized_operand(self):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse("A((p && q) U r)") == ("AU", ("&&", "p", "q"), "r")

    @pytest.mark.parametrize("formula", ["A(p U)", "A[p U q)", "A(p U q]", "A[p U"])
    def test_rejects_an_unclosed_or_mismatched_until(self, formula):
        parser = FormulaParserFactory.get_parser_instance("ICTL")
        assert parser.parse(formula) is None
