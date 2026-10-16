"""Explanation of an extracted document in English, Tamil and Hindi.

Each language text carries its own status, verification record and display mode: English can verify while Tamil fails.
Unverified model text is never presented as verified; the fallback is the original extracted English plus a notice.
"""

from typing import Literal

from pydantic import BaseModel, Field, computed_field

Lang = Literal["en", "ta", "hi"]
LANGS: tuple[str, ...] = ("en", "ta", "hi")
Kind = Literal["disclaimer", "medicine", "follow_up", "advice", "warning", "not_found"]
LineStatus = Literal["template", "verified", "unverified", "original_only"]
DisplayMode = Literal["explanation", "original_with_notice"]
# not_required: English fixed text written by the authors. Every Tamil/Hindi string and every model-written line starts as draft_unreviewed.
ReviewStatus = Literal["draft_unreviewed", "reviewed", "not_required"]
Verdict = Literal["supported", "adds_information", "omits_information", "contradicts", "unclear"]
Level = Literal["must_confirm", "note", "none"]
# Where a displayed text came from. model_checked = written by the local model and passed software checks (never by a human).
Provenance = Literal["template", "phrase_library", "model_checked", "original_only"]
LabelKey = Literal["native_reviewed", "draft_unreviewed", "machine_checked", "original_only"]


def label_key(provenance: str, review_status: str) -> str | None:
    """Trust label for one displayed text. RULE: only a fixed (template / phrase_library) text whose review_status is `reviewed`
    can be native_reviewed; a model-written text is machine_checked whatever its review_status says. Authored English
    (review_status not_required) has no human-review claim to make, so it gets no label (None)."""
    if provenance == "original_only":
        return "original_only"
    if provenance == "model_checked":
        return "machine_checked"
    return {"reviewed": "native_reviewed", "draft_unreviewed": "draft_unreviewed"}.get(review_status)


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
    provenance: Provenance = "template"
    label: str | None = Field(None, description="Rendered label text (phrase_library and model_checked lines); the key is label_key.")

    @computed_field
    @property
    def label_key(self) -> str | None:
        return label_key(self.provenance, self.review_status)


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
    provenance: Provenance = Field("template", description="Line-level summary; the per-language LangText.provenance is authoritative (languages fall back independently).")
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
