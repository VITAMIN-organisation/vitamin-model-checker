"""Unified logic discovery for the VITAMIN core library."""

import logging
from functools import cache
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@cache
def get_entry_points(group: str) -> tuple[Any, ...]:
    """The entry points of `group`. Cached: each scan of the installed packages
    takes about 2 ms, and they do not change while the process runs."""
    eps = entry_points()
    if hasattr(eps, "select"):
        return tuple(eps.select(group=group))
    return tuple(eps.get(group, []))


def is_integrated_logic(logic_name: str) -> bool:
    """Check if the logic name exists in the integration registry.

    The registry is located at the repository root in '.vmi-integrated-modules/'.
    """
    try:
        current = Path(__file__).resolve()
        root = current.parents[1]
        registry_dir = root / ".vmi-integrated-modules"
        if not registry_dir.is_dir():
            return False

        manifest_file = registry_dir / f"{logic_name}.json"
        return manifest_file.is_file()
    except Exception:
        return False


def discover_logic_resource(
    logic_name: str,
    group: str,
    resource_type_label: str = "Logic resource",
) -> Any:
    """Load the resource `logic_name` from the entry point `group`, such as
    `vitamin.parsers`."""
    eps = get_entry_points(group)
    for ep in eps:
        if ep.name == logic_name:
            try:
                return ep.load()
            except Exception as e:
                error_msg = (
                    f"{resource_type_label} '{logic_name}' is registered via entry "
                    f"points but failed to load: {e}"
                )
                logger.error(error_msg)
                raise ImportError(error_msg) from e

    raise LookupError(f"Unknown {resource_type_label.lower()}: '{logic_name}'.")
