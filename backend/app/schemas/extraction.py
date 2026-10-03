"""Structured output of document extraction. Every extracted field traces to the source text via SourceSpan."""

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class DocumentType(str, Enum):
    discharge_summary = "discharge_summary"
    prescription = "prescription"


class TimingLabel(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"
    with_meals = "with_meals"
    before_meals = "before_meals"
    after_meals = "after_meals"
    bedtime = "bedtime"
    as_needed = "as_needed"
    unspecified = "unspecified"  # frequency stated but no time of day / meal relation
    other = "other"  # genuinely unusual instruction


class Form(str, Enum):
    tablet = "tablet"
    capsule = "capsule"
    syrup = "syrup"
    injection = "injection"
    ointment = "ointment"
    drops = "drops"
    inhaler = "inhaler"
    other = "other"


class Route(str, Enum):
    oral = "oral"
    topical = "topical"
    injection = "injection"
    inhalation = "inhalation"
    other = "other"


class SourceSpan(BaseModel):
    """Character offsets into the document text; text must equal document[start:end]."""

    start: int = Field(ge=0, description="Start offset (inclusive).")
    end: int = Field(ge=0, description="End offset (exclusive).")
    text: str = Field(description="Exact source text at [start:end].")

    @model_validator(mode="after")
    def _offsets_consistent(self):
        if self.end < self.start:
            raise ValueError("end must be >= start")
        if self.end - self.start != len(self.text):
            raise ValueError("span length does not match text length")
        return self


class Frequency(BaseModel):
    """How often a medicine is taken."""

    times_per_day: int | None = Field(None, ge=0, description="Doses per day; null if unstated or PRN.")
    timing_label: TimingLabel = Field(description="When in the day / relative to meals.")
    original_abbreviation: str | None = Field(None, description='Shorthand as written, e.g. "BD", "TDS", "SOS".')
    is_prn: bool = Field(False, description="True if taken only as needed.")


class Medication(BaseModel):
    """One medicine as written in the document. Do not infer fields that are not stated."""

    brand_name: str | None = Field(None, description="Brand name as written, if any.")
    generic_name: str | None = Field(None, description="Generic name as written, if any.")
    strength: str | None = Field(None, description='e.g. "500 mg".')
    form: Form
    route: Route
    dose: str | None = Field(None, description='Amount per intake, e.g. "1 tablet".')
    frequency: Frequency
    duration_days: int | None = Field(None, ge=0, description="Duration in days, if stated.")
    duration_text: str | None = Field(None, description='Duration as written, e.g. "x 5/7".')
    special_instructions: str | None = Field(None, description="Other instructions written for this medicine.")
    source_span: SourceSpan = Field(description="Span covering the medicine line/entry.")


class FollowUp(BaseModel):
    """A follow-up visit or test mentioned in the document."""

    description: str
    date_text: str | None = Field(None, description="Date/timeframe as written.")
    days_from_discharge: int | None = Field(None, ge=0)
    source_span: SourceSpan


class RedFlag(BaseModel):
    """A warning sign that appears IN the document. Never invented."""

    text: str
    source_span: SourceSpan


class ExtractedDocument(BaseModel):
    """Full extraction result for one document."""

    document_type: DocumentType
    medications: list[Medication] = Field(default_factory=list)
    follow_ups: list[FollowUp] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    diet_activity_advice: list[str] = Field(default_factory=list, description="Advice lines as written.")
    document_language: str = "en"


SCHEMA_PATH = Path(__file__).with_name("extraction.schema.json")


def export_schema() -> str:
    return json.dumps(ExtractedDocument.model_json_schema(), indent=2) + "\n"


if __name__ == "__main__":
    SCHEMA_PATH.write_text(export_schema(), encoding="utf-8")
