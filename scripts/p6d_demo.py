"""Phase 6d strings: the sample (demo) mode. id -> (en, ta, hi). ta/hi are machine drafts (draft_unreviewed). English follows the honest-copy rules
(docs/DESIGN.md): no claim of accuracy or speed, nothing implies a review, the word "safe" is not used."""
STRINGS: dict[str, tuple[str, str, str]] = {
    "ui.title.demo": ("Sample · CareBridge", "மாதிரி · CareBridge", "नमूना · CareBridge"),
    "ui.demo.label": (
        "Pre-recorded sample. No photo is processed and nothing you do here is saved.",
        "முன்பே பதிவு செய்யப்பட்ட மாதிரி. எந்தப் புகைப்படமும் செயலாக்கப்படுவதில்லை; இங்கு நீங்கள் செய்யும் எதுவும் சேமிக்கப்படாது.",
        "पहले से रिकॉर्ड किया गया नमूना। कोई फ़ोटो प्रोसेस नहीं होती और यहाँ आप जो कुछ करते हैं वह सहेजा नहीं जाता।",
    ),
    "ui.demo.tag": ("Sample", "மாதிரி", "नमूना"),
    "ui.demo.leave": ("Leave the sample", "மாதிரியிலிருந்து வெளியேறு", "नमूना छोड़ें"),
    "ui.demo.nothing_to_delete": (
        "Nothing is saved in the sample, so there is nothing to delete.",
        "மாதிரியில் எதுவும் சேமிக்கப்படுவதில்லை, எனவே நீக்க எதுவும் இல்லை.",
        "नमूने में कुछ भी सहेजा नहीं जाता, इसलिए हटाने के लिए कुछ नहीं है।",
    ),
    "ui.demo.prerecorded_note": (
        "In this sample the result is pre-recorded and does not change with your choices.",
        "இந்த மாதிரியில் முடிவு முன்பே பதிவு செய்யப்பட்டது; உங்கள் தேர்வுகளால் அது மாறாது.",
        "इस नमूने में नतीजा पहले से रिकॉर्ड किया हुआ है और आपके चुनाव से नहीं बदलता।",
    ),
    "ui.demo.marks_note": (
        "Marks you make here stay in this page only and are cleared when you leave the sample.",
        "இங்கு நீங்கள் இடும் குறிகள் இந்தப் பக்கத்தில் மட்டுமே இருக்கும்; மாதிரியை விட்டு வெளியேறும்போது அழிந்துவிடும்.",
        "यहाँ आप जो निशान लगाते हैं वे केवल इसी पेज पर रहते हैं और नमूना छोड़ने पर मिट जाते हैं।",
    ),
    "ui.demo.try": ("Try a sample document", "மாதிரி ஆவணத்தை முயன்று பாருங்கள்", "एक नमूना दस्तावेज़ आज़माएँ"),
    "ui.demo.unreachable": (
        "You can still look at a pre-recorded sample. It needs no connection to the service.",
        "முன்பே பதிவு செய்யப்பட்ட மாதிரியை இன்னும் பார்க்கலாம். அதற்குச் சேவையுடன் இணைப்பு தேவையில்லை.",
        "आप अब भी पहले से रिकॉर्ड किया हुआ नमूना देख सकते हैं। इसके लिए सेवा से कनेक्शन की ज़रूरत नहीं है।",
    ),
    "ui.demo.intro.label": ("Sample", "மாதிரி", "नमूना"),
    "ui.demo.intro.title": ("A pre-recorded walk-through", "முன்பே பதிவு செய்யப்பட்ட நடைமுறை விளக்கம்", "पहले से रिकॉर्ड किया हुआ प्रदर्शन"),
    "ui.demo.intro.body1": (
        "This is a pre-recorded walk-through of one synthetic sample document. No photo is processed here, nothing you do is saved, and no model runs.",
        "இது ஒரு செயற்கை மாதிரி ஆவணத்தின் முன்பே பதிவு செய்யப்பட்ட நடைமுறை விளக்கம். இங்கு எந்தப் புகைப்படமும் செயலாக்கப்படுவதில்லை, நீங்கள் செய்யும் எதுவும் சேமிக்கப்படுவதில்லை, எந்த மாடலும் இயங்குவதில்லை.",
        "यह एक कृत्रिम नमूना दस्तावेज़ का पहले से रिकॉर्ड किया हुआ प्रदर्शन है। यहाँ कोई फ़ोटो प्रोसेस नहीं होती, आप जो करते हैं वह सहेजा नहीं जाता और कोई मॉडल नहीं चलता।",
    ),
    "ui.demo.intro.body2": (
        "The document is made up for software testing. Its photo is of poor quality, so one medicine name was read wrongly. You will see how the check step lets you correct it.",
        "இந்த ஆவணம் மென்பொருள் சோதனைக்காக உருவாக்கப்பட்டது. அதன் புகைப்படத் தரம் குறைவு; அதனால் ஒரு மருந்தின் பெயர் தவறாகப் படிக்கப்பட்டது. அதை எப்படித் திருத்தலாம் என்பதைச் சரிபார்ப்புப் படியில் காண்பீர்கள்.",
        "यह दस्तावेज़ सॉफ़्टवेयर परीक्षण के लिए बनाया गया है। इसकी फ़ोटो की गुणवत्ता कम है, इसलिए एक दवा का नाम ग़लत पढ़ा गया। जाँच वाले चरण में आप देखेंगे कि उसे कैसे सुधारा जाता है।",
    ),
    "ui.demo.intro.s1": (
        "Check the medicines the software read from the photo, and correct the one it read wrongly.",
        "மென்பொருள் புகைப்படத்திலிருந்து படித்த மருந்துகளைச் சரிபாருங்கள்; தவறாகப் படித்ததைத் திருத்துங்கள்.",
        "फ़ोटो से सॉफ़्टवेयर ने जो दवाएँ पढ़ीं उन्हें जाँचें और जो ग़लत पढ़ी गई उसे सुधारें।",
    ),
    "ui.demo.intro.s2": (
        "Read the explanation in English, Tamil or Hindi, and see which interactions were found.",
        "விளக்கத்தை ஆங்கிலம், தமிழ் அல்லது இந்தியில் படியுங்கள்; எந்தத் தொடர்புகள் கண்டறியப்பட்டன என்று பாருங்கள்.",
        "व्याख्या अंग्रेज़ी, तमिल या हिंदी में पढ़ें और देखें कि कौन-से इंटरैक्शन मिले।",
    ),
    "ui.demo.intro.s3": (
        "Look at the daily schedule and at the summary you could show a doctor.",
        "தினசரி அட்டவணையையும், மருத்துவரிடம் காட்டக்கூடிய சுருக்கத்தையும் பாருங்கள்.",
        "रोज़ का शेड्यूल और डॉक्टर को दिखाने लायक सारांश देखें।",
    ),
    "ui.demo.intro.start": ("Start the sample", "மாதிரியைத் தொடங்கு", "नमूना शुरू करें"),
    "ui.demo.intro.not_advice": (
        "This is not medical advice. Always confirm medicines with your doctor or pharmacist.",
        "இது மருத்துவ ஆலோசனை அல்ல. மருந்துகளை எப்போதும் உங்கள் மருத்துவர் அல்லது மருந்தாளரிடம் உறுதிசெய்யுங்கள்.",
        "यह चिकित्सीय सलाह नहीं है। दवाओं के बारे में हमेशा अपने डॉक्टर या फ़ार्मासिस्ट से पुष्टि करें।",
    ),
    # in the sample these replace ui.flow.review.* wording that would say "saved" (I18n.tsx: ui.demo.alt.<key without "ui.">)
    "ui.demo.alt.flow.review.saved_title": (
        "Your checks are noted for this walk-through",
        "இந்த நடைமுறை விளக்கத்திற்காக உங்கள் சரிபார்ப்புகள் குறிக்கப்பட்டன",
        "इस प्रदर्शन के लिए आपकी जाँचें दर्ज की गईं",
    ),
    "ui.demo.alt.flow.review.saved_ok": (
        "Noted for this walk-through. Nothing is saved.",
        "இந்த நடைமுறை விளக்கத்திற்காகக் குறிக்கப்பட்டது. எதுவும் சேமிக்கப்படவில்லை.",
        "इस प्रदर्शन के लिए दर्ज किया गया। कुछ भी सहेजा नहीं गया।",
    ),
    "ui.demo.alt.flow.review.saved_open": (
        "Noted for this walk-through. This medicine would still need confirmation.",
        "இந்த நடைமுறை விளக்கத்திற்காகக் குறிக்கப்பட்டது. இந்த மருந்துக்கு இன்னும் உறுதிப்படுத்தல் தேவைப்படும்.",
        "इस प्रदर्शन के लिए दर्ज किया गया। इस दवा की पुष्टि फिर भी ज़रूरी होगी।",
    ),
    "ui.demo.alt.flow.review.unsaved": ("Not noted yet", "இன்னும் குறிக்கப்படவில்லை", "अभी दर्ज नहीं हुआ"),
    "ui.demo.photo_note": (
        "The sample photo is a deliberately blurry scan, so you can see how the check step helps when a name is hard to read.",
        "மாதிரிப் புகைப்படம் வேண்டுமென்றே மங்கலாக எடுக்கப்பட்ட ஸ்கேன்; பெயரைப் படிப்பது கடினமாக இருக்கும்போது சரிபார்ப்புப் படி எப்படி உதவுகிறது என்பதைப் பார்க்கலாம்.",
        "नमूना फ़ोटो जानबूझकर धुंधला स्कैन है, ताकि आप देख सकें कि नाम पढ़ना मुश्किल होने पर जाँच वाला चरण कैसे मदद करता है।",
    ),
}
