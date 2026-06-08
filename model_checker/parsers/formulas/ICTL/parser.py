from model_checker.parsers.formulas.shared_parser import BaseLogicParser

from .ictl_ply_parser import do_parsingICTL, verifyICTL


class ICTLParser(BaseLogicParser):
    """VMI Wrapper for the standalone ICTL parser."""

    def __init__(self):
        super().__init__()
        self.lexer = None
        self.parser = None

    def build(self, **kwargs):
        pass

    def parse(self, formula: str, **kwargs) -> tuple | None:
        return do_parsingICTL(formula)

    def verify(self, token_name: str, string: str) -> bool:
        return verifyICTL(token_name, string)
