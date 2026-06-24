"""Core registries for built-in VITAMIN logics and model types."""

import logging
from typing import Any

from model_checker.discovery import discover_logic_resource

logger = logging.getLogger(__name__)


def _load_logic_metadata(logic_type: str) -> dict[str, Any] | None:
    """Return vitamin.metadata entry for a logic, or None when unavailable."""
    try:
        metadata = discover_logic_resource(
            logic_name=logic_type,
            group="vitamin.metadata",
            resource_type_label="Metadata",
        )
        if isinstance(metadata, dict):
            return metadata
    except LookupError:
        pass
    except ImportError as exc:
        logger.error(str(exc))
    return None


def get_expected_model_type(logic_type: str) -> str | None:
    """Detect the expected model type for a given logic name.

    Uses standard entry points discoverable via 'vitamin.metadata'.
    """
    metadata = _load_logic_metadata(logic_type)
    if metadata and "model_type" in metadata:
        return metadata["model_type"]
    return "CGS"


def get_benchmark_group(logic_type: str) -> str:
    """Return the model family used for synthetic model generation.

    Prioritizes 'benchmark_group' in metadata, falling back to 'model_type'.
    """
    metadata = _load_logic_metadata(logic_type)
    if metadata:
        if "benchmark_group" in metadata:
            return metadata["benchmark_group"]
        if "model_type" in metadata:
            return metadata["model_type"]
    return "CGS"
