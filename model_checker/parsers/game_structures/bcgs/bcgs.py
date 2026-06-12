"""BCGS (Birelational Concurrent Game Structure) model parser for IATL."""

from typing import Any, Dict, Optional


class BCGS:
    """Parser and in-memory representation for an IATL BCGS model file."""

    def __init__(self) -> None:
        self._data: Optional[Dict[str, Any]] = None
        self.filename: str = ""

    def read_file(self, filename: str) -> None:
        """Load and validate a BCGS model from a file path."""
        from model_checker.algorithms.explicit.IATL.util.graph import read_file

        self.filename = filename
        self._data = read_file(filename)

    @property
    def data(self) -> Dict[str, Any]:
        if self._data is None:
            raise ValueError("BCGS model not loaded; call read_file first.")
        return self._data
