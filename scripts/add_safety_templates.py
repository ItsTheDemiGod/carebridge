"""Phase 4: adds the safety template ids to data/templates/templates.json (idempotent) and writes data/templates/review_sheet_phase4_new.csv
(only these ids, same columns as review_sheet.csv, UTF-8 with BOM). Every ta/hi string is draft_unreviewed.   python scripts/add_safety_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import export_review_sheet as X  # noqa: E402

# id -> (en, ta, hi). Placeholders: {a} {b} medicine names, {n} count, {name} shared name.
NEW = {
    "heading.safety": ("Medicine interactions", "மருந்து இடைவினைகள்", "दवाओं के आपसी असर"),
    "safety.level.major": (
        "{a} and {b} may interact in a serious way. Talk to your doctor or pharmacist before taking them together. Do not stop or change either medicine on your own.",
        "{a} மற்றும் {b} தீவிரமான முறையில் ஒன்றோடொன்று தொடர்பு கொள்ளலாம். இவற்றை சேர்த்து எடுப்பதற்கு முன் உங்கள் மருத்துவர் அல்லது மருந்தாளருடன் பேசவும். எந்த மருந்தையும் நீங்களாகவே நிறுத்தவோ மாற்றவோ வேண்டாம்.",
        "{a} और {b} आपस में गंभीर तरीके से असर कर सकते हैं। इन्हें साथ में लेने से पहले अपने डॉक्टर या फ़ार्मासिस्ट से बात करें। किसी भी दवा को अपने आप बंद न करें और न बदलें।"),
    "safety.level.moderate": (
        "{a} and {b} may interact. Ask your doctor or pharmacist whether they are suitable together.",
        "{a} மற்றும் {b} ஒன்றோடொன்று தொடர்பு கொள்ளலாம். இவை சேர்த்து எடுக்கத் தகுந்தவையா என்று உங்கள் மருத்துவர் அல்லது மருந்தாளரிடம் கேளுங்கள்.",
        "{a} और {b} आपस में असर कर सकते हैं। ये साथ में लेने के लिए ठीक हैं या नहीं, यह अपने डॉक्टर या फ़ार्मासिस्ट से पूछें।"),
    "safety.level.minor": (
        "A minor interaction is listed for {a} and {b}. You may mention it to your pharmacist.",
        "{a} மற்றும் {b} இடையே சிறிய இடைவினை பட்டியலிடப்பட்டுள்ளது. இதை உங்கள் மருந்தாளரிடம் தெரிவிக்கலாம்.",
        "{a} और {b} के बीच एक हल्का असर सूचीबद्ध है। आप इसके बारे में अपने फ़ार्मासिस्ट को बता सकते हैं।"),
    "safety.level.unknown": (
        "An interaction is listed for {a} and {b}, but its seriousness is not known. Ask your pharmacist.",
        "{a} மற்றும் {b} இடையே இடைவினை பட்டியலிடப்பட்டுள்ளது, ஆனால் அதன் தீவிரம் தெரியவில்லை. உங்கள் மருந்தாளரிடம் கேளுங்கள்.",
        "{a} और {b} के बीच असर सूचीबद्ध है, लेकिन उसकी गंभीरता मालूम नहीं है। अपने फ़ार्मासिस्ट से पूछें।"),
    "safety.not_checked": (
        "{n} medicine pairs could not be checked for interactions in our limited database. This does not mean they are safe. Ask your pharmacist.",
        "எங்கள் குறைந்த தரவுத்தளத்தில் {n} மருந்து ஜோடிகளுக்கு இடைவினைகளைச் சரிபார்க்க முடியவில்லை. இவை பாதுகாப்பானவை என்று இதன் பொருள் அல்ல. உங்கள் மருந்தாளரிடம் கேளுங்கள்.",
        "हमारे सीमित डेटाबेस में {n} दवा-जोड़ियों के आपसी असर की जाँच नहीं हो सकी। इसका मतलब यह नहीं कि वे सुरक्षित हैं। अपने फ़ार्मासिस्ट से पूछें।"),
    "safety.not_checked_1": (
        "1 medicine pair could not be checked for interactions in our limited database. This does not mean it is safe. Ask your pharmacist.",
        "எங்கள் குறைந்த தரவுத்தளத்தில் 1 மருந்து ஜோடிக்கு இடைவினையைச் சரிபார்க்க முடியவில்லை. இது பாதுகாப்பானது என்று பொருள் அல்ல. உங்கள் மருந்தாளரிடம் கேளுங்கள்.",
        "हमारे सीमित डेटाबेस में 1 दवा-जोड़ी के आपसी असर की जाँच नहीं हो सकी। इसका मतलब यह नहीं कि वह सुरक्षित है। अपने फ़ार्मासिस्ट से पूछें।"),
    "safety.unconfirmed": (
        "{n} medicine pairs were not checked for interactions because a medicine name needs to be confirmed first. Please confirm the medicine names.",
        "{n} மருந்து ஜோடிகளுக்கு இடைவினை சரிபார்க்கப்படவில்லை, ஏனெனில் ஒரு மருந்தின் பெயரை முதலில் உறுதிசெய்ய வேண்டும். மருந்துப் பெயர்களை உறுதிசெய்யவும்.",
        "{n} दवा-जोड़ियों का आपसी असर जाँचा नहीं गया, क्योंकि किसी दवा का नाम पहले पक्का करना है। कृपया दवाओं के नाम पक्का करें।"),
    "safety.unconfirmed_1": (
        "1 medicine pair was not checked for interactions because a medicine name needs to be confirmed first. Please confirm the medicine names.",
        "1 மருந்து ஜோடிக்கு இடைவினை சரிபார்க்கப்படவில்லை, ஏனெனில் ஒரு மருந்தின் பெயரை முதலில் உறுதிசெய்ய வேண்டும். மருந்துப் பெயர்களை உறுதிசெய்யவும்.",
        "1 दवा-जोड़ी का आपसी असर जाँचा नहीं गया, क्योंकि किसी दवा का नाम पहले पक्का करना है। कृपया दवाओं के नाम पक्का करें।"),
    "safety.db_missing": (
        "We could not check your medicines for interactions because our interaction data is not available. Ask your pharmacist.",
        "எங்கள் இடைவினைத் தரவு கிடைக்காததால் உங்கள் மருந்துகளுக்கான இடைவினைகளைச் சரிபார்க்க முடியவில்லை. உங்கள் மருந்தாளரிடம் கேளுங்கள்.",
        "हमारा इंटरैक्शन डेटा उपलब्ध नहीं होने के कारण आपकी दवाओं के आपसी असर की जाँच नहीं हो सकी। अपने फ़ार्मासिस्ट से पूछें।"),
    "safety.duplicate": (
        "{name} appears more than once in this document. This could mean a double dose. Please confirm with your doctor or pharmacist.",
        "{name} இந்த ஆவணத்தில் ஒன்றுக்கு மேற்பட்ட முறை வருகிறது. இது இரட்டை அளவைக் குறிக்கலாம். உங்கள் மருத்துவர் அல்லது மருந்தாளருடன் உறுதிசெய்யவும்.",
        "{name} इस दस्तावेज़ में एक से ज़्यादा बार आया है। इसका मतलब दोहरी खुराक हो सकता है। कृपया अपने डॉक्टर या फ़ार्मासिस्ट से पुष्टि करें।"),
    "banner.safety.confirm_first": (
        "Some medicine details need your confirmation first, so the interaction results below may be incomplete. Please confirm them with your doctor or pharmacist.",
        "சில மருந்து விவரங்களை முதலில் நீங்கள் உறுதிசெய்ய வேண்டும், எனவே கீழே உள்ள இடைவினை முடிவுகள் முழுமையற்றதாக இருக்கலாம். உங்கள் மருத்துவர் அல்லது மருந்தாளருடன் உறுதிசெய்யவும்.",
        "कुछ दवाओं के विवरण पहले आपको पक्के करने हैं, इसलिए नीचे के असर के नतीजे अधूरे हो सकते हैं। कृपया अपने डॉक्टर या फ़ार्मासिस्ट से पुष्टि करें।"),
    "banner.safety.review_interactions": (
        "One or more possible interactions were found. Please talk to your doctor or pharmacist about them.",
        "ஒன்று அல்லது அதற்கு மேற்பட்ட சாத்தியமான இடைவினைகள் கண்டறியப்பட்டன. இவற்றைப் பற்றி உங்கள் மருத்துவர் அல்லது மருந்தாளருடன் பேசவும்.",
        "एक या अधिक संभावित असर मिले हैं। कृपया इनके बारे में अपने डॉक्टर या फ़ार्मासिस्ट से बात करें।"),
    "safety.schedule_reminder": (
        "Some medicines have a schedule that is not daily or is not stated. Please check the notes on those medicines.",
        "சில மருந்துகளின் அட்டவணை தினசரி அல்ல அல்லது குறிப்பிடப்படவில்லை. அந்த மருந்துகளின் குறிப்புகளைச் சரிபார்க்கவும்.",
        "कुछ दवाओं की समय-सारणी रोज़ाना नहीं है या बताई नहीं गई है। कृपया उन दवाओं के नोट देख लें।"),
}
# English only (the attribution line is not translated); not part of "strings", so it is not in any review sheet.
ENGLISH_ONLY = {
    "safety.attribution_reviewed": "Interaction data: DDInter (CC BY-NC-SA 4.0) plus a supplement reviewed by a pharmacist.",
    "safety.attribution_unreviewed": "Interaction data: DDInter (CC BY-NC-SA 4.0). A supplement of extra pairs is waiting for pharmacist review and is not used yet.",
}


def main():
    p = X.TEMPLATES
    data = json.loads(p.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in NEW.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    data["english_only"] = ENGLISH_ONLY
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase4_new.csv", only=set(NEW))
    print(f"{len(NEW)} templates, {n} sheet rows")


if __name__ == "__main__":
    main()
