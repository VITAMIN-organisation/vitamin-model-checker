"""Core registries for built-in VITAMIN logics and model types."""

import logging
from typing import Optional

from model_checker.discovery import discover_logic_resource

logger = logging.getLogger(__name__)


def get_expected_model_type(logic_type: str) -> Optional[str]:
    """Detect the expected model type for a given logic name.

    Uses standard entry points discoverable via 'vitamin.metadata'.
    """
    try:
        metadata = discover_logic_resource(
            logic_name=logic_type,
            group="vitamin.metadata",
            resource_type_label="Metadata",
        )
        if isinstance(metadata, dict) and "model_type" in metadata:
            return metadata["model_type"]
    except LookupError:
        pass
    except ImportError as e:
        logger.error(str(e))
        return None

    # Default to CGS for unknown logics
    return "CGS"
