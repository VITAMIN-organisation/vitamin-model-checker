"""Candidate rejection is separate from model/parse/internal errors."""
class InadmissibleStrategy(ValueError):
    """The supplied rule list does not define an admissible strategy."""
