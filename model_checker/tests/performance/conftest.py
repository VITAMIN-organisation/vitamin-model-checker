from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
# A case with `max_time` is stopped at this multiple of it, so a hang fails the
# run instead of blocking it; the case itself still asserts elapsed < max_time.
_TIMEOUT_FACTOR = 3


def pytest_collection_modifyitems(items):
    """Mark the tests of this directory as performance tests and give each case
    with a `max_time` parameter a timeout (pytest ignores `pytestmark` in a conftest).
    """
    for item in items:
        if _HERE not in Path(item.path).parents:
            continue
        item.add_marker(pytest.mark.performance)
        callspec = getattr(item, "callspec", None)
        max_time = callspec.params.get("max_time") if callspec else None
        if max_time is not None and item.get_closest_marker("timeout") is None:
            item.add_marker(pytest.mark.timeout(_TIMEOUT_FACTOR * max_time))
