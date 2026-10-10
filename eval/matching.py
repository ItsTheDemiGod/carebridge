"""Normalisation, matching and per-document scoring. No dependencies beyond the stdlib (difflib)."""

import re
from collections import Counter
from difflib import SequenceMatcher

from app.normalisation import quote_check as qc

PREFIXES = {"tab", "t", "cap", "c", "inj", "syp", "syrup", "oint", "ointment", "inh", "inhaler", "tablet", "capsule", "injection"}
UNITS = {"tab": "tablet", "tabs": "tablet", "tablets": "tablet", "cap": "capsule", "caps": "capsule", "capsules": "capsule", "puff": "puffs", "ml": "ml"}
NAME_THRESHOLD = 0.8
TEXT_THRESHOLD = 0.6
FUZZY_QUOTE = 0.9
MED_FIELDS = ["strength", "form", "dose", "times_per_day", "timing_label", "is_prn", "duration_days", "brand_name", "generic_name"]
INVENTABLE = ["strength", "dose", "times_per_day", "duration_days", "brand_name", "generic_name"]  # fields where ground truth can be null


def norm_text(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s/]", " ", (s or "").lower())).strip()


def norm_name(s):
    if not s:
        return None
    toks = norm_text(s).split()
    while len(toks) > 1 and toks[0] in PREFIXES:
        toks.pop(0)
    return " ".join(toks) or None


def norm_strength(s):
    return re.sub(r"\s+", "", s.lower()) if s else None


def norm_dose(s):
    return " ".join(UNITS.get(t, t) for t in norm_text(s).split()) or None


def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def med_similarity(g, p):
    gn = [n for n in (norm_name(g.brand_name), norm_name(g.generic_name)) if n]
    pn = [n for n in (norm_name(p.brand_name), norm_name(p.generic_name)) if n]
    return max((ratio(a, b) for a in gn for b in pn), default=0.0)


def one_to_one(n_gt, n_pred, sim, threshold):
    """Greedy best-first assignment. Returns list of (gt_index, pred_index)."""
    pairs = sorted(((sim(i, j), i, j) for i in range(n_gt) for j in range(n_pred)), reverse=True)
    used_g, used_p, out = set(), set(), []
    for s, i, j in pairs:
        if s >= threshold and i not in used_g and j not in used_p:
            used_g.add(i), used_p.add(j), out.append((i, j))
    return out


def field_value(m, f):
    if f in ("times_per_day", "timing_label", "is_prn"):
        v = getattr(m.frequency, f)
    else:
        v = getattr(m, f)
    v = getattr(v, "value", v)
    if f == "strength":
        return norm_strength(v)
    if f == "dose":
        return norm_dose(v)
    if f in ("brand_name", "generic_name"):
        return norm_name(v)
    return v


def best_window_ratio(quote, doc):
    """Share of quote characters found in order inside the document (fuzzy containment)."""
    q = re.sub(r"\s+", " ", quote).strip()
    d = re.sub(r"\s+", " ", doc)
    if not q:
        return 0.0
    m = SequenceMatcher(None, d, q, autojunk=False)
    return sum(b.size for b in m.get_matching_blocks()) / len(q)


def text_sim(g_text, p_text, p_quote=None):
    return max(ratio(norm_text(g_text), norm_text(p_text)), ratio(norm_text(g_text), norm_text(p_quote)))


def exact_ci(s):
    """Name equality after case and spacing normalisation only (no prefix stripping)."""
    return re.sub(r"\s+", " ", s.lower()).strip() if s else None


def classify_invented(f, pv, g, doc_text):
    """Why a value exists where ground truth is null: role_confusion (a real name in the wrong field), in_document (the value is written
    somewhere in the document but is not this field's), or made_up (appears nowhere in the document text)."""
    if f in ("brand_name", "generic_name") and pv in {field_value(g, "brand_name"), field_value(g, "generic_name")} - {None}:
        return "role"
    doc = re.sub(r"[^a-z0-9]", "", doc_text.lower())
    if f in ("times_per_day", "duration_days"):
        return "in_doc" if re.search(rf"(?<!\d){pv}(?!\d)", doc_text) else "made_up"
    return "in_doc" if re.sub(r"[^a-z0-9]", "", str(pv).lower()) in doc else "made_up"


def score_document(gt, pred, doc_text, pair_with=None):
    """gt, pred: ExtractionOutput. pred=None means the call failed (counts as an empty prediction).
    pair_with: optional second list of predicted medications (same order), e.g. the raw extraction when pred is normalised; a
    medicine pairs with the ground truth if EITHER name set matches, so detection never gets worse by dropping a name."""
    c = Counter()
    c["docs"] = 1
    if pred is None:
        c["parse_fail"] = 1
        from app.schemas.extraction_output import ExtractionOutput

        pred = ExtractionOutput(document_type=gt.document_type)
    G, P = gt.medications, pred.medications
    sim = (lambda i, j: max(med_similarity(G[i], P[j]), med_similarity(G[i], pair_with[j]))) if pair_with else (lambda i, j: med_similarity(G[i], P[j]))
    pairs = one_to_one(len(G), len(P), sim, NAME_THRESHOLD)
    c["med_tp"], c["med_fn"], c["med_fp"] = len(pairs), len(G) - len(pairs), len(P) - len(pairs)
    for i, j in pairs:
        ok_all = True
        for f in MED_FIELDS:
            gv, pv = field_value(G[i], f), field_value(P[j], f)
            c[f"field_total_{f}"] += 1
            c[f"field_ok_{f}"] += gv == pv
            ok_all &= gv == pv
            if f in INVENTABLE and gv is None:
                c["null_total"] += 1
                c["invented"] += pv is not None
                c[f"null_{f}"] += 1
                if pv is not None:
                    c[f"inv_{f}"] += 1
                    c[f"inv_{f}_{classify_invented(f, pv, G[i], doc_text)}"] += 1
            if f in ("brand_name", "generic_name"):
                gn, pn = getattr(G[i], f), getattr(P[j], f)
                c[f"exact_total_{f}"] += 1
                c[f"exact_ok_{f}"] += exact_ci(gn) == exact_ci(pn)
        c["med_fully_correct"] += ok_all

    # follow-ups
    GF, PF = gt.follow_ups, pred.follow_ups
    fp_pairs = one_to_one(len(GF), len(PF), lambda i, j: text_sim(GF[i].description, PF[j].description, PF[j].source_quote), TEXT_THRESHOLD)
    c["fu_tp"], c["fu_fn"], c["fu_fp"] = len(fp_pairs), len(GF) - len(fp_pairs), len(PF) - len(fp_pairs)
    for i, j in fp_pairs:
        c["fu_days_total"] += 1
        c["fu_days_ok"] += GF[i].days_from_discharge == PF[j].days_from_discharge

    # red flags
    GR, PR = gt.red_flags, pred.red_flags
    rf_pairs = one_to_one(len(GR), len(PR), lambda i, j: text_sim(GR[i].text, PR[j].text, PR[j].source_quote), TEXT_THRESHOLD)
    c["rf_tp"], c["rf_fn"], c["rf_fp"] = len(rf_pairs), len(GR) - len(rf_pairs), len(PR) - len(rf_pairs)

    # quote validity and confidence
    items = [(m.source_quote, m.confidence) for m in P] + [(x.source_quote, x.confidence) for x in PF + PR]
    for q, conf in items:
        c["quotes"] += 1
        c["quote_exact"] += q in doc_text
        c["quote_fuzzy"] += best_window_ratio(q, doc_text) >= FUZZY_QUOTE  # old loose check, kept for comparison
        k = qc.check(q, doc_text)
        c["quote_norm_exact"] += k["normalised_exact"]
        ok = k["normalised_exact"] or k["strict_fuzzy"]
        c["quote_strict"] += ok
        if not ok:
            c["quote_fail_digits" if k["ratio"] >= qc.STRICT_FUZZY_MIN and not k["digits_match"] else "quote_fail_similarity"] += 1
        c["items"] += 1
        c["low_conf"] += conf.value == "low"
    c["docs_with_unreadable"] = bool(pred.unreadable_parts)
    return c


def div(a, b):
    return round(a / b, 4) if b else None


def summarize(c):
    """Turn summed counters into metrics."""
    p, r = div(c["med_tp"], c["med_tp"] + c["med_fp"]), div(c["med_tp"], c["med_tp"] + c["med_fn"])
    f1 = div(2 * p * r, p + r) if p and r else (0.0 if p is not None and r is not None else None)
    m = dict(
        docs=c["docs"], med_precision=p, med_recall=r, med_f1=f1,
        med_fully_correct_rate=div(c["med_fully_correct"], c["med_tp"]),
        followup_recall=div(c["fu_tp"], c["fu_tp"] + c["fu_fn"]), followup_precision=div(c["fu_tp"], c["fu_tp"] + c["fu_fp"]),
        followup_days_accuracy=div(c["fu_days_ok"], c["fu_days_total"]),
        redflag_recall=div(c["rf_tp"], c["rf_tp"] + c["rf_fn"]), redflag_precision=div(c["rf_tp"], c["rf_tp"] + c["rf_fp"]),
        hallucinated_meds=c["med_fp"], hallucinated_followups=c["fu_fp"], hallucinated_redflags=c["rf_fp"],
        invented_value_rate=div(c["invented"], c["null_total"]),
        quote_exact_rate=div(c["quote_exact"], c["quotes"]), quote_fuzzy_rate=div(c["quote_fuzzy"], c["quotes"]),
        quote_norm_exact_rate=div(c["quote_norm_exact"], c["quotes"]), quote_strict_rate=div(c["quote_strict"], c["quotes"]),
        quote_fail_digits=c["quote_fail_digits"], quote_fail_similarity=c["quote_fail_similarity"],
        parse_failure_rate=div(c["parse_fail"], c["docs"]), low_confidence_rate=div(c["low_conf"], c["items"]),
    )
    for f in MED_FIELDS:
        m[f"acc_{f}"] = div(c[f"field_ok_{f}"], c[f"field_total_{f}"])
    for f in ("brand_name", "generic_name"):
        m[f"exact_ci_{f}"] = div(c[f"exact_ok_{f}"], c[f"exact_total_{f}"])
    for f in INVENTABLE:
        m[f"invented_{f}"] = dict(of_null=c[f"null_{f}"], invented=c[f"inv_{f}"], role_confusion=c[f"inv_{f}_role"], in_document=c[f"inv_{f}_in_doc"], made_up=c[f"inv_{f}_made_up"])
    return m
