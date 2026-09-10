"""Guards the top-level `automata` public API surface: every name in
`__all__` must actually be importable from the package root. Pure Python
(no Spot dependency), this is about import wiring, not behavior."""

import model_checker.automata as automata


def test_all_names_are_actually_importable_from_package_root():
    for name in automata.__all__:
        assert hasattr(automata, name), f"{name!r} listed in __all__ but not importable"


def test_pipeline_pieces_are_exported_at_top_level():
    # M5's whole point was making product() -> concurrent_to_turnbased() compose;
    # both (plus remap_priorities) must be reachable as `automata.<name>`,
    # not just via their submodules.
    assert automata.product is not None
    assert automata.concurrent_to_turnbased is not None
    assert automata.remap_priorities is not None
