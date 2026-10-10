import pytest

from app.normalisation import quote_check as qc

DOC = "Rx on discharge:\n1) Tab. Pantoprazole 40 mg\n   1 tab OD AC x 5/7\n2) Tab Glucophage 500 mg 1 tab BD PC x 10 days\n"


def test_exact_vs_normalised_exact_line_breaks_and_case():
    q = "Tab. Pantoprazole 40 mg 1 tab OD AC x 5/7"  # the document has a line break and indentation inside this entry
    assert not qc.exact(q, DOC) and qc.normalised_exact(q, DOC)
    assert qc.normalised_exact("TAB GLUCOPHAGE 500 MG 1 TAB BD PC X 10 DAYS.", DOC)  # case, trailing punctuation
    assert qc.normalised_exact("  - Tab Glucophage 500 mg 1 tab BD PC x 10 days ", DOC)  # leading punctuation, spaces
    assert qc.normalised_exact("Tab Glucophage 500 mg", DOC)  # non-breaking spaces (Unicode normalisation)
    assert not qc.normalised_exact("", DOC)


def test_strict_fuzzy_accepts_ocr_style_noise_with_same_digits():
    assert qc.strict_fuzzy("Tab Glucophage 500 mg 1 tab BD PC x 10 daya", DOC)  # one letter misread
    assert qc.strict_fuzzy("Tab. Pantoprazol 40 mg 1 tab OD AC x 5/7", DOC)


@pytest.mark.parametrize("quote", [
    "Tab Glucophage 50 mg 1 tab BD PC x 10 days",  # strength digit lost
    "Tab Glucophage 500 mg 1 tab BD PC x 16 days",  # changed duration digits
    "Tab Glucophage 600 mg 1 tab BD PC x 10 days",  # changed strength digits
    "Tab Atorvastatin 500 mg 1 tab BD PC x 10 days",  # different drug name
    "Tab Glucophage 500 mg 1 tab BD x 10 days",  # dropped dosing token PC
    "Tab Pantoprazole 40 mg 1 tab OD x 5/7",  # dropped AC
    "Totally different text about something else 123",
])
def test_strict_fuzzy_rejects_wrong_quotes(quote):
    assert not qc.strict_fuzzy(quote, DOC)


def test_digit_gate_rejects_high_similarity_with_different_digits():
    r = qc.check("Tab Glucophage 500 mg 1 tab BD PC x 16 days", DOC)
    assert r["ratio"] >= qc.STRICT_FUZZY_MIN and not r["digits_match"] and not r["strict_fuzzy"]


def test_check_reports_all_levels():
    r = qc.check("Tab Glucophage 500 mg 1 tab BD PC x 10 days", DOC)
    assert r["exact"] and r["normalised_exact"] and r["strict_fuzzy"]
