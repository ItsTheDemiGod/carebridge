"""Medication after rule-based normalisation. Every changed value keeps the model's value, the rule's value and its provenance."""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.extraction import DocumentType, Form, Route
from app.schemas.extraction_output import Confidence, OutFollowUp, OutRedFlag


class Provenance(str, Enum):
    rule = "rule"  # derived from the quote by the abbreviation table (final value)
    model = "model"  # the rules derived nothing; the model's value is kept
    conflict = "conflict"  # rule and model disagree; the rule value is final and a conflict flag is raised


class Sourced(BaseModel):
    """A final value plus where it came from."""

    value: int | str | bool | None = None
    provenance: Provenance = Provenance.model
    model_value: int | str | bool | None = None
    rule_value: int | str | bool | None = None


class NormalisedFrequency(BaseModel):
    times_per_day: Sourced
    timing_label: Sourced
    is_prn: Sourced
    original_abbreviation: str | None = None


class NormalisedMedication(BaseModel):
    # names: as written by the model, what the document prints (formulary spelling), and the formulary's generic
    as_written_brand_name: str | None = None
    as_written_generic_name: str | None = None
    printed_brand: str | None = None
    printed_generic: str | None = None
    resolved_generic: str | None = Field(None, description='Generic from the formulary for the printed drug; provenance "formulary", not from the document.')
    resolved_generic_provenance: str | None = None
    brand_name: str | None = Field(None, description="Final brand: printed in the document, else the model's unknown-to-formulary name if it is in the quote.")
    generic_name: str | None = None
    name_match_type: str = "none"  # exact | fuzzy | none
    near_miss_name: str | None = None

    strength: str | None = None
    form: Form
    route: Route
    dose: str | None = None
    frequency: NormalisedFrequency
    duration_days: Sourced
    duration_text: str | None = None
    special_instructions: str | None = None
    source_quote: str
    confidence: Confidence

    flags: list[str] = Field(default_factory=list)
    needs_verification: bool = False
    reasons: list[str] = Field(default_factory=list)


class NormalisedDocument(BaseModel):
    document_type: DocumentType
    document_language: str = "en"
    medications: list[NormalisedMedication] = Field(default_factory=list)
    follow_ups: list[OutFollowUp] = Field(default_factory=list)
    red_flags: list[OutRedFlag] = Field(default_factory=list)
    diet_activity_advice: list[str] = Field(default_factory=list)
    unreadable_parts: list[str] = Field(default_factory=list)
