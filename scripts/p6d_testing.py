"""Phase 6d strings: the "How we tested it" page (/how-we-tested-it). id -> (en, ta, hi). ta/hi are machine drafts (draft_unreviewed).
No number is typed here: every figure and count is a {placeholder} filled from frontend/src/data/testing.generated.json (scripts/build_testing_page_data.py).
Honest-copy rules: none of the words the test forbids (accuracy, safe, validated ...), nothing implies a review that did not happen."""
S: dict[str, tuple[str, str, str]] = {}


def s(id: str, en: str, ta: str, hi: str) -> None:
    S[id] = (en, ta, hi)


s("ui.title.testing", "How we tested it · CareBridge", "நாங்கள் எப்படிச் சோதித்தோம் · CareBridge", "हमने इसे कैसे परखा · CareBridge")
s("ui.nav.testing", "Testing", "சோதனை", "परीक्षण")
s("ui.testing.page.lede",
  "Here is what we measured, on what, and what the numbers do not tell you. Everything on this page was measured on made-up documents.",
  "நாங்கள் எதை அளந்தோம், எதன் மீது அளந்தோம், இந்த எண்கள் எதைச் சொல்லாது என்பது இங்கே. இந்தப் பக்கத்திலுள்ள அனைத்தும் கற்பனை ஆவணங்களின் மீது அளக்கப்பட்டவை.",
  "हमने क्या मापा, किस पर मापा और ये संख्याएँ क्या नहीं बतातीं, यह यहाँ है। इस पेज की हर चीज़ गढ़े हुए दस्तावेज़ों पर मापी गई है।")
s("ui.testing.method.title", "How we test", "நாங்கள் எப்படிச் சோதிக்கிறோம்", "हम कैसे परखते हैं")
s("ui.testing.method.dev",
  "A development set is a group of documents we may look at while we build. We used it to tune the rules and the prompts, so results on it look better than they would on documents we had never seen.",
  "மேம்பாட்டுத் தொகுப்பு என்பது நாங்கள் உருவாக்கும்போது பார்க்க அனுமதிக்கப்பட்ட ஆவணங்களின் குழு. விதிகளையும் தூண்டுதல்களையும் சரிசெய்ய அதைப் பயன்படுத்தினோம்; எனவே அதன் முடிவுகள், நாங்கள் பார்த்திராத ஆவணங்களில் வருவதை விட நன்றாகத் தெரியும்.",
  "विकास सेट दस्तावेज़ों का वह समूह है जिसे हम बनाते समय देख सकते हैं। हमने इसी पर नियम और प्रॉम्प्ट ठीक किए, इसलिए इसके नतीजे उन दस्तावेज़ों से बेहतर दिखते हैं जिन्हें हमने पहले कभी नहीं देखा।")
s("ui.testing.method.test",
  "A final test set is a separate group we kept untouched until the end. We ran it once, so its results could not be tuned. Its results are at the top of this page.",
  "இறுதிச் சோதனைத் தொகுப்பு என்பது இறுதிவரை தொடாமல் வைத்திருந்த தனிக் குழு. அதை ஒரு முறை மட்டுமே இயக்கினோம்; எனவே அதன் முடிவுகளைச் சரிசெய்ய முடியவில்லை. அதன் முடிவுகள் இந்தப் பக்கத்தின் மேலே உள்ளன.",
  "अंतिम परीक्षण सेट एक अलग समूह है जिसे हमने अंत तक छुए बिना रखा। इसे केवल एक बार चलाया, इसलिए इसके नतीजों को ट्यून नहीं किया जा सका। इसके नतीजे इस पेज के ऊपर हैं।")
s("ui.testing.method.synthetic",
  "Every document is synthetic: invented patients and invented medicine lists, generated and turned into images. We never use real patients' papers for testing. That keeps people's data out of the project, but real documents may behave differently.",
  "ஒவ்வொரு ஆவணமும் செயற்கையானது: கற்பனை நோயாளிகள், கற்பனை மருந்துப் பட்டியல்கள்; உருவாக்கிப் படங்களாக மாற்றப்பட்டவை. சோதனைக்கு உண்மையான நோயாளிகளின் ஆவணங்களை ஒருபோதும் பயன்படுத்துவதில்லை. இது மக்களின் தரவைத் திட்டத்திலிருந்து விலக்கி வைக்கிறது; ஆனால் உண்மையான ஆவணங்கள் வேறுவிதமாக நடந்துகொள்ளலாம்.",
  "हर दस्तावेज़ कृत्रिम है: गढ़े हुए मरीज़ और गढ़ी हुई दवा-सूचियाँ, जिन्हें बनाकर तस्वीरों में बदला गया। परीक्षण के लिए हम असली मरीज़ों के कागज़ कभी इस्तेमाल नहीं करते। इससे लोगों का डेटा प्रोजेक्ट से बाहर रहता है, पर असली दस्तावेज़ अलग व्यवहार कर सकते हैं।")
s("ui.testing.table.caption",
  "Figures measured so far. Each row says what was measured, on which data, and which file the number comes from.",
  "இதுவரை அளந்த எண்கள். ஒவ்வொரு வரிசையும் எதை அளந்தோம், எந்தத் தரவில், எந்தக் கோப்பிலிருந்து எண் வந்தது என்பதைச் சொல்கிறது.",
  "अब तक मापी गई संख्याएँ। हर पंक्ति बताती है कि क्या मापा गया, किस डेटा पर, और संख्या किस फ़ाइल से आई।")
s("ui.testing.col.measure", "Measure", "அளவீடு", "माप")
s("ui.testing.col.result", "Result", "முடிவு", "नतीजा")
s("ui.testing.col.data", "Data", "தரவு", "डेटा")
s("ui.testing.col.measures", "What this measures", "இது எதை அளக்கிறது", "यह क्या मापता है")
s("ui.testing.col.source", "Source file", "மூலக் கோப்பு", "स्रोत फ़ाइल")
s("ui.testing.caveat_label", "Caveat:", "குறிப்பு:", "सावधानी:")
s("ui.testing.split.dev", "Development set", "மேம்பாட்டுத் தொகுப்பு", "विकास सेट")
s("ui.testing.split.test", "Final test set", "இறுதிச் சோதனைத் தொகுப்பு", "अंतिम परीक्षण सेट")
s("ui.testing.date", "source file committed {date}", "மூலக் கோப்பு சேர்க்கப்பட்ட நாள் {date}", "स्रोत फ़ाइल जोड़ी गई {date}")
s("ui.testing.k_of_n", "{n} of {of}", "{of} இல் {n}", "{of} में से {n}")
s("ui.testing.g.extraction", "Reading the document", "ஆவணத்தைப் படித்தல்", "दस्तावेज़ पढ़ना")
s("ui.testing.g.invented", "Made-up values", "கற்பனையாக நிரப்பிய மதிப்புகள்", "गढ़े हुए मान")
s("ui.testing.g.flags", "Asking you to check", "உங்களைச் சரிபார்க்கச் சொல்லுதல்", "आपसे जाँच करवाना")
s("ui.testing.g.verification", "Checking the explanations", "விளக்கங்களைச் சரிபார்த்தல்", "व्याख्याओं की जाँच")
s("ui.testing.g.language", "Languages", "மொழிகள்", "भाषाएँ")
s("ui.testing.g.safety", "Interaction checks", "இடைவினைச் சோதனைகள்", "इंटरैक्शन जाँच")
s("ui.testing.g.live", "The whole flow", "முழுப் பயணம்", "पूरा प्रवाह")

# figure labels
s("ui.testing.f.ex_f1_raw", "Medicines found and not wrongly added, as the model returned them", "கண்டறிந்த, தவறாகச் சேர்க்கப்படாத மருந்துகள், மாடல் தந்தபடி", "मिली और ग़लती से न जोड़ी गई दवाएँ, मॉडल के लौटाए अनुसार")
s("ui.testing.f.ex_f1_norm", "Medicines found and not wrongly added, after the rules", "கண்டறிந்த, தவறாகச் சேர்க்கப்படாத மருந்துகள், விதிகளுக்குப் பிறகு", "मिली और ग़लती से न जोड़ी गई दवाएँ, नियमों के बाद")
s("ui.testing.f.ex_every_raw", "Medicines with every field right, as returned", "எல்லா புலங்களும் சரியான மருந்துகள், மாடல் தந்தபடி", "हर फ़ील्ड सही वाली दवाएँ, लौटाए अनुसार")
s("ui.testing.f.ex_every_norm", "Medicines with every field right, after the rules", "எல்லா புலங்களும் சரியான மருந்துகள், விதிகளுக்குப் பிறகு", "हर फ़ील्ड सही वाली दवाएँ, नियमों के बाद")
s("ui.testing.f.inv_raw", "Values made up where the document gives none, as returned", "ஆவணம் தராத இடத்தில் நிரப்பிய மதிப்புகள், மாடல் தந்தபடி", "जहाँ दस्तावेज़ में कुछ नहीं, वहाँ गढ़े मान, लौटाए अनुसार")
s("ui.testing.f.inv_norm", "Values made up where the document gives none, after the rules", "ஆவணம் தராத இடத்தில் நிரப்பிய மதிப்புகள், விதிகளுக்குப் பிறகு", "जहाँ दस्तावेज़ में कुछ नहीं, वहाँ गढ़े मान, नियमों के बाद")
s("ui.testing.f.fl_must", "Medicines the app asks you to confirm", "நீங்கள் உறுதிசெய்யும்படி செயலி கேட்கும் மருந்துகள்", "वे दवाएँ जिनकी पुष्टि ऐप आपसे करवाता है")
s("ui.testing.f.fl_name", "Wrong medicine names with no check flag", "சரிபார்ப்புக் குறி இல்லாத தவறான மருந்துப் பெயர்கள்", "बिना जाँच-चिह्न के ग़लत दवा-नाम")
s("ui.testing.f.fl_identity", "Interaction-checked medicines with the wrong drug identity", "தவறான மருந்து அடையாளத்துடன் இடைவினை சோதிக்கப்பட்ட மருந்துகள்", "ग़लत दवा-पहचान के साथ इंटरैक्शन-जाँची गई दवाएँ")
s("ui.testing.f.fl_timing", "Wrong when-to-take values with no check flag", "சரிபார்ப்புக் குறி இல்லாத தவறான எப்போது-எடுப்பது மதிப்புகள்", "बिना जाँच-चिह्न के ग़लत कब-लेना मान")
s("ui.testing.f.vf_en_fr", "English: correct lines wrongly rejected", "ஆங்கிலம்: தவறாக நிராகரிக்கப்பட்ட சரியான வரிகள்", "अंग्रेज़ी: ग़लती से अस्वीकार हुई सही पंक्तियाँ")
s("ui.testing.f.vf_en_det", "English: wrong lines caught", "ஆங்கிலம்: பிடிபட்ட தவறான வரிகள்", "अंग्रेज़ी: पकड़ी गई ग़लत पंक्तियाँ")
s("ui.testing.f.vf_ta_fr", "Tamil: correct lines wrongly rejected", "தமிழ்: தவறாக நிராகரிக்கப்பட்ட சரியான வரிகள்", "तमिल: ग़लती से अस्वीकार हुई सही पंक्तियाँ")
s("ui.testing.f.vf_ta_det", "Tamil: wrong lines caught", "தமிழ்: பிடிபட்ட தவறான வரிகள்", "तमिल: पकड़ी गई ग़लत पंक्तियाँ")
s("ui.testing.f.vf_hi_fr", "Hindi: correct lines wrongly rejected", "இந்தி: தவறாக நிராகரிக்கப்பட்ட சரியான வரிகள்", "हिंदी: ग़लती से अस्वीकार हुई सही पंक्तियाँ")
s("ui.testing.f.vf_hi_det", "Hindi: wrong lines caught", "இந்தி: பிடிபட்ட தவறான வரிகள்", "हिंदी: पकड़ी गई ग़लत पंक्तियाँ")
s("ui.testing.f.lg_en", "English: lines shown in English", "ஆங்கிலம்: ஆங்கிலத்தில் காட்டப்பட்ட வரிகள்", "अंग्रेज़ी: अंग्रेज़ी में दिखाई गई पंक्तियाँ")
s("ui.testing.f.lg_ta", "Tamil: lines shown in Tamil", "தமிழ்: தமிழில் காட்டப்பட்ட வரிகள்", "तमिल: तमिल में दिखाई गई पंक्तियाँ")
s("ui.testing.f.lg_hi", "Hindi: lines shown in Hindi", "இந்தி: இந்தியில் காட்டப்பட்ட வரிகள்", "हिंदी: हिंदी में दिखाई गई पंक्तियाँ")
s("ui.testing.f.sf_silent", "Known interactions missed with no flag", "எந்தக் குறியும் இல்லாமல் தவறவிட்ட அறியப்பட்ட இடைவினைகள்", "बिना किसी चिह्न के छूटे ज्ञात इंटरैक्शन")
s("ui.testing.f.sf_strict", "Known interactions not reported (strict count)", "அறிவிக்கப்படாத அறியப்பட்ட இடைவினைகள் (கடுமையான எண்ணிக்கை)", "रिपोर्ट नहीं हुए ज्ञात इंटरैक्शन (सख़्त गिनती)")
s("ui.testing.f.sf_false", "Interactions reported that are not in the data", "தரவில் இல்லாத, அறிவிக்கப்பட்ட இடைவினைகள்", "डेटा में न होने पर भी रिपोर्ट किए गए इंटरैक्शन")
s("ui.testing.f.sf_nc_clean", "Pairs reported as could not check, clean images", "சோதிக்க இயலவில்லை எனக் காட்டப்பட்ட ஜோடிகள், தெளிவான படங்கள்", "जाँच नहीं हो सकी बताई गई जोड़ियाँ, साफ़ तस्वीरें")
s("ui.testing.f.sf_nc_poor", "Pairs reported as could not check, poor images", "சோதிக்க இயலவில்லை எனக் காட்டப்பட்ட ஜோடிகள், மோசமான படங்கள்", "जाँच नहीं हो सकी बताई गई जोड़ियाँ, ख़राब तस्वीरें")
s("ui.testing.f.live_flows", "End-to-end flows completed in the real app", "உண்மையான செயலியில் முடிந்த முழுப் பயணங்கள்", "असली ऐप में पूरे हुए आरंभ-से-अंत प्रवाह")

# what it measures
s("ui.testing.m.f1",
  "F1 balances two things: medicines found, and medicines added that are not on the document. Higher is better. Shown as a percentage.",
  "F1 இரண்டு விஷயங்களைச் சமப்படுத்துகிறது: கண்டறிந்த மருந்துகள், ஆவணத்தில் இல்லாமல் சேர்க்கப்பட்ட மருந்துகள். அதிகம் நல்லது. சதவீதமாகக் காட்டப்படுகிறது.",
  "F1 दो बातों को संतुलित करता है: मिली दवाएँ, और वे दवाएँ जो दस्तावेज़ में नहीं हैं पर जोड़ दी गईं। अधिक बेहतर है। प्रतिशत में दिखाया गया है।")
s("ui.testing.m.every_field",
  "Share of found medicines whose name, strength, dose, how often, when and duration were all right.",
  "கண்டறிந்த மருந்துகளில், பெயர், வலிமை, அளவு, எத்தனை முறை, எப்போது, காலம் அனைத்தும் சரியாக இருந்தவற்றின் பங்கு.",
  "मिली दवाओं में से उनका हिस्सा जिनका नाम, ताक़त, मात्रा, कितनी बार, कब और अवधि सब सही थे।")
s("ui.testing.m.invented",
  "Of the fields where the document says nothing, the share in which the software still produced a value. Lower is better.",
  "ஆவணம் எதுவும் சொல்லாத புலங்களில், மென்பொருள் இருந்தும் ஒரு மதிப்பை உருவாக்கியவற்றின் பங்கு. குறைவு நல்லது.",
  "जिन फ़ील्ड में दस्तावेज़ कुछ नहीं कहता, उनमें से उनका हिस्सा जहाँ सॉफ़्टवेयर ने फिर भी कोई मान बना दिया। कम बेहतर है।")
s("ui.testing.m.must_confirm",
  "Share of medicines where the app asks you to confirm something before it checks interactions or builds a schedule.",
  "இடைவினைகளைச் சோதிக்கும் அல்லது அட்டவணை அமைக்கும் முன் நீங்கள் ஏதாவது உறுதிசெய்யும்படி செயலி கேட்கும் மருந்துகளின் பங்கு.",
  "उन दवाओं का हिस्सा जहाँ इंटरैक्शन जाँचने या शेड्यूल बनाने से पहले ऐप आपसे कुछ पुष्टि करवाता है।")
s("ui.testing.m.name_unflagged",
  "Medicine names still wrong after the rules that carried no confirmation flag, out of all names that were still wrong.",
  "விதிகளுக்குப் பிறகும் தவறாக இருந்த பெயர்களில், உறுதிப்படுத்தல் குறி இல்லாதவை.",
  "नियमों के बाद भी ग़लत रहे नामों में से वे जिन पर पुष्टि-चिह्न नहीं था।")
s("ui.testing.m.identity_wrong",
  "Medicines sent to the interaction check with a different drug identity than the one written, out of all medicines sent.",
  "இடைவினைச் சோதனைக்கு அனுப்பப்பட்ட மருந்துகளில், எழுதப்பட்டதிலிருந்து வேறுபட்ட மருந்து அடையாளம் கொண்டவை.",
  "इंटरैक्शन जाँच को भेजी गई दवाओं में से वे जिनकी पहचान लिखी हुई से अलग थी।")
s("ui.testing.m.timing_unflagged",
  "Wrong when-to-take values that carried no confirmation flag, out of all such values still wrong.",
  "இன்னும் தவறாக இருந்த எப்போது-எடுப்பது மதிப்புகளில், உறுதிப்படுத்தல் குறி இல்லாதவை.",
  "ग़लत रहे कब-लेना मानों में से वे जिन पर पुष्टि-चिह्न नहीं था।")
s("ui.testing.m.false_reject",
  "Correct explanation lines that the checks wrongly refused to show as verified; the person would see the original English instead. Lower is better.",
  "சரிபார்ப்புகள் தவறாக நிராகரித்த சரியான விளக்க வரிகள்; அவற்றுக்குப் பதிலாக மூல ஆங்கிலம் காட்டப்படும். குறைவு நல்லது.",
  "सही व्याख्या-पंक्तियाँ जिन्हें जाँच ने ग़लती से सत्यापित मानने से मना कर दिया; व्यक्ति को उनकी जगह मूल अंग्रेज़ी दिखती है। कम बेहतर है।")
s("ui.testing.m.detected",
  "Deliberately wrong explanation lines (a changed number, a dropped warning, invented advice and similar) that the checks caught. Higher is better.",
  "வேண்டுமென்றே தவறாக எழுதப்பட்ட விளக்க வரிகளில் (மாற்றிய எண், விடுபட்ட எச்சரிக்கை, கற்பனை அறிவுரை போன்றவை) சரிபார்ப்புகள் பிடித்தவை. அதிகம் நல்லது.",
  "जानबूझकर ग़लत लिखी व्याख्या-पंक्तियों (बदली संख्या, छूटी चेतावनी, गढ़ी सलाह आदि) में से जो जाँच ने पकड़ीं। अधिक बेहतर है।")
s("ui.testing.m.shown_in_language",
  "Share of free-text lines (advice, follow-up, warnings) that passed every check and are shown in this language; the rest show the original English with a notice.",
  "அனைத்துச் சரிபார்ப்புகளையும் கடந்து இந்த மொழியில் காட்டப்படும் கட்டற்ற உரை வரிகளின் (அறிவுரை, தொடர் சந்திப்பு, எச்சரிக்கைகள்) பங்கு; மற்றவை அறிவிப்புடன் மூல ஆங்கிலத்தைக் காட்டும்.",
  "उन मुक्त-पाठ पंक्तियों (सलाह, फ़ॉलो-अप, चेतावनियाँ) का हिस्सा जो हर जाँच से गुज़रकर इस भाषा में दिखती हैं; बाक़ी सूचना के साथ मूल अंग्रेज़ी दिखाती हैं।")
s("ui.testing.m.silent_unflagged",
  "Known interactions that were not reported and that no confirmation flag covered, out of all known interactions in the test pairs.",
  "அறிவிக்கப்படாத, எந்த உறுதிப்படுத்தல் குறியும் இல்லாத அறியப்பட்ட இடைவினைகள் (சோதனை ஜோடிகளிலுள்ள அனைத்து அறியப்பட்ட இடைவினைகளில்).",
  "ज्ञात इंटरैक्शन जो रिपोर्ट नहीं हुए और जिन पर कोई पुष्टि-चिह्न नहीं था (परीक्षण जोड़ियों के सभी ज्ञात इंटरैक्शन में से)।")
s("ui.testing.m.silent_strict",
  "Known interactions the check did not report at all, whatever the reason, out of all known interactions. Counted strictly.",
  "எந்தக் காரணமாக இருந்தாலும் சோதனை அறிவிக்காத அறியப்பட்ட இடைவினைகள் (அனைத்து அறியப்பட்ட இடைவினைகளில்). கடுமையாக எண்ணப்பட்டது.",
  "ज्ञात इंटरैक्शन जिन्हें जाँच ने किसी भी कारण से बिल्कुल रिपोर्ट नहीं किया (सभी ज्ञात इंटरैक्शन में से)। सख़्ती से गिना गया।")
s("ui.testing.m.false_alarm",
  "Interactions reported for a pair that has none in the source data, out of all pairs.",
  "மூலத் தரவில் இடைவினை இல்லாத ஜோடிக்கு அறிவிக்கப்பட்ட இடைவினைகள் (அனைத்து ஜோடிகளில்).",
  "ऐसी जोड़ी के लिए रिपोर्ट किए गए इंटरैक्शन जिसका स्रोत डेटा में कोई इंटरैक्शन नहीं है (सभी जोड़ियों में से)।")
s("ui.testing.m.not_checked_clean",
  "Share of medicine pairs reported as could not check on clean images. It shows how often the interaction data has no answer for a pair.",
  "தெளிவான படங்களில் சோதிக்க இயலவில்லை எனக் காட்டப்பட்ட மருந்து ஜோடிகளின் பங்கு. ஒரு ஜோடிக்கு இடைவினைத் தரவில் பதில் இல்லாத அளவை இது காட்டுகிறது.",
  "साफ़ तस्वीरों पर जाँच नहीं हो सकी बताई गई दवा-जोड़ियों का हिस्सा। यह दिखाता है कि इंटरैक्शन डेटा में कितनी बार किसी जोड़ी का उत्तर नहीं होता।")
s("ui.testing.m.not_checked_poor",
  "Share of medicine pairs reported as could not check on poor images. It shows how often the interaction data has no answer, or a medicine needed your confirmation first.",
  "மோசமான படங்களில் சோதிக்க இயலவில்லை எனக் காட்டப்பட்ட மருந்து ஜோடிகளின் பங்கு. இடைவினைத் தரவில் பதில் இல்லாத அல்லது முதலில் உங்கள் உறுதிப்படுத்தல் தேவைப்பட்ட அளவை இது காட்டுகிறது.",
  "ख़राब तस्वीरों पर जाँच नहीं हो सकी बताई गई दवा-जोड़ियों का हिस्सा। यह दिखाता है कि कितनी बार इंटरैक्शन डेटा में उत्तर नहीं था या पहले आपकी पुष्टि चाहिए थी।")
s("ui.testing.m.live_flows",
  "Runs of the real app, from consent to delete-my-data, that finished with no error on screen and nothing left behind.",
  "ஒப்புதல் முதல் எனது தரவை நீக்கு வரை, திரையில் பிழை இல்லாமல் முடிந்த, எதுவும் மீதமில்லாத உண்மையான செயலி ஓட்டங்கள்.",
  "सहमति से 'मेरा डेटा हटाएँ' तक असली ऐप के वे रन जो स्क्रीन पर बिना किसी त्रुटि के पूरे हुए और कुछ बाक़ी नहीं बचा।")

# data
s("ui.testing.d.dev_docs",
  "{docs} synthetic development documents, each in {conditions} image conditions ({n} document images in all)",
  "{docs} செயற்கை மேம்பாட்டு ஆவணங்கள், ஒவ்வொன்றும் {conditions} பட நிலைகளில் (மொத்தம் {n} ஆவணப் படங்கள்)",
  "{docs} कृत्रिम विकास दस्तावेज़, हर एक {conditions} तस्वीर-स्थितियों में (कुल {n} दस्तावेज़ तस्वीरें)")
s("ui.testing.d.dev_meds",
  "{meds} medicines read from {n} document images of {docs} synthetic development documents",
  "{docs} செயற்கை மேம்பாட்டு ஆவணங்களின் {n} ஆவணப் படங்களிலிருந்து படித்த {meds} மருந்துகள்",
  "{docs} कृत्रिम विकास दस्तावेज़ों की {n} दस्तावेज़ तस्वीरों से पढ़ी गई {meds} दवाएँ")
s("ui.testing.d.stress",
  "{n} lines written for this test, half correct and half deliberately wrong",
  "இந்தச் சோதனைக்காக எழுதிய {n} வரிகள்; பாதி சரியானவை, பாதி வேண்டுமென்றே தவறானவை",
  "इस परीक्षण के लिए लिखी गई {n} पंक्तियाँ, आधी सही और आधी जानबूझकर ग़लत")
s("ui.testing.d.dev_lines",
  "{lines} free-text lines from {docs} synthetic development documents (clean images)",
  "{docs} செயற்கை மேம்பாட்டு ஆவணங்களின் {lines} கட்டற்ற உரை வரிகள் (தெளிவான படங்கள்)",
  "{docs} कृत्रिम विकास दस्तावेज़ों की {lines} मुक्त-पाठ पंक्तियाँ (साफ़ तस्वीरें)")
s("ui.testing.d.dev_pairs",
  "{pairs} medicine pairs from {docs} synthetic development documents, in {conditions} image conditions; {found} of the pairs have a known interaction",
  "{docs} செயற்கை மேம்பாட்டு ஆவணங்களின் {pairs} மருந்து ஜோடிகள், {conditions} பட நிலைகளில்; அவற்றில் {found} ஜோடிகளுக்கு அறியப்பட்ட இடைவினை உள்ளது",
  "{docs} कृत्रिम विकास दस्तावेज़ों की {pairs} दवा-जोड़ियाँ, {conditions} तस्वीर-स्थितियों में; इनमें से {found} जोड़ियों में ज्ञात इंटरैक्शन है")
s("ui.testing.d.live",
  "{n} runs on one synthetic development document ({doc})",
  "ஒரு செயற்கை மேம்பாட்டு ஆவணத்தில் ({doc}) {n} ஓட்டங்கள்",
  "एक कृत्रिम विकास दस्तावेज़ ({doc}) पर {n} रन")

# caveats
s("ui.testing.c.dev_tuned", "The rules and prompts were tuned on this set, so it flatters the result.", "விதிகளும் தூண்டுதல்களும் இந்தத் தொகுப்பில் சரிசெய்யப்பட்டன; எனவே இது முடிவை நன்றாகக் காட்டும்.", "नियम और प्रॉम्प्ट इसी सेट पर ट्यून किए गए, इसलिए यह नतीजे को बेहतर दिखाता है।")
s("ui.testing.c.upper_bound",
  "Upper bound: the document generator and the name matcher share one list of {formulary} medicines, and the rules were tuned on this set.",
  "உச்ச வரம்பு: ஆவண உருவாக்கியும் பெயர் பொருத்தியும் {formulary} மருந்துகளின் ஒரே பட்டியலைப் பகிர்கின்றன; விதிகளும் இந்தத் தொகுப்பில் சரிசெய்யப்பட்டன.",
  "ऊपरी सीमा: दस्तावेज़ जनरेटर और नाम-मिलान दोनों {formulary} दवाओं की एक ही सूची साझा करते हैं, और नियम इसी सेट पर ट्यून किए गए।")
s("ui.testing.c.flags_not_errors", "A flag asks you to look again. Most flagged medicines were in fact read correctly.", "குறி என்பது மீண்டும் பார்க்கச் சொல்வது. குறியிடப்பட்ட பெரும்பாலான மருந்துகள் உண்மையில் சரியாகப் படிக்கப்பட்டிருந்தன.", "चिह्न आपसे दोबारा देखने को कहता है। चिह्नित अधिकांश दवाएँ वास्तव में सही पढ़ी गई थीं।")
s("ui.testing.c.one_timing", "The one case was a medicine line that was cut off in the model's reading.", "அந்த ஒரு நிகழ்வில் மாடலின் வாசிப்பில் மருந்து வரி துண்டிக்கப்பட்டிருந்தது.", "वह एक मामला मॉडल की पढ़ाई में कटी हुई दवा-पंक्ति का था।")
s("ui.testing.c.same_model", "A small set written for this test. The same local model writes and judges the lines, so the judge is weak.", "இந்தச் சோதனைக்காக எழுதிய சிறிய தொகுப்பு. அதே உள்ளூர் மாடல் வரிகளை எழுதியும் மதிப்பிட்டும் செய்கிறது; எனவே மதிப்பீட்டாளர் பலவீனமானவர்.", "इस परीक्षण के लिए लिखा गया छोटा सेट। वही स्थानीय मॉडल पंक्तियाँ लिखता और जाँचता है, इसलिए जाँचकर्ता कमज़ोर है।")
s("ui.testing.c.small_unchecked", "A very small set, not checked by native speakers. The same model writes and judges the lines.", "மிகச் சிறிய தொகுப்பு; தாய்மொழி பேசுபவர்கள் சரிபார்க்கவில்லை. அதே மாடல் வரிகளை எழுதியும் மதிப்பிட்டும் செய்கிறது.", "बहुत छोटा सेट, जिसे मातृभाषा बोलने वालों ने नहीं जाँचा। वही मॉडल पंक्तियाँ लिखता और जाँचता है।")
s("ui.testing.c.varies", "This varies from run to run and by language; in the live runs fewer Tamil lines passed than Hindi lines.", "இது ஒவ்வொரு ஓட்டத்திலும் மொழிக்கு மொழியும் மாறும்; நேரடி ஓட்டங்களில் இந்தியை விடத் தமிழ் வரிகள் குறைவாகவே கடந்தன.", "यह हर रन में और भाषा के अनुसार बदलता है; लाइव रनों में हिंदी से कम तमिल पंक्तियाँ पास हुईं।")
s("ui.testing.c.partial_db", "The interaction data is incomplete, so many pairs have no answer. See the limits below.", "இடைவினைத் தரவு முழுமையற்றது; எனவே பல ஜோடிகளுக்குப் பதில் இல்லை. கீழுள்ள வரம்புகளைப் பாருங்கள்.", "इंटरैक्शन डेटा अधूरा है, इसलिए कई जोड़ियों का उत्तर नहीं है। नीचे सीमाएँ देखें।")
s("ui.testing.c.strict_covered", "All {n} were covered by a confirmation flag on the medicine.", "அந்த {n} அனைத்தும் மருந்தின் மீதான உறுதிப்படுத்தல் குறியால் உள்ளடக்கப்பட்டிருந்தன.", "वे सभी {n} दवा पर लगे पुष्टि-चिह्न से कवर थे।")
s("ui.testing.c.live_not_perf", "These runs show that the flow completes. Their timings are not a measure of how fast it is.", "இந்த ஓட்டங்கள் பயணம் முடிவடைகிறது என்பதைக் காட்டுகின்றன. அவற்றின் நேரங்கள் அது எவ்வளவு வேகம் என்பதன் அளவீடு அல்ல.", "ये रन दिखाते हैं कि प्रवाह पूरा होता है। इनके समय इस बात का माप नहीं कि यह कितना तेज़ है।")

# limits and the final test
s("ui.testing.limits.title", "Limits", "வரம்புகள்", "सीमाएँ")
s("ui.testing.limits.l1", "Everything shown is measured on synthetic documents. Real discharge summaries and prescriptions look different.", "இங்கு காட்டப்படுவன அனைத்தும் செயற்கை ஆவணங்களில் அளக்கப்பட்டவை. உண்மையான வெளியேற்றச் சுருக்கங்களும் மருந்துச் சீட்டுகளும் வேறுபடும்.", "यहाँ दिखाई हर चीज़ कृत्रिम दस्तावेज़ों पर मापी गई है। असली डिस्चार्ज सारांश और पर्चे अलग दिखते हैं।")
s("ui.testing.limits.l2", "The development-set figures were measured on the documents the rules and prompts were tuned on. They flatter the results; compare the final test figures instead.", "மேம்பாட்டுத் தொகுப்பு எண்கள், விதிகளும் தூண்டுதல்களும் சரிசெய்யப்பட்ட ஆவணங்களிலேயே அளக்கப்பட்டவை. அவை முடிவுகளை நன்றாகக் காட்டும்; அதற்குப் பதிலாக இறுதிச் சோதனை எண்களை ஒப்பிடுங்கள்.", "विकास सेट के आँकड़े उन्हीं दस्तावेज़ों पर मापे गए जिन पर नियम और प्रॉम्प्ट ट्यून किए गए। ये नतीजों को बेहतर दिखाते हैं; इसकी जगह अंतिम परीक्षण के आँकड़ों की तुलना करें।")
s("ui.testing.limits.l3", "Name-matching scores are an upper bound: the document generator and the name matcher share one list of {formulary} medicines, so every name in the tests is on that list.", "பெயர் பொருத்த மதிப்பெண்கள் உச்ச வரம்பு: ஆவண உருவாக்கியும் பெயர் பொருத்தியும் {formulary} மருந்துகளின் ஒரே பட்டியலைப் பகிர்கின்றன; எனவே சோதனைகளிலுள்ள ஒவ்வொரு பெயரும் அந்தப் பட்டியலில் உள்ளது.", "नाम-मिलान के स्कोर ऊपरी सीमा हैं: दस्तावेज़ जनरेटर और नाम-मिलान {formulary} दवाओं की एक ही सूची साझा करते हैं, इसलिए परीक्षण का हर नाम उसी सूची में है।")
s("ui.testing.limits.l4", "The Tamil and Hindi test sets are tiny and have not been checked by native speakers. Tamil and Hindi texts are machine drafts.", "தமிழ், இந்திச் சோதனைத் தொகுப்புகள் மிகச் சிறியவை; தாய்மொழி பேசுபவர்கள் அவற்றைச் சரிபார்க்கவில்லை. தமிழ், இந்தி உரைகள் இயந்திர வரைவுகள்.", "तमिल और हिंदी के परीक्षण सेट बहुत छोटे हैं और मातृभाषा बोलने वालों ने उन्हें नहीं जाँचा है। तमिल और हिंदी पाठ मशीन के बनाए मसौदे हैं।")
s("ui.testing.limits.l5", "Interaction data is incomplete: the downloaded set covers only some drug groups, so a missing record says nothing. The extra interaction notes written for this project were checked by their author, not reviewed by a pharmacist.", "இடைவினைத் தரவு முழுமையற்றது: பதிவிறக்கிய தொகுப்பு சில மருந்துக் குழுக்களை மட்டுமே உள்ளடக்கியது; எனவே பதிவு இல்லாதது எதையும் சொல்லாது. இந்தத் திட்டத்திற்காக எழுதிய கூடுதல் இடைவினைக் குறிப்புகளை அவற்றின் ஆசிரியரே சரிபார்த்தார்; மருந்தாளர் மதிப்பாய்வு செய்யவில்லை.", "इंटरैक्शन डेटा अधूरा है: डाउनलोड किया गया सेट केवल कुछ दवा-समूहों को कवर करता है, इसलिए रिकॉर्ड न मिलने से कुछ नहीं कहा जा सकता। इस प्रोजेक्ट के लिए लिखे अतिरिक्त इंटरैक्शन नोट उनके लेखक ने जाँचे हैं, किसी फ़ार्मासिस्ट ने उनकी समीक्षा नहीं की।")
s("ui.testing.limits.l6", "Brand names are matched against a list that no pharmacist has verified.", "பிராண்ட் பெயர்கள், எந்த மருந்தாளரும் சரிபார்க்காத ஒரு பட்டியலுடன் பொருத்தப்படுகின்றன.", "ब्रांड नाम एक ऐसी सूची से मिलाए जाते हैं जिसे किसी फ़ार्मासिस्ट ने सत्यापित नहीं किया है।")
s("ui.testing.limits.l7", "The same local model that writes an explanation line also judges it, so that check is weak.", "விளக்க வரியை எழுதும் அதே உள்ளூர் மாடலே அதை மதிப்பிடுகிறது; எனவே அந்தச் சரிபார்ப்பு பலவீனமானது.", "जो स्थानीय मॉडल व्याख्या-पंक्ति लिखता है वही उसे जाँचता भी है, इसलिए वह जाँच कमज़ोर है।")
s("ui.testing.final.title", "Final test results", "இறுதிச் சோதனை முடிவுகள்", "अंतिम परीक्षण के नतीजे")
s("ui.testing.final.not_run", "Not yet run. The held-out final test set is used once, after the work is finished. Its results will be added here; until then no test-set number is shown.", "இன்னும் இயக்கப்படவில்லை. ஒதுக்கி வைத்த இறுதிச் சோதனைத் தொகுப்பு, வேலை முடிந்த பிறகு ஒரு முறை பயன்படுத்தப்படும். அதன் முடிவுகள் இங்கே சேர்க்கப்படும்; அதுவரை சோதனைத் தொகுப்பின் எந்த எண்ணும் காட்டப்படாது.", "अभी चलाया नहीं गया। अलग रखा गया अंतिम परीक्षण सेट काम पूरा होने के बाद एक बार इस्तेमाल होगा। उसके नतीजे यहाँ जोड़े जाएँगे; तब तक परीक्षण सेट की कोई संख्या नहीं दिखाई जाएगी।")
s("ui.testing.teaser_body", "We test on made-up documents only, never on real patients' papers. The method, the figures we have so far and their limits are on one page.", "நாங்கள் கற்பனை ஆவணங்களில் மட்டுமே சோதிக்கிறோம்; உண்மையான நோயாளிகளின் ஆவணங்களில் ஒருபோதும் இல்லை. முறை, இதுவரையிலான எண்கள், அவற்றின் வரம்புகள் ஒரே பக்கத்தில் உள்ளன.", "हम केवल गढ़े हुए दस्तावेज़ों पर परखते हैं, असली मरीज़ों के कागज़ों पर कभी नहीं। तरीक़ा, अब तक की संख्याएँ और उनकी सीमाएँ एक ही पेज पर हैं।")
s("ui.testing.teaser_link", "How we tested it, and the limits", "நாங்கள் எப்படிச் சோதித்தோம், வரம்புகள்", "हमने कैसे परखा, और सीमाएँ")

STRINGS = S
