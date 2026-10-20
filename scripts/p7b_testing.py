"""Phase 7b write-up strings: the held-out test section of "How we tested it". id -> (en, ta, hi). ta/hi are machine drafts (draft_unreviewed).
No number is typed here: every figure is a {placeholder} filled from frontend/src/data/testing.generated.json (scripts/build_testing_page_data.py).
Honest-copy rules as in 6d: none of the words the test forbids, nothing implies a review that did not happen."""
S: dict[str, tuple[str, str, str]] = {}


def s(id: str, en: str, ta: str, hi: str) -> None:
    S[id] = (en, ta, hi)


s("ui.testing.t.intro",
  "These figures come from one run on the final test set. The documents are invented, made by the same generator as the development set. They were never used to tune anything, but they look alike, so this is not the same as real papers. {docs} documents is a small sample: read every figure together with its interval.",
  "இந்த எண்கள் இறுதிச் சோதனைத் தொகுப்பில் நடத்திய ஒரே ஒரு ஓட்டத்திலிருந்து வந்தவை. ஆவணங்கள் கற்பனையானவை; மேம்பாட்டுத் தொகுப்பை உருவாக்கிய அதே உருவாக்கியால் செய்யப்பட்டவை. எதையும் சரிசெய்ய இவை பயன்படுத்தப்படவில்லை, ஆனால் தோற்றத்தில் ஒன்றுபோல் இருப்பதால் இது உண்மையான ஆவணங்களுக்குச் சமமல்ல. {docs} ஆவணங்கள் சிறிய மாதிரி: ஒவ்வொரு எண்ணையும் அதன் இடைவெளியுடன் சேர்த்துப் படியுங்கள்.",
  "ये आँकड़े अंतिम परीक्षण सेट पर चलाए गए एक ही रन से हैं। दस्तावेज़ गढ़े हुए हैं और विकास सेट वाले उसी जनरेटर से बने हैं। इनसे कुछ भी ठीक नहीं किया गया, पर ये दिखने में एक जैसे हैं, इसलिए यह असली कागज़ों जैसा नहीं है। {docs} दस्तावेज़ एक छोटा नमूना है: हर संख्या को उसके अंतराल के साथ पढ़ें।")
s("ui.testing.t.run",
  "One official run on {date}, on one computer, never repeated. {docs} documents were read in {conditions} conditions (typed text, clean image, scan, phone photo, poor photo): {scored} of {runs} readings were scored and {skipped} were skipped.",
  "{date} அன்று ஒரு கணினியில் ஒரே ஒரு அதிகாரப்பூர்வ ஓட்டம்; மீண்டும் நடத்தப்படவில்லை. {docs} ஆவணங்கள் {conditions} நிலைகளில் (தட்டச்சு உரை, தெளிவான படம், ஸ்கேன், கைபேசிப் புகைப்படம், மோசமான புகைப்படம்) படிக்கப்பட்டன: {runs} வாசிப்புகளில் {scored} மதிப்பிடப்பட்டன, {skipped} தவிர்க்கப்பட்டன.",
  "{date} को एक कंप्यूटर पर केवल एक आधिकारिक रन, दोहराया नहीं गया। {docs} दस्तावेज़ {conditions} स्थितियों (टाइप किया पाठ, साफ़ छवि, स्कैन, फ़ोन फ़ोटो, खराब फ़ोटो) में पढ़े गए: {runs} में से {scored} पढ़ाइयाँ आँकी गईं, {skipped} छोड़ी गईं।")
s("ui.testing.t.rundate", "run on {date}", "{date} அன்று இயக்கப்பட்டது", "{date} को चलाया गया")
s("ui.testing.t.dev_heading", "Development-set figures", "மேம்பாட்டுத் தொகுப்பு எண்கள்", "विकास सेट के आँकड़े")
s("ui.testing.t.dev_note",
  "The figures below were measured while we were still building and tuning, so they look better than a fresh test would. They are kept for comparison.",
  "கீழுள்ள எண்கள் நாங்கள் உருவாக்கி சரிசெய்துகொண்டிருந்தபோது அளக்கப்பட்டவை; எனவே புதிய சோதனையை விட நன்றாகத் தெரியும். ஒப்பிடுவதற்காக வைக்கப்பட்டுள்ளன.",
  "नीचे के आँकड़े तब मापे गए जब हम बना और ट्यून कर रहे थे, इसलिए ये नई जाँच से बेहतर दिखते हैं। तुलना के लिए रखे गए हैं।")
s("ui.testing.t.col_test", "Final test result", "இறுதிச் சோதனை முடிவு", "अंतिम परीक्षण का नतीजा")
s("ui.testing.t.col_dev", "Development set", "மேம்பாட்டுத் தொகுப்பு", "विकास सेट")
s("ui.testing.t.ci_wilson", "{level}% interval (Wilson method)", "{level}% இடைவெளி (வில்சன் முறை)", "{level}% अंतराल (विल्सन विधि)")
s("ui.testing.t.ci_boot", "{level}% interval (resampling documents)", "{level}% இடைவெளி (ஆவணங்களை மறுமாதிரி எடுத்து)", "{level}% अंतराल (दस्तावेज़ दोबारा चुनकर)")
s("ui.testing.t.no_dev", "not measured on the development set", "மேம்பாட்டுத் தொகுப்பில் அளக்கப்படவில்லை", "विकास सेट पर नहीं मापा गया")
s("ui.testing.t.outside", "outside the test interval", "சோதனை இடைவெளிக்கு வெளியே", "परीक्षण अंतराल के बाहर")
s("ui.testing.t.diff", "test minus development: {v}", "சோதனை − மேம்பாடு: {v}", "परीक्षण − विकास: {v}")
s("ui.testing.t.pts", "{v} percentage points", "{v} சதவீதப் புள்ளிகள்", "{v} प्रतिशत अंक")
s("ui.testing.t.seconds", "{v} s", "{v} வி", "{v} से.")
s("ui.testing.t.also",
  "Also measured but not listed here: the same figures for each of the {conditions} conditions separately, and the share of made-up values for each field. They are in {doc}, built from {source} and {per_doc}.",
  "இங்கு பட்டியலிடாமல் அளக்கப்பட்டவை: {conditions} நிலைகள் ஒவ்வொன்றிற்கும் தனித்தனியே அதே எண்கள், ஒவ்வொரு புலத்திற்கும் கற்பனை மதிப்புகளின் பங்கு. அவை {doc} கோப்பில் உள்ளன; {source} மற்றும் {per_doc} கோப்புகளிலிருந்து உருவாக்கப்பட்டவை.",
  "यहाँ सूचीबद्ध नहीं पर मापे गए: {conditions} स्थितियों में से हर एक के लिए अलग-अलग वही आँकड़े, और हर फ़ील्ड में गढ़े गए मानों का हिस्सा। वे {doc} में हैं, जो {source} और {per_doc} से बनी है।")

s("ui.testing.t.g.ex_raw", "Reading the document: as the model returned it", "ஆவணத்தைப் படித்தல்: மாதிரி தந்தபடி", "दस्तावेज़ पढ़ना: मॉडल ने जैसा लौटाया")
s("ui.testing.t.g.ex_norm", "Reading the document: after the rules", "ஆவணத்தைப் படித்தல்: விதிகளுக்குப் பிறகு", "दस्तावेज़ पढ़ना: नियमों के बाद")
s("ui.testing.t.g.flags", "Asking you to check, and readiness", "நீங்கள் சரிபார்க்கக் கேட்பது, தயார்நிலை", "आपसे जाँच करवाना, और तैयारी")
s("ui.testing.t.g.safety", "Interaction checks", "இடைவினைச் சோதனைகள்", "इंटरैक्शन जाँच")
s("ui.testing.t.g.expl", "Explanations (clean images)", "விளக்கங்கள் (தெளிவான படங்கள்)", "स्पष्टीकरण (साफ़ छवियाँ)")
s("ui.testing.t.g.ops", "Runs and speed", "ஓட்டங்களும் வேகமும்", "रन और गति")

s("ui.testing.t.d.ex", "{docs} final-test documents read in {conditions} conditions: {mentions} medicines on the answer keys. Invented documents.",
  "{conditions} நிலைகளில் படிக்கப்பட்ட {docs} இறுதிச் சோதனை ஆவணங்கள்: விடைக் குறிப்புகளில் {mentions} மருந்துகள். கற்பனை ஆவணங்கள்.",
  "{conditions} स्थितियों में पढ़े गए {docs} अंतिम परीक्षण दस्तावेज़: उत्तर-कुंजियों में {mentions} दवाएँ। गढ़े हुए दस्तावेज़।")
s("ui.testing.t.d.flags", "{mentions} medicine mentions over {runs} readings (documents times conditions), after the rules, from the model's output only.",
  "{runs} வாசிப்புகளில் (ஆவணங்கள் × நிலைகள்) {mentions} மருந்துக் குறிப்புகள், விதிகளுக்குப் பிறகு, மாதிரியின் வெளியீடு மட்டும்.",
  "{runs} पढ़ाइयों (दस्तावेज़ × स्थितियाँ) में {mentions} दवा-उल्लेख, नियमों के बाद, केवल मॉडल के आउटपुट से।")
s("ui.testing.t.d.safety", "{pairs} medicine-pair checks over {conditions} conditions, using the downloaded interaction data plus the project's own notes.",
  "{conditions} நிலைகளில் {pairs} மருந்து இணைச் சோதனைகள்; பதிவிறக்கிய இடைவினைத் தரவு மற்றும் திட்டத்தின் சொந்தக் குறிப்புகளுடன்.",
  "{conditions} स्थितियों में {pairs} दवा-जोड़ी जाँच, डाउनलोड किए इंटरैक्शन डेटा और प्रोजेक्ट के अपने नोट के साथ।")
s("ui.testing.t.d.expl", "{lines} free-text lines from {docs} final-test documents, clean images, written in English, Tamil and Hindi.",
  "{docs} இறுதிச் சோதனை ஆவணங்களின் {lines} உரைவரிகள், தெளிவான படங்கள், ஆங்கிலம், தமிழ், இந்தியில் எழுதப்பட்டவை.",
  "{docs} अंतिम परीक्षण दस्तावेज़ों की {lines} मुक्त-पाठ पंक्तियाँ, साफ़ छवियाँ, अंग्रेज़ी, तमिल और हिंदी में लिखी गईं।")
s("ui.testing.t.d.ops", "{runs} readings of {docs} final-test documents on one local computer.",
  "ஒரு உள்ளூர்க் கணினியில் {docs} இறுதிச் சோதனை ஆவணங்களின் {runs} வாசிப்புகள்.",
  "एक स्थानीय कंप्यूटर पर {docs} अंतिम परीक्षण दस्तावेज़ों की {runs} पढ़ाइयाँ।")

# row labels (t.f.*) and what they measure (t.m.*)
for key, (lab, mea) in {
    "precision": (("Listed medicines that are real", "பட்டியலிட்ட மருந்துகளில் உண்மையானவை", "सूचीबद्ध दवाओं में असली"),
                  ("Of the medicines the system listed, the share that are on the answer key.", "அமைப்பு பட்டியலிட்ட மருந்துகளில் விடைக் குறிப்பில் இருப்பவற்றின் பங்கு.", "सिस्टम की सूचीबद्ध दवाओं में से जो उत्तर-कुंजी में हैं उनका हिस्सा।")),
    "recall": (("Real medicines found", "கண்டுபிடித்த உண்மை மருந்துகள்", "मिली असली दवाएँ"),
               ("Of the medicines on the answer key, the share the system found.", "விடைக் குறிப்பிலுள்ள மருந்துகளில் அமைப்பு கண்டுபிடித்தவற்றின் பங்கு.", "उत्तर-कुंजी की दवाओं में से जो सिस्टम को मिलीं उनका हिस्सा।")),
    "f1": (("Both of the above together", "மேலே உள்ள இரண்டும் சேர்த்து", "ऊपर के दोनों साथ में"),
           ("F1: one number that is high only when both figures above are high.", "F1: மேலே உள்ள இரு எண்களும் அதிகமாக இருக்கும்போது மட்டும் அதிகமாகும் ஒரே எண்.", "F1: एक संख्या जो तभी ऊँची होती है जब ऊपर की दोनों संख्याएँ ऊँची हों।")),
    "every": (("Medicines with every field right", "எல்லாப் புலங்களும் சரியான மருந்துகள்", "हर फ़ील्ड सही वाली दवाएँ"),
              ("Of the medicines found, the share where every field matches the answer key.", "கண்டுபிடித்த மருந்துகளில் எல்லாப் புலங்களும் விடைக் குறிப்புடன் பொருந்துபவற்றின் பங்கு.", "मिली दवाओं में से जिनके सभी फ़ील्ड उत्तर-कुंजी से मिलते हैं उनका हिस्सा।")),
    "hall": (("Listed medicines that match nothing", "எதனுடனும் பொருந்தாத பட்டியலிட்ட மருந்துகள்", "सूचीबद्ध दवाएँ जो किसी से नहीं मिलतीं"),
             ("A count of medicines the system listed that are not on the answer key.", "விடைக் குறிப்பில் இல்லாத, அமைப்பு பட்டியலிட்ட மருந்துகளின் எண்ணிக்கை.", "सिस्टम की सूचीबद्ध उन दवाओं की गिनती जो उत्तर-कुंजी में नहीं हैं।")),
    "inv": (("Values made up", "கற்பனையாக நிரப்பிய மதிப்புகள்", "गढ़े गए मान"),
            ("Of the fields a document leaves empty, the share the system filled in anyway.", "ஆவணம் காலியாக விட்ட புலங்களில் அமைப்பு எப்படியும் நிரப்பியவற்றின் பங்கு.", "दस्तावेज़ ने जो फ़ील्ड खाली छोड़े उनमें से जिन्हें सिस्टम ने फिर भी भरा उनका हिस्सा।")),
    "field": (("Field right: {field}", "சரியான புலம்: {field}", "सही फ़ील्ड: {field}"),
              ("Of the medicines found, the share where this field matches the answer key.", "கண்டுபிடித்த மருந்துகளில் இந்தப் புலம் விடைக் குறிப்புடன் பொருந்துபவற்றின் பங்கு.", "मिली दवाओं में से जिनमें यह फ़ील्ड उत्तर-कुंजी से मिलता है उनका हिस्सा।")),
    "must": (("Medicines that ask you to confirm", "நீங்கள் உறுதிசெய்யக் கேட்கும் மருந்துகள்", "जो दवाएँ आपसे पुष्टि माँगती हैं"),
             ("The share of medicines shown with a request to check them against the paper.", "தாளுடன் சரிபார்க்கும்படி கோரிக்கையுடன் காட்டப்படும் மருந்துகளின் பங்கு.", "कागज़ से मिलाने के अनुरोध के साथ दिखाई जाने वाली दवाओं का हिस्सा।")),
    "nameerr": (("Wrong medicine names left after the rules", "விதிகளுக்குப் பிறகும் எஞ்சிய தவறான மருந்துப் பெயர்கள்", "नियमों के बाद बचे गलत दवा नाम"),
                ("A count of medicines whose name is still wrong after the rules ran.", "விதிகள் இயங்கிய பிறகும் பெயர் தவறாக உள்ள மருந்துகளின் எண்ணிக்கை.", "उन दवाओं की गिनती जिनका नाम नियमों के बाद भी गलत है।")),
    "nameunfl": (("Wrong names with no request to check", "சரிபார்க்கக் கோரிக்கை இல்லாத தவறான பெயர்கள்", "जाँच के अनुरोध के बिना गलत नाम"),
                 ("Of the wrong names left, how many carry no request to check. This is the riskier kind.", "எஞ்சிய தவறான பெயர்களில் சரிபார்க்கக் கோரிக்கை இல்லாதவை எத்தனை. இது அதிக ஆபத்தான வகை.", "बचे गलत नामों में से कितनों में जाँच का अनुरोध नहीं है। यह ज़्यादा जोखिम वाली किस्म है।")),
    "timeunfl": (("Wrong times of day with no request to check", "சரிபார்க்கக் கோரிக்கை இல்லாத தவறான நேரங்கள்", "जाँच के अनुरोध के बिना गलत समय"),
                 ("Of the wrong times of day left, how many carry no request to check.", "எஞ்சிய தவறான நேரங்களில் சரிபார்க்கக் கோரிக்கை இல்லாதவை எத்தனை.", "बचे गलत समयों में से कितनों में जाँच का अनुरोध नहीं है।")),
    "intready": (("Medicines ready for the interaction check", "இடைவினைச் சோதனைக்குத் தயாரான மருந்துகள்", "इंटरैक्शन जाँच के लिए तैयार दवाएँ"),
                 ("A count of medicines whose identity is firm enough to be checked for interactions.", "இடைவினைக்குச் சோதிக்கும் அளவு அடையாளம் உறுதியான மருந்துகளின் எண்ணிக்கை.", "उन दवाओं की गिनती जिनकी पहचान इंटरैक्शन जाँच के लिए पर्याप्त पक्की है।")),
}.items():
    s("ui.testing.t.f." + key, *lab)
    s("ui.testing.t.m." + key, *mea)

for key, lab, mea in [
    ("schedready", ("Medicines ready for a schedule", "அட்டவணைக்குத் தயாரான மருந்துகள்", "समय-सारणी के लिए तैयार दवाएँ"),
     ("A count of medicines with a daily schedule firm enough to build reminders from.", "நினைவூட்டல்கள் அமைக்கும் அளவு தினசரி அட்டவணை உறுதியான மருந்துகளின் எண்ணிக்கை.", "उन दवाओं की गिनती जिनकी दैनिक समय-सारणी रिमाइंडर बनाने लायक पक्की है।")),
    ("wrongid", ("Wrong identity among those ready for the interaction check", "இடைவினைச் சோதனைக்குத் தயாரானவற்றில் தவறான அடையாளம்", "इंटरैक्शन जाँच के लिए तैयार दवाओं में गलत पहचान"),
     ("Of the medicines ready for the interaction check, how many were given the wrong generic name.", "இடைவினைச் சோதனைக்குத் தயாரான மருந்துகளில் எத்தனைக்குத் தவறான பொதுப் பெயர் தரப்பட்டது.", "इंटरैक्शन जाँच के लिए तैयार दवाओं में से कितनों को गलत जेनेरिक नाम मिला।")),
    ("wrongsched", ("Wrong schedule among those ready for a schedule", "அட்டவணைக்குத் தயாரானவற்றில் தவறான அட்டவணை", "समय-सारणी के लिए तैयार दवाओं में गलत समय-सारणी"),
     ("Of the medicines ready for a schedule, how many had a wrong schedule.", "அட்டவணைக்குத் தயாரான மருந்துகளில் எத்தனைக்குத் தவறான அட்டவணை இருந்தது.", "समय-सारणी के लिए तैयार दवाओं में से कितनों की समय-सारणी गलत थी।")),
    ("strict", ("Known interactions not reported", "தெரிந்த இடைவினைகள் தெரிவிக்கப்படவில்லை", "ज्ञात इंटरैक्शन जो नहीं बताए गए"),
     ("Known interactions that were not reported as found. A strict count: it includes cases where the scoring could not match a garbled name.", "கண்டறியப்பட்டதாகத் தெரிவிக்கப்படாத தெரிந்த இடைவினைகள். கடுமையான எண்ணிக்கை: சிதைந்த பெயரை மதிப்பீடு பொருத்த முடியாத நிகழ்வுகளும் அடங்கும்.", "ज्ञात इंटरैक्शन जो मिले हुए के रूप में नहीं बताए गए। सख़्त गिनती: इसमें वे मामले भी हैं जहाँ मूल्यांकन बिगड़े नाम को नहीं मिला सका।")),
    ("silent", ("Known interactions not reported and not flagged", "தெரிவிக்கப்படாத, குறிக்கப்படாத தெரிந்த இடைவினைகள்", "ज्ञात इंटरैक्शन जो न बताए गए, न चिह्नित"),
     ("The same count, but only where no medicine of the pair carried a request to check.", "அதே எண்ணிக்கை, ஆனால் இணையின் எந்த மருந்திலும் சரிபார்க்கக் கோரிக்கை இல்லாதவை மட்டும்.", "वही गिनती, पर केवल वहाँ जहाँ जोड़ी की किसी दवा में जाँच का अनुरोध नहीं था।")),
    ("false", ("Interactions reported that are not on the answer key", "விடைக் குறிப்பில் இல்லாத, தெரிவிக்கப்பட்ட இடைவினைகள்", "बताए गए इंटरैक्शन जो उत्तर-कुंजी में नहीं हैं"),
     ("A count of reported interactions that are not on the answer key.", "விடைக் குறிப்பில் இல்லாத, தெரிவிக்கப்பட்ட இடைவினைகளின் எண்ணிக்கை.", "बताए गए उन इंटरैक्शन की गिनती जो उत्तर-कुंजी में नहीं हैं।")),
    ("nc", ("Pairs we could not check: {cond}", "சோதிக்க முடியாத இணைகள்: {cond}", "जिन जोड़ियों को जाँच नहीं सके: {cond}"),
     ("The share of medicine pairs reported as could not check rather than as a result. It is high on purpose: when unsure, the app says it could not check.", "முடிவாகத் தெரிவிக்காமல் சோதிக்க முடியவில்லை எனத் தெரிவித்த மருந்து இணைகளின் பங்கு. இது வேண்டுமென்றே அதிகம்: உறுதியில்லாதபோது செயலி சோதிக்க முடியவில்லை என்று சொல்லும்.", "उन दवा-जोड़ियों का हिस्सा जिन्हें नतीजे की जगह जाँच नहीं सके बताया गया। यह जान-बूझकर ऊँचा है: अनिश्चित होने पर ऐप कहता है कि जाँच नहीं सका।")),
    ("ver", ("Lines passed by the software checks: {lang}, {kind}", "மென்பொருள் சோதனைகளைக் கடந்த வரிகள்: {lang}, {kind}", "सॉफ़्टवेयर जाँच पास करने वाली पंक्तियाँ: {lang}, {kind}"),
     ("Model-written lines that passed every software check and the judge, as a share of all lines of that kind. The same model writes and judges. No native speaker has reviewed any text.", "மாதிரி எழுதிய வரிகளில் எல்லா மென்பொருள் சோதனைகளையும் நடுவரையும் கடந்தவை, அந்த வகை எல்லா வரிகளிலும் பங்காக. எழுதுவதும் மதிப்பிடுவதும் ஒரே மாதிரி. தாய்மொழி பேசுபவர் யாரும் எந்த உரையையும் மதிப்பாய்வு செய்யவில்லை.", "मॉडल की लिखी पंक्तियाँ जो हर सॉफ़्टवेयर जाँच और जज को पास कर गईं, उस प्रकार की सभी पंक्तियों के हिस्से के रूप में। वही मॉडल लिखता और जाँचता है। किसी मातृभाषी ने कोई पाठ नहीं जाँचा।")),
    ("shown", ("Lines shown in the chosen language: {lang}", "தேர்ந்த மொழியில் காட்டப்படும் வரிகள்: {lang}", "चुनी भाषा में दिखाई गई पंक्तियाँ: {lang}"),
     ("The share of free-text lines shown in this language rather than as the original English. A fixed phrase library supplies some of them.", "அசல் ஆங்கிலத்திற்குப் பதிலாக இந்த மொழியில் காட்டப்படும் உரைவரிகளின் பங்கு. சில வரிகள் நிலையான சொற்றொடர் நூலகத்திலிருந்து வருகின்றன.", "मूल अंग्रेज़ी की जगह इस भाषा में दिखाई गई मुक्त-पाठ पंक्तियों का हिस्सा। इनमें से कुछ एक तय वाक्यांश-पुस्तकालय से आती हैं।")),
    ("att", ("Document readings attempted", "முயன்ற ஆவண வாசிப்புகள்", "कोशिश की गई दस्तावेज़ पढ़ाइयाँ"),
     ("A count of document readings started (documents times conditions).", "தொடங்கிய ஆவண வாசிப்புகளின் எண்ணிக்கை (ஆவணங்கள் × நிலைகள்).", "शुरू की गई दस्तावेज़ पढ़ाइयों की गिनती (दस्तावेज़ × स्थितियाँ)।")),
    ("sco", ("Readings scored", "மதிப்பிடப்பட்ட வாசிப்புகள்", "आँकी गई पढ़ाइयाँ"),
     ("Of the readings attempted, how many produced a result that was scored.", "முயன்ற வாசிப்புகளில் எத்தனை மதிப்பிடப்பட்ட முடிவைத் தந்தன.", "कोशिश की गई पढ़ाइयों में से कितनों का नतीजा आँका गया।")),
    ("skip", ("Readings skipped", "தவிர்த்த வாசிப்புகள்", "छोड़ी गई पढ़ाइयाँ"),
     ("Of the readings attempted, how many could not be processed.", "முயன்ற வாசிப்புகளில் எத்தனையைச் செயலாக்க முடியவில்லை.", "कोशिश की गई पढ़ाइयों में से कितनी प्रोसेस नहीं हो सकीं।")),
    ("med", ("Time per reading, middle value", "ஒரு வாசிப்புக்கான நேரம், நடு மதிப்பு", "प्रति पढ़ाई समय, बीच का मान"),
     ("The middle time one document reading took on this one computer. Not a promise of speed on other computers.", "இந்த ஒரு கணினியில் ஒரு ஆவண வாசிப்புக்கு ஆன நடு நேரம். மற்ற கணினிகளில் வேகத்திற்கான உறுதி அல்ல.", "इस एक कंप्यूटर पर एक दस्तावेज़ पढ़ाई का बीच का समय। दूसरे कंप्यूटरों पर गति का वादा नहीं।")),
    ("p95", ("Time per reading, upper end", "ஒரு வாசிப்புக்கான நேரம், மேல் முனை", "प्रति पढ़ाई समय, ऊपरी छोर"),
     ("Almost all readings finished within this time (percentile {level}), on this one computer.", "கிட்டத்தட்ட எல்லா வாசிப்புகளும் இந்த நேரத்திற்குள் முடிந்தன (சதமானம் {level}), இந்த ஒரு கணினியில்.", "लगभग सभी पढ़ाइयाँ इस समय के भीतर पूरी हुईं (पर्सेंटाइल {level}), इसी एक कंप्यूटर पर।")),
]:
    s("ui.testing.t.f." + key, *lab)
    s("ui.testing.t.m." + key, *mea)

for k, names in {
    "strength": ("strength", "வீரியம்", "मात्रा-सामर्थ्य"), "form": ("form", "வடிவம்", "रूप"), "dose": ("dose", "அளவு", "खुराक"),
    "times_per_day": ("times a day", "ஒரு நாளில் எத்தனை முறை", "दिन में कितनी बार"), "timing_label": ("time of day", "நாளின் நேரம்", "दिन का समय"),
    "is_prn": ("as-needed flag", "தேவைப்படும்போது குறி", "ज़रूरत पड़ने पर वाला निशान"), "duration_days": ("number of days", "நாட்களின் எண்ணிக்கை", "दिनों की संख्या"),
    "brand_name": ("brand name", "பிராண்ட் பெயர்", "ब्रांड नाम"), "generic_name": ("generic name", "பொதுப் பெயர்", "जेनेरिक नाम"),
}.items():
    s("ui.testing.t.fld." + k, *names)
for k, names in {"en": ("English", "ஆங்கிலம்", "अंग्रेज़ी"), "ta": ("Tamil", "தமிழ்", "तमिल"), "hi": ("Hindi", "இந்தி", "हिंदी")}.items():
    s("ui.testing.t.lang." + k, *names)
for k, names in {
    "all": ("all lines", "எல்லா வரிகள்", "सभी पंक्तियाँ"), "advice": ("advice lines", "ஆலோசனை வரிகள்", "सलाह की पंक्तियाँ"),
    "follow_up": ("follow-up lines", "தொடர் சந்திப்பு வரிகள்", "फ़ॉलो-अप की पंक्तियाँ"), "warning": ("warning lines", "எச்சரிக்கை வரிகள்", "चेतावनी की पंक्तियाँ"),
}.items():
    s("ui.testing.t.kind." + k, *names)
for k, names in {
    "text": ("typed text", "தட்டச்சு உரை", "टाइप किया पाठ"), "clean": ("clean image", "தெளிவான படம்", "साफ़ छवि"), "scan": ("scan", "ஸ்கேன்", "स्कैन"),
    "photo": ("phone photo", "கைபேசிப் புகைப்படம்", "फ़ोन फ़ोटो"), "poor": ("poor photo", "மோசமான புகைப்படம்", "खराब फ़ोटो"),
}.items():
    s("ui.testing.t.cond." + k, *names)

s("ui.testing.limits.l8",
  "The final test documents come from the same generator as the development documents. They were never used for tuning, but they look alike, so they show less than real documents would.",
  "இறுதிச் சோதனை ஆவணங்கள் மேம்பாட்டு ஆவணங்களை உருவாக்கிய அதே உருவாக்கியிலிருந்து வருகின்றன. அவை சரிசெய்ய ஒருபோதும் பயன்படுத்தப்படவில்லை, ஆனால் தோற்றத்தில் ஒன்றுபோல் இருப்பதால் உண்மையான ஆவணங்களை விடக் குறைவாகவே காட்டுகின்றன.",
  "अंतिम परीक्षण के दस्तावेज़ उसी जनरेटर से आते हैं जिससे विकास के दस्तावेज़ बने। इनसे कभी कुछ ट्यून नहीं हुआ, पर ये दिखने में एक जैसे हैं, इसलिए ये असली दस्तावेज़ों से कम दिखाते हैं।")
s("ui.testing.limits.l9",
  "The final test is small: {docs} documents. The intervals are wide, and a difference smaller than an interval should not be read as a difference.",
  "இறுதிச் சோதனை சிறியது: {docs} ஆவணங்கள். இடைவெளிகள் அகலமானவை; இடைவெளியை விடச் சிறிய வேறுபாட்டை வேறுபாடாகப் படிக்கக் கூடாது.",
  "अंतिम परीक्षण छोटा है: {docs} दस्तावेज़। अंतराल चौड़े हैं, और अंतराल से छोटे अंतर को अंतर नहीं पढ़ना चाहिए।")
s("ui.testing.limits.l10",
  "Every result and timing here comes from one run, on one computer, with one local model. Another computer or model may give other numbers.",
  "இங்குள்ள ஒவ்வொரு முடிவும் நேரமும் ஒரு கணினியில், ஒரு உள்ளூர் மாதிரியுடன், ஒரே ஒரு ஓட்டத்திலிருந்து வருகின்றன. வேறு கணினி அல்லது மாதிரி வேறு எண்களைத் தரலாம்.",
  "यहाँ का हर नतीजा और समय एक कंप्यूटर पर, एक स्थानीय मॉडल के साथ, एक ही रन से है। दूसरा कंप्यूटर या मॉडल अलग संख्याएँ दे सकता है।")
