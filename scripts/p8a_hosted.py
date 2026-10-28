"""Phase 8a strings: the hosted-sample (GitHub Pages) build. id -> (en, ta, hi). ta/hi are machine drafts (draft_unreviewed).
Honest-copy rules as before: no forbidden words, nothing implies a review, no number except placeholders."""
S: dict[str, tuple[str, str, str]] = {}


def s(id: str, en: str, ta: str, hi: str) -> None:
    S[id] = (en, ta, hi)


s("ui.title.hosted", "Sample only", "மாதிரி மட்டும்", "केवल नमूना")
s("ui.hosted.title", "This hosted site is the pre-recorded sample only",
  "இந்த இணையதளம் முன்பதிவு செய்த மாதிரி மட்டுமே",
  "यह होस्ट की गई साइट केवल पहले से रिकॉर्ड किया गया नमूना है")
s("ui.hosted.body1",
  "The real CareBridge reads a photo of a document with a local model on the owner's own computer. That part is not available here: nothing is uploaded or processed on this site, and nothing is saved.",
  "உண்மையான CareBridge ஆவணத்தின் புகைப்படத்தை உரிமையாளரின் சொந்தக் கணினியில் உள்ள உள்ளூர் மாதிரியால் படிக்கிறது. அந்தப் பகுதி இங்கே கிடைக்காது: இந்த இணையதளத்தில் எதுவும் பதிவேற்றப்படுவதில்லை, செயலாக்கப்படுவதில்லை, சேமிக்கப்படுவதும் இல்லை.",
  "असली CareBridge किसी दस्तावेज़ की फ़ोटो को मालिक के अपने कंप्यूटर पर चल रहे स्थानीय मॉडल से पढ़ता है। वह हिस्सा यहाँ उपलब्ध नहीं है: इस साइट पर कुछ भी अपलोड या प्रोसेस नहीं होता, और कुछ भी सहेजा नहीं जाता।")
s("ui.hosted.body2",
  "You can open the pre-recorded walk-through of one invented document, or read the project's code and its test results.",
  "ஒரு கற்பனை ஆவணத்தின் முன்பதிவு செய்த விளக்கப் பயணத்தைத் திறக்கலாம், அல்லது திட்டத்தின் நிரலையும் சோதனை முடிவுகளையும் படிக்கலாம்.",
  "आप एक गढ़े हुए दस्तावेज़ का पहले से रिकॉर्ड किया हुआ walk-through खोल सकते हैं, या प्रोजेक्ट का कोड और उसके परीक्षण के नतीजे पढ़ सकते हैं।")
s("ui.hosted.link_repo", "Project code and test results", "திட்டத்தின் நிரலும் சோதனை முடிவுகளும்", "प्रोजेक्ट का कोड और परीक्षण के नतीजे")
s("ui.hosted.landing_note",
  "This is a hosted sample: a pre-recorded walk-through of one invented document. The real app runs only on the owner's own computer, with a local model. It is a class project prototype and not medical advice.",
  "இது ஒரு மாதிரி இணையதளம்: ஒரு கற்பனை ஆவணத்தின் முன்பதிவு செய்த விளக்கப் பயணம். உண்மையான செயலி உரிமையாளரின் சொந்தக் கணினியில், உள்ளூர் மாதிரியுடன் மட்டுமே இயங்குகிறது. இது வகுப்புத் திட்ட முன்மாதிரி; மருத்துவ ஆலோசனை அல்ல.",
  "यह एक होस्ट किया गया नमूना है: एक गढ़े हुए दस्तावेज़ का पहले से रिकॉर्ड किया हुआ walk-through। असली ऐप केवल मालिक के अपने कंप्यूटर पर, स्थानीय मॉडल के साथ चलता है। यह कक्षा-प्रोजेक्ट का प्रोटोटाइप है, चिकित्सकीय सलाह नहीं।")
s("ui.hosted.pp.note",
  "This is the consent notice the real app shows before it processes a document (version {version}). It was copied into this site when the site was built; nothing is requested from a server.",
  "ஆவணத்தைச் செயலாக்கும் முன் உண்மையான செயலி காட்டும் ஒப்புதல் அறிவிப்பு இது (பதிப்பு {version}). இணையதளம் உருவாக்கப்பட்டபோது இதில் நகலெடுக்கப்பட்டது; சேவையகத்திலிருந்து எதுவும் கோரப்படுவதில்லை.",
  "यह वह सहमति-सूचना है जो असली ऐप दस्तावेज़ प्रोसेस करने से पहले दिखाता है (संस्करण {version})। साइट बनाते समय इसे यहाँ कॉपी किया गया; किसी सर्वर से कुछ नहीं माँगा जाता।")
s("ui.hosted.pp.nodelete",
  "This hosted sample stores nothing, so there is nothing to delete here. The real app, running on a person's own computer, has a delete-my-data function.",
  "இந்த மாதிரி இணையதளம் எதையும் சேமிப்பதில்லை, எனவே இங்கே நீக்க எதுவும் இல்லை. ஒருவரின் சொந்தக் கணினியில் இயங்கும் உண்மையான செயலியில் என் தரவை நீக்கும் வசதி உள்ளது.",
  "यह होस्ट किया गया नमूना कुछ भी सहेजता नहीं, इसलिए यहाँ मिटाने को कुछ नहीं है। किसी के अपने कंप्यूटर पर चलने वाले असली ऐप में मेरा डेटा मिटाने की सुविधा है।")
