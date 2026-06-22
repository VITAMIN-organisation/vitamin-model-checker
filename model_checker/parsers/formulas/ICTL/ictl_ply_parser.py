import ply.lex as lex
import ply.yacc as yacc

from model_checker.parsers.syntax_patterns import ICTL_PROPOSITION_TOKEN

_LEXER_HAS_ERROR = False
_PARSER_HAS_ERROR = False
_MODULE_REF = __import__(__name__, fromlist=["_MODULE_REF"])

# Tokens
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
    "FORALL",
    "EXIST",
)

# Regular expressions for tokens
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_AND = r"&&|\&|and"
t_OR = r"\|\||\||or"
t_NOT = r"!|not"
t_IMPLIES = r"->|>|implies"
t_PROP = ICTL_PROPOSITION_TOKEN
t_UNTIL = r"U|until"
t_RELEASE = r"R|release"
t_GLOBALLY = r"G|globally|always"
t_NEXT = r"X|next"
t_EVENTUALLY = r"F|eventually"
t_FORALL = r"A|forall"
t_EXIST = r"E|exist"
t_ignore = " \t\n"


# A function that if you don't define, it will generate warnings and error
def p_error(p):
    global _PARSER_HAS_ERROR
    _PARSER_HAS_ERROR = True


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


def p_expression_ternary(p):
    """expression : FORALL expression UNTIL expression
    | EXIST expression UNTIL expression
    | FORALL expression RELEASE expression
    | EXIST expression RELEASE expression"""
    p[0] = (p[1] + p[3], p[2], p[4])


def p_expression_unary(p):
    """expression : FORALL GLOBALLY expression
    | FORALL NEXT expression
    | FORALL EVENTUALLY expression
    | EXIST GLOBALLY expression
    | EXIST NEXT expression
    | EXIST EVENTUALLY expression"""
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


# given a ICTL formula as input, returns a tuple representing the formula divided into sub formulas.
def do_parsingICTL(formula):
    global _PARSER_HAS_ERROR, _LEXER_HAS_ERROR
    _PARSER_HAS_ERROR = False
    _LEXER_HAS_ERROR = False
    try:
        # Create fresh local lexer/parser
        local_lexer = lex.lex(module=_MODULE_REF)
        local_parser = yacc.yacc(module=_MODULE_REF, write_tables=False, debug=False)
        result = local_parser.parse(formula, lexer=local_lexer)
        if _PARSER_HAS_ERROR or _LEXER_HAS_ERROR:
            return None
        return result
    except (SyntaxError, Exception):  # if parser fails
        return None


# checks whether the input operator corresponds to a given operator defined in the grammar
def verifyICTL(token_name, string):
    # Use a separate lexer instance for verification
    v_lexer = lex.lex(module=_MODULE_REF)
    v_lexer.input(string)
    for token in v_lexer:
        if token.type == token_name and token.value in string:
            return True
    return False
