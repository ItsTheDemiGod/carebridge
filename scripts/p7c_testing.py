"""Phase 7c-lite strings: the stress-test section of "How we tested it". id -> (en, ta, hi). ta/hi are machine drafts (draft_unreviewed).
No number is typed here: every figure is a {placeholder} filled from frontend/src/data/testing.generated.json (scripts/build_testing_page_data.py).
Honest-copy rules as before: none of the words the test forbids, nothing implies a review that did not happen."""
S: dict[str, tuple[str, str, str]] = {}


def s(id: str, en: str, ta: str, hi: str) -> None:
    S[id] = (en, ta, hi)


s("ui.testing.split.stress", "stress set (written by the project, never tuned on, separate from the final test)",
  "அழுத்தச் சோதனைத் தொகுப்பு (திட்டக் குழு எழுதியது, இதன் மீது சரிசெய்யப்படவில்லை, இறுதிச் சோதனையிலிருந்து வேறானது)",
  "तनाव-परीक्षण सेट (प्रोजेक्ट ने लिखा, इस पर ट्यून नहीं किया गया, अंतिम परीक्षण से अलग)")
s("ui.testing.s.title", "Stress test of the interaction, schedule and name checks",
  "இடைவினை, அட்டவணை, பெயர் சோதனைகளுக்கான அழுத்தச் சோதனை",
  "इंटरैक्शन, समय-सारणी और नाम की जाँच का तनाव-परीक्षण")
s("ui.testing.s.intro",
  "This is a smaller, harder test. The project wrote {docs} invented prescriptions on purpose to stress the interaction, repeated-medicine, schedule and name checks. They were written without looking at how the system reads them, and nothing was tuned on them. They are not the final test set, and {docs} is a small number, so every interval is wide. Each prescription was drawn twice: as a clean image and as a simulated phone photo.",
  "இது சிறிய, கடினமான சோதனை. இடைவினை, மீண்டும் வரும் மருந்து, அட்டவணை, பெயர் சோதனைகளை நெருக்கடிக்கு உள்ளாக்க திட்டக் குழு வேண்டுமென்றே {docs} கற்பனை மருந்துச்சீட்டுகளை எழுதியது. அமைப்பு அவற்றை எப்படிப் படிக்கும் என்று பார்க்காமல் எழுதப்பட்டவை; எதுவும் அவற்றின் மீது சரிசெய்யப்படவில்லை. இவை இறுதிச் சோதனைத் தொகுப்பு அல்ல; {docs} என்பது சிறிய எண்ணிக்கை, எனவே ஒவ்வொரு இடைவெளியும் அகலமானது. ஒவ்வொரு மருந்துச்சீட்டும் இருமுறை வரையப்பட்டது: தெளிவான படமாகவும், உருவகப்படுத்திய கைபேசிப் புகைப்படமாகவும்.",
  "यह छोटा और कठिन परीक्षण है। इंटरैक्शन, दोहराई गई दवा, समय-सारणी और नाम की जाँच पर दबाव डालने के लिए प्रोजेक्ट ने जान-बूझकर {docs} गढ़े हुए पर्चे लिखे। ये यह देखे बिना लिखे गए कि सिस्टम इन्हें कैसे पढ़ेगा, और इन पर कुछ भी ट्यून नहीं किया गया। ये अंतिम परीक्षण सेट नहीं हैं, और {docs} छोटी संख्या है, इसलिए हर अंतराल चौड़ा है। हर पर्चा दो बार बनाया गया: साफ़ छवि के रूप में और नक़ली फ़ोन-फ़ोटो के रूप में।")
s("ui.testing.s.run",
  "One run on {date}, on one computer: {readings} readings ({docs} prescriptions in {conditions} renders), {failed} failed. A scripted confirmation step, which uses the answer key's names and is for testing only, shows what happens after a person has confirmed the flagged medicines.",
  "{date} அன்று ஒரு கணினியில் ஒரு ஓட்டம்: {readings} வாசிப்புகள் ({conditions} வடிவங்களில் {docs} மருந்துச்சீட்டுகள்), {failed} தோல்வி. எழுதப்பட்ட உறுதிப்படுத்தும் படி (விடைக் குறிப்பின் பெயர்களைப் பயன்படுத்துகிறது; சோதனைக்கு மட்டும்) குறிக்கப்பட்ட மருந்துகளை ஒருவர் உறுதிசெய்த பிறகு என்ன நடக்கும் என்பதைக் காட்டுகிறது.",
  "{date} को एक कंप्यूटर पर एक रन: {readings} पढ़ाइयाँ ({conditions} रूपों में {docs} पर्चे), {failed} विफल। एक स्क्रिप्ट वाला पुष्टि-चरण (उत्तर-कुंजी के नामों का उपयोग करता है; केवल परीक्षण के लिए) दिखाता है कि चिह्नित दवाओं की पुष्टि के बाद क्या होता है।")
s("ui.testing.s.deviation",
  "The local model software was updated between the final test and this run (version {running} now, {pinned} then; the same model file). These figures are not comparable with the final-test figures above.",
  "இறுதிச் சோதனைக்கும் இந்த ஓட்டத்திற்கும் இடையில் உள்ளூர் மாதிரி மென்பொருள் புதுப்பிக்கப்பட்டது (இப்போது பதிப்பு {running}, அப்போது {pinned}; அதே மாதிரிக் கோப்பு). இந்த எண்களை மேலுள்ள இறுதிச் சோதனை எண்களுடன் ஒப்பிட முடியாது.",
  "अंतिम परीक्षण और इस रन के बीच स्थानीय मॉडल सॉफ़्टवेयर अपडेट हुआ (अब संस्करण {running}, तब {pinned}; वही मॉडल फ़ाइल)। इन आँकड़ों की तुलना ऊपर के अंतिम परीक्षण के आँकड़ों से नहीं की जा सकती।")
s("ui.testing.s.d.all",
  "{docs} invented prescriptions, each as a clean image and as a simulated phone photo: {meds} medicines and {pairs} interaction pairs per render, read by the real system.",
  "{docs} கற்பனை மருந்துச்சீட்டுகள், ஒவ்வொன்றும் தெளிவான படமாகவும் உருவகப்படுத்திய கைபேசிப் புகைப்படமாகவும்: ஒரு வடிவத்திற்கு {meds} மருந்துகளும் {pairs} இடைவினை இணைகளும், உண்மையான அமைப்பால் படிக்கப்பட்டவை.",
  "{docs} गढ़े हुए पर्चे, हर एक साफ़ छवि और नक़ली फ़ोन-फ़ोटो के रूप में: प्रति रूप {meds} दवाएँ और {pairs} इंटरैक्शन जोड़ियाँ, असली सिस्टम द्वारा पढ़ी गईं।")
s("ui.testing.s.col_clean", "Clean image", "தெளிவான படம்", "साफ़ छवि")
s("ui.testing.s.col_photo", "Simulated photo", "உருவகப்படுத்திய புகைப்படம்", "नक़ली फ़ोटो")
s("ui.testing.s.limit_zero", "Limit set in advance: none allowed", "முன்கூட்டியே நிர்ணயித்த வரம்பு: ஒன்றும் அனுமதிக்கப்படாது", "पहले से तय सीमा: एक भी नहीं")
s("ui.testing.s.limit_all", "Limit set in advance: every pair", "முன்கூட்டியே நிர்ணயித்த வரம்பு: ஒவ்வொரு இணையும்", "पहले से तय सीमा: हर जोड़ी")
s("ui.testing.s.met", "Met, both renders together", "இரு வடிவங்களிலும் சேர்த்து நிறைவேறியது", "दोनों रूप मिलाकर पूरा हुआ")
s("ui.testing.s.notmet", "Not met", "நிறைவேறவில்லை", "पूरा नहीं हुआ")
s("ui.testing.s.also",
  "Not listed here: the same figures for each of the ten kinds of prescription, and which flag held back each pair. They are in {doc}, built from {source} and {per_doc}. Passing these limits on a small set of invented prescriptions says nothing about how often they hold for real documents.",
  "இங்கு பட்டியலிடப்படாதவை: பத்து வகை மருந்துச்சீட்டுகள் ஒவ்வொன்றிற்கும் அதே எண்கள், மற்றும் ஒவ்வொரு இணையையும் எந்தக் குறி நிறுத்தியது என்பது. அவை {doc} இல் உள்ளன; {source} மற்றும் {per_doc} இலிருந்து உருவாக்கப்பட்டவை. சிறிய கற்பனை மருந்துச்சீட்டுத் தொகுப்பில் இந்த வரம்புகளை எட்டியது, உண்மையான ஆவணங்களில் எவ்வளவு அடிக்கடி நிகழும் என்பதைப் பற்றி எதுவும் சொல்லாது.",
  "यहाँ सूचीबद्ध नहीं: दस प्रकार के पर्चों में से हर एक के लिए वही आँकड़े, और किस चिह्न ने कौन-सी जोड़ी रोकी। वे {doc} में हैं, {source} और {per_doc} से बने। गढ़े हुए पर्चों के छोटे सेट पर इन सीमाओं का पूरा होना यह नहीं बताता कि असली दस्तावेज़ों पर ये कितनी बार पूरी होंगी।")

for k, (en, ta, hi) in {
    "crit": ("The four limits set in advance", "முன்கூட்டியே நிர்ணயித்த நான்கு வரம்புகள்", "पहले से तय चार सीमाएँ"),
    "detect_raw": ("Finding the medicines: as the model returned them", "மருந்துகளைக் கண்டறிதல்: மாதிரி தந்தபடி", "दवाएँ ढूँढना: मॉडल ने जैसा लौटाया"),
    "detect_norm": ("Finding the medicines: after the rules", "மருந்துகளைக் கண்டறிதல்: விதிகளுக்குப் பிறகு", "दवाएँ ढूँढना: नियमों के बाद"),
    "review": ("Asking you to check", "நீங்கள் சரிபார்க்கக் கேட்பது", "आपसे जाँच करने को कहना"),
    "inter": ("Interaction pairs", "இடைவினை இணைகள்", "इंटरैक्शन जोड़ियाँ"),
    "checks": ("Repeated medicines, weekly doses, eye drops, strengths and names", "மீண்டும் வரும் மருந்துகள், வாராந்திர அளவுகள், கண் சொட்டுகள், வலிமைகள், பெயர்கள்", "दोहराई दवाएँ, साप्ताहिक खुराक, आँख की बूँदें, मात्राएँ और नाम"),
    "overlay": ("After a scripted confirmation", "எழுதப்பட்ட உறுதிப்படுத்தலுக்குப் பிறகு", "स्क्रिप्ट वाली पुष्टि के बाद"),
    "ops": ("Runs", "ஓட்டங்கள்", "रन"),
}.items():
    s("ui.testing.s.g." + k, en, ta, hi)

for k, (en, ta, hi) in {
    "major": ("level major", "நிலை: முக்கியமானது", "स्तर: गंभीर"),
    "moderate": ("level moderate", "நிலை: மிதமானது", "स्तर: मध्यम"),
    "minor": ("level minor", "நிலை: சிறியது", "स्तर: हल्का"),
    "unknown": ("level not stated", "நிலை: குறிப்பிடப்படவில்லை", "स्तर: उल्लेख नहीं"),
}.items():
    s("ui.testing.s.lvl." + k, en, ta, hi)

ROWS = {
    # criteria
    "p1": (("First limit: pairs neither shown nor held back with a request to check", "முதல் வரம்பு: காட்டப்படாத, சரிபார்க்கக் கோரிக்கையுடன் நிறுத்தப்படாத இணைகள்", "पहली सीमा: जो जोड़ियाँ न दिखीं, न जाँच के अनुरोध के साथ रोकी गईं"),
           ("Of the interaction pairs the check finds when names are read perfectly, how many were neither shown nor held back with a request to confirm. The limit was none.",
            "பெயர்கள் சரியாகப் படிக்கப்பட்டால் சோதனை கண்டறியும் இடைவினை இணைகளில், எத்தனை காட்டப்படவும் இல்லை, உறுதிசெய்யக் கோரிக்கையுடன் நிறுத்தப்படவும் இல்லை. வரம்பு: ஒன்றும் இல்லை.",
            "नाम सही पढ़े जाने पर जाँच जो इंटरैक्शन जोड़ियाँ पाती है, उनमें से कितनी न दिखीं और न पुष्टि के अनुरोध के साथ रोकी गईं। सीमा: एक भी नहीं।")),
    "p2": (("Second limit: weekly medicines given a daily schedule", "இரண்டாம் வரம்பு: தினசரி அட்டவணை தரப்பட்ட வாராந்திர மருந்துகள்", "दूसरी सीमा: साप्ताहिक दवाएँ जिन्हें रोज़ की समय-सारणी मिली"),
           ("Of the medicines taken less often than daily, how many were set up with a daily reminder. The limit was none.",
            "தினமும் அல்லாமல் குறைவாக எடுக்கும் மருந்துகளில், எத்தனைக்கு தினசரி நினைவூட்டல் அமைக்கப்பட்டது. வரம்பு: ஒன்றும் இல்லை.",
            "रोज़ से कम बार ली जाने वाली दवाओं में से कितनों के लिए रोज़ का रिमाइंडर बना। सीमा: एक भी नहीं।")),
    "p3": (("Third limit: wrong drug identity among medicines ready for the check", "மூன்றாம் வரம்பு: சோதனைக்குத் தயாரான மருந்துகளில் தவறான மருந்து அடையாளம்", "तीसरी सीमा: जाँच के लिए तैयार दवाओं में ग़लत दवा-पहचान"),
           ("Of the medicines marked ready for the interaction check, how many had the wrong generic name. The limit was none.",
            "இடைவினைச் சோதனைக்குத் தயார் எனக் குறிக்கப்பட்ட மருந்துகளில், எத்தனைக்கு தவறான பொதுப் பெயர் இருந்தது. வரம்பு: ஒன்றும் இல்லை.",
            "इंटरैक्शन जाँच के लिए तैयार चिह्नित दवाओं में से कितनों का जेनेरिक नाम ग़लत था। सीमा: एक भी नहीं।")),
    "p4": (("Fourth limit: pairs shown at the right level after confirmation", "நான்காம் வரம்பு: உறுதிப்படுத்தலுக்குப் பிறகு சரியான நிலையில் காட்டப்பட்ட இணைகள்", "चौथी सीमा: पुष्टि के बाद सही स्तर पर दिखी जोड़ियाँ"),
           ("After the scripted confirmation step, of the pairs the check finds with perfect names between medicines that were read, how many were shown at the right level. The limit was every pair.",
            "எழுதப்பட்ட உறுதிப்படுத்தும் படிக்குப் பிறகு, படிக்கப்பட்ட மருந்துகளுக்கிடையே பெயர்கள் சரியாக இருந்தால் சோதனை கண்டறியும் இணைகளில், எத்தனை சரியான நிலையில் காட்டப்பட்டன. வரம்பு: ஒவ்வொரு இணையும்.",
            "स्क्रिप्ट वाले पुष्टि-चरण के बाद, पढ़ी गई दवाओं के बीच सही नामों पर जाँच जो जोड़ियाँ पाती है, उनमें से कितनी सही स्तर पर दिखीं। सीमा: हर जोड़ी।")),
    # review load
    "review_must_confirm": (("Medicines that ask you to confirm", "நீங்கள் உறுதிசெய்யக் கேட்கும் மருந்துகள்", "जो दवाएँ आपसे पुष्टि माँगती हैं"),
                            ("The share of medicines shown with a request to check them against the paper.", "தாளுடன் சரிபார்க்கும்படி கோரிக்கையுடன் காட்டப்படும் மருந்துகளின் பங்கு.", "उन दवाओं का हिस्सा जो काग़ज़ से मिलान की माँग के साथ दिखाई गईं।")),
    "review_note": (("Medicines with a note only", "குறிப்பு மட்டுமுள்ள மருந்துகள்", "सिर्फ़ टिप्पणी वाली दवाएँ"),
                    ("The share of medicines shown with a note but no request to confirm.", "குறிப்புடன் ஆனால் உறுதிசெய்யக் கோரிக்கை இல்லாமல் காட்டப்படும் மருந்துகளின் பங்கு.", "उन दवाओं का हिस्सा जो टिप्पणी के साथ पर पुष्टि के अनुरोध के बिना दिखीं।")),
    "review_none": (("Medicines with nothing to check", "சரிபார்க்க எதுவும் இல்லாத மருந்துகள்", "जिन दवाओं में जाँचने को कुछ नहीं"),
                    ("The share of medicines shown with neither a note nor a request to confirm.", "குறிப்பும் உறுதிசெய்யக் கோரிக்கையும் இல்லாமல் காட்டப்படும் மருந்துகளின் பங்கு.", "उन दवाओं का हिस्सा जो न टिप्पणी और न पुष्टि के अनुरोध के साथ दिखीं।")),
    # interaction pairs
    "gt_level": (("Pairs the check finds with perfect names: {level}", "பெயர்கள் சரியாக இருந்தால் சோதனை கண்டறியும் இணைகள்: {level}", "सही नामों पर जाँच जो जोड़ियाँ पाती है: {level}"),
                 ("Of all pairs the check finds when names are read perfectly, how many have this level in the downloaded interaction data.", "பெயர்கள் சரியாகப் படிக்கப்பட்டால் சோதனை கண்டறியும் எல்லா இணைகளில், பதிவிறக்கிய இடைவினைத் தரவில் இந்த நிலை கொண்டவை எத்தனை.", "नाम सही पढ़े जाने पर जाँच जो सभी जोड़ियाँ पाती है, उनमें से कितनी का डाउनलोड किए इंटरैक्शन डेटा में यह स्तर है।")),
    "found": (("Pairs shown straight away from the real reading", "உண்மையான வாசிப்பிலிருந்து உடனே காட்டப்பட்ட இணைகள்", "असली पढ़ाई से तुरंत दिखीं जोड़ियाँ"),
              ("Of the pairs found with perfect names, how many were shown straight away, before any confirmation.", "பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில், எந்த உறுதிப்படுத்தலுக்கும் முன்பே உடனே காட்டப்பட்டவை எத்தனை.", "सही नामों पर मिलने वाली जोड़ियों में से कितनी किसी पुष्टि से पहले ही तुरंत दिखीं।")),
    "found_right": (("Of those, shown at the right level", "அவற்றில், சரியான நிலையில் காட்டப்பட்டவை", "इनमें से सही स्तर पर दिखीं"),
                    ("Of the pairs found with perfect names, how many were shown straight away at the same level.", "பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில், அதே நிலையில் உடனே காட்டப்பட்டவை எத்தனை.", "सही नामों पर मिलने वाली जोड़ियों में से कितनी उसी स्तर पर तुरंत दिखीं।")),
    "fd_level": (("Pairs shown straight away: {level}", "உடனே காட்டப்பட்ட இணைகள்: {level}", "तुरंत दिखीं जोड़ियाँ: {level}"),
                 ("Of the pairs found with perfect names, how many were shown straight away at this level.", "பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில், இந்த நிலையில் உடனே காட்டப்பட்டவை எத்தனை.", "सही नामों पर मिलने वाली जोड़ियों में से कितनी इस स्तर पर तुरंत दिखीं।")),
    "strict": (("Pairs not shown straight away", "உடனே காட்டப்படாத இணைகள்", "जो जोड़ियाँ तुरंत नहीं दिखीं"),
               ("Of the pairs found with perfect names, how many were not shown straight away for any reason (held back with a request to confirm, or lost).", "பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில், எந்தக் காரணத்தாலும் உடனே காட்டப்படாதவை (உறுதிசெய்யக் கோரிக்கையுடன் நிறுத்தப்பட்டவை அல்லது இழந்தவை).", "सही नामों पर मिलने वाली जोड़ियों में से कितनी किसी भी कारण से तुरंत नहीं दिखीं (पुष्टि के अनुरोध के साथ रोकी गईं, या खो गईं)।")),
    "unconf": (("Pairs held back until names are confirmed", "பெயர்கள் உறுதிசெய்யப்படும் வரை நிறுத்தப்பட்ட இணைகள்", "नाम की पुष्टि होने तक रोकी गई जोड़ियाँ"),
               ("Of the pairs found with perfect names, how many were held back with a request to confirm a medicine first. These were reported as not checked.", "பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில், முதலில் ஒரு மருந்தை உறுதிசெய்யக் கோரிக்கையுடன் நிறுத்தப்பட்டவை எத்தனை. இவை 'சோதிக்கப்படவில்லை' என அறிவிக்கப்பட்டன.", "सही नामों पर मिलने वाली जोड़ियों में से कितनी पहले किसी दवा की पुष्टि के अनुरोध के साथ रोकी गईं। इन्हें 'जाँची नहीं गई' बताया गया।")),
    "other": (("Pairs lost for another reason", "வேறு காரணத்தால் இழந்த இணைகள்", "किसी और कारण से खोई जोड़ियाँ"),
              ("Of the pairs found with perfect names, how many were lost without a request to confirm, for example because a medicine was not read at all.", "பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில், உறுதிசெய்யக் கோரிக்கை இல்லாமல் இழந்தவை எத்தனை, எ.கா. ஒரு மருந்து படிக்கப்படாததால்.", "सही नामों पर मिलने वाली जोड़ियों में से कितनी पुष्टि के अनुरोध के बिना खो गईं, जैसे किसी दवा के बिल्कुल न पढ़े जाने से।")),
    "false": (("Pairs shown that the answer key does not have", "விடைக் குறிப்பில் இல்லாமல் காட்டப்பட்ட இணைகள்", "जो जोड़ियाँ दिखीं पर उत्तर-कुंजी में नहीं हैं"),
              ("Of the pairs shown straight away, how many are not among the pairs found with perfect names.", "உடனே காட்டப்பட்ட இணைகளில், பெயர்கள் சரியாக இருந்தால் கண்டறியப்படும் இணைகளில் இல்லாதவை எத்தனை.", "तुरंत दिखीं जोड़ियों में से कितनी सही नामों पर मिलने वाली जोड़ियों में नहीं हैं।")),
    # category checks
    "dup": (("Repeated medicines that raised a double-dose notice", "இரட்டை அளவு அறிவிப்பை எழுப்பிய மீண்டும் வந்த மருந்துகள்", "दोहराई दवाएँ जिन पर दोहरी-खुराक की सूचना आई"),
            ("Of the medicines written twice on one prescription, how many produced the 'possible double dose' notice.", "ஒரே மருந்துச்சீட்டில் இருமுறை எழுதப்பட்ட மருந்துகளில், எத்தனை 'இரட்டை அளவு இருக்கலாம்' அறிவிப்பை உருவாக்கின.", "एक पर्चे पर दो बार लिखी दवाओं में से कितनों ने 'संभावित दोहरी खुराक' की सूचना दी।")),
    "nondaily": (("Weekly or non-daily medicines that were flagged", "குறிக்கப்பட்ட வாராந்திர அல்லது தினசரி அல்லாத மருந்துகள்", "चिह्नित साप्ताहिक या रोज़ न ली जाने वाली दवाएँ"),
                 ("Of the medicines taken less often than daily that were read, how many carried the flag saying so.", "படிக்கப்பட்ட, தினமும் அல்லாமல் எடுக்கும் மருந்துகளில், எத்தனைக்கு அதைச் சொல்லும் குறி இருந்தது.", "पढ़ी गई, रोज़ से कम ली जाने वाली दवाओं में से कितनों पर यह बताने वाला चिह्न था।")),
    "eye_od": (("Eye drops with an unclear 'OD' that were flagged", "தெளிவற்ற 'OD' உள்ள குறிக்கப்பட்ட கண் சொட்டுகள்", "अस्पष्ट 'OD' वाली चिह्नित आँख की बूँदें"),
               ("Of the eye drops written with 'OD' (which can mean once daily or right eye), how many were flagged as unclear.", "'OD' (தினமொருமுறை அல்லது வலது கண் என்று பொருள்படலாம்) என எழுதப்பட்ட கண் சொட்டுகளில், எத்தனை தெளிவற்றவை எனக் குறிக்கப்பட்டன.", "'OD' (जिसका मतलब रोज़ एक बार या दाईं आँख हो सकता है) लिखी आँख की बूँदों में से कितनी अस्पष्ट के रूप में चिह्नित हुईं।")),
    "eye_sched": (("Those eye drops given a daily schedule", "அந்தக் கண் சொட்டுகளில் தினசரி அட்டவணை தரப்பட்டவை", "इन आँख की बूँदों में से जिन्हें रोज़ की समय-सारणी मिली"),
                  ("Of the same eye drops, how many were set up with a daily reminder.", "அதே கண் சொட்டுகளில், எத்தனைக்கு தினசரி நினைவூட்டல் அமைக்கப்பட்டது.", "इन्हीं आँख की बूँदों में से कितनों के लिए रोज़ का रिमाइंडर बना।")),
    "unusual": (("Prescriptions with an unusual strength that were flagged", "அசாதாரண வலிமை உள்ள குறிக்கப்பட்ட மருந்துச்சீட்டுகள்", "असामान्य मात्रा वाले चिह्नित पर्चे"),
                ("Of the prescriptions written with an unusual strength, how many carried the unusual-strength flag.", "அசாதாரண வலிமையுடன் எழுதப்பட்ட மருந்துச்சீட்டுகளில், எத்தனைக்கு அசாதாரண வலிமைக் குறி இருந்தது.", "असामान्य मात्रा के साथ लिखे पर्चों में से कितनों पर असामान्य-मात्रा का चिह्न था।")),
    "garbled": (("Garbled medicine names that were flagged", "குறிக்கப்பட்ட சிதைந்த மருந்துப் பெயர்கள்", "चिह्नित बिगड़े दवा-नाम"),
                ("Of the medicines whose name was misspelt on purpose and that were read, how many carried a name flag. A name the model quietly corrected shows here as not flagged.", "வேண்டுமென்றே தவறாக எழுதப்பட்ட பெயர் கொண்ட, படிக்கப்பட்ட மருந்துகளில், எத்தனைக்கு பெயர்க் குறி இருந்தது. மாதிரி அமைதியாகத் திருத்திய பெயர் இங்கே குறிக்கப்படாததாகத் தெரியும்.", "जानबूझकर ग़लत लिखे नाम वाली, पढ़ी गई दवाओं में से कितनों पर नाम का चिह्न था। मॉडल ने जिस नाम को चुपचाप सुधार दिया, वह यहाँ बिना चिह्न के दिखता है।")),
    "garbled_ready": (("Garbled names marked ready for the interaction check", "இடைவினைச் சோதனைக்குத் தயார் எனக் குறிக்கப்பட்ட சிதைந்த பெயர்கள்", "इंटरैक्शन जाँच के लिए तैयार चिह्नित बिगड़े नाम"),
                      ("Of the same garbled-name medicines, how many were treated as firmly identified and checked without asking.", "அதே சிதைந்த-பெயர் மருந்துகளில், எத்தனை உறுதியாக அடையாளம் காணப்பட்டதாகக் கருதப்பட்டு கேட்காமல் சோதிக்கப்பட்டன.", "इन्हीं बिगड़े-नाम वाली दवाओं में से कितनों को पक्की पहचान मानकर बिना पूछे जाँचा गया।")),
    # scripted confirmation
    "ov_equal": (("Prescriptions where the confirmed result equals the perfect-names result", "உறுதிப்படுத்திய முடிவு, சரியான பெயர்கள் முடிவுக்குச் சமமான மருந்துச்சீட்டுகள்", "पर्चे जहाँ पुष्टि के बाद का नतीजा सही-नामों के नतीजे के बराबर है"),
                 ("After the scripted confirmation step, on how many prescriptions the pairs shown equal the pairs found with perfect names for the medicines that were read.", "எழுதப்பட்ட உறுதிப்படுத்தும் படிக்குப் பிறகு, படிக்கப்பட்ட மருந்துகளுக்கு காட்டப்படும் இணைகள் சரியான பெயர்களில் கண்டறியும் இணைகளுக்குச் சமமாக இருந்த மருந்துச்சீட்டுகள் எத்தனை.", "स्क्रिप्ट वाले पुष्टि-चरण के बाद, कितने पर्चों पर दिखीं जोड़ियाँ पढ़ी गई दवाओं के लिए सही नामों पर मिलने वाली जोड़ियों के बराबर हैं।")),
    "ov_newly": (("Held-back pairs shown after confirmation", "உறுதிப்படுத்தலுக்குப் பிறகு காட்டப்பட்ட நிறுத்தப்பட்ட இணைகள்", "पुष्टि के बाद दिखीं रोकी गई जोड़ियाँ"),
                 ("Of the pairs held back until names were confirmed, how many were shown after the scripted confirmation.", "பெயர்கள் உறுதிசெய்யப்படும் வரை நிறுத்தப்பட்ட இணைகளில், எழுதப்பட்ட உறுதிப்படுத்தலுக்குப் பிறகு எத்தனை காட்டப்பட்டன.", "नाम की पुष्टि तक रोकी गई जोड़ियों में से कितनी स्क्रिप्ट वाली पुष्टि के बाद दिखीं।")),
    "ov_false": (("Pairs shown after confirmation that the answer key does not have", "உறுதிப்படுத்தலுக்குப் பிறகு விடைக் குறிப்பில் இல்லாமல் காட்டப்பட்ட இணைகள்", "पुष्टि के बाद दिखीं जोड़ियाँ जो उत्तर-कुंजी में नहीं हैं"),
                 ("Of the pairs shown after the scripted confirmation, how many are not among the pairs found with perfect names. A name the model quietly corrected can cause this.", "எழுதப்பட்ட உறுதிப்படுத்தலுக்குப் பிறகு காட்டப்பட்ட இணைகளில், சரியான பெயர்களில் கண்டறியும் இணைகளில் இல்லாதவை எத்தனை. மாதிரி அமைதியாகத் திருத்திய பெயர் இதற்குக் காரணமாகலாம்.", "स्क्रिप्ट वाली पुष्टि के बाद दिखीं जोड़ियों में से कितनी सही नामों पर मिलने वाली जोड़ियों में नहीं हैं। मॉडल द्वारा चुपचाप सुधारा गया नाम इसका कारण हो सकता है।")),
    # runs
    "failed": (("Readings that failed", "தோல்வியடைந்த வாசிப்புகள்", "विफल पढ़ाइयाँ"),
               ("Of the readings made in this render, how many failed to produce a result.", "இந்த வடிவத்தில் செய்த வாசிப்புகளில், எத்தனை முடிவைத் தரத் தவறின.", "इस रूप में की गई पढ़ाइयों में से कितनी नतीजा देने में विफल रहीं।")),
}
for key, (lab, mea) in ROWS.items():
    s("ui.testing.s.f." + key, *lab)
    s("ui.testing.s.m." + key, *mea)
# precision, recall, f1, hall reuse the held-out section's row texts (ui.testing.t.f.* / t.m.*): the stress rows point at them by id in the generated file

import p7b_testing as _P7B  # noqa: E402  (same row wording as the held-out section for the four detection rows)

for _k in ("precision", "recall", "f1", "hall"):
    s("ui.testing.s.f." + _k, *_P7B.S["ui.testing.t.f." + _k])
    s("ui.testing.s.m." + _k, *_P7B.S["ui.testing.t.m." + _k])
