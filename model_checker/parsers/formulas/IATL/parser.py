from model_checker.parsers.formulas.shared_parser import BaseLogicParser

from .iatl_ply_parser import do_parsingIATL, verifyIATL


class IATLParser(BaseLogicParser):
    """VMI Wrapper for the standalone IATL parser."""

    def __init__(self):
        super().__init__()
        # We don't use the BaseLogicParser lexer/parser since IATL defines its own
        self.lexer = None
        self.parser = None

    def build(self, **kwargs):
        """Bypass standard build because the IATL parser is globally built."""
        pass

    def parse(self, formula: str, **kwargs) -> tuple | None:
        """Parse using IATL logic. Needs max_coalition which is hardcoded for now,
        or dynamically assumed since VMI doesn't pass it yet."""
        n_agents = kwargs.get("max_coalition", 10)  # Workaround for VMI limitation
        return do_parsingIATL(formula, n_agents)

    def verify(self, token_name: str, string: str) -> bool:
        """Verify token using IATL logic."""
        return verifyIATL(token_name, string)
