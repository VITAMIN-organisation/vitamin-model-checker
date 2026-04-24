"""Unified logic discovery for the VITAMIN core library."""

import logging
from pathlib import Path
from typing import Any, List
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)


def get_entry_points(group: str) -> List[Any]:
    """Gets entry points for the specified group in a cross-version way."""
    eps = entry_points()
    if hasattr(eps, "select"):
        return eps.select(group=group)
    return eps.get(group, [])


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
    """Discover a logic-related resource via entry points.

    Args:
        logic_name: Name of the logic or resource key.
        group: Entry point group to search in (e.g. 'vitamin.parsers').
        resource_type_label: Label for error messages.

    Returns:
        The discovered resource (module, class, or callable).

    Raises:
        ImportError: If the resource exists but fails to load.
        LookupError: If the resource name is unknown.
    """
    eps = get_entry_points(group)
    for ep in eps:
        if ep.name == logic_name:
            try:
                return ep.load()
            except Exception as e:
                error_msg = f"{resource_type_label} '{logic_name}' is registered via entry points but failed to load: {e}"
                logger.error(error_msg)

    raise LookupError(f"Unknown {resource_type_label.lower()}: '{logic_name}'.")
