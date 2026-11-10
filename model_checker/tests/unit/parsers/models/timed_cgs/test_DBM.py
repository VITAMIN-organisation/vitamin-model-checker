"""Difference-bound matrices: the zone operations the timed checkers build on.

Entry (i, j) bounds clock_i - clock_j, with clock 0 the constant zero; so (1, 0)
is an upper bound on x1 and (0, 1) is minus its lower bound. Each expected matrix
below is worked out by hand.
"""

import numpy as np
import pytest

from model_checker.parsers.game_structures.timed_cgs.DBM import DBM


@pytest.fixture
def empty_dbm() -> DBM:
    return DBM(2)


@pytest.fixture
def constraint_dbm() -> DBM:
    """x1 < 20, x2 <= 20, x2 - x1 <= 10, x1 - x2 <= -10 (so x2 = x1 + 10)."""
    dbm = DBM(2)
    dbm.add_initial_constraint(1, 0, 20, "<")
    dbm.add_initial_constraint(2, 0, 20, "<=")
    dbm.add_initial_constraint(2, 1, 10, "<=")
    dbm.add_initial_constraint(1, 2, -10, "<=")
    return dbm


@pytest.mark.unit
def test_includes_means_self_is_inside_other(empty_dbm):
    """`a.includes(b)` is True when zone a lies inside zone b (regions.py relies on this)."""
    looser = DBM(2)
    looser.add_initial_constraint(0, 1, 1, "<=")  # x1 >= -1, weaker than x1 >= 0
    assert empty_dbm.includes(looser)
    assert not looser.includes(empty_dbm)
    assert empty_dbm.includes(empty_dbm.close())


@pytest.mark.unit
def test_includes_tells_strict_from_non_strict():
    """x1 >= -1 strict is inside x1 >= -1 non-strict, not the reverse."""
    strict, closed = DBM(2), DBM(2)
    strict.add_initial_constraint(0, 1, 1, "<")
    closed.add_initial_constraint(0, 1, 1, "<=")
    assert strict.includes(closed)
    assert not closed.includes(strict)


@pytest.mark.unit
def test_close_raises_on_negative_cycle():
    """x1 - x0 >= -1 ... around a cycle summing to -2 has no solution."""
    dbm = DBM(3)
    dbm.add_initial_constraint(0, 1, 1, "<=")
    dbm.add_initial_constraint(1, 2, -1, "<=")
    dbm.add_initial_constraint(2, 3, -1, "<=")
    dbm.add_initial_constraint(3, 0, -1, "<=")
    with pytest.raises(ValueError, match="not consistent"):
        dbm.close()


@pytest.mark.unit
def test_close_tightens_bounds(constraint_dbm):
    """x2 = x1 + 10 and x2 <= 20 give x1 <= 10, tighter than x1 < 20."""
    expected = DBM(2)
    expected.add_constraint(1, 0, 10, "<=")
    expected.add_constraint(2, 0, 20, "<=")
    expected.add_constraint(2, 1, 10, "<=")
    expected.add_constraint(1, 2, -10, "<=")
    assert expected == constraint_dbm.close()


@pytest.mark.unit
def test_close_bouyer_example():
    """Bouyer et al. (2018), Model Checking Timed Automata, p. 24."""
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
    """x1 - x2 <= 1 is kept; adding x2 - x1 <= -10 contradicts it."""
    empty_dbm.add_constraint(1, 2, 1)
    assert empty_dbm.elements[1][2].constant == 1
    empty_dbm.add_constraint(2, 1, -10)
    assert empty_dbm.is_empty()


@pytest.mark.unit
def test_reset_sets_clock_value(constraint_dbm):
    """After x1 := 5 the zone has x1 = 5 and stays canonical."""
    constraint_dbm.reset(1, 5)
    assert constraint_dbm.elements[1][0].constant == 5
    assert constraint_dbm.elements[0][1].constant == -5
    assert constraint_dbm == constraint_dbm.close()


@pytest.mark.unit
def test_guard_then_reset_sequence():
    """x1 = 5 then x1 := 0 gives x1 = 0; x2 > 5 is still satisfiable."""
    dbm = DBM(2)
    dbm.add_constraint(1, 0, 5)
    dbm.add_constraint(0, 1, -5)
    dbm.reset(1)
    assert dbm.elements[1][0].constant == 0
    assert dbm.elements[0][1].constant == 0
    dbm.add_constraint(0, 2, -5, "<")
    assert not dbm.is_empty()


@pytest.mark.unit
def test_down_removes_the_lower_bound():
    """The time predecessors of x1 >= 3 are all x1 >= 0."""
    dbm = DBM(1)
    dbm.add_constraint(0, 1, -3)
    dbm.down()
    assert dbm.elements[0][1].constant == 0
    assert not dbm.is_empty()


@pytest.mark.unit
def test_up_preserves_canonicity(constraint_dbm):
    """Letting time pass on a closed zone leaves it closed."""
    dbm = constraint_dbm.close()
    dbm.up()
    assert dbm == dbm.close()


@pytest.mark.unit
def test_k_normalize():
    """With max constants (2, 1), x2 >= 2 becomes x2 > 1 and the upper bounds go."""
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
def test_k_normalize_past_the_max_constant():
    """10 <= x <= 20 with max constant 5 becomes x > 5 with no upper bound."""
    dbm = DBM(1)
    dbm.add_constraint(1, 0, 20, "<=")
    dbm.add_constraint(0, 1, -10, "<=")
    dbm.k_normalize([5])
    assert dbm.elements[1][0].constant == np.inf
    assert dbm.elements[0][1].constant == -5
    assert dbm.elements[0][1].operator == "<"


@pytest.mark.unit
def test_get_free(constraint_dbm):
    """Freeing x1 drops every bound on it and keeps x2 <= 20."""
    expected = DBM(2)
    expected.add_initial_constraint(2, 0, 20, "<=")
    expected.add_initial_constraint(2, 1, 20, "<=")
    assert expected == constraint_dbm.get_free(1)


@pytest.mark.unit
def test_copy_is_deep_and_independent(constraint_dbm):
    """Emptying a copy leaves the original zone as it was."""
    original = constraint_dbm.copy()
    assert original == constraint_dbm
    mutated = original.copy()
    mutated.add_constraint(2, 1, -100)
    assert not original.is_empty()
    assert mutated.is_empty()


@pytest.mark.unit
def test_intersect():
    """2 <= x <= 5 meet 4 <= x <= 8 is 4 <= x <= 5."""
    dbm1 = DBM(2)
    dbm1.add_constraint(1, 0, 5, "<=")
    dbm1.add_constraint(0, 1, -2, "<=")
    dbm2 = DBM(2)
    dbm2.add_constraint(1, 0, 8, "<=")
    dbm2.add_constraint(0, 1, -4, "<=")
    dbm1.intersect(dbm2)
    assert dbm1.elements[1][0].constant == 5
    assert dbm1.elements[0][1].constant == -4


@pytest.mark.unit
def test_intersect_disjoint():
    """x <= 3 meet x >= 5 is empty."""
    dbm1 = DBM(2)
    dbm1.add_constraint(1, 0, 3, "<=")
    dbm2 = DBM(2)
    dbm2.add_constraint(0, 1, -5, "<=")
    dbm1.intersect(dbm2)
    assert dbm1.is_empty()
