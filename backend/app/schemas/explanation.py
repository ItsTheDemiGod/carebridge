"""Explanation of an extracted document in English, Tamil and Hindi.

Each language text carries its own status, verification record and display mode: English can verify while Tamil fails.
Unverified model text is never presented as verified; the fallback is the original extracted English plus a notice.
"""

from typing import Literal

from pydantic import BaseModel, Field

Lang = Literal["en", "ta", "hi"]
LANGS: tuple[str, ...] = ("en", "ta", "hi")
Kind = Literal["disclaimer", "medicine", "follow_up", "advice", "warning", "not_found"]
LineStatus = Literal["template", "verified", "unverified", "original_only"]
DisplayMode = Literal["explanation", "original_with_notice"]
# not_required: English fixed text written by the authors. Every Tamil/Hindi string and every model-written line starts as draft_unreviewed.
ReviewStatus = Literal["draft_unreviewed", "reviewed", "not_required"]
Verdict = Literal["supported", "adds_information", "omits_information", "contradicts", "unclear"]
Level = Literal["must_confirm", "note", "none"]


class Verification(BaseModel):
    """What was checked for one language text of one model-written line. Empty for template text."""

    deterministic: dict[str, bool] = Field(default_factory=dict, description="check name -> passed")
    deterministic_reasons: list[str] = Field(default_factory=list, description="exact reason for every failed check")
    judge_verdict: Verdict | None = None
    judge_reason: str | None = None
    candidate: str | None = Field(None, description="The model-written text that was checked. Kept for review; shown to the user ONLY when passed is True.")
    back_translation: str | None = Field(None, description="Tamil/Hindi only: literal English back-translation the judge saw.")
    passed: bool = False
    reason: str | None = Field(None, description="Why the line is not verified (first failing check, judge verdict, or model/call failure).")


class LangText(BaseModel):
    text: str
    status: LineStatus
    display_mode: DisplayMode = "explanation"
    review_status: ReviewStatus = "draft_unreviewed"
    verification: Verification = Field(default_factory=Verification)


class Notice(BaseModel):
    """A short fixed notice (must-confirm banner, flag notice) in all three languages."""

    code: str
    text: dict[str, LangText]


class ExplanationLine(BaseModel):
    line_id: str
    source_ref: int | None = Field(None, description="Index of the medication / follow-up / advice item / warning this line came from; null for not_found lines.")
    kind: Kind
    text: dict[str, LangText]
    source_text: str = Field(description="The extracted English exactly as returned by extraction (medicines: the verbatim source quote).")
    status: LineStatus = Field(description="template | verified (all three languages) | unverified (any language failed) | original_only (no model text).")
    display_mode: DisplayMode = Field(description="Summary: explanation only if every language shows its explanation. Each LangText has its own mode.")
    review_level: Level = "none"
    flags: list[str] = Field(default_factory=list, description="Normalisation flags to surface to the user.")
    notices: list[Notice] = Field(default_factory=list, description="Confirm banner and flag notices (medicines).")
    settled: bool = Field(False, description="Medicines only: True when review_level is not must_confirm AND the schedule is ready. A False value must never be presented as settled.")


class Section(BaseModel):
    id: Literal["disclaimer", "medicines", "follow_ups", "advice", "warnings", "not_found"]
    heading: dict[str, str]
    lines: list[ExplanationLine] = Field(default_factory=list)


class ExplanationDocument(BaseModel):
    document_id: str | None = None
    document_type: str
    sections: list[Section]
    templates_version: str = ""
    prompt_version: str = ""
    model: str = ""

    def lines(self, kind: str | None = None) -> list[ExplanationLine]:
        return [ln for s in self.sections for ln in s.lines if kind is None or ln.kind == kind]
