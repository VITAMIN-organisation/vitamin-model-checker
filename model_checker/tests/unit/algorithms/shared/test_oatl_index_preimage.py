"""Unit tests for shared OATL/COTL index pre-image helpers."""

import pytest

from model_checker.algorithms.explicit.shared.oatl_index_preimage import (
    check_if_action_is_extension,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "mask,joint,expected",
    [
        ("A--", "AAB", True),
        ("A--", "BBB", False),
        ("A|-|-", "A|A|B", True),
        ("A|-|-", "B|B|B", False),
        ("B|-|-", "B|B|B", True),
        ("A|-|-", "A|A", False),
    ],
)
def test_check_if_action_is_extension(mask, joint, expected):
    """Compact and pipe coalition masks match full joints by agent token."""
    assert check_if_action_is_extension(mask, joint) is expected
