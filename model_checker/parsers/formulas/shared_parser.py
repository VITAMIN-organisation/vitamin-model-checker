"""Shared parser infrastructure for VITAMIN temporal logics.

Provides BaseLogicParser (PLY lex/yacc), common tokens, and hooks for
pre/post validation. Subclasses (ATL, CTL, LTL, etc.) add logic-specific
tokens and grammar rules.
"""

import inspect
import logging
import os
import sys
from typing import Any

import ply.lex as lex
import ply.yacc as yacc

from model_checker.parsers.syntax_patterns import (
    OPERATOR_WORDS,
    operator_regex,
    spelling_regex,
)

from .common_tokens import COMMON_TOKEN_NAMES
from .parser_utils import (
    NodeMarks,
    OpenPrefix,
    ambiguous_prefix_error,
    run_common_prechecks,
    validate_proposition_identifier,
)


def word_rule(token: str, symbol_regex: str | None = None, *, normalize: bool = True):
    """Return a PLY rule for `token` that reads its symbol or one of its words in
    `OPERATOR_WORDS`; with `normalize` the token's value is the symbol, whatever
    the spelling.

    `symbol_regex` replaces the table's symbol when a logic reads it in context
    (`A` before `F`, `:` or `,`). Every rule from here is a function, which PLY
    tries before the string rule `t_PROP`; the rules share one line number, so PLY
    orders them by name, which is safe while no two match the same text.
    """
    symbol, words = OPERATOR_WORDS[token]

    def rule(self, t):
        # Kept for p_error, which names what the user wrote (`weak`, not `W`).
        t.text = t.value
        if normalize:
            t.value = symbol
        return t

    if symbol_regex is None:
        rule.__doc__ = operator_regex(token)
    else:
        rule.__doc__ = "|".join([symbol_regex, *map(spelling_regex, words)])
    return rule


def quantifier_rules(operator_letters: str):
    """Return the FORALL and EXIST rules: `A` and `E` are quantifiers only before
    one of `operator_letters`, a space, `(`, `[` or the end, so `AF` splits and
    `Abc` does not."""
    lookahead = rf"(?=[{operator_letters}\s(\[]|$)"
    return word_rule("FORALL", "A" + lookahead), word_rule("EXIST", "E" + lookahead)


class BaseLogicParser:
    """Base of the PLY formula parsers: subclasses add tokens and grammar rules, then
    call `build()`."""

    def __init__(self):
        """Initialize logger, token list, and lexer/parser placeholders."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tokens = list(COMMON_TOKEN_NAMES)
        self.lexer = None
        self.parser = None
        self.errors = []
        self._reset_marks()

    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_ignore = " \t"

    t_UNTIL = word_rule("UNTIL")
    t_GLOBALLY = word_rule("GLOBALLY")
    t_NEXT = word_rule("NEXT")
    t_EVENTUALLY = word_rule("EVENTUALLY")

    def t_FALSE(self, t):
        r"false\b"
        return t

    def t_TRUE(self, t):
        r"true\b"
        return t

    # A single & or | is an invalid character, and a lone > is not implication.
    # The AST keeps the spelling of a connective (`and` or `&&`), as the solvers
    # read both.
    t_AND = word_rule("AND", normalize=False)
    t_OR = word_rule("OR", normalize=False)
    t_NOT = word_rule("NOT", normalize=False)
    t_IMPLIES = word_rule("IMPLIES", normalize=False)

    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        """Error handling for illegal characters."""
        err_msg = f"Invalid character '{t.value[0]}' at position {t.lexpos + 1}"
        self._log_error(err_msg)
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
        self._connective(p[0], p[1], p[2], p[3])

    def p_expression_not(self, p):
        """expression : NOT expression"""
        p[0] = (p[1], p[2])
        self._negation(p[0], p[2])

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = p[2]
        self._grouped.mark(p[0])

    # --- Prefix scope ---
    # A prefix no parenthesis closes is open (`<1>F p && q` has two readings). These
    # rules mark nodes and reject a connective next to an open prefix, however grouped.

    def _reset_marks(self) -> None:
        self._grouped: NodeMarks[None] = NodeMarks()
        self._connectives: NodeMarks[str] = NodeMarks()
        self._open: NodeMarks[OpenPrefix] = NodeMarks()

    def _open_prefix_of(self, node) -> OpenPrefix | None:
        return None if node in self._grouped else self._open.value(node)

    def _prefix_over(self, node, prefix: str, position: int, body, operator=None):
        """Record `node`, built by a prefix rule whose last operand `body` is not
        closed by a parenthesis; `operator` is the U, R or W of a prefix Until."""
        open_prefix = OpenPrefix(prefix, position, operator)
        connective = self._connectives.value(body)
        if connective is not None and body not in self._grouped:
            raise ambiguous_prefix_error(open_prefix, connective)
        self._open.mark(node, open_prefix)

    def _prefix_unary(self, p, node, prefix: str) -> None:
        """Record `node` of the rule `prefix OP body`, such as `<1>F p`."""
        self._prefix_over(node, prefix, p.lexpos(1), p[3])

    def _prefix_until(self, p, node, prefix: str) -> None:
        """Record `node` of a rule read by `until_operands`; `prefix (x U y)` is
        closed, `prefix x U y` is open."""
        if len(p) == 5:
            self._prefix_over(node, prefix, p.lexpos(1), p[4], p[3])

    def _connective(self, node, left, connective: str, right) -> None:
        open_left = self._open_prefix_of(left)
        if open_left is not None:
            raise ambiguous_prefix_error(open_left, connective)
        self._connectives.mark(node, connective)
        open_right = self._open_prefix_of(right)
        if open_right is not None:
            self._open.mark(node, open_right)

    def _attachment(self, node, attached) -> None:
        """Record a rule that attaches a part, such as the clock constraint in
        `p : x<5`, so that `AF p : x<5 && q` is still rejected as ambiguous."""
        if attached in self._connectives and attached not in self._grouped:
            self._connectives.mark(node, self._connectives.value(attached))
        open_attached = self._open_prefix_of(attached)
        if open_attached is not None:
            self._open.mark(node, open_attached)

    def _negation(self, node, operand) -> None:
        open_operand = self._open_prefix_of(operand)
        if open_operand is not None:
            self._open.mark(node, open_operand)

    def p_expression_boolean(self, p):
        """expression : FALSE
        | TRUE"""
        p[0] = p[1]

    def p_expression_prop(self, p):
        """expression : PROP"""
        self._check_proposition_name(p[1])
        p[0] = self._proposition_node(p[1])

    def _proposition_node(self, name: str) -> Any:
        """The AST leaf for proposition `name`; logics with typed nodes override it."""
        return name

    def _check_proposition_name(
        self, name: str, kind: str = "Atomic proposition"
    ) -> None:
        """Log why `name` cannot be a proposition, clock or capacity (a reserved
        word in any letter case), so `parse` returns None with that reason."""
        _, err = validate_proposition_identifier(name, kind=kind)
        if err is not None:
            self._log_error(err)

    def p_error(self, p):
        """Syntax error handler."""
        if p:
            lexpos = getattr(p, "lexpos", None)
            if lexpos is not None:
                shown = getattr(p, "text", p.value)
                err_msg = f"Syntax error near token '{shown}' at position {lexpos + 1}"
            else:
                err_msg = f"Syntax error near token '{p.value}'"
        else:
            err_msg = "Syntax error at end of input"
        self._log_error(err_msg)

    def _log_error(self, err_msg: str):
        """Helper to log and store errors."""
        self.logger.debug(err_msg)
        self.errors.append(err_msg)

    def build(self, **kwargs):
        """Build the lexer and parser, reusing the stored tables; PLY's harmless
        grammar warnings are silenced."""
        parser_file = inspect.getfile(self.__class__)
        parser_dir = os.path.dirname(parser_file)
        generated_dir = os.path.join(parser_dir, "generated")
        os.makedirs(generated_dir, exist_ok=True)

        if generated_dir not in sys.path:
            sys.path.insert(0, generated_dir)

        # Generate unique module names based on the class name to prevent sys.path import collisions
        class_name = self.__class__.__name__
        unique_prefix = f"{class_name}"

        # --- Lexer ---
        lex_kwargs = {k: v for k, v in kwargs.items() if k != "start"}
        if "errorlog" not in lex_kwargs:
            lex_kwargs["errorlog"] = lex.NullLogger()
        if "outputdir" not in lex_kwargs:
            lex_kwargs["outputdir"] = generated_dir
        if "lextab" not in lex_kwargs:
            lex_kwargs["lextab"] = f"{unique_prefix}_lextab"

        self.lexer = lex.lex(module=self, **lex_kwargs)

        # --- Parser ---
        parser_kwargs = {
            "debug": False,
            "write_tables": True,
            "optimize": False,  # Default to False to verify signatures and avoid stale tables
            "outputdir": generated_dir,
            "tabmodule": f"{unique_prefix}_parsetab",
            **kwargs,
        }
        if "errorlog" not in parser_kwargs:
            parser_kwargs["errorlog"] = yacc.NullLogger()

        self.parser = yacc.yacc(module=self, **parser_kwargs)

    def parse(self, formula: str, **kwargs: Any) -> Any:
        """Parse `formula` into an AST, or return None with reasons in `self.errors`."""
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
        finally:
            # The next parse starts empty, and no nodes of this one stay alive.
            self._reset_marks()

    def _pre_validation(self, formula) -> tuple[bool, str | None]:
        """Hook for pre-parsing validation."""
        return run_common_prechecks(formula)

    def _post_validation(self, formula, result):
        """Hook for post-parsing validation."""
        return result is not None

    def verify(self, token_name: str, string: Any) -> bool:
        if self.lexer is None:
            return False
        return self._run_lexer_verify(self.lexer.clone(), token_name, string)

    def _run_lexer_verify(self, lexer: Any, token_name: str, string: Any) -> bool:
        """Internal helper to verify a token against a lexer instance."""
        lexer.input(str(string))
        for token in lexer:
            if token.type == token_name:
                return True
        return False
