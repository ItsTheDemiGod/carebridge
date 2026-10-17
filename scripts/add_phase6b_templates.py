"""Phase 6b: adds the ui.flow.* template ids (consent, upload, processing, review, results, schedule, summary, delete dialog, errors) to
data/templates/templates.json (idempotent) and writes data/templates/review_sheet_phase6b_new.csv (only these ids, UTF-8 with BOM).
Every ta/hi string is draft_unreviewed (machine-drafted). English follows the honest-copy rules in docs/DESIGN.md: no "safe" except the negated form,
no claim that anyone reviewed anything, no numbers. Backend-owned text (consent notice, errors, confirmation, schedule, results) is NOT duplicated here.
python scripts/add_phase6b_templates.py"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import export_review_sheet as X  # noqa: E402

# id -> (en, ta, hi). Placeholders in {braces}. Western digits; drug names stay in Latin script.
NEW: dict[str, tuple[str, str, str]] = {}

# ---------------------------------------------------------------- shell, progress, delete dialog, generic problems (6b-2)
NEW.update({
    "ui.flow.nav.documents": ("Your documents", "உங்கள் ஆவணங்கள்", "आपके दस्तावेज़"),
    "ui.flow.loading": ("Loading…", "ஏற்றுகிறது…", "लोड हो रहा है…"),
    "ui.flow.retry": ("Try again", "மீண்டும் முயலுங்கள்", "फिर से कोशिश करें"),
    "ui.flow.progress.label": ("Progress", "முன்னேற்றம்", "प्रगति"),
    "ui.flow.progress.done": ("(done)", "(முடிந்தது)", "(पूरा हुआ)"),
    "ui.flow.stage.consent": ("Consent", "ஒப்புதல்", "सहमति"),
    "ui.flow.stage.photo": ("Photo", "புகைப்படம்", "फ़ोटो"),
    "ui.flow.stage.check": ("Check", "சரிபார்ப்பு", "जाँच"),
    "ui.flow.stage.results": ("Results", "முடிவுகள்", "नतीजे"),
    "ui.flow.stage.schedule": ("Schedule", "அட்டவணை", "समय-सारणी"),
    "ui.flow.delete.button": ("Delete my data", "என் தரவை நீக்கு", "मेरा डेटा हटाएँ"),
    "ui.flow.delete.title": ("Delete everything for this session?", "இந்த அமர்வின் எல்லாவற்றையும் நீக்கவா?", "इस सत्र का सब कुछ हटाएँ?"),
    "ui.flow.delete.body": ("This erases everything CareBridge holds for this session. It cannot be undone, and it also withdraws your consent.",
                            "இந்த அமர்வுக்காக CareBridge வைத்திருக்கும் அனைத்தையும் இது அழிக்கும். இதைத் திரும்பப் பெற முடியாது; உங்கள் ஒப்புதலும் திரும்பப் பெறப்படும்.",
                            "इस सत्र के लिए CareBridge के पास जो कुछ है, यह सब मिटा देता है। इसे वापस नहीं किया जा सकता, और इससे आपकी सहमति भी वापस हो जाती है।"),
    "ui.flow.delete.c1": ("Your results and explanations", "உங்கள் முடிவுகளும் விளக்கங்களும்", "आपके नतीजे और स्पष्टीकरण"),
    "ui.flow.delete.c2": ("Your checks, schedule times and the taken or skipped marks", "நீங்கள் செய்த சரிபார்ப்புகள், நேரங்கள், எடுத்த அல்லது தவிர்த்த குறிப்புகள்", "आपकी जाँचें, समय और ली या छोड़ी गई खुराक के निशान"),
    "ui.flow.delete.c3": ("The photo, if you chose to keep it", "நீங்கள் வைத்திருக்கத் தேர்ந்தால் புகைப்படம்", "फ़ोटो, अगर आपने उसे रखना चुना था"),
    "ui.flow.delete.cancel": ("Keep my data", "என் தரவை வைத்திருங்கள்", "मेरा डेटा रहने दें"),
    "ui.flow.delete.confirm": ("Delete everything", "எல்லாவற்றையும் நீக்கு", "सब कुछ हटाएँ"),
    "ui.flow.delete.failed": ("Deleting did not work. Please try again.", "நீக்க முடியவில்லை. மீண்டும் முயலுங்கள்.", "हटाना नहीं हो सका। कृपया फिर कोशिश करें।"),
    "ui.flow.delete.nothing": ("There was nothing to delete.", "நீக்க எதுவும் இல்லை.", "हटाने के लिए कुछ नहीं था।"),
    "ui.flow.expired.title": ("Your session has ended", "உங்கள் அமர்வு முடிந்துவிட்டது", "आपका सत्र समाप्त हो गया है"),
    "ui.flow.expired.body": ("The session expired or was deleted, and its data is gone. Nothing from it can be recovered. You can start again.",
                             "அமர்வு காலாவதியானது அல்லது நீக்கப்பட்டது; அதன் தரவு போய்விட்டது. அதிலிருந்து எதையும் மீட்க முடியாது. நீங்கள் மீண்டும் தொடங்கலாம்.",
                             "सत्र समाप्त हो गया या हटा दिया गया, और उसका डेटा मिट गया है। उसमें से कुछ भी वापस नहीं लाया जा सकता। आप फिर से शुरू कर सकते हैं।"),
    "ui.flow.expired.again": ("Start again", "மீண்டும் தொடங்குங்கள்", "फिर से शुरू करें"),
    "ui.flow.problem.network.title": ("The server is not reachable", "சேவையகத்தை அடைய முடியவில்லை", "सर्वर तक पहुँचा नहीं जा सका"),
    "ui.flow.problem.network": ("The CareBridge server on this computer did not answer. Check that the backend is running, then try again.",
                                "இந்தக் கணினியில் உள்ள CareBridge சேவையகம் பதிலளிக்கவில்லை. பின்தளம் இயங்குகிறதா என்று பார்த்து மீண்டும் முயலுங்கள்.",
                                "इस कंप्यूटर का CareBridge सर्वर जवाब नहीं दे रहा। देखें कि बैकएंड चल रहा है, फिर दोबारा कोशिश करें।"),
    "ui.flow.problem.expired": ("Your session has ended. Please start again.", "உங்கள் அமர்வு முடிந்துவிட்டது. மீண்டும் தொடங்குங்கள்.", "आपका सत्र समाप्त हो गया है। कृपया फिर से शुरू करें।"),
    "ui.flow.problem.consent_required": ("Please read and accept the notice first.", "முதலில் அறிவிப்பைப் படித்து ஏற்றுக்கொள்ளுங்கள்.", "पहले सूचना पढ़कर स्वीकार करें।"),
    "ui.flow.problem.blocked": ("The request was blocked for security reasons.", "பாதுகாப்புக் காரணங்களுக்காகக் கோரிக்கை தடுக்கப்பட்டது.", "सुरक्षा कारणों से अनुरोध रोका गया।"),
    "ui.flow.problem.not_found": ("We could not find that. It may have been deleted.", "அது கிடைக்கவில்லை. அது நீக்கப்பட்டிருக்கலாம்.", "यह नहीं मिला। हो सकता है यह हटा दिया गया हो।"),
    "ui.flow.problem.not_ready": ("This is not ready yet. Please wait a moment.", "இது இன்னும் தயாராகவில்லை. சற்றுக் காத்திருங்கள்.", "यह अभी तैयार नहीं है। कृपया थोड़ा रुकें।"),
    "ui.flow.problem.queue_full": ("The reader is busy. Please try again in a minute.", "வாசிப்பான் பரபரப்பாக உள்ளது. ஒரு நிமிடத்தில் மீண்டும் முயலுங்கள்.", "रीडर व्यस्त है। कृपया एक मिनट बाद फिर कोशिश करें।"),
    "ui.flow.problem.queue_full_retry": ("The reader is busy. Please try again in about {seconds} seconds.", "வாசிப்பான் பரபரப்பாக உள்ளது. சுமார் {seconds} விநாடிகளில் மீண்டும் முயலுங்கள்.", "रीडर व्यस्त है। लगभग {seconds} सेकंड बाद फिर कोशिश करें।"),
    "ui.flow.problem.too_many_documents": ("The limit of documents for this session has been reached. Delete your data to start again.", "இந்த அமர்வுக்கான ஆவண வரம்பை எட்டிவிட்டீர்கள். மீண்டும் தொடங்க உங்கள் தரவை நீக்குங்கள்.", "इस सत्र के दस्तावेज़ों की सीमा पूरी हो गई। फिर शुरू करने के लिए अपना डेटा हटाएँ।"),
    "ui.flow.problem.too_large": ("This file is too large. Please use a smaller photo.", "இந்தக் கோப்பு மிகப் பெரியது. சிறிய புகைப்படத்தைப் பயன்படுத்துங்கள்.", "यह फ़ाइल बहुत बड़ी है। कृपया छोटी फ़ोटो लें।"),
    "ui.flow.problem.pdf": ("Please upload a photo or image (PNG or JPG). PDF is not supported yet.", "புகைப்படம் அல்லது படத்தை (PNG அல்லது JPG) பதிவேற்றுங்கள். PDF இன்னும் ஆதரிக்கப்படவில்லை.", "कृपया फ़ोटो या चित्र (PNG या JPG) अपलोड करें। PDF अभी समर्थित नहीं है।"),
    "ui.flow.problem.unsupported": ("Please upload a photo or image (PNG or JPG).", "புகைப்படம் அல்லது படத்தை (PNG அல்லது JPG) பதிவேற்றுங்கள்.", "कृपया फ़ोटो या चित्र (PNG या JPG) अपलोड करें।"),
    "ui.flow.problem.invalid": ("The request was not valid. Please check it and try again.", "கோரிக்கை சரியில்லை. சரிபார்த்து மீண்டும் முயலுங்கள்.", "अनुरोध सही नहीं था। जाँचकर फिर कोशिश करें।"),
    "ui.flow.problem.server": ("Something went wrong on our side. Please try again.", "எங்கள் பக்கத்தில் ஏதோ தவறு நடந்தது. மீண்டும் முயலுங்கள்.", "हमारी तरफ़ कुछ गड़बड़ हुई। कृपया फिर कोशिश करें।"),
    "ui.flow.problem.unknown": ("Something unexpected happened. Please try again.", "எதிர்பாராத ஒன்று நடந்தது. மீண்டும் முயலுங்கள்.", "कुछ अनपेक्षित हुआ। कृपया फिर कोशिश करें।"),
})

# ---------------------------------------------------------------- start, consent, upload (6b-2)
NEW.update({
    "ui.title.consent": ("Before we start · CareBridge", "தொடங்கும் முன் · CareBridge", "शुरू करने से पहले · CareBridge"),
    "ui.title.upload": ("Upload a photo · CareBridge", "புகைப்படத்தைப் பதிவேற்றுங்கள் · CareBridge", "फ़ोटो अपलोड करें · CareBridge"),
    "ui.flow.start.step1.title": ("Add a photo", "புகைப்படம் சேர்க்கவும்", "फ़ोटो जोड़ें"),
    "ui.flow.start.step1.body": ("Photograph your discharge summary or prescription, or choose a picture from this computer.", "உங்கள் வெளியேற்றச் சுருக்கம் அல்லது மருந்துச்சீட்டைப் படம் எடுங்கள், அல்லது இந்தக் கணினியிலிருந்து படத்தைத் தேர்ந்தெடுங்கள்.", "अपने डिस्चार्ज सारांश या पर्चे की फ़ोटो लें, या इस कंप्यूटर से कोई तस्वीर चुनें।"),
    "ui.flow.start.step2.title": ("Check the medicines", "மருந்துகளைச் சரிபார்க்கவும்", "दवाओं की जाँच करें"),
    "ui.flow.start.step2.body": ("You compare each medicine with your own paper and confirm it. Nothing is assumed for you.", "ஒவ்வொரு மருந்தையும் உங்கள் காகிதத்துடன் ஒப்பிட்டு உறுதிசெய்கிறீர்கள். உங்களுக்காக எதுவும் ஊகிக்கப்படாது.", "आप हर दवा को अपने कागज़ से मिलाकर पुष्टि करते हैं। आपके लिए कुछ भी मान नहीं लिया जाता।"),
    "ui.flow.start.step3.title": ("Read the results", "முடிவுகளைப் படிக்கவும்", "नतीजे पढ़ें"),
    "ui.flow.start.step3.body": ("A plain-language explanation, interactions that were found, and a suggested schedule you can adjust.", "எளிய மொழி விளக்கம், கண்டறியப்பட்ட இடைவினைகள், நீங்கள் மாற்றக்கூடிய பரிந்துரை அட்டவணை.", "सरल भाषा में स्पष्टीकरण, मिली हुई इंटरैक्शन, और एक सुझाया गया समय-सारणी जिसे आप बदल सकते हैं।"),
    "ui.flow.start.local": ("The photo is read by a model on this computer. Nothing is sent to an outside service. You can delete everything at any time with the button in the header.",
                            "புகைப்படம் இந்தக் கணினியிலுள்ள மாதிரியால் படிக்கப்படுகிறது. வெளிச் சேவைக்கு எதுவும் அனுப்பப்படாது. தலைப்புப் பட்டியிலுள்ள பொத்தானால் எப்போது வேண்டுமானாலும் எல்லாவற்றையும் நீக்கலாம்.",
                            "फ़ोटो इसी कंप्यूटर पर एक मॉडल पढ़ता है। किसी बाहरी सेवा को कुछ नहीं भेजा जाता। आप ऊपर के बटन से कभी भी सब कुछ हटा सकते हैं।"),
    "ui.flow.start.begin": ("Begin", "தொடங்குங்கள்", "शुरू करें"),
    "ui.flow.start.continue": ("Continue with a new photo", "புதிய புகைப்படத்துடன் தொடருங்கள்", "नई फ़ोटो के साथ आगे बढ़ें"),
    "ui.flow.consent.title": ("Please read and agree", "படித்து ஒப்புக்கொள்ளுங்கள்", "कृपया पढ़ें और सहमत हों"),
    "ui.flow.consent.intro": ("CareBridge needs your permission before it reads anything. This is the notice the app itself uses.", "எதையும் படிக்கும் முன் CareBridge உங்கள் அனுமதியைக் கேட்கிறது. இது செயலி பயன்படுத்தும் அதே அறிவிப்பு.", "कुछ भी पढ़ने से पहले CareBridge को आपकी अनुमति चाहिए। यह वही सूचना है जो ऐप खुद इस्तेमाल करता है।"),
    "ui.flow.consent.purposes": ("What you agree to", "நீங்கள் எதற்கு ஒப்புக்கொள்கிறீர்கள்", "आप किसके लिए सहमत हैं"),
    "ui.flow.consent.required": ("Required", "தேவை", "ज़रूरी"),
    "ui.flow.consent.optional": ("Optional, off by default", "விருப்பம், இயல்பாக அணைந்தது", "वैकल्पिक, शुरू में बंद"),
    "ui.flow.consent.keep_photo_help": ("If you keep the photo, it is stored encrypted for this session only. That lets you retry a failed reading and lets the check screen show your photo from the server. If you do not, the photo is discarded after reading.",
                                        "புகைப்படத்தை வைத்திருந்தால், இந்த அமர்வுக்கு மட்டும் குறியாக்கம் செய்து சேமிக்கப்படும். இதனால் தோல்வியடைந்த வாசிப்பை மீண்டும் முயலலாம்; சரிபார்ப்புத் திரையும் சேவையகத்திலிருந்து உங்கள் புகைப்படத்தைக் காட்டும். வைத்திருக்காவிட்டால், வாசித்த பின் புகைப்படம் நீக்கப்படும்.",
                                        "अगर आप फ़ोटो रखते हैं तो वह सिर्फ़ इस सत्र के लिए एन्क्रिप्टेड रूप में रखी जाती है। इससे विफल पढ़ाई दोबारा हो सकती है और जाँच-स्क्रीन सर्वर से आपकी फ़ोटो दिखा सकती है। न रखने पर पढ़ने के बाद फ़ोटो हटा दी जाती है।"),
    "ui.flow.consent.accept": ("I agree, continue", "ஒப்புக்கொள்கிறேன், தொடருங்கள்", "मैं सहमत हूँ, आगे बढ़ें"),
    "ui.flow.upload.title": ("Add a photo of your document", "உங்கள் ஆவணத்தின் புகைப்படத்தைச் சேர்க்கவும்", "अपने दस्तावेज़ की फ़ोटो जोड़ें"),
    "ui.flow.upload.intro": ("Choose one page at a time. You will check what was read before anything is explained.", "ஒரு நேரத்தில் ஒரு பக்கத்தைத் தேர்ந்தெடுங்கள். எதுவும் விளக்கப்படும் முன், படிக்கப்பட்டதை நீங்கள் சரிபார்ப்பீர்கள்.", "एक बार में एक पन्ना चुनें। कुछ भी समझाए जाने से पहले आप पढ़े गए को जाँचेंगे।"),
    "ui.flow.upload.drop": ("Drop a photo here, or choose one", "இங்கே புகைப்படத்தை விடுங்கள், அல்லது தேர்ந்தெடுங்கள்", "फ़ोटो यहाँ छोड़ें, या चुनें"),
    "ui.flow.upload.pick": ("Choose a file", "கோப்பைத் தேர்ந்தெடுங்கள்", "फ़ाइल चुनें"),
    "ui.flow.upload.camera": ("Take a photo", "படம் எடுங்கள்", "फ़ोटो खींचें"),
    "ui.flow.upload.types": ("PNG or JPG only. PDF is not supported yet.", "PNG அல்லது JPG மட்டும். PDF இன்னும் ஆதரிக்கப்படவில்லை.", "सिर्फ़ PNG या JPG। PDF अभी समर्थित नहीं है।"),
    "ui.flow.upload.preview_alt": ("Preview of the photo you chose", "நீங்கள் தேர்ந்தெடுத்த புகைப்படத்தின் முன்னோட்டம்", "आपकी चुनी हुई फ़ोटो का पूर्वावलोकन"),
    "ui.flow.upload.preview_note": ("This preview stays in this browser tab only. Check that the page is flat, sharp and fully in the frame.", "இந்த முன்னோட்டம் இந்த உலாவித் தாவலில் மட்டுமே இருக்கும். பக்கம் தட்டையாகவும், தெளிவாகவும், முழுமையாகவும் உள்ளதா என்று பாருங்கள்.", "यह पूर्वावलोकन सिर्फ़ इस ब्राउज़र टैब में रहता है। देखें कि पन्ना सपाट, साफ़ और पूरा फ़्रेम में है।"),
    "ui.flow.upload.use": ("Use this photo", "இந்தப் புகைப்படத்தைப் பயன்படுத்து", "यही फ़ोटो इस्तेमाल करें"),
    "ui.flow.upload.another": ("Choose another", "வேறொன்றைத் தேர்ந்தெடுங்கள்", "दूसरी चुनें"),
    "ui.flow.upload.guide.title": ("For a good reading", "நல்ல வாசிப்புக்கு", "अच्छी पढ़ाई के लिए"),
    "ui.flow.upload.guide.1": ("Lay the page flat.", "பக்கத்தைத் தட்டையாக வையுங்கள்.", "पन्ने को सपाट रखें।"),
    "ui.flow.upload.guide.2": ("Use good light and avoid shadows and glare.", "நல்ல வெளிச்சம் பயன்படுத்துங்கள்; நிழலையும் பளபளப்பையும் தவிருங்கள்.", "अच्छी रोशनी लें; छाया और चमक से बचें।"),
    "ui.flow.upload.guide.3": ("Keep the whole page in the frame.", "முழுப் பக்கத்தையும் சட்டத்துக்குள் வையுங்கள்.", "पूरा पन्ना फ़्रेम में रखें।"),
    "ui.flow.upload.guide.4": ("Do not include other people's information.", "மற்றவர்களின் தகவலைச் சேர்க்காதீர்கள்.", "दूसरों की जानकारी शामिल न करें।"),
    "ui.flow.upload.local": ("The photo is read by a model on this computer. Nothing is sent to an outside service.", "புகைப்படம் இந்தக் கணினியிலுள்ள மாதிரியால் படிக்கப்படுகிறது. வெளிச் சேவைக்கு எதுவும் அனுப்பப்படாது.", "फ़ोटो इसी कंप्यूटर पर एक मॉडल पढ़ता है। किसी बाहरी सेवा को कुछ नहीं भेजा जाता।"),
})

# ---------------------------------------------------------------- page titles + processing (6b-3)
NEW.update({
    "ui.title.processing": ("Reading your photo · CareBridge", "உங்கள் புகைப்படத்தைப் படிக்கிறது · CareBridge", "आपकी फ़ोटो पढ़ी जा रही है · CareBridge"),
    "ui.title.review": ("Check your medicines · CareBridge", "உங்கள் மருந்துகளைச் சரிபார்க்கவும் · CareBridge", "अपनी दवाओं की जाँच करें · CareBridge"),
    "ui.title.result": ("Your results · CareBridge", "உங்கள் முடிவுகள் · CareBridge", "आपके नतीजे · CareBridge"),
    "ui.title.schedule": ("Your schedule · CareBridge", "உங்கள் அட்டவணை · CareBridge", "आपकी समय-सारणी · CareBridge"),
    "ui.title.summary": ("Summary for your doctor · CareBridge", "உங்கள் மருத்துவருக்கான சுருக்கம் · CareBridge", "आपके डॉक्टर के लिए सारांश · CareBridge"),
    "ui.title.documents": ("Your documents · CareBridge", "உங்கள் ஆவணங்கள் · CareBridge", "आपके दस्तावेज़ · CareBridge"),
    "ui.flow.processing.title": ("Reading your photo", "உங்கள் புகைப்படத்தைப் படிக்கிறது", "आपकी फ़ोटो पढ़ी जा रही है"),
    "ui.flow.processing.estimate": ("This usually takes one to three minutes on this computer. It can take longer.", "இந்தக் கணினியில் இது பொதுவாக ஒன்று முதல் மூன்று நிமிடங்கள் ஆகும். அதிக நேரமும் ஆகலாம்.", "इस कंप्यूटर पर इसमें आम तौर पर एक से तीन मिनट लगते हैं। इससे ज़्यादा समय भी लग सकता है।"),
    "ui.flow.processing.stage.queued": ("Waiting for the reader", "வாசிப்பானுக்காகக் காத்திருக்கிறது", "रीडर का इंतज़ार"),
    "ui.flow.processing.stage.extracting": ("Reading the photo", "புகைப்படத்தைப் படிக்கிறது", "फ़ोटो पढ़ी जा रही है"),
    "ui.flow.processing.stage.normalising": ("Organising the results", "முடிவுகளை ஒழுங்குபடுத்துகிறது", "नतीजे व्यवस्थित हो रहे हैं"),
    "ui.flow.processing.nothing_to_do": ("There is nothing for you to do yet. You can leave this page open and come back; your place is kept.", "இப்போது நீங்கள் செய்ய எதுவும் இல்லை. இந்தப் பக்கத்தைத் திறந்தே வைக்கலாம், திரும்பியும் வரலாம்; உங்கள் இடம் பாதுகாக்கப்படும்.", "अभी आपको कुछ करने की ज़रूरत नहीं है। आप यह पन्ना खुला छोड़ सकते हैं या बाद में लौट सकते हैं; आपकी जगह बनी रहती है।"),
    "ui.flow.processing.offline": ("The connection to the server was lost. Trying again.", "சேவையகத்துடனான இணைப்பு துண்டிக்கப்பட்டது. மீண்டும் முயல்கிறது.", "सर्वर से संपर्क टूट गया। फिर कोशिश हो रही है।"),
    "ui.flow.processing.failed_title": ("The photo could not be read", "புகைப்படத்தைப் படிக்க முடியவில்லை", "फ़ोटो पढ़ी नहीं जा सकी"),
    "ui.flow.processing.kept_hint": ("You chose to keep the photo, so you can try reading it again.", "புகைப்படத்தை வைத்திருக்கத் தேர்ந்தீர்கள்; எனவே மீண்டும் படிக்க முயலலாம்.", "आपने फ़ोटो रखना चुना था, इसलिए आप उसे फिर से पढ़वा सकते हैं।"),
    "ui.flow.processing.not_kept_hint": ("The photo was not kept, so it has to be uploaded again.", "புகைப்படம் வைத்திருக்கப்படவில்லை; எனவே மீண்டும் பதிவேற்ற வேண்டும்.", "फ़ोटो रखी नहीं गई थी, इसलिए उसे फिर से अपलोड करना होगा।"),
    "ui.flow.processing.retry": ("Try reading again", "மீண்டும் படிக்க முயலுங்கள்", "फिर से पढ़वाएँ"),
    "ui.flow.processing.upload_again": ("Upload a photo again", "புகைப்படத்தை மீண்டும் பதிவேற்றுங்கள்", "फ़ोटो फिर से अपलोड करें"),
    "ui.flow.processing.to_start": ("Return to the start", "தொடக்கத்துக்குத் திரும்புங்கள்", "शुरुआत पर लौटें"),
})


def main():
    p = X.TEMPLATES
    data = json.loads(p.read_text(encoding="utf-8"))
    for tid, (en, ta, hi) in NEW.items():
        data["strings"][tid] = {"en": {"text": en, "review_status": "not_required"}, "ta": {"text": ta, "review_status": "draft_unreviewed"},
                                "hi": {"text": hi, "review_status": "draft_unreviewed"}}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n = X.export(sheet=REPO / "data" / "templates" / "review_sheet_phase6b_new.csv", only=set(NEW))
    print(f"{len(NEW)} templates, {n} sheet rows")


if __name__ == "__main__":
    main()
