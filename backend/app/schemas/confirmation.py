"""User decisions in the confirm-first step. Strict models (unknown fields are rejected). Rules and invariants: docs/CONFIRMATION.md."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.extraction import TimingLabel
from app.schemas.normalised import NormalisedDocument, NormalisedMedication

# Fixed dose options for a medicine the user adds from the picker. Scheduling conveniences, not clinical statements.
DOSE_OPTIONS = ("1/2 tablet", "1 tablet", "2 tablets", "1 capsule", "2 capsules", "5 ml", "10 ml", "1 puff", "2 puffs", "1 drop", "2 drops", "1 application")
AS_ON_LABEL = "as_on_my_label"
Action = Literal["confirm_as_extracted", "select_formulary_drug", "not_in_list", "remove"]
TimesPerDay = Annotated[int, Field(ge=1, le=6)] | Literal["as_needed"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScheduleEdit(Strict):
    times_per_day: TimesPerDay
    timing_label: TimingLabel
    duration_days: int | None = Field(None, ge=1, le=365)


class MedicineDecision(Strict):
    index: int = Field(ge=0)
    action: Action
    formulary_id: str | None = Field(None, max_length=80)
    strength_choice: str | None = Field(None, max_length=40)
    note: str | None = Field(None, max_length=80)  # stored, never used for any lookup
    schedule_edit: ScheduleEdit | None = None
    acknowledged_flags: list[str] = Field(default_factory=list, max_length=20)


class AddedMedicine(Strict):
    formulary_id: str = Field(max_length=80)
    strength_choice: str = Field(max_length=40)
    dose: Literal[DOSE_OPTIONS]
    schedule: ScheduleEdit


class Confirmations(Strict):
    decisions: list[MedicineDecision] = Field(default_factory=list, max_length=40)
    added_medicines: list[AddedMedicine] = Field(default_factory=list, max_length=10)


Resolution = Literal["unchanged", "confirmed", "selected", "not_in_list", "added"]


class ConfirmedMedicine(BaseModel):
    """One medicine after the overlay: the updated COPY plus where each changed value came from."""

    ref: str = Field(description="Stable reference: m<source index> for extracted medicines, a<k> for added ones.")
    source_index: int | None = None
    resolution: Resolution
    med: NormalisedMedication
    provenance: dict[str, str] = Field(default_factory=dict, description="field -> rule | model | formulary | user_selected | user_confirmed | user_added")
    unresolved: list[str] = Field(default_factory=list, description="Reason ids still open; non-empty means the medicine stays must_confirm.")
    not_checked_reason: Literal["not_identifiable", "needs_confirmation", "user_not_in_list"] | None = None


class Overlay(BaseModel):
    doc: NormalisedDocument = Field(description="Copy of the normalised document without removed medicines, with added ones appended.")
    meds: list[ConfirmedMedicine]
    removed: list[int] = Field(default_factory=list, description="Source indices the user removed.")
