"""Wallet_ATL parser (PLY-based) - Standardized Robust Version."""

import os
import re
import sys
import unicodedata

import ply.lex as lex
import ply.yacc as yacc

from model_checker.parsers.formulas.parser_utils import (
    run_common_prechecks,
    validate_ast,
    verify_token,
)
from model_checker.parsers.formulas.shared_parser import BaseLogicParser

# Error flags for robust error tracking
_LEXER_HAS_ERROR = False
_PARSER_HAS_ERROR = False
_MAX_COALITION = 0

# <<1>>X p -> <<1>> X p so temporal letters are not lexed as propositions
_COALITION_TEMPORAL_SPACING = re.compile(r">>(?=[FGXU])")


# Lexer rules
tokens = (
    "LPAREN",
    "RPAREN",
    "AND",
    "OR",
    "NOT",
    "IMPLIES",
    "UNTIL",
    "GLOBALLY",
    "NEXT",
    "EVENTUALLY",
    "PROP",
    "WALLET",
    "GE",
    "LE",
    "EQ",
    "COLON",
    "COMMA",
    "COALITION",
)

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_AND = r"&&|\&|and"
t_OR = r"\|\||\||or"
t_NOT = r"!|not"
t_IMPLIES = r"->|>|implies"
t_GE = r">="
t_LE = r"<="
t_EQ = r"==|="
t_COLON = r":"
t_COMMA = r","
t_WALLET = r"wallet"


def _parse_coalition_logic(text):
    """Parse coalition specification with optional wallet constraints."""
    coalition_match = re.match(r"<<\s*([^:>]*)(?::(.*))?>>", text)
    if not coalition_match:
        raise SyntaxError("Invalid coalition specification")

    agents_part = coalition_match.group(1).strip()
    agents = [int(a.strip()) for a in agents_part.split(",") if a.strip().isdigit()]

    constraints = []
    constraints_part = coalition_match.group(2)

    if constraints_part:
        for constraint in re.split(r"\s*&&\s*", constraints_part.strip()):
            wallet_match = re.match(
                r"wallet\(\s*(\d+)\s*,\s*(>=|<=|==|>|<)\s*(\d+)\s*\)",
                constraint.strip(),
            )
            if wallet_match:
                constraints.append(
                    {
                        "agent": int(wallet_match.group(1)),
                        "operator": wallet_match.group(2),
                        "value": int(wallet_match.group(3)),
                    }
                )
            elif constraint.strip():
                raise SyntaxError(f"Invalid wallet constraint: {constraint}")

    return {
        "agents": agents,
        "constraints": constraints,
    }


def t_COALITION(t):
    r"<<\s*\d+(?:\s*,\s*\d+)*\s*(?::\s*wallet\(\s*\d+\s*,\s*(?:>=|<=|==|>|<)\s*\d+\s*\)(?:\s*&&\s*wallet\(\s*\d+\s*,\s*(?:>=|<=|==|>|<)\s*\d+\s*\))*)?\s*>>"
    t.value = _parse_coalition_logic(t.value)
    return t


def t_NEXT(t):
    r"X|next\b"
    t.value = "X"
    return t


def t_EVENTUALLY(t):
    r"F|eventually\b"
    t.value = "F"
    return t


def t_GLOBALLY(t):
    r"G|globally|always\b"
    t.value = "G"
    return t


def t_UNTIL(t):
    r"U|until\b"
    t.value = "U"
    return t


def t_PROP(t):
    r"[a-zA-Z][a-zA-Z0-9_]*"
    return t


t_ignore = " \t\n"


def t_error(t):
    global _LEXER_HAS_ERROR
    _LEXER_HAS_ERROR = True
    t.lexer.skip(1)


# Parser rules
def p_formula(p):
    """formula : coalition_formula
    | boolean_unary
    | boolean_binary
    | prop_formula
    | group_formula"""
    p[0] = p[1]


def p_boolean_unary(p):
    """boolean_unary : NOT formula"""
    p[0] = {
        "type": "unary",
        "operator": p[1],
        "formula": p[2],
    }


def p_boolean_binary(p):
    """boolean_binary : formula AND formula
    | formula OR formula
    | formula IMPLIES formula"""
    p[0] = {
        "type": "binary",
        "operator": p[2],
        "left": p[1],
        "right": p[3],
    }


def p_coalition_formula(p):
    """coalition_formula : COALITION temporal_body"""
    coalition_info = p[1]
    for agent in coalition_info["agents"]:
        if agent > _MAX_COALITION:
            raise ValueError(
                f"Agent {agent} exceeds maximum coalition size {_MAX_COALITION}"
            )
    p[0] = {
        "type": "coalition_wallet",
        "agents": coalition_info["agents"],
        "constraints": coalition_info["constraints"],
        "formula": p[2],
    }


def p_temporal_body(p):
    """temporal_body : GLOBALLY formula
    | NEXT formula
    | EVENTUALLY formula
    | formula UNTIL formula"""
    if len(p) == 3:
        p[0] = {
            "type": "unary",
            "operator": p[1],
            "formula": p[2],
        }
    else:
        p[0] = {
            "type": "binary",
            "operator": p[2],
            "left": p[1],
            "right": p[4],
        }


def p_prop_formula(p):
    """prop_formula : PROP"""
    p[0] = {
        "type": "proposition",
        "proposition": p[1],
    }


def p_group_formula(p):
    """group_formula : LPAREN formula RPAREN"""
    p[0] = p[2]


def p_error(p):
    global _PARSER_HAS_ERROR
    _PARSER_HAS_ERROR = True


def _reset_parse_session(max_coalition):
    global _LEXER_HAS_ERROR, _PARSER_HAS_ERROR, _MAX_COALITION
    _LEXER_HAS_ERROR = False
    _PARSER_HAS_ERROR = False
    _MAX_COALITION = max_coalition


def _normalize_wallet_atl_formula(formula_text):
    """Unicode cleanup, whitespace collapse, and coalition/temporal token spacing."""
    text = unicodedata.normalize("NFKC", formula_text)
    text = text.replace("\ufeff", "").replace("\u00a0", " ")
    text = " ".join(text.strip().split())
    return _COALITION_TEMPORAL_SPACING.sub(">> ", text)


def _create_wallet_atl_ply_parser():
    """Build a fresh PLY lexer and parser for one parse attempt."""
    lexer = lex.lex(module=sys.modules[__name__], errorlog=lex.NullLogger())

    output_dir = os.path.join(os.path.dirname(__file__), "generated")
    os.makedirs(output_dir, exist_ok=True)

    parser = yacc.yacc(
        module=sys.modules[__name__],
        debug=False,
        write_tables=True,
        optimize=True,
        outputdir=output_dir,
        errorlog=yacc.NullLogger(),
    )
    return lexer, parser


def do_parsingWallet_ATL(formula_text, max_coalition=0):
    """Parse Wallet_ATL formula and return a structured AST dict or None on failure."""
    if not formula_text.strip():
        return None

    _reset_parse_session(max_coalition)

    try:
        normalized = _normalize_wallet_atl_formula(formula_text)
        lexer, parser = _create_wallet_atl_ply_parser()
        result = parser.parse(normalized, lexer=lexer)
        if _LEXER_HAS_ERROR or _PARSER_HAS_ERROR:
            return None
        return result
    except Exception:
        return None


class Wallet_ATLParser(BaseLogicParser):
    """Parser for Wallet_ATL formulas (dict AST via module-level PLY grammar)."""

    _VALID_OPERATORS = frozenset(
        {
            "U",
            "X",
            "F",
            "G",
            "&&",
            "AND",
            "NOT",
            "UNTIL",
            "NEXT",
            "EVENTUALLY",
            "GLOBALLY",
            "!",
            "->",
        }
    )

    def __init__(self, **kwargs):
        super().__init__()
        self.MAX_COALITION = 0

    def _pre_validation(self, formula):
        return run_common_prechecks(
            formula,
            allow_hash_at=False,
            coalition_required=False,
            allow_negative_agents=False,
        )

    def _post_validation(self, formula, result) -> bool:
        if result is None:
            return False
        if not isinstance(result, tuple):
            return True
        return validate_ast(result, self._VALID_OPERATORS)

    def parse(self, formula_text, max_coalition=None, n_agent=None, **kwargs):
        self.errors = []
        valid, err = self._pre_validation(formula_text)
        if not valid:
            if err:
                self.errors.append(err)
            return None
        if n_agent is not None and max_coalition is None:
            max_coalition = n_agent
        if max_coalition is not None:
            self.MAX_COALITION = max_coalition
        try:
            res = do_parsingWallet_ATL(formula_text, self.MAX_COALITION)
            if res is None:
                if not self.errors:
                    self.errors.append("Syntax or lexical error in formula")
                return None
            if not self._post_validation(formula_text, res):
                return None
            return res
        except Exception as e:
            self.logger.debug("Wallet_ATL parse failed: %s", e)
            self.errors.append(str(e))
            return None

    def verify(self, token_name, string):
        v_lexer = lex.lex(module=sys.modules[__name__], errorlog=lex.NullLogger())
        return verify_token(v_lexer, token_name, str(string), case_sensitive=False)

    def build(self, **kwargs) -> None:
        """Wallet_ATL uses module-level PLY tables; no build on this class."""


class Wallet_ATLFormulaParser(Wallet_ATLParser):
    """Backward-compatible alias for older imports."""

    pass
