"""Reference implementation of the Cortical-Column Memory (CCM) protocol.

The package is deliberately dependency-free.  It provides inspectable data
contracts and a deterministic symbolic adapter for the repository smoke test;
it is not a claim that a symbolic adapter is a language-model result.
"""

__version__ = "0.1.0"

from ccm.schemas.models import (
    ActionResult,
    ColumnState,
    EvidenceAction,
    Hypothesis,
    Observation,
    Prediction,
    Relation,
    ReferenceFrame,
    State,
    Transition,
    Vote,
)

__all__ = [
    "ActionResult",
    "ColumnState",
    "EvidenceAction",
    "Hypothesis",
    "Observation",
    "Prediction",
    "Relation",
    "ReferenceFrame",
    "State",
    "Transition",
    "Vote",
    "__version__",
]
