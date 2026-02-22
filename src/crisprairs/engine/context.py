"""Typed session context for CRISPR AI pipeline state.

SessionContext replaces untyped memory dicts with a structured dataclass
that holds all state accumulated during a pipeline run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class GuideRNA:
    """A single guide RNA candidate."""

    sequence: str = ""
    target_site: str = ""
    pam: str = ""
    strand: str = ""
    score: float = 0.0
    off_target_score: float = 0.0
    source: str = ""  # e.g. "crispor", "manual"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryInfo:
    """Delivery method selection results."""

    method: str = ""         # lipofection, electroporation, lentiviral, AAV, LNP
    format: str = ""         # plasmid, RNP, mRNA
    product: str = ""        # specific product recommendation
    reasoning: str = ""
    alternatives: str = ""


@dataclass
class PrimerPair:
    """A pair of validation primers."""

    forward: str = ""
    reverse: str = ""
    product_size: int = 0
    tm_forward: float = 0.0
    tm_reverse: float = 0.0
    blast_status: str = ""  # "specific", "non-specific", "pending", "error"


@dataclass
class SessionContext:
    """Typed, mutable session state shared across all pipeline steps.

    This replaces the untyped ``memory`` dict used by the old state machine.
    All workflow steps read from and write to this context.
    """

    # Session identity
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    # Core experiment parameters
    target_gene: str = ""
    species: str = ""
    modality: str = ""           # knockout, base_editing, prime_editing, activation, repression
    cas_system: str = ""         # SpCas9, SaCas9, enCas12a, etc.

    # Guide RNA results
    guides: list[GuideRNA] = field(default_factory=list)
    selected_guide_index: int = -1

    # Base editing specifics
    base_editor: str = ""        # CBE, ABE
    target_base_change: str = "" # e.g. "C>T at position 6"

    # Prime editing specifics
    prime_editor: str = ""       # PE2, PE3, PEmax
    pegrna_extension: str = ""
    nick_guide: str = ""

    # Activation/repression specifics
    effector_system: str = ""    # dCas9-VP64, dCas9-KRAB, etc.
    target_region: str = ""      # promoter, enhancer, etc.

    # Delivery
    delivery: DeliveryInfo = field(default_factory=DeliveryInfo)

    # Validation
    primers: list[PrimerPair] = field(default_factory=list)
    validation_strategy: str = ""

    # Off-target analysis
    off_target_results: list[dict[str, Any]] = field(default_factory=list)

    # Troubleshooting
    troubleshoot_issue: str = ""
    troubleshoot_recommendations: list[str] = field(default_factory=list)

    # Chat history for this session
    chat_history: list[tuple[str, str]] = field(default_factory=list)

    # Arbitrary extra data (escape hatch for workflow-specific state)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for JSON persistence."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionContext:
        """Reconstruct from a serialized dict.

        Handles nested dataclass fields (GuideRNA, DeliveryInfo, PrimerPair).
        """
        data = dict(data)  # shallow copy

        # Reconstruct nested types
        if "guides" in data:
            data["guides"] = [
                GuideRNA(**g) if isinstance(g, dict) else g
                for g in data["guides"]
            ]
        if "delivery" in data and isinstance(data["delivery"], dict):
            data["delivery"] = DeliveryInfo(**data["delivery"])
        if "primers" in data:
            data["primers"] = [
                PrimerPair(**p) if isinstance(p, dict) else p
                for p in data["primers"]
            ]

        # Filter to known fields only
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
