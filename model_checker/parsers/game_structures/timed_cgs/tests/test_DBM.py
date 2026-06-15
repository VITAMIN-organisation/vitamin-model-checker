"""Unit tests for DBM zone operations."""

import pytest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBM


@pytest.fixture
def empty_dbm() -> DBM:
    return DBM(2)


@pytest.fixture
def constraint_dbm() -> DBM:
    dbm = DBM(2)
    dbm.add_initial_constraint(1, 0, 20, "<")
    dbm.add_initial_constraint(2, 0, 20, "<=")
    dbm.add_initial_constraint(2, 1, 10, "<=")
    dbm.add_initial_constraint(1, 2, -10, "<=")
    return dbm


@pytest.mark.unit
def test_init_is_consistent(empty_dbm):
    assert not empty_dbm.is_empty()
    assert all(entry.constant == 0 for entry in empty_dbm.elements.diagonal())
    assert all(empty_dbm.elements[0][j].constant == 0 for j in range(empty_dbm.size))


@pytest.mark.unit
def test_includes_zone_containment(empty_dbm, constraint_dbm):
    closed = empty_dbm.close()
    assert empty_dbm.includes(empty_dbm)
    assert empty_dbm.includes(closed)
    assert closed.includes(empty_dbm)

    stricter = DBM(2)
    stricter.add_initial_constraint(0, 1, 1, "<=")
    assert not stricter.includes(empty_dbm)

    empty_dbm.add_initial_constraint(0, 1, 1, "<")
    assert not stricter.includes(empty_dbm)


@pytest.mark.unit
def test_close_raises_on_negative_cycle():
    dbm = DBM(3)
    dbm.add_initial_constraint(0, 1, 1, "<=")
    dbm.add_initial_constraint(1, 2, -1, "<=")
    dbm.add_initial_constraint(2, 3, -1, "<=")
    dbm.add_initial_constraint(3, 0, -1, "<=")
    with pytest.raises(ValueError, match="not consistent"):
        dbm.close()


@pytest.mark.unit
def test_close_tightens_bounds(constraint_dbm):
    expected = DBM(2)
    expected.add_constraint(1, 0, 10, "<=")
    expected.add_constraint(2, 0, 20, "<=")
    expected.add_constraint(2, 1, 10, "<=")
    expected.add_constraint(1, 2, -10, "<=")
    assert expected == constraint_dbm.close()


@pytest.mark.unit
def test_close_bouyer_example():
    """Example from Bouyer et al. (2018), Model Checking Timed Automata, p.24."""
    dbm = DBM(2)
    dbm.add_initial_constraint(0, 1, -3, "<=")
    dbm.add_initial_constraint(1, 2, 4, "<=")
    dbm.add_initial_constraint(2, 0, 5, "<=")

    expected = DBM(2)
    expected.add_initial_constraint(0, 1, -3)
    expected.add_initial_constraint(1, 0, 9)
    expected.add_initial_constraint(1, 2, 4)
    expected.add_initial_constraint(2, 0, 5)
    expected.add_initial_constraint(2, 1, 2)
    assert expected == dbm.close()


@pytest.mark.unit
def test_add_constraint_tightens_and_detects_inconsistency(empty_dbm):
    empty_dbm.add_constraint(1, 2, 1)
    assert empty_dbm.elements[1][2].constant == 1

    empty_dbm.add_constraint(2, 1, -10)
    assert empty_dbm.is_empty()


@pytest.mark.unit
def test_reset_sets_clock_value(constraint_dbm):
    constraint_dbm.reset(1, 5)
    assert constraint_dbm.elements[1][0].constant == 5
    assert constraint_dbm.elements[0][1].constant == -5
    assert constraint_dbm == constraint_dbm.close()


@pytest.mark.unit
def test_guard_then_reset_sequence():
    dbm = DBM(2)
    dbm.add_constraint(1, 0, 5)
    dbm.add_constraint(0, 1, -5)
    dbm.reset(1)
    assert dbm.elements[1][0].constant == 0
    assert dbm.elements[0][1].constant == 0
    dbm.add_constraint(0, 2, -5, "<")
    assert not dbm.is_empty()


@pytest.mark.unit
def test_down_time_predecessor():
    dbm = DBM(1)
    dbm.add_constraint(0, 1, -3)
    dbm.down()
    assert dbm.elements[0][1].constant == 0
    assert not dbm.is_empty()


@pytest.mark.unit
def test_up_preserves_canonicity(constraint_dbm):
    dbm = constraint_dbm.close()
    dbm.up()
    assert dbm == dbm.close()


@pytest.mark.unit
def test_k_normalize():
    dbm = DBM(2)
    dbm.add_constraint(1, 0, 3, "<=")
    dbm.add_constraint(0, 1, -1, "<=")
    dbm.add_constraint(2, 0, 3, "<=")
    dbm.add_constraint(0, 2, -2, "<=")
    dbm.k_normalize([2, 1])

    expected = DBM(2)
    expected.add_constraint(0, 1, -1, "<=")
    expected.add_constraint(0, 2, -1, "<")
    expected.add_constraint(1, 2, 1, "<=")
    assert expected == dbm


@pytest.mark.unit
def test_get_free(constraint_dbm):
    expected = DBM(2)
    expected.add_initial_constraint(2, 0, 20, "<=")
    expected.add_initial_constraint(2, 1, 20, "<=")
    assert expected == constraint_dbm.get_free(1)


@pytest.mark.unit
def test_copy_is_deep_and_independent(constraint_dbm):
    original = constraint_dbm.copy()
    assert original == constraint_dbm

    mutated = original.copy()
    mutated.add_constraint(2, 1, -100)
    assert not original.is_empty()
    assert mutated.is_empty()
    assert original.elements[0][0] is not mutated.elements[0][0]
