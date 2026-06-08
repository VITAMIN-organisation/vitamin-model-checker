import re

import ply.lex as lex
import ply.yacc as yacc

MAX_COALITION = 0
_PARSER_HAS_ERROR = False
_LEXER_HAS_ERROR = False
_MODULE_REF = __import__(__name__, fromlist=["_MODULE_REF"])

# Token
tokens = (
    "LPAREN",
    "RPAREN",
    "AND",
    "OR",
    "NOT",
    "IMPLIES",
    "UNTIL",
    "RELEASE",
    "GLOBALLY",
    "NEXT",
    "EVENTUALLY",
    "PROP",
    "ECOALITION",
    "ACOALITION",
)

# Regular expressions for tokens
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_AND = r"&&|\&|and"
t_OR = r"\|\||\||or"
t_NOT = r"!|not"
t_IMPLIES = r"->|>|implies"
t_PROP = r"[a-z]+"
t_UNTIL = r"U|until"
t_RELEASE = r"R|release"
t_GLOBALLY = r"G|globally|always"
t_NEXT = r"X|next"
t_EVENTUALLY = r"F|eventually"
t_ECOALITION = r"<\d+(?:,\d+)*>"
t_ACOALITION = r"\[\d+(?:,\d+)*\]"
t_ignore = " \t\n"


# Token error handling
def t_error(t):
    global _LEXER_HAS_ERROR
    _LEXER_HAS_ERROR = True
    t.lexer.skip(1)


# Grammar
def p_expression_binary(p):
    """expression : expression AND expression
    | expression OR expression
    | expression IMPLIES expression"""
    p[0] = (p[2], p[1], p[3])


class CoalitionValueError(Exception):
    pass


def p_expression_ternary(p):
    """expression : ECOALITION expression UNTIL expression
    | ECOALITION expression RELEASE expression
    | ACOALITION expression UNTIL expression
    | ACOALITION expression RELEASE expression"""
    coalition_values = re.findall(r"\d+", p[1])
    for value in coalition_values:
        if int(value) > int(MAX_COALITION):
            raise CoalitionValueError(
                f"Coalition value {value} exceeds maximum of {MAX_COALITION}"
            )
    p[0] = (p[1] + p[3], p[2], p[4])


def p_expression_unary(p):
    """expression : ECOALITION GLOBALLY expression
    | ECOALITION NEXT expression
    | ECOALITION EVENTUALLY expression
    | ACOALITION GLOBALLY expression
    | ACOALITION NEXT expression
    | ACOALITION EVENTUALLY expression"""
    coalition_values = re.findall(r"\d+", p[1])
    for value in coalition_values:
        if int(value) > int(MAX_COALITION):
            raise CoalitionValueError(
                f"Coalition value {value} exceeds maximum of {MAX_COALITION}"
            )
    p[0] = (p[1] + p[2], p[3])


def p_expression_not(p):
    """expression : NOT expression"""
    p[0] = (p[1], p[2])


def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""
    p[0] = p[2]


def p_expression_prop(p):
    """expression : PROP"""
    p[0] = p[1]


def p_error(p):
    global _PARSER_HAS_ERROR
    _PARSER_HAS_ERROR = True


# lexer and parser
lexer = lex.lex(module=_MODULE_REF)
parser = yacc.yacc(module=_MODULE_REF, write_tables=False, debug=False)


def get_lexer():
    return lexer


def do_parsingIATL(formula, n_agent):
    global MAX_COALITION, _PARSER_HAS_ERROR, _LEXER_HAS_ERROR
    MAX_COALITION = n_agent
    _PARSER_HAS_ERROR = False
    _LEXER_HAS_ERROR = False
    try:
        # Create a fresh local lexer and parser to avoid any global pollution/state issues
        local_lexer = lex.lex(module=_MODULE_REF)
        local_parser = yacc.yacc(module=_MODULE_REF, write_tables=False, debug=False)
        result = local_parser.parse(formula, lexer=local_lexer)
        if _PARSER_HAS_ERROR or _LEXER_HAS_ERROR:
            return None
        return result
    except (SyntaxError, CoalitionValueError):  # if parser fails
        return None
    except Exception:
        return None


# checks whether the input operator corresponds to a given operator defined in the grammar
def verifyIATL(token_name, string):
    # Use a separate lexer instance for verification to avoid messing with global state
    v_lexer = lex.lex(module=_MODULE_REF)
    v_lexer.input(string)
    for token in v_lexer:
        if token.type == token_name and token.value in string:
            return True
    return False
