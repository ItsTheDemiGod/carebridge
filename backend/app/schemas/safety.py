"""Safety report for one normalised document. Data only: fixed templates turn it into user text (services/explain.py).

Statuses are exactly four: interaction_found, not_checked_no_record, not_checked_unconfirmed, not_checked_database_missing.
The report can say "an interaction was found" or "we could not check"; it never says a combination is safe."""

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["interaction_found", "not_checked_no_record", "not_checked_unconfirmed", "not_checked_database_missing"]
Level = Literal["major", "moderate", "minor", "unknown"]
OverallState = Literal["confirm_first", "review_interactions", "ok_to_review"]  # internal names; never shown to users


class PairResult(BaseModel):
    a: int = Field(description="Index of the first medicine row (a < b).")
    b: int
    generic_a: str | None = Field(None, description="Formulary generic used for the lookup; None when that medicine is not interaction_ready.")
    generic_b: str | None = None
    status: Status
    level: Level | None = None
    source: Literal["ddinter", "curated_reviewed", "curated_author_checked"] | None = None
    same_medicine: bool = Field(False, description="Both rows are the same resolved generic: reported as a duplicate notice, not as an unchecked pair.")


class DuplicateNotice(BaseModel):
    indices: list[int]
    name: str = Field(description="The shared resolved generic or printed name.")
    basis: Literal["resolved_generic", "printed_name"]


class Counts(BaseModel):
    medicines: int
    must_confirm: int
    interaction_ready: int
    pairs: int
    pairs_by_status: dict[str, int]
    interactions_by_level: dict[str, int]


class SafetyReport(BaseModel):
    pair_results: list[PairResult]
    duplicate_notices: list[DuplicateNotice]
    counts: Counts
    overall_state: OverallState
    schedule_reminder: list[int] = Field(default_factory=list, description="Medicine rows with an unspecified or non-daily frequency; points to their existing notices (no alarm).")
    supplement_reviewed: bool = Field(False, description="True when the supplement has enabled entries, none pending and none author_checked; selects the attribution line.")
    supplement_author_checked: bool = Field(False, description="True when at least one enabled supplement entry is author_checked (prototype self-check, NOT a pharmacist review).")
    supplement_ignored: int = Field(0, description="Supplement entries ignored because they are not reviewed.")
