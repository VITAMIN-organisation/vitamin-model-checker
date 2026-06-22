import re
import sys
import unicodedata

import ply.lex as lex
import ply.yacc as yacc

from model_checker.parsers.syntax_patterns import TCTL_TOL_PROPOSITION_TOKEN

_LEXER_HAS_ERROR = False
_PARSER_HAS_ERROR = False


class Expr:
    def __init__(self):
        self.satisfying_states = set()
        self.constraints = None


class Unary(Expr):
    def __init__(self, op: str, operand: Expr):
        super().__init__()
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"{self.op}({self.operand})"


class Binary(Expr):
    def __init__(self, op: str, left: Expr, right: Expr):
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.op} {self.left},{self.right}"


class AtomicProp(Expr):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class DemonicOp(Expr):
    def __init__(self, demonic_cost: str, op: str, operand: Expr):
        super().__init__()
        self.demonic_cost = demonic_cost
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"{self.demonic_cost}{self.op}({self.operand})"


class DemonicBinary(Expr):
    def __init__(self, demonic_cost: str, op: str, left: Expr, right: Expr):
        super().__init__()
        self.demonic_cost = demonic_cost
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.demonic_cost}{self.op}({self.left},{self.right})"


class ClockExpr(Expr):
    def __init__(self, subject: Expr, constraints: Expr):
        super().__init__()
        self.subject = subject
        self.constraints = str(constraints)

    def __repr__(self):
        return f"{self.subject}: {self.constraints}"

    def __str__(self):
        return f"{self.subject}: {self.constraints}"


class SimpleTimeExpr(Expr):
    def __init__(self, constraints: tuple):
        super().__init__()
        self.constraints = constraints

    def __repr__(self):
        return "".join(self.constraints)

    def __str__(self):
        return "".join(self.constraints)


reserved = {
    "implies": "IMPLIES",
    "with": "TIME_SEP",
    "not": "NOT",
    "or": "OR",
    "and": "AND",
    "globally": "GLOBALLY",
    "G": "GLOBALLY",
}

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
    "WEAK",
    "GLOBALLY",
    "NEXT",
    "EVENTUALLY",
    "FALSE",
    "TRUE",
    "PROP",
    "DEMONIC",
    "GREATER",
    "LESS",
    "LEQ",
    "GEQ",
    "CONST",
    "TIME_SEP",
)

# Regular expressions for tokens
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_AND = r"&&|\&|and"
t_OR = r"\|\||\||or"
t_NOT = r"!|not"
t_IMPLIES = r"->|implies"
t_UNTIL = r"U|until"
t_RELEASE = r"R|release"
t_WEAK = r"W|weak"
t_GLOBALLY = r"G|globally|always"
t_NEXT = r"X|next"
t_EVENTUALLY = r"F|eventually"
t_FALSE = r"\#|false"
t_TRUE = r"\@|true"
# t_PROP = r'[a-z]+'
t_DEMONIC = r"{J[1-9]\d*}"
t_LESS = r"\<"
t_LEQ = r"\<\="
t_GREATER = r"\>"
t_GEQ = r"\>\="
t_CONST = r"\d+"
t_TIME_SEP = r":|,|with"
t_ignore = " \t\n"

precedence = (("right", "NOT"),)


def t_PROP(t):
    t.type = reserved.get(t.value, "PROP")
    return t


t_PROP.__doc__ = TCTL_TOL_PROPOSITION_TOKEN


# Token error handling
def t_error(t):
    global _LEXER_HAS_ERROR
    _LEXER_HAS_ERROR = True
    t.lexer.skip(1)


class DemonicValueError(Exception):
    pass


# Grammar
def p_expression_binary(p):
    """expression : expression AND expression
    | expression OR expression
    | expression IMPLIES expression"""
    p[0] = Binary(p[2], p[1], p[3])


def p_expression_ternary(p):
    """expression : DEMONIC expression UNTIL expression
    | DEMONIC expression WEAK expression
    | DEMONIC expression RELEASE expression"""
    demonic_cost = re.findall(r"\d+", p[1])[0]
    try:
        int(demonic_cost)
    except ValueError:
        raise DemonicValueError(
            f"Provided cost ({demonic_cost}) is not an int."
        ) from None
    p[0] = DemonicBinary(p[1], p[3], p[2], p[4])


def p_expression_unary(p):
    """expression : DEMONIC GLOBALLY expression
    | DEMONIC NEXT expression
    | DEMONIC EVENTUALLY expression"""
    demonic_cost = re.findall(r"\d+", p[1])[0]
    try:
        int(demonic_cost)
    except ValueError:
        raise DemonicValueError(
            f"Provided cost ({demonic_cost}) is not an int."
        ) from None
    p[0] = DemonicOp(p[1], p[2], p[3])


def p_expression_not(p):
    """expression : NOT expression"""
    p[0] = Unary(p[1], p[2])


def p_expression_group(p):
    """expression : LPAREN expression RPAREN"""
    p[0] = p[2]


def p_expression_boolean(p):
    """expression : FALSE
    | TRUE"""
    p[0] = p[1]


def p_expression_clock_constraint_on_expr(p):
    """expression : expression TIME_SEP expression"""
    p[0] = ClockExpr(p[1], p[3])


def p_expression_time_atomic_constraint(p):
    """expression : PROP LEQ CONST
    | PROP LESS CONST
    | PROP GEQ CONST
    | PROP GREATER CONST
    """
    p[0] = SimpleTimeExpr(p[1] + p[2] + p[3])


def p_expression_prop(p):
    """expression : PROP"""
    p[0] = AtomicProp(p[1])


def p_error(p):
    global _PARSER_HAS_ERROR
    _PARSER_HAS_ERROR = True


# given an ATL formula as input
# returns a tuple representing the formula divided into subformulas.
def do_parsing(formula):
    global _PARSER_HAS_ERROR, _LEXER_HAS_ERROR
    _PARSER_HAS_ERROR = False
    _LEXER_HAS_ERROR = False
    try:
        if isinstance(formula, str):
            s = unicodedata.normalize("NFKC", formula)
            s = s.replace("\ufeff", "").replace("\u00a0", " ")
            s = " ".join(s.strip().split())
        else:
            s = formula

        # Create fresh local lexer/parser
        local_lexer = lex.lex(module=sys.modules[__name__])
        local_parser = yacc.yacc(
            module=sys.modules[__name__], write_tables=False, debug=False
        )
        result = local_parser.parse(s, lexer=local_lexer)
        if _PARSER_HAS_ERROR or _LEXER_HAS_ERROR:
            return None
        return result
    except (SyntaxError, DemonicValueError, Exception):  # if parser fails
        return None


# checks whether the input operator corresponds to a given operator defined in the grammar
def verify(token_name, string):
    # Use a separate lexer instance for verification
    v_lexer = lex.lex(module=sys.modules[__name__])
    v_lexer.input(string)
    for token in v_lexer:
        if token.type == token_name and token.value in string:
            return True
    return False
