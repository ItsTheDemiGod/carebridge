"""Phase 5: adds the consent, privacy, error, confirmation, schedule and summary template ids to data/templates/templates.json (idempotent)
and writes data/templates/review_sheet_phase5_new.csv (only these ids, same columns as review_sheet.csv, UTF-8 with BOM).
Every ta/hi string is draft_unreviewed. Style: simple everyday words, short sentences, Western digits, drug names in Latin script.
python scripts/add_phase5_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import export_review_sheet as X  # noqa: E402

# id -> (en, ta, hi). Placeholders: {documents} {payloads} {images} (receipt), {n} (schedule days).
NEW = {
    # --- consent notice ---------------------------------------------------------------------------------------------------------------
    "consent.title": ("Before we start", "தொடங்குவதற்கு முன்", "शुरू करने से पहले"),
    "consent.item.what": (
        "CareBridge reads a photo of your medical document and explains it in simple words.",
        "கேர்பிரிட்ஜ் உங்கள் மருத்துவ ஆவணத்தின் புகைப்படத்தைப் படித்து எளிய சொற்களில் விளக்குகிறது.",
        "केयरब्रिज आपके चिकित्सा दस्तावेज़ की फ़ोटो पढ़ता है और उसे आसान शब्दों में समझाता है।"),
    "consent.item.where": (
        "The photo is read on this computer by a local model. Nothing is sent to any outside service.",
        "புகைப்படம் இந்தக் கணினியிலேயே உள்ளூர் மாதிரியால் படிக்கப்படுகிறது. எந்த வெளிச் சேவைக்கும் எதுவும் அனுப்பப்படுவதில்லை.",
        "फ़ोटो इसी कंप्यूटर पर एक स्थानीय मॉडल द्वारा पढ़ी जाती है। किसी बाहरी सेवा को कुछ नहीं भेजा जाता।"),
    "consent.item.stored": (
        "We keep the results, not the photo, unless you choose to keep the photo. Everything we keep is encrypted.",
        "நீங்கள் புகைப்படத்தை வைத்திருக்கத் தேர்வு செய்யாவிட்டால், முடிவுகளை மட்டும் வைத்திருப்போம், புகைப்படத்தை அல்ல. நாங்கள் வைத்திருப்பவை அனைத்தும் மறையாக்கம் செய்யப்படும்.",
        "जब तक आप फ़ोटो रखने का चुनाव नहीं करते, हम केवल नतीजे रखते हैं, फ़ोटो नहीं। जो कुछ हम रखते हैं वह सब एन्क्रिप्ट किया जाता है।"),
    "consent.item.how_long": (
        "Saved results are kept until you delete them or 24 hours pass, whichever comes first.",
        "சேமித்த முடிவுகள் நீங்கள் அவற்றை நீக்கும் வரை அல்லது 24 மணி நேரம் கடக்கும் வரை, எது முதலில் வருகிறதோ அதுவரை வைக்கப்படும்.",
        "सहेजे गए नतीजे तब तक रखे जाते हैं जब तक आप उन्हें मिटा नहीं देते या 24 घंटे नहीं बीत जाते, जो भी पहले हो।"),
    "consent.item.delete": (
        "You can delete everything now with one button. This also withdraws your consent.",
        "ஒரே பொத்தானால் எல்லாவற்றையும் இப்போதே நீக்கலாம். இது உங்கள் ஒப்புதலையும் திரும்பப் பெறும்.",
        "आप एक बटन से अभी सब कुछ मिटा सकते हैं। इससे आपकी सहमति भी वापस हो जाती है।"),
    "consent.item.no_sharing": ("We do not sell or share your data.", "உங்கள் தரவை நாங்கள் விற்கவோ பகிரவோ மாட்டோம்.", "हम आपका डेटा न बेचते हैं, न साझा करते हैं।"),
    "consent.item.prototype": (
        "This is a class project prototype. It is not medical advice. Always confirm with your doctor or pharmacist.",
        "இது ஒரு வகுப்புத் திட்ட மாதிரி. இது மருத்துவ ஆலோசனை அல்ல. எப்போதும் உங்கள் மருத்துவர் அல்லது மருந்தாளருடன் உறுதிசெய்யுங்கள்.",
        "यह एक कक्षा परियोजना का प्रोटोटाइप है। यह चिकित्सा सलाह नहीं है। हमेशा अपने डॉक्टर या फ़ार्मासिस्ट से पुष्टि करें।"),
    "consent.item.contact": (
        "Questions? Contact: [contact person to be added].",
        "கேள்விகள் உள்ளதா? தொடர்புக்கு: [தொடர்பு நபர் சேர்க்கப்படும்].",
        "सवाल हैं? संपर्क करें: [संपर्क व्यक्ति जोड़ा जाएगा]।"),
    "consent.purpose.process_photo": ("Read the photo of my document (required)", "என் ஆவணத்தின் புகைப்படத்தைப் படிக்க (கட்டாயம்)", "मेरे दस्तावेज़ की फ़ोटो पढ़ना (ज़रूरी)"),
    "consent.purpose.store_results_for_session": ("Save the results for this session (required)", "இந்த அமர்வுக்கு முடிவுகளைச் சேமிக்க (கட்டாயம்)", "इस सत्र के लिए नतीजे सहेजना (ज़रूरी)"),
    "consent.purpose.keep_photo_for_session": ("Also keep the photo for this session (optional)", "இந்த அமர்வுக்கு புகைப்படத்தையும் வைத்திருக்க (விருப்பம்)", "इस सत्र के लिए फ़ोटो भी रखना (वैकल्पिक)"),
    # --- deletion ---------------------------------------------------------------------------------------------------------------------
    "delete.confirm": (
        "Delete everything now? This removes your session, results and any kept photo. It cannot be undone.",
        "இப்போதே எல்லாவற்றையும் நீக்கவா? இது உங்கள் அமர்வு, முடிவுகள் மற்றும் வைத்த புகைப்படத்தை நீக்கும். இதைத் திரும்பப் பெற முடியாது.",
        "क्या अभी सब कुछ मिटाएँ? इससे आपका सत्र, नतीजे और रखी गई फ़ोटो हट जाएगी। इसे वापस नहीं किया जा सकता।"),
    "delete.receipt": (
        "Deleted: {documents} documents, {payloads} saved results, {images} photos.",
        "நீக்கப்பட்டவை: {documents} ஆவணங்கள், {payloads} சேமித்த முடிவுகள், {images} புகைப்படங்கள்.",
        "मिटाया गया: {documents} दस्तावेज़, {payloads} सहेजे गए नतीजे, {images} फ़ोटो।"),
    "delete.done": (
        "Your data has been deleted and your consent is withdrawn.",
        "உங்கள் தரவு நீக்கப்பட்டது, உங்கள் ஒப்புதலும் திரும்பப் பெறப்பட்டது.",
        "आपका डेटा मिटा दिया गया है और आपकी सहमति वापस ले ली गई है।"),
    # --- errors -----------------------------------------------------------------------------------------------------------------------
    "error.consent_required": ("Please read and accept the notice before continuing.", "தொடர்வதற்கு முன் அறிவிப்பைப் படித்து ஒப்புக்கொள்ளுங்கள்.", "आगे बढ़ने से पहले कृपया सूचना पढ़ें और स्वीकार करें।"),
    "error.consent_invalid": (
        "The consent could not be saved. Please accept the required items and try again.",
        "ஒப்புதலைச் சேமிக்க முடியவில்லை. கட்டாயமானவற்றை ஏற்றுக்கொண்டு மீண்டும் முயலுங்கள்.",
        "सहमति सहेजी नहीं जा सकी। कृपया ज़रूरी बातें स्वीकार करके फिर कोशिश करें।"),
    "error.no_session": ("No active session. Please start again.", "செயலில் உள்ள அமர்வு இல்லை. மீண்டும் தொடங்குங்கள்.", "कोई सक्रिय सत्र नहीं है। कृपया फिर से शुरू करें।"),
    "error.session_expired": (
        "Your session has expired and the data was removed. Please start again.",
        "உங்கள் அமர்வு காலாவதியானது, தரவு நீக்கப்பட்டது. மீண்டும் தொடங்குங்கள்.",
        "आपका सत्र समाप्त हो गया है और डेटा हटा दिया गया है। कृपया फिर से शुरू करें।"),
    "error.upload_too_large": ("This file is too large. Please use a smaller photo.", "இந்தக் கோப்பு மிகப் பெரியது. சிறிய புகைப்படத்தைப் பயன்படுத்துங்கள்.", "यह फ़ाइल बहुत बड़ी है। कृपया छोटी फ़ोटो इस्तेमाल करें।"),
    "error.unsupported_file": (
        "Please upload a photo or image (PNG or JPG).",
        "புகைப்படம் அல்லது படத்தைப் (PNG அல்லது JPG) பதிவேற்றுங்கள்.",
        "कृपया फ़ोटो या छवि (PNG या JPG) अपलोड करें।"),
    "error.pdf_not_supported": (
        "Please upload a photo or image (PNG or JPG). PDF is not supported yet.",
        "புகைப்படம் அல்லது படத்தைப் (PNG அல்லது JPG) பதிவேற்றுங்கள். PDF இன்னும் ஆதரிக்கப்படவில்லை.",
        "कृपया फ़ोटो या छवि (PNG या JPG) अपलोड करें। PDF अभी समर्थित नहीं है।"),
    "error.image_invalid": (
        "This image could not be opened or is too large in pixels. Please try another photo.",
        "இந்தப் படத்தைத் திறக்க முடியவில்லை அல்லது பிக்சல் அளவு மிகப் பெரியது. வேறு புகைப்படத்தை முயலுங்கள்.",
        "यह छवि खोली नहीं जा सकी या पिक्सेल में बहुत बड़ी है। कृपया दूसरी फ़ोटो आज़माएँ।"),
    "error.queue_full": ("The reader is busy. Please try again in a minute.", "படிக்கும் பகுதி பிஸியாக உள்ளது. ஒரு நிமிடம் கழித்து மீண்டும் முயலுங்கள்.", "पढ़ने वाला हिस्सा व्यस्त है। कृपया एक मिनट बाद फिर कोशिश करें।"),
    "error.too_many_documents": (
        "The limit of documents for this session has been reached. Delete your data to start again.",
        "இந்த அமர்வுக்கான ஆவண வரம்பை அடைந்துவிட்டீர்கள். மீண்டும் தொடங்க தரவை நீக்குங்கள்.",
        "इस सत्र के लिए दस्तावेज़ों की सीमा पूरी हो गई है। फिर से शुरू करने के लिए अपना डेटा मिटाएँ।"),
    "error.not_found": ("We could not find that.", "அது கிடைக்கவில்லை.", "वह नहीं मिला।"),
    "error.not_ready": (
        "This is not ready yet. Please wait for the reading to finish.",
        "இது இன்னும் தயாராகவில்லை. படித்து முடியும் வரை காத்திருங்கள்.",
        "यह अभी तैयार नहीं है। कृपया पढ़ना पूरा होने तक प्रतीक्षा करें।"),
    "error.invalid_confirmation": (
        "Some of your choices could not be used. Please check them and try again.",
        "உங்கள் சில தேர்வுகளைப் பயன்படுத்த முடியவில்லை. சரிபார்த்து மீண்டும் முயலுங்கள்.",
        "आपके कुछ चुनाव इस्तेमाल नहीं हो सके। कृपया जाँचकर फिर कोशिश करें।"),
    "error.request_blocked": ("This request was blocked for security reasons.", "பாதுகாப்பு காரணங்களுக்காக இந்தக் கோரிக்கை தடுக்கப்பட்டது.", "सुरक्षा कारणों से यह अनुरोध रोका गया।"),
    "error.invalid_request": (
        "The request was not valid. Please check it and try again.",
        "கோரிக்கை சரியாக இல்லை. சரிபார்த்து மீண்டும் முயலுங்கள்.",
        "अनुरोध सही नहीं था। कृपया जाँचकर फिर कोशिश करें।"),
    "error.internal_error": ("Something went wrong on our side. Please try again.", "எங்கள் பக்கத்தில் ஏதோ தவறு நடந்தது. மீண்டும் முயலுங்கள்.", "हमारी तरफ़ से कुछ गड़बड़ हुई। कृपया फिर कोशिश करें।"),
    "error.retry_unavailable": (
        "The photo was not kept, so it has to be uploaded again.",
        "புகைப்படம் வைக்கப்படவில்லை, எனவே மீண்டும் பதிவேற்ற வேண்டும்.",
        "फ़ोटो रखी नहीं गई थी, इसलिए उसे फिर से अपलोड करना होगा।"),
    "job.failed.ollama_unavailable": (
        "The local reader is not running. Please start it and upload again.",
        "உள்ளூர் வாசிப்பான் இயங்கவில்லை. அதைத் தொடங்கி மீண்டும் பதிவேற்றுங்கள்.",
        "स्थानीय रीडर चालू नहीं है। कृपया उसे चालू करके फिर अपलोड करें।"),
    "job.failed.image_unreadable": (
        "We could not read this photo. Please try a clearer photo.",
        "இந்தப் புகைப்படத்தைப் படிக்க முடியவில்லை. தெளிவான புகைப்படத்தை முயலுங்கள்.",
        "यह फ़ोटो पढ़ी नहीं जा सकी। कृपया साफ़ फ़ोटो आज़माएँ।"),
    "job.failed.context_truncated": (
        "This document is too long to read in one go. Please upload one page at a time.",
        "இந்த ஆவணம் ஒரே நேரத்தில் படிக்க மிக நீளமானது. ஒரு நேரத்தில் ஒரு பக்கத்தைப் பதிவேற்றுங்கள்.",
        "यह दस्तावेज़ एक बार में पढ़ने के लिए बहुत लंबा है। कृपया एक बार में एक पन्ना अपलोड करें।"),
    "job.failed.image_not_received": (
        "The reader did not receive the photo. Please upload it again.",
        "வாசிப்பான் புகைப்படத்தைப் பெறவில்லை. மீண்டும் பதிவேற்றுங்கள்.",
        "रीडर को फ़ोटो नहीं मिली। कृपया उसे फिर से अपलोड करें।"),
    "job.failed.provider_not_allowed": (
        "This app is set to read photos with an outside service, which is not allowed for your photos. Nothing was sent.",
        "இந்தப் பயன்பாடு புகைப்படங்களை வெளிச் சேவை மூலம் படிக்கும்படி அமைக்கப்பட்டுள்ளது; உங்கள் புகைப்படங்களுக்கு இது அனுமதிக்கப்படாது. எதுவும் அனுப்பப்படவில்லை.",
        "यह ऐप फ़ोटो को बाहरी सेवा से पढ़ने के लिए सेट है, जो आपकी फ़ोटो के लिए मंज़ूर नहीं है। कुछ भी नहीं भेजा गया।"),
    "job.failed.timeout": ("Reading took too long. Please try again.", "படிக்க அதிக நேரம் ஆனது. மீண்டும் முயலுங்கள்.", "पढ़ने में बहुत समय लगा। कृपया फिर कोशिश करें।"),
    "job.failed.interrupted": (
        "Reading was interrupted when the app restarted. Please upload again.",
        "பயன்பாடு மறுதொடக்கம் ஆனதால் படிப்பது நின்றுவிட்டது. மீண்டும் பதிவேற்றுங்கள்.",
        "ऐप दोबारा चालू होने से पढ़ना रुक गया। कृपया फिर से अपलोड करें।"),
    "status.narrative_preparing": (
        "Still preparing this explanation. Please check again in a moment.",
        "இந்த விளக்கம் இன்னும் தயாராகிறது. சிறிது நேரம் கழித்துப் பாருங்கள்.",
        "यह व्याख्या अभी तैयार हो रही है। कृपया थोड़ी देर बाद फिर देखें।"),
    # --- confirmation screen ----------------------------------------------------------------------------------------------------------
    "confirm.action.confirm_as_extracted": ("This matches my document", "இது என் ஆவணத்துடன் பொருந்துகிறது", "यह मेरे दस्तावेज़ से मेल खाता है"),
    "confirm.action.select_formulary_drug": ("Choose the right medicine from the list", "பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்", "सूची से सही दवा चुनें"),
    "confirm.action.not_in_list": ("My medicine is not in the list", "என் மருந்து பட்டியலில் இல்லை", "मेरी दवा सूची में नहीं है"),
    "confirm.action.remove": ("Remove: this is not on my document", "நீக்கு: இது என் ஆவணத்தில் இல்லை", "हटाएँ: यह मेरे दस्तावेज़ में नहीं है"),
    "confirm.you_confirmed": ("You confirmed this.", "நீங்கள் இதை உறுதிசெய்தீர்கள்.", "आपने इसकी पुष्टि की है।"),
    "confirm.you_selected": ("You chose this medicine from the list.", "நீங்கள் பட்டியலிலிருந்து இந்த மருந்தைத் தேர்ந்தெடுத்தீர்கள்.", "आपने सूची से यह दवा चुनी है।"),
    "confirm.you_added": ("You added this medicine from the list.", "நீங்கள் பட்டியலிலிருந்து இந்த மருந்தைச் சேர்த்தீர்கள்.", "आपने सूची से यह दवा जोड़ी है।"),
    "confirm.note_label": ("Note (optional, up to 80 characters)", "குறிப்பு (விருப்பம், 80 எழுத்துகள் வரை)", "टिप्पणी (वैकल्पिक, 80 अक्षरों तक)"),
    "picker.compare_note": (
        "Compare the brand name, generic name and strength with your document before you choose.",
        "தேர்ந்தெடுக்கும் முன் பிராண்ட் பெயர், பொதுப் பெயர் மற்றும் வலிமையை உங்கள் ஆவணத்துடன் ஒப்பிடுங்கள்.",
        "चुनने से पहले ब्रांड नाम, जेनेरिक नाम और मात्रा की अपने दस्तावेज़ से तुलना करें।"),
    "picker.search": ("Search medicine by brand or generic name", "பிராண்ட் அல்லது பொதுப் பெயரால் மருந்தைத் தேடுங்கள்", "ब्रांड या जेनेरिक नाम से दवा खोजें"),
    "picker.no_results": ("No medicine found in the list.", "பட்டியலில் மருந்து எதுவும் இல்லை.", "सूची में कोई दवा नहीं मिली।"),
    "picker.brand": ("Brand names", "பிராண்ட் பெயர்கள்", "ब्रांड नाम"),
    "picker.generic": ("Generic name", "பொதுப் பெயர்", "जेनेरिक नाम"),
    "picker.strength": ("Strength", "வலிமை", "मात्रा"),
    "picker.strength_as_label": ("Strength as on my label", "என் லேபிளில் உள்ள வலிமை", "मेरे लेबल पर लिखी मात्रा"),
    "confirm.flag.unresolved_name": (
        "The name could not be found in our list. Choose the right medicine from the list, or say it is not in the list.",
        "எங்கள் பட்டியலில் இந்தப் பெயர் கிடைக்கவில்லை. பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள், அல்லது அது பட்டியலில் இல்லை என்று சொல்லுங்கள்.",
        "यह नाम हमारी सूची में नहीं मिला। सूची से सही दवा चुनें, या बताएँ कि वह सूची में नहीं है।"),
    "confirm.flag.near_miss_name": (
        "The name is close to a known medicine but not an exact match. Choose the right medicine from the list.",
        "இந்தப் பெயர் அறிந்த மருந்துக்கு நெருக்கமானது, ஆனால் சரியாகப் பொருந்தவில்லை. பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "यह नाम किसी जानी-पहचानी दवा के क़रीब है पर ठीक वही नहीं है। सूची से सही दवा चुनें।"),
    "confirm.flag.role_corrected": (
        "The brand and generic names may have been mixed up. Choose the right medicine from the list.",
        "பிராண்ட் மற்றும் பொதுப் பெயர்கள் மாறியிருக்கலாம். பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "ब्रांड और जेनेरिक नाम आपस में बदल गए हो सकते हैं। सूची से सही दवा चुनें।"),
    "confirm.flag.duplicate_name_fields": (
        "Only one name was found for this medicine. Choose the right medicine from the list.",
        "இந்த மருந்துக்கு ஒரே ஒரு பெயர் மட்டுமே கிடைத்தது. பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "इस दवा का केवल एक नाम मिला। सूची से सही दवा चुनें।"),
    "confirm.flag.name_not_in_quote": (
        "The name does not appear in the text that was read. Choose the right medicine from the list.",
        "படிக்கப்பட்ட உரையில் இந்தப் பெயர் இல்லை. பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "पढ़े गए पाठ में यह नाम नहीं है। सूची से सही दवा चुनें।"),
    "confirm.flag.missing_name": (
        "No medicine name was found. Choose the right medicine from the list.",
        "மருந்தின் பெயர் கிடைக்கவில்லை. பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "दवा का कोई नाम नहीं मिला। सूची से सही दवा चुनें।"),
    "confirm.flag.multiple_drugs_in_quote": (
        "More than one medicine seems to be on this line. Choose the right medicine from the list.",
        "இந்த வரியில் ஒன்றுக்கு மேற்பட்ட மருந்துகள் இருப்பதாகத் தெரிகிறது. பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "इस पंक्ति में एक से ज़्यादा दवाएँ दिखती हैं। सूची से सही दवा चुनें।"),
    "confirm.flag.possible_combination": (
        "This may be a combination medicine that we could not match. Choose the right medicine from the list.",
        "இது எங்களால் பொருத்த முடியாத கூட்டு மருந்தாக இருக்கலாம். பட்டியலிலிருந்து சரியான மருந்தைத் தேர்ந்தெடுங்கள்.",
        "यह मिली-जुली दवा हो सकती है जिसे हम मिला नहीं सके। सूची से सही दवा चुनें।"),
    "confirm.flag.incomplete_quote": (
        "Some details may be missing from what was read. I have compared them with my document.",
        "படிக்கப்பட்டதில் சில விவரங்கள் விடுபட்டிருக்கலாம். அவற்றை என் ஆவணத்துடன் ஒப்பிட்டுப் பார்த்தேன்.",
        "पढ़ी गई बातों में कुछ ब्यौरे छूटे हो सकते हैं। मैंने उन्हें अपने दस्तावेज़ से मिला लिया है।"),
    "confirm.flag.unusual_strength": (
        "This strength is not one of the usual strengths for this medicine. I have checked it on my label.",
        "இந்த வலிமை இந்த மருந்துக்கான வழக்கமான வலிமைகளில் ஒன்று அல்ல. என் லேபிளில் சரிபார்த்தேன்.",
        "यह मात्रा इस दवा की सामान्य मात्राओं में से नहीं है। मैंने इसे अपने लेबल पर जाँच लिया है।"),
    "confirm.flag.non_daily_frequency": (
        "This medicine does not seem to be taken every day. I have checked how often with my document.",
        "இந்த மருந்து தினமும் எடுக்கப்படுவதாகத் தெரியவில்லை. எத்தனை முறை என்பதை என் ஆவணத்தில் சரிபார்த்தேன்.",
        "यह दवा रोज़ लेने वाली नहीं लगती। मैंने अपने दस्तावेज़ में देख लिया है कि कितनी बार लेनी है।"),
    "confirm.flag.ambiguous_OD": (
        "The short form OD can mean once a day or the right eye. I have checked what it means here.",
        "OD என்பது தினமும் ஒரு முறை அல்லது வலது கண் என்று பொருள்படலாம். இங்கே அதன் பொருளைச் சரிபார்த்தேன்.",
        "OD का मतलब दिन में एक बार या दाईं आँख हो सकता है। मैंने देख लिया है कि यहाँ इसका क्या मतलब है।"),
    "confirm.flag.conflicting_frequency": (
        "The text gives more than one way to take this medicine. I have checked it with my document.",
        "இந்த மருந்தை எடுக்கும் முறை ஒன்றுக்கு மேற்பட்ட விதமாக எழுதப்பட்டுள்ளது. என் ஆவணத்தில் சரிபார்த்தேன்.",
        "पाठ में इस दवा को लेने के एक से ज़्यादा तरीक़े लिखे हैं। मैंने अपने दस्तावेज़ से जाँच लिया है।"),
    "confirm.flag.conflicting_meal_relation": (
        "The text says both before and after meals. I have checked it with my document.",
        "உணவுக்கு முன் மற்றும் பின் என இரண்டும் எழுதப்பட்டுள்ளது. என் ஆவணத்தில் சரிபார்த்தேன்.",
        "पाठ में खाने से पहले और बाद दोनों लिखा है। मैंने अपने दस्तावेज़ से जाँच लिया है।"),
    "confirm.flag.conflicting_duration": (
        "The text gives more than one duration. I have checked it with my document.",
        "காலம் ஒன்றுக்கு மேற்பட்ட விதமாக எழுதப்பட்டுள்ளது. என் ஆவணத்தில் சரிபார்த்தேன்.",
        "पाठ में अवधि एक से ज़्यादा तरह से लिखी है। मैंने अपने दस्तावेज़ से जाँच ली है।"),
    "confirm.flag.low_confidence": (
        "The reader was not sure about this line. I have compared it with my document.",
        "இந்த வரியைப் பற்றி வாசிப்பான் உறுதியாக இல்லை. என் ஆவணத்துடன் ஒப்பிட்டுப் பார்த்தேன்.",
        "रीडर को इस पंक्ति के बारे में पक्का भरोसा नहीं था। मैंने इसे अपने दस्तावेज़ से मिला लिया है।"),
    "confirm.flag.quote_not_in_document": (
        "This line could not be matched to the document text. I have compared it with my document.",
        "இந்த வரியை ஆவண உரையுடன் பொருத்த முடியவில்லை. என் ஆவணத்துடன் ஒப்பிட்டுப் பார்த்தேன்.",
        "इस पंक्ति को दस्तावेज़ के पाठ से मिलाया नहीं जा सका। मैंने इसे अपने दस्तावेज़ से मिला लिया है।"),
    "confirm.flag.user_not_in_list": (
        "You said this medicine is not in the list. It was not checked for interactions.",
        "இந்த மருந்து பட்டியலில் இல்லை என்று சொன்னீர்கள். இடைவினைகளுக்காக இது சரிபார்க்கப்படவில்லை.",
        "आपने कहा कि यह दवा सूची में नहीं है। इसके आपसी असर की जाँच नहीं की गई।"),
    "confirm.flag.not_identifiable": (
        "We could not identify this medicine, so it was not checked for interactions.",
        "இந்த மருந்தை அடையாளம் காண முடியவில்லை, எனவே இடைவினைகளுக்காகச் சரிபார்க்கப்படவில்லை.",
        "हम इस दवा की पहचान नहीं कर सके, इसलिए इसके आपसी असर की जाँच नहीं की गई।"),
    # --- schedule ---------------------------------------------------------------------------------------------------------------------
    "schedule.notice": (
        "Suggested times only; adjust them to match your doctor's instructions.",
        "பரிந்துரைக்கப்பட்ட நேரங்கள் மட்டுமே; உங்கள் மருத்துவரின் அறிவுறுத்தலுக்கு ஏற்ப அவற்றை மாற்றிக்கொள்ளுங்கள்.",
        "ये केवल सुझाए गए समय हैं; अपने डॉक्टर के निर्देश के अनुसार इन्हें बदल लें।"),
    "schedule.no_meal_timing": (
        "No meal timing was found in the document, so these times are spread through the day.",
        "ஆவணத்தில் உணவு நேரம் குறிப்பிடப்படவில்லை, எனவே இந்த நேரங்கள் நாள் முழுவதும் பிரித்து வைக்கப்பட்டுள்ளன.",
        "दस्तावेज़ में खाने का समय नहीं मिला, इसलिए ये समय दिन भर में बाँटे गए हैं।"),
    "schedule.duration_days": ("About {n} days in total.", "மொத்தம் சுமார் {n} நாட்கள்.", "कुल लगभग {n} दिन।"),
    "schedule.not.not_confirmed": ("Not scheduled: please confirm this medicine first.", "அட்டவணையில் இல்லை: முதலில் இந்த மருந்தை உறுதிசெய்யுங்கள்.", "समय-सारणी में नहीं: पहले इस दवा की पुष्टि करें।"),
    "schedule.not.non_daily": (
        "Not scheduled: this medicine is not taken every day. Follow your document.",
        "அட்டவணையில் இல்லை: இந்த மருந்து தினமும் எடுக்கப்படுவதில்லை. உங்கள் ஆவணத்தைப் பின்பற்றுங்கள்.",
        "समय-सारणी में नहीं: यह दवा रोज़ नहीं ली जाती। अपने दस्तावेज़ के अनुसार चलें।"),
    "schedule.not.as_needed": (
        "Not scheduled: this medicine is only taken when needed.",
        "அட்டவணையில் இல்லை: இந்த மருந்து தேவைப்படும்போது மட்டுமே எடுக்கப்படும்.",
        "समय-सारणी में नहीं: यह दवा केवल ज़रूरत पड़ने पर ली जाती है।"),
    "schedule.not.too_many_doses": (
        "Not scheduled automatically: please set your own times for this medicine.",
        "தானாக அட்டவணையிடப்படவில்லை: இந்த மருந்துக்கான நேரங்களை நீங்களே அமையுங்கள்.",
        "अपने आप तय नहीं हुआ: इस दवा के समय आप खुद तय करें।"),
    "schedule.not.no_identity": (
        "Not scheduled: we could not identify this medicine.",
        "அட்டவணையில் இல்லை: இந்த மருந்தை அடையாளம் காண முடியவில்லை.",
        "समय-सारणी में नहीं: हम इस दवा की पहचान नहीं कर सके।"),
    # --- doctor summary ---------------------------------------------------------------------------------------------------------------
    "summary.title": ("Summary to show your doctor", "உங்கள் மருத்துவரிடம் காட்டுவதற்கான சுருக்கம்", "डॉक्टर को दिखाने के लिए सार"),
    "summary.heading.medicines": ("Medicines", "மருந்துகள்", "दवाएँ"),
    "summary.heading.adherence": ("Taken, skipped and missed", "எடுத்தவை, தவிர்த்தவை, தவறியவை", "ली गईं, छोड़ी गईं और छूटी हुई"),
    "summary.heading.unconfirmed": ("Not confirmed yet", "இன்னும் உறுதிசெய்யப்படாதவை", "जिनकी पुष्टि अभी नहीं हुई"),
    "summary.heading.interactions": ("Interactions found", "கண்டறியப்பட்ட இடைவினைகள்", "मिले आपसी असर"),
    "summary.label.taken": ("Taken", "எடுத்தது", "ली गई"),
    "summary.label.skipped": ("Skipped", "தவிர்த்தது", "छोड़ी गई"),
    "summary.label.missed": ("Missed", "தவறியது", "छूटी"),
    "summary.disclaimer": (
        "This summary lists what was read from your document and what you entered. It may contain mistakes. It is not medical advice. Your doctor decides about your treatment.",
        "இந்தச் சுருக்கம் உங்கள் ஆவணத்திலிருந்து படிக்கப்பட்டவற்றையும் நீங்கள் உள்ளிட்டவற்றையும் பட்டியலிடுகிறது. இதில் தவறுகள் இருக்கலாம். இது மருத்துவ ஆலோசனை அல்ல. உங்கள் சிகிச்சை பற்றி மருத்துவர் முடிவு செய்வார்.",
        "यह सार आपके दस्तावेज़ से पढ़ी गई बातें और आपकी दर्ज की हुई बातें बताता है। इसमें ग़लतियाँ हो सकती हैं। यह चिकित्सा सलाह नहीं है। आपके इलाज के बारे में डॉक्टर तय करते हैं।"),
}


def main():
    p = X.TEMPLATES
    data = json.loads(p.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in NEW.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase5_new.csv", only=set(NEW))
    print(f"{len(NEW)} templates, {n} sheet rows")


if __name__ == "__main__":
    main()
