import json

import pytest
from pydantic import ValidationError

from app.schemas.extraction import SCHEMA_PATH, ExtractedDocument, SourceSpan, export_schema


def span(text="Tab Metformin 500 mg BD", start=10):
    return {"start": start, "end": start + len(text), "text": text}


def valid():
    return {
        "document_type": "prescription",
        "medications": [
            {
                "generic_name": "Metformin",
                "strength": "500 mg",
                "form": "tablet",
                "route": "oral",
                "dose": "1 tablet",
                "frequency": {"times_per_day": 2, "timing_label": "after_meals", "original_abbreviation": "BD", "is_prn": False},
                "source_span": span(),
            }
        ],
    }


def test_valid_object():
    d = ExtractedDocument.model_validate(valid())
    assert d.medications[0].frequency.times_per_day == 2
    assert d.document_language == "en"


def test_missing_required_field():
    bad = valid()
    del bad["medications"][0]["source_span"]
    with pytest.raises(ValidationError):
        ExtractedDocument.model_validate(bad)


def test_bad_enum():
    bad = valid()
    bad["medications"][0]["form"] = "lozenge"
    with pytest.raises(ValidationError):
        ExtractedDocument.model_validate(bad)


def test_offsets_sanity():
    with pytest.raises(ValidationError):
        SourceSpan(start=5, end=3, text="")
    with pytest.raises(ValidationError):
        SourceSpan(start=0, end=5, text="abc")
    with pytest.raises(ValidationError):
        SourceSpan(start=-1, end=2, text="abc")


def test_json_schema_export_matches_model():
    assert json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) == json.loads(export_schema())


def test_round_trip():
    d = ExtractedDocument.model_validate(valid())
    assert ExtractedDocument.model_validate_json(d.model_dump_json()) == d


def test_negative_duration_rejected():
    bad = valid()
    bad["medications"][0]["duration_days"] = -3
    with pytest.raises(ValidationError):
        ExtractedDocument.model_validate(bad)
