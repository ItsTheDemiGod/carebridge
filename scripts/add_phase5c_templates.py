"""Phase 5c: adds/changes the prototype-review-mode template ids in data/templates/templates.json (idempotent) and writes
data/templates/review_sheet_phase5c_new.csv (only these ids, same columns as review_sheet.csv, UTF-8 with BOM). Every ta/hi string is draft_unreviewed.
python scripts/add_phase5c_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import export_review_sheet as X  # noqa: E402

# id -> (en, ta, hi). Placeholders: {a} {b} medicine names, {contact} contact line (name, plus email when configured).
NEW = {
    "safety.attribution_author_checked": (
        "Interaction data: DDInter (CC BY-NC-SA 4.0) plus a supplement drafted from official drug labels by the project author; not reviewed by a pharmacist (prototype).",
        "இடைவினைத் தரவு: DDInter (CC BY-NC-SA 4.0), மேலும் அதிகாரப்பூர்வ மருந்து லேபிள்களிலிருந்து திட்ட ஆசிரியர் தயாரித்த கூடுதல் தொகுப்பு; இது மருந்தாளரால் சரிபார்க்கப்படவில்லை (மாதிரி).",
        "इंटरैक्शन डेटा: DDInter (CC BY-NC-SA 4.0) तथा आधिकारिक दवा लेबलों से परियोजना लेखक द्वारा तैयार किया गया एक पूरक; इसे किसी फ़ार्मासिस्ट ने जाँचा नहीं है (प्रोटोटाइप)।"),
    "safety.notice.brand_mapping": (
        "In this prototype, brand names are matched to generic names using a list that has not been verified by a pharmacist.",
        "இந்த மாதிரியில், பிராண்ட் பெயர்கள் பொதுப் பெயர்களுடன் பொருத்தப்படும் பட்டியல் மருந்தாளரால் சரிபார்க்கப்படவில்லை.",
        "इस प्रोटोटाइप में ब्रांड नामों को जेनेरिक नामों से मिलाने की सूची किसी फ़ार्मासिस्ट ने जाँची नहीं है।"),
    "safety.author.major": (
        "{a} and {b} may interact in a serious way, according to drug-label information collected by the project author (not checked by a pharmacist). Talk to your doctor or pharmacist before taking them together. Do not stop or change either medicine on your own.",
        "{a} மற்றும் {b} தீவிரமான முறையில் ஒன்றோடொன்று தொடர்பு கொள்ளலாம் என்று திட்ட ஆசிரியர் சேகரித்த மருந்து லேபிள் தகவல் கூறுகிறது (மருந்தாளரால் சரிபார்க்கப்படவில்லை). இவற்றை சேர்த்து எடுப்பதற்கு முன் உங்கள் மருத்துவர் அல்லது மருந்தாளருடன் பேசவும். எந்த மருந்தையும் நீங்களாகவே நிறுத்தவோ மாற்றவோ வேண்டாம்.",
        "परियोजना लेखक द्वारा जुटाई गई दवा-लेबल की जानकारी के अनुसार {a} और {b} आपस में गंभीर तरीके से असर कर सकते हैं (किसी फ़ार्मासिस्ट ने जाँचा नहीं है)। इन्हें साथ में लेने से पहले अपने डॉक्टर या फ़ार्मासिस्ट से बात करें। किसी भी दवा को अपने आप बंद न करें और न बदलें।"),
    "safety.author.other": (
        "{a} and {b} may interact, according to drug-label information collected by the project author (not checked by a pharmacist). Ask your doctor or pharmacist whether they are suitable together.",
        "{a} மற்றும் {b} ஒன்றோடொன்று தொடர்பு கொள்ளலாம் என்று திட்ட ஆசிரியர் சேகரித்த மருந்து லேபிள் தகவல் கூறுகிறது (மருந்தாளரால் சரிபார்க்கப்படவில்லை). இவை சேர்த்து எடுக்கத் தகுந்தவையா என்று உங்கள் மருத்துவர் அல்லது மருந்தாளரிடம் கேளுங்கள்.",
        "परियोजना लेखक द्वारा जुटाई गई दवा-लेबल की जानकारी के अनुसार {a} और {b} आपस में असर कर सकते हैं (किसी फ़ार्मासिस्ट ने जाँचा नहीं है)। ये साथ में लेने के लिए ठीक हैं या नहीं, यह अपने डॉक्टर या फ़ार्मासिस्ट से पूछें।"),
    "consent.item.translation_draft": (
        "The Tamil and Hindi texts are machine-drafted and have not been reviewed by native speakers.",
        "தமிழ் மற்றும் இந்தி உரைகள் இயந்திரத்தால் வரையப்பட்டவை; தாய்மொழி பேசுபவர்கள் அவற்றைச் சரிபார்க்கவில்லை.",
        "तमिल और हिंदी पाठ मशीन से तैयार किए गए हैं और किसी मातृभाषी ने उनकी जाँच नहीं की है।"),
    "consent.item.interaction_limited": (
        "The interaction information is limited. It was drafted from official drug labels by the project author and has not been reviewed by a pharmacist.",
        "இடைவினைத் தகவல் குறைவானது. இது அதிகாரப்பூர்வ மருந்து லேபிள்களிலிருந்து திட்ட ஆசிரியரால் தயாரிக்கப்பட்டது; மருந்தாளர் இதைச் சரிபார்க்கவில்லை.",
        "इंटरैक्शन की जानकारी सीमित है। इसे आधिकारिक दवा लेबलों से परियोजना लेखक ने तैयार किया है और किसी फ़ार्मासिस्ट ने इसकी जाँच नहीं की है।"),
    "consent.item.contact": (  # changed: the placeholder replaces "[contact person to be added]"
        "Questions? Contact: {contact}.",
        "கேள்விகள் உள்ளதா? தொடர்புக்கு: {contact}.",
        "सवाल हैं? संपर्क करें: {contact}।"),
}


def main():
    p = X.TEMPLATES
    data = json.loads(p.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in NEW.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase5c_new.csv", only=set(NEW))
    print(f"{len(NEW)} templates, {n} sheet rows")


if __name__ == "__main__":
    main()
