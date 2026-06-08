from model_checker.parsers.formulas.shared_parser import BaseLogicParser

from .tctl_ply_parser import do_parsingTCTL, verifyTCTL


class TCTLParser(BaseLogicParser):
    """VMI Wrapper for the standalone TCTL parser."""

    def __init__(self):
        super().__init__()
        self.lexer = None
        self.parser = None

    def build(self, **kwargs):
        pass

    def parse(self, formula: str, **kwargs) -> tuple | None:
        return do_parsingTCTL(formula)

    def verify(self, token_name: str, string: str) -> bool:
        return verifyTCTL(token_name, string)
