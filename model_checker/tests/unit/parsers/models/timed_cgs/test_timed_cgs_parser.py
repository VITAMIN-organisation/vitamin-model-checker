"""timedCGS files: the Clocks, Clock_constraints and Invariants sections.

Clock_constraints holds one cell per transition (guards and resets, `0`, `*` or
`-` for none); Invariants holds one row per state and allows only `<` and `<=`.
"""

from pathlib import Path

import pytest

from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.timed_cgs import timed_cgs_parser
from model_checker.parsers.game_structures.timed_cgs.timed_cgs import TimedCGS

_FIXTURE = (
    Path(__file__).resolve().parents[4] / "fixtures/timedCGS/tctl_tol_minimal.txt"
)


def _sections(*lines, states=("s0", "s1")):
    """Parse only the timed sections of `lines` for a model with `states`."""
    instance = type("Timed", (), {})()
    instance.states = list(states)
    timed_cgs_parser.parse_timed_sections([f"{line}\n" for line in lines], instance)
    return instance


@pytest.mark.unit
def test_fixture_loads_clocks_guards_and_invariants():
    """The minimal TCTL/TOL fixture: one clock x, guard x<=1, invariant x<=2 at s0."""
    model = TimedCGS()
    model.read_file(_FIXTURE)
    assert list(model.states) == ["s0", "s1"]
    assert model.clocks_dict == {"x": 0}
    assert model.clock_constraint_struct[0][0] == "x<=1"
    assert model.invariants_arr[0] == [("x", "<=", 2.0)]


@pytest.mark.unit
def test_cells_keep_guards_with_resets_and_empty_markers_are_empty():
    """`x>=1,x=0` stays one cell; `-`, `0` and `*` mean no constraint."""
    parsed = _sections("Clocks", "x", "Clock_constraints", "x>=1,x=0 -", "0 *")
    assert parsed.clock_constraint_struct == [["x>=1,x=0", ""], ["", ""]]


@pytest.mark.unit
def test_two_clocks_on_one_line():
    """`x y` declares two clocks, each with its own guard cell."""
    parsed = _sections("Clocks", "x y", "Clock_constraints", "x<=1 y>=2", "0 0")
    assert parsed.clocks == ["x", "y"]
    assert parsed.clock_constraint_struct[0] == ["x<=1", "y>=2"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("section", "cell", "message"),
    [
        (
            "Clock_constraints",
            "x>3y 0",
            "Malformed clock constraint 'x>3y' at row 0, column 0",
        ),
        ("Invariants", "x>=5", "Malformed invariant 'x>=5' at location 0"),
    ],
)
def test_malformed_constraint_is_refused_with_its_place(section, cell, message):
    """A broken guard, or a lower bound used as an invariant, names the cell."""
    with pytest.raises(ValueError, match=message):
        _sections("Clocks", "x", section, cell, "0 0")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("Goal", "Clock 'Goal' is invalid"),
        ("P", "Clock 'P' is invalid"),
        ("Next", "Clock 'Next' clashes with reserved keyword"),
        ("true", "Clock 'true' clashes with reserved keyword"),
        ("with", "Clock 'with' clashes with reserved keyword"),
    ],
)
def test_clock_name_follows_the_name_rule(name, message):
    """A TCTL or TOL formula cannot name these clocks, so the model may not declare them."""
    with pytest.raises(ValueError, match=message):
        _sections("Clocks", f"x {name}")


@pytest.mark.unit
def test_core_section_header_ends_the_invariants():
    """A row after `Number_of_agents` is not an invariant of the next state."""
    parsed = _sections("Invariants", "x<=2", "Number_of_agents", "x<=9", states=("s0",))
    assert parsed.invariants_arr == [[("x", "<=", 2.0)]]


@pytest.mark.unit
@pytest.mark.parametrize("comment", ["# note", "// note"])
def test_comments_are_neither_rows_nor_clocks(comment):
    """A comment line between rows does not shift the rows after it."""
    parsed = _sections(
        "Clocks", "x", comment,
        "Clock_constraints", comment, "x<=1 0", comment, "x>=2 0",
        "Invariants", comment, "x<=2",
    )  # fmt: skip
    assert parsed.clocks == ["x"]
    assert [row[0] for row in parsed.clock_constraint_struct] == ["x<=1", "x>=2"]
    assert parsed.invariants_arr[0] == [("x", "<=", 2.0)]


@pytest.mark.unit
def test_timed_sections_are_dropped_before_the_cgs_parser_runs():
    """The CGS parser must not see Clocks rows; cost sections pass through."""
    lines = [
        "Transition",
        "0",
        "Clocks",
        "x",
        "Costs_for_actions",
        "a s0$1",
        "Name_State",
        "s0",
    ]
    filtered = cgs_parser.filter_lines_for_common_sections(
        lines,
        timed_cgs_parser.TIMED_SECTION_HEADERS,
        exit_skip_on=cgs_parser.SECTION_HEADERS | cgs_parser.EXTENSION_SECTION_HEADERS,
    )
    assert filtered == [
        "Transition",
        "0",
        "Costs_for_actions",
        "a s0$1",
        "Name_State",
        "s0",
    ]
