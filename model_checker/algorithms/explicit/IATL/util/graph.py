"""Graph extraction and model file loading for IATL BCGS models."""

from model_checker.algorithms.explicit.IATL.util.validation import (
    check_conditions_hold,
)
from model_checker.algorithms.explicit.shared.model_io import (
    SECTION_HANDLERS,
    read_sectioned_model_file,
)


def read_file(filename):
    """Load and validate an IATL BCGS model from a text file."""
    data = read_sectioned_model_file(
        filename=filename,
        initial_data={
            "graph": [],
            "preorder": [],
            "states": [],
            "atomic_propositions": [],
            "matrix_prop": [],
            "initial_state": "",
            "states_counter": 0,
            "atomic_propositions_counter": 0,
            "number_of_agents": 0,
        },
        section_handlers=SECTION_HANDLERS,
        extra_array_dtypes={"preorder": int},
    )

    check_conditions_hold(data)
    return data
