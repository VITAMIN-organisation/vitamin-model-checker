"""COTL integration test fixtures."""

import pytest


@pytest.fixture
def attack_graph(test_data_dir):
    """Path of the case-study attack graph with three security teams as demons."""
    return str(
        test_data_dir / "ObstructionModel/COTL/cotl_attack_graph_3demons_6states.txt"
    )
