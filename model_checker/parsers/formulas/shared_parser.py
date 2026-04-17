"""Shared parser infrastructure for VITAMIN temporal logics.

Provides BaseLogicParser (PLY lex/yacc), common tokens, and hooks for
pre/post validation. Subclasses (ATL, CTL, LTL, etc.) add logic-specific
tokens and grammar rules.
"""

import inspect
import logging
import os
from typing import Any, Optional

import ply.lex as lex
import ply.yacc as yacc

from .common_tokens import COMMON_TOKEN_NAMES
from .parser_utils import run_common_prechecks, verify_token


class BaseLogicParser:
    """Base class for PLY-based formula parsers.

    Subclasses define tokens and grammar rules; parse(formula) returns an AST
    tuple or None on invalid input. Use build() after setting tokens.
    """

    def __init__(self):
        """Initialize logger, token list, and lexer/parser placeholders."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tokens = list(COMMON_TOKEN_NAMES)
        self.lexer = None
        self.parser = None
        self.errors = []

    t_LPAREN = r"\("
    t_RPAREN = r"\)"

    def t_UNTIL(self, t):
        r"U|until\b"
        t.value = "U"
        return t

    def t_GLOBALLY(self, t):
        r"G|globally\b|always\b"
        t.value = "G"
        return t

    def t_NEXT(self, t):
        r"X|next\b"
        t.value = "X"
        return t

    def t_EVENTUALLY(self, t):
        r"F|eventually\b"
        t.value = "F"
        return t

    def t_FALSE(self, t):
        r"false\b"
        return t

    def t_TRUE(self, t):
        r"true\b"
        return t

    def t_AND(self, t):
        # Canonical: &&. Aliases: &, word and
        r"&&|\&|and\b"
        return t

    def t_OR(self, t):
        # Canonical: ||. Aliases: single |, word or
        r"\|\||\||or\b"
        return t

    def t_NOT(self, t):
        # Canonical: !. Alias: word not
        r"!|not\b"
        return t

    def t_IMPLIES(self, t):
        # Canonical: ->. Aliases: >, word implies
        r"->|>|implies\b"
        return t

    t_ignore = " \t"

    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        """Error handling for illegal characters."""
        err_msg = f"Invalid character '{t.value[0]}' at position {t.lexpos + 1}"
        self.logger.debug(err_msg)
        self.errors.append(err_msg)
        t.lexer.skip(1)

    precedence = (
        ("right", "IMPLIES"),
        ("left", "OR"),
        ("left", "AND"),
        ("right", "NOT"),
        ("right", "UNTIL"),
        ("right", "GLOBALLY", "NEXT", "EVENTUALLY"),
    )

    def p_expression_binary(self, p):
        """expression : expression AND expression
        | expression OR expression
        | expression IMPLIES expression"""
        p[0] = (p[2], p[1], p[3])

    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = (p[1], p[2])

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]

    def p_expression_boolean(self, p):
        """expression : FALSE
        | TRUE"""
        p[0] = p[1]

    def p_expression_prop(self, p):
        """expression : PROP"""
        p[0] = p[1]

    def p_error(self, p):
        """Syntax error handler."""
        if p:
            err_msg = f"Syntax error near token '{p.value}' at position {getattr(p, 'lexpos', '?') + 1}"
            self.logger.debug(err_msg)
            self.errors.append(err_msg)
        else:
            err_msg = "Syntax error at end of input"
            self.logger.debug(err_msg)
            self.errors.append(err_msg)

    def build(self, **kwargs):
        """Build the lexer and parser.

        Reuses existing parser tables when available to avoid regeneration.
        PLY errorlog is set to NullLogger by default to suppress benign
        token/grammar warnings (unused tokens, multiply defined, unreachable).
        """
        parser_file = inspect.getfile(self.__class__)
        parser_dir = os.path.dirname(parser_file)
        generated_dir = os.path.join(parser_dir, "generated")
        os.makedirs(generated_dir, exist_ok=True)

        lex_kwargs = {k: v for k, v in kwargs.items() if k != "start"}
        if "errorlog" not in lex_kwargs:
            lex_kwargs["errorlog"] = lex.NullLogger()
        self.lexer = lex.lex(module=self, **lex_kwargs)

        parser_kwargs = {
            "debug": False,
            "write_tables": True,
            "optimize": True,
            "outputdir": generated_dir,
            **kwargs,
        }
        if "errorlog" not in parser_kwargs:
            parser_kwargs["errorlog"] = yacc.NullLogger()
        self.parser = yacc.yacc(module=self, **parser_kwargs)

    def parse(self, formula: str, **kwargs: Any) -> Any:
        """Parse a formula string into an AST or return None if invalid.

        Args:
            formula: Formula string to parse.
            **kwargs: Passed to the PLY parser.

        Returns:
            AST tuple on success, or None if pre-validation fails, parse fails,
            or post-validation fails. Specific errors are available in self.errors.
        """
        self.errors = []
        valid, err = self._pre_validation(formula)
        if not valid:
            if err:
                self.errors.append(err)
            return None

        try:
            self.lexer.input(formula)
            result = self.parser.parse(formula, lexer=self.lexer)

            if not self._post_validation(formula, result):
                # errors might already be populated by p_error or t_error
                return None

            if self.errors:
                return None

            return result
        except Exception as e:
            self.logger.debug(f"Parsing failed: {e}")
            if not self.errors:
                self.errors.append(str(e))
            return None

    def _pre_validation(self, formula) -> tuple[bool, Optional[str]]:
        """Hook for pre-parsing validation."""
        return run_common_prechecks(formula)

    def _post_validation(self, formula, result):
        """Hook for post-parsing validation."""
        return result is not None

    def verify(self, token_name, string):
        """Verify if a token exists in the string using the lexer."""
        return verify_token(self.lexer, token_name, string)
