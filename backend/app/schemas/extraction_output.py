"""What the model returns from a document image/text. Differs from ExtractedDocument (ground truth):
offsets are replaced by an exact `source_quote`, and items carry a confidence."""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.extraction import DocumentType, ExtractedDocument, Form, Route, TimingLabel

SCHEMA_VERSION = "1"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class OutFrequency(BaseModel):
    times_per_day: int | None = Field(None, description="Doses per day; null if unstated or PRN.")
    timing_label: TimingLabel = Field(description="unspecified if a frequency is stated but no time of day or meal relation.")
    original_abbreviation: str | None = Field(None, description='Frequency shorthand exactly as written, e.g. "BD".')
    is_prn: bool = Field(False, description="True only if taken as needed (SOS/PRN).")


class OutMedication(BaseModel):
    brand_name: str | None = Field(None, description="Brand name as written; null if none written.")
    generic_name: str | None = Field(None, description="Generic name as written; null if none written.")
    strength: str | None = Field(None, description='e.g. "500 mg"; null if not written.')
    form: Form
    route: Route
    dose: str | None = Field(None, description='Amount per intake, e.g. "1 tablet"; null if not written.')
    frequency: OutFrequency
    duration_days: int | None = Field(None, description="Duration in days; null if not written.")
    duration_text: str | None = Field(None, description="Duration exactly as written.")
    special_instructions: str | None = None
    source_quote: str = Field(description="Exact text copied from the document for this medicine.")
    confidence: Confidence


class OutFollowUp(BaseModel):
    description: str
    date_text: str | None = None
    days_from_discharge: int | None = None
    source_quote: str
    confidence: Confidence


class OutRedFlag(BaseModel):
    text: str
    source_quote: str
    confidence: Confidence


class ExtractionOutput(BaseModel):
    document_type: DocumentType
    document_language: str = "en"
    medications: list[OutMedication] = Field(default_factory=list)
    follow_ups: list[OutFollowUp] = Field(default_factory=list)
    red_flags: list[OutRedFlag] = Field(default_factory=list)
    diet_activity_advice: list[str] = Field(default_factory=list)
    unreadable_parts: list[str] = Field(default_factory=list, description="Short notes on anything that could not be read.")


def from_ground_truth(doc: ExtractedDocument) -> ExtractionOutput:
    """Ground truth in prediction format (used for the oracle evaluation run)."""
    d = doc.model_dump(mode="json")
    for m in d["medications"]:
        m["source_quote"] = m.pop("source_span")["text"]
        m["confidence"] = "high"
    for k, f in (("follow_ups", "description"), ("red_flags", "text")):
        for x in d[k]:
            x["source_quote"] = x.pop("source_span")["text"]
            x["confidence"] = "high"
    return ExtractionOutput.model_validate({**d, "unreadable_parts": []})
