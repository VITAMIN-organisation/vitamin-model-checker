"""The model factory picks the parser from the section headers of the file.

A header counts only as a whole line, so a proposition named `hasWalletsFlag` does
not make a file a WalletCGS. When a file has several extension headers, the order
in detect_model_type_from_content decides.
"""

import pytest

from model_checker.models import model_factory
from model_checker.models.model_factory import (
    detect_model_type_from_content,
    detect_model_type_from_file,
)
from model_checker.parsers.game_structures.cgs import cgs_parser
from model_checker.parsers.game_structures.fuzzy_cgs.fuzzy_cgs import FuzzyCGS

_PLAIN = (
    "Transition\n*\nName_State\ns0\nInitial_State\ns0\n"
    "Atomic_propositions\n{props}\nLabelling\n1\nNumber_of_agents\n1\n"
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("headers", "model_type"),
    [
        ("Number_of_demons\n1\n", "ObstructionModel"),
        ("Wallets\ns0: 1\n", "WalletCGS"),
        ("Clocks\nx\n", "timedCGS"),
        ("Clock_constraints\nx>=1\n", "timedCGS"),
        ("Transition_With_Costs\n*\n", "costCGS"),
        ("Costs_for_actions\nI s0$1\n", "costCGS"),
        ("Costs_for_actions_split\nAA s0$1\n", "costCGS"),
        ("Capacities\nc\n", "capCGS"),
        ("Capacities_assignment\n1\n", "capCGS"),
        ("Preorder\n1\n", "BCGS"),
        ("Wallets\ns0: 1\nClocks\nx\n", "WalletCGS"),
        ("Number_of_demons\n1\nWallets\ns0: 1\n", "ObstructionModel"),
    ],
)
def test_extension_header_selects_the_model_type(headers, model_type):
    """Each extension header maps to one parser; Wallets wins over Clocks, demons over all."""
    assert (
        detect_model_type_from_content(_PLAIN.format(props="p") + headers) == model_type
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "name", ["hasWalletsFlag", "hasCosts_for_actionsFlag", "Clocks1"]
)
def test_header_inside_a_name_is_not_a_header(name):
    """Detection reads whole lines, not substrings."""
    assert detect_model_type_from_content(_PLAIN.format(props=name)) == "CGS"


@pytest.mark.unit
@pytest.mark.parametrize("comment", ["", "// frame\n"])
def test_birelational_cells_select_the_birelational_matrix(comment):
    """ICTL frames write transition cells as P, R or P,R instead of joint actions.

    A `//` line is a comment, as in the parsers, not a transition row.
    """
    content = (
        f"Transition\n{comment}P,R P\n0 P,R\nName_State\ns0 s1\nInitial_State\ns0\n"
        "Atomic_propositions\ne\nLabelling\n1\n0\nNumber_of_agents\n1\n"
    )
    assert detect_model_type_from_content(content) == "BirelationalMatrix"


@pytest.mark.unit
def test_cgs_with_only_r_actions_is_not_birelational():
    """Without a P marker, an `R` cell is a joint action of a CGS."""
    content = (
        "Transition\nR 0\n0 R\nName_State\ns0 s1\nInitial_State\ns0\n"
        "Atomic_propositions\ne\nLabelling\n1\n0\nNumber_of_agents\n1\n"
    )
    assert detect_model_type_from_content(content) == "CGS"


@pytest.mark.unit
def test_detection_knows_every_header_the_cgs_parser_knows():
    """The factory keeps its own header list; a header missing there would end the Transition scan early or late."""
    assert model_factory._MODEL_SECTION_HEADERS == (
        cgs_parser.SECTION_HEADERS | cgs_parser.EXTENSION_SECTION_HEADERS
    )


@pytest.mark.unit
def test_atlf_reads_its_model_as_fuzzy_cgs(tmp_path):
    """A fuzzyCGS file has only CGS headers, so the logic, not detection, picks it."""
    path = tmp_path / "model.txt"
    path.write_text(_PLAIN.format(props="p"))
    assert detect_model_type_from_content(path.read_text()) == "CGS"
    assert isinstance(
        model_factory.create_model_parser_for_logic(str(path), "ATLF"), FuzzyCGS
    )


@pytest.mark.unit
def test_missing_file_is_an_error_naming_it(tmp_path):
    """A wrong path fails before any parsing, with the path in the message."""
    missing = tmp_path / "nope.txt"
    with pytest.raises(FileNotFoundError, match="nope.txt"):
        detect_model_type_from_file(str(missing))
