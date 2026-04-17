"""NatATL idle-matrix validation: invalid matrices raise ValueError with expected message."""

import pytest

from model_checker.parsers.game_structures.cgs.cgs_validation import (
    validate_nat_idle_requirements as matrixParser,
)


class TestMatrixParserInvalidMatrices:
    """Test handling of invalid matrices."""

    @pytest.mark.parametrize(
        "matrix,n,expected_error,error_match,description",
        [
            # All-zero row (no transitions)
            (
                [[0, 0, 0], ["IDLE|IDLE|IDLE", "IDLE|IDLE|Z", "IDLE|Z|Z"]],
                3,
                ValueError,
                "All elements in row",
                "All-zero row raises ValueError",
            ),
            # All-zero row with short idle token "I"
            (
                [[0, 0, 0], ["I|I|I", "I|I|Z", "I|Z|Z"]],
                3,
                ValueError,
                "All elements in row",
                "All-zero row with I tokens raises ValueError",
            ),
            # No idle token for any agent in any joint action
            (
                [["Z|Z|Z", "Z|Z|Z", "Z|Z|Z"]],
                3,
                ValueError,
                "Idle error",
                "Missing idle action in any position raises error",
            ),
            # Partial idle coverage (only some agents can idle)
            (
                [["IDLE|Z|Z", "Z|Z|Z", "Z|Z|Z"]],
                3,
                ValueError,
                "Idle error",
                "Partial idle coverage raises error",
            ),
            # Matrix with an empty row
            (
                [[], ["IDLE|IDLE|IDLE", "IDLE|IDLE|Z", "IDLE|Z|Z"]],
                3,
                ValueError,
                "All elements in row",
                "Matrix with empty row raises error",
            ),
        ],
    )
    def test_invalid_matrices_raise_error(
        self, matrix, n, expected_error, error_match, description
    ):
        """Test that invalid matrices raise appropriate errors."""
        with pytest.raises(expected_error, match=error_match):
            matrixParser(matrix, n)
