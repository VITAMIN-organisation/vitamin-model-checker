"""Wallet_ATL parser (PLY-based) - Standardized Robust Version."""

import os
import re
import sys
import unicodedata

import ply.lex as lex
import ply.yacc as yacc

from model_checker.parsers.formulas.parser_utils import verify_token
from model_checker.parsers.syntax_patterns import PROPOSITION_TOKEN

# Error flags for robust error tracking
_LEXER_HAS_ERROR = False
_PARSER_HAS_ERROR = False
_MAX_COALITION = 0


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
t_PROP = PROPOSITION_TOKEN
t_UNTIL = r"U|until"
t_GLOBALLY = r"G|globally|always"
t_NEXT = r"X|next"
t_EVENTUALLY = r"F|eventually"
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


t_ignore = " \t\n"


def t_error(t):
    global _LEXER_HAS_ERROR
    _LEXER_HAS_ERROR = True
    t.lexer.skip(1)


# Parser rules
def p_formula(p):
    """formula : coalition_formula
    | unary_formula
    | binary_formula
    | prop_formula
    | group_formula"""
    p[0] = p[1]


def p_coalition_formula(p):
    """coalition_formula : COALITION formula"""
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


def p_unary_formula(p):
    """unary_formula : GLOBALLY formula
    | NEXT formula
    | EVENTUALLY formula
    | NOT formula"""
    p[0] = {
        "type": "unary",
        "operator": p[1],
        "formula": p[2],
    }


def p_binary_formula(p):
    """binary_formula : formula AND formula
    | formula OR formula
    | formula IMPLIES formula
    | formula UNTIL formula"""
    p[0] = {
        "type": "binary",
        "operator": p[2],
        "left": p[1],
        "right": p[3],
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


def do_parsingWallet_ATL(formula_text, max_coalition=0):
    """Parse Wallet_ATL formula and return a structured AST dict or None on failure."""
    global _LEXER_HAS_ERROR, _PARSER_HAS_ERROR, _MAX_COALITION
    _LEXER_HAS_ERROR = False
    _PARSER_HAS_ERROR = False
    _MAX_COALITION = max_coalition

    if not formula_text.strip():
        return None

    try:
        # Normalize input
        s = unicodedata.normalize("NFKC", formula_text)
        s = s.replace("\ufeff", "").replace("\u00a0", " ")
        s = " ".join(s.strip().split())

        # Create fresh local lexer/parser
        local_lexer = lex.lex(module=sys.modules[__name__], errorlog=lex.NullLogger())

        parser_dir = os.path.dirname(__file__)
        output_dir = os.path.join(parser_dir, "generated")
        os.makedirs(output_dir, exist_ok=True)

        local_parser = yacc.yacc(
            module=sys.modules[__name__],
            debug=False,
            write_tables=True,
            optimize=True,
            outputdir=output_dir,
            errorlog=yacc.NullLogger(),
        )

        result = local_parser.parse(s, lexer=local_lexer)

        if _LEXER_HAS_ERROR or _PARSER_HAS_ERROR:
            return None

        return result
    except Exception:
        return None


class Wallet_ATLParser:
    """Wrapper class for Wallet_ATL parser to maintain backward compatibility."""

    def __init__(self):
        self.errors = []
        self.MAX_COALITION = 0

    def parse(self, formula_text, max_coalition=None, n_agent=None):
        if n_agent is not None and max_coalition is None:
            max_coalition = n_agent
        if max_coalition is not None:
            self.MAX_COALITION = max_coalition

        res = do_parsingWallet_ATL(formula_text, self.MAX_COALITION)
        if res is None:
            self.errors = ["Syntax or lexical error in formula"]
        return res

    def verify(self, token_name, string):
        # Use a fresh lexer for verification
        v_lexer = lex.lex(module=sys.modules[__name__], errorlog=lex.NullLogger())
        return verify_token(v_lexer, token_name, str(string), case_sensitive=False)

    def build(self):
        """integrator conformance expects a build method."""
        pass


class Wallet_ATLFormulaParser(Wallet_ATLParser):
    """Backward-compatible alias for older imports."""

    pass
