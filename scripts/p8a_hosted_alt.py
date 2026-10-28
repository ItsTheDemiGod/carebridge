"""Phase 8a follow-up strings: wording of the hosted-sample build. id -> (en, ta, hi). ta/hi are machine drafts (draft_unreviewed).
`ui.hosted.alt.<rest>` replaces `ui.<rest>` in the hosted build ONLY (frontend/src/i18n/I18n.tsx); the normal build keeps the original text.
Honest-copy rules: no promise to upload, process a photo or read the visitor's own document; nothing says that nothing at all is sent anywhere."""
S: dict[str, tuple[str, str, str]] = {}


def s(id: str, en: str, ta: str, hi: str) -> None:
    S[id] = (en, ta, hi)


s("ui.hosted.pp.github",
  "This sample is hosted by GitHub Pages. GitHub may log visits under its own privacy policy. The site itself sets no cookies, uses no analytics and loads nothing from other sites.",
  "இந்த மாதிரி GitHub Pages மூலம் வழங்கப்படுகிறது. GitHub தனது சொந்த தனியுரிமைக் கொள்கையின்படி வருகைகளைப் பதிவு செய்யலாம். இணையதளம் தானாக குக்கீகளை அமைப்பதில்லை, பகுப்பாய்வு கருவிகளைப் பயன்படுத்துவதில்லை, வேறு தளங்களிலிருந்து எதையும் ஏற்றுவதில்லை.",
  "यह नमूना GitHub Pages पर होस्ट किया गया है। GitHub अपनी गोपनीयता नीति के अनुसार विज़िट दर्ज कर सकता है। साइट स्वयं कोई कुकी नहीं लगाती, कोई एनालिटिक्स नहीं चलाती और दूसरी साइटों से कुछ भी लोड नहीं करती।")
s("ui.hosted.pp.note",
  "This is the consent notice the real app shows before it processes a document (version {version}). It was copied into this site when the site was built.",
  "ஆவணத்தைச் செயலாக்கும் முன் உண்மையான செயலி காட்டும் ஒப்புதல் அறிவிப்பு இது (பதிப்பு {version}). இணையதளம் உருவாக்கப்பட்டபோது இதில் நகலெடுக்கப்பட்டது.",
  "यह वह सहमति-सूचना है जो असली ऐप दस्तावेज़ प्रोसेस करने से पहले दिखाता है (संस्करण {version})। साइट बनाते समय इसे यहाँ कॉपी किया गया।")
s("ui.hosted.pp.nodelete",
  "This hosted sample stores no documents and no results, so there is nothing to delete here. The real app, running on a person's own computer, has a delete-my-data function.",
  "இந்த மாதிரி இணையதளம் ஆவணங்களையும் முடிவுகளையும் சேமிப்பதில்லை, எனவே இங்கே நீக்க எதுவும் இல்லை. ஒருவரின் சொந்தக் கணினியில் இயங்கும் உண்மையான செயலியில் என் தரவை நீக்கும் வசதி உள்ளது.",
  "यह होस्ट किया गया नमूना दस्तावेज़ और नतीजे नहीं सहेजता, इसलिए यहाँ मिटाने को कुछ नहीं है। किसी के अपने कंप्यूटर पर चलने वाले असली ऐप में मेरा डेटा मिटाने की सुविधा है।")
s("ui.hosted.pp.intro",
  "This is the notice a person is asked to accept before uploading anything in the real app. This hosted sample has no upload; its pages are static files.",
  "உண்மையான செயலியில் எதையும் பதிவேற்றும் முன் ஒருவர் ஏற்க வேண்டிய அறிவிப்பு இது. இந்த மாதிரி இணையதளத்தில் பதிவேற்றம் இல்லை; இதன் பக்கங்கள் நிலையான கோப்புகள்.",
  "यह वह सूचना है जिसे असली ऐप में कुछ भी अपलोड करने से पहले स्वीकार करने को कहा जाता है। इस होस्ट किए गए नमूने में अपलोड नहीं है; इसके पेज स्थिर फ़ाइलें हैं।")
s("ui.hosted.alt.hero.sub",
  "This hosted site is a pre-recorded sample of CareBridge. See how it reads a prescription, helps you check it, and explains it in English, தமிழ் or हिन्दी.",
  "இந்த இணையதளம் CareBridge இன் முன்பதிவு செய்த மாதிரி. அது மருந்துச்சீட்டை எப்படிப் படிக்கிறது, சரிபார்க்க எப்படி உதவுகிறது, ஆங்கிலம், தமிழ் அல்லது हिन्दी மொழியில் எப்படி விளக்குகிறது என்பதைப் பாருங்கள்.",
  "यह होस्ट की गई साइट CareBridge का पहले से रिकॉर्ड किया हुआ नमूना है। देखिए कि यह पर्चे को कैसे पढ़ता है, जाँचने में कैसे मदद करता है, और English, தமிழ் या हिन्दी में कैसे समझाता है।")
s("ui.hosted.alt.steps.1.body",
  "In the real app, you take a clear photo of a prescription or discharge summary, or choose one you already have. This hosted sample has no upload.",
  "உண்மையான செயலியில், மருந்துச்சீட்டு அல்லது வெளியேற்றச் சுருக்கத்தின் தெளிவான புகைப்படம் எடுக்கிறீர்கள், அல்லது ஏற்கெனவே உள்ளதைத் தேர்ந்தெடுக்கிறீர்கள். இந்த மாதிரி இணையதளத்தில் பதிவேற்றம் இல்லை.",
  "असली ऐप में आप पर्चे या डिस्चार्ज सारांश की साफ़ फ़ोटो लेते हैं, या पहले से मौजूद फ़ोटो चुनते हैं। इस होस्ट किए गए नमूने में अपलोड नहीं है।")
s("ui.hosted.alt.steps.2.body",
  "The real app lists each medicine it found. You compare the list with your paper and correct anything that looks wrong. The sample shows this step on one invented document.",
  "உண்மையான செயலி அது கண்ட ஒவ்வொரு மருந்தையும் பட்டியலிடுகிறது. பட்டியலைத் தாளுடன் ஒப்பிட்டு தவறாகத் தோன்றுவதைத் திருத்துகிறீர்கள். மாதிரி இந்தப் படியை ஒரு கற்பனை ஆவணத்தில் காட்டுகிறது.",
  "असली ऐप हर पाई गई दवा की सूची दिखाता है। आप सूची को अपने काग़ज़ से मिलाते हैं और जो ग़लत लगे उसे सुधारते हैं। नमूना यह चरण एक गढ़े हुए दस्तावेज़ पर दिखाता है।")
s("ui.hosted.alt.steps.3.body",
  "The real app shows a short explanation, a daily timetable you can adjust, and any interaction it found or could not check. The sample shows these for one invented document.",
  "உண்மையான செயலி ஒரு குறுகிய விளக்கம், நீங்கள் மாற்றக்கூடிய தினசரி அட்டவணை, மற்றும் அது கண்ட அல்லது சோதிக்க முடியாத இடைவினைகளைக் காட்டுகிறது. மாதிரி இவற்றை ஒரு கற்பனை ஆவணத்திற்குக் காட்டுகிறது.",
  "असली ऐप एक छोटी व्याख्या, आपके बदलने योग्य रोज़ की समय-सारणी, और जो इंटरैक्शन मिला या जाँचा न जा सका वह दिखाता है। नमूना ये सब एक गढ़े हुए दस्तावेज़ के लिए दिखाता है।")
s("ui.hosted.alt.how.n1.body",
  "In the real app, you upload a photo of a prescription or discharge summary. This hosted sample has no upload.",
  "உண்மையான செயலியில், மருந்துச்சீட்டு அல்லது வெளியேற்றச் சுருக்கத்தின் புகைப்படத்தைப் பதிவேற்றுகிறீர்கள். இந்த மாதிரி இணையதளத்தில் பதிவேற்றம் இல்லை.",
  "असली ऐप में आप पर्चे या डिस्चार्ज सारांश की फ़ोटो अपलोड करते हैं। इस होस्ट किए गए नमूने में अपलोड नहीं है।")
s("ui.hosted.alt.privacy.title",
  "In the real app, your photo is read on your own computer.",
  "உண்மையான செயலியில், உங்கள் புகைப்படம் உங்கள் சொந்தக் கணினியிலேயே படிக்கப்படுகிறது.",
  "असली ऐप में आपकी फ़ोटो आपके अपने कंप्यूटर पर ही पढ़ी जाती है।")
s("ui.hosted.alt.privacy.local.title",
  "In the real app: read on your own computer",
  "உண்மையான செயலியில்: உங்கள் சொந்தக் கணினியில் படிக்கப்படுகிறது",
  "असली ऐप में: आपके अपने कंप्यूटर पर पढ़ा जाता है")
s("ui.hosted.alt.privacy.local.body",
  "In the real app, the photo is processed by a model running on the same computer, and the app sends it to no outside service. This hosted sample processes no photo.",
  "உண்மையான செயலியில், புகைப்படம் அதே கணினியில் இயங்கும் மாதிரியால் செயலாக்கப்படுகிறது; செயலி அதை எந்த வெளிச் சேவைக்கும் அனுப்புவதில்லை. இந்த மாதிரி இணையதளம் எந்தப் புகைப்படத்தையும் செயலாக்குவதில்லை.",
  "असली ऐप में फ़ोटो उसी कंप्यूटर पर चल रहे मॉडल से प्रोसेस होती है, और ऐप उसे किसी बाहरी सेवा को नहीं भेजता। यह होस्ट किया गया नमूना कोई फ़ोटो प्रोसेस नहीं करता।")
s("ui.hosted.alt.privacy.delete.title",
  "Delete-my-data, in the real app",
  "உண்மையான செயலியில் என் தரவை நீக்குதல்",
  "असली ऐप में मेरा डेटा मिटाना")
s("ui.hosted.alt.privacy.delete.body",
  "The real app has a button that deletes the session and everything stored for it, and gives a receipt. This hosted sample stores no documents or results.",
  "உண்மையான செயலியில் அமர்வையும் அதற்காகச் சேமித்த அனைத்தையும் நீக்கும் ஒரு பொத்தான் உள்ளது; அது ரசீதும் தருகிறது. இந்த மாதிரி இணையதளம் ஆவணங்களையோ முடிவுகளையோ சேமிப்பதில்லை.",
  "असली ऐप में एक बटन है जो सत्र और उसके लिए सहेजी हर चीज़ मिटा देता है और रसीद देता है। यह होस्ट किया गया नमूना दस्तावेज़ या नतीजे नहीं सहेजता।")
s("ui.hosted.alt.privacy.stored.title",
  "In the real app: stored encrypted, for a short time",
  "உண்மையான செயலியில்: குறுகிய காலத்திற்கு குறியாக்கம் செய்து சேமிக்கப்படுகிறது",
  "असली ऐप में: कुछ समय के लिए एन्क्रिप्ट करके सहेजा जाता है")
s("ui.hosted.alt.privacy.stored.body",
  "In the real app, results are kept encrypted for your session and removed automatically after 24 hours. The photo is discarded unless you choose to keep it. This hosted sample keeps no results.",
  "உண்மையான செயலியில், முடிவுகள் உங்கள் அமர்வுக்காக குறியாக்கம் செய்து வைக்கப்பட்டு 24 மணி நேரத்திற்குப் பிறகு தானாக நீக்கப்படும். நீங்கள் வைத்திருக்கத் தேர்ந்தெடுத்தால் தவிர புகைப்படம் நீக்கப்படும். இந்த மாதிரி இணையதளம் முடிவுகளை வைத்திருப்பதில்லை.",
  "असली ऐप में नतीजे आपके सत्र के लिए एन्क्रिप्ट करके रखे जाते हैं और 24 घंटे बाद अपने-आप हट जाते हैं। फ़ोटो तब तक हटा दी जाती है जब तक आप उसे रखना न चुनें। यह होस्ट किया गया नमूना कोई नतीजा नहीं रखता।")
