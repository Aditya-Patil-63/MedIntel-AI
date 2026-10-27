"""
MedIntel AI — Clinical Guidance & Health Insights Engine.

Provides deterministic, patient-friendly educational alert messages,
possible health implications, and precautions/next steps for laboratory analytes.

Core Safety Guarantees:
    - Strictly non-diagnostic and educational.
    - Never prescribes specific medications or dosages.
    - Directs patients to consult qualified healthcare professionals.
    - Multilingual support for English, Hindi, Marathi, and Gujarati.
"""

from typing import Dict, Optional, Tuple


# Clinical educational guidance dictionary
# Structure: canonical_name -> status -> language -> (alert_message, implications, precautions)
CLINICAL_GUIDANCE: Dict[str, Dict[str, Dict[str, Tuple[str, str, str]]]] = {
    "Fasting Blood Glucose": {
        "LOW": {
            "en": (
                "Blood glucose is below the standard fasting reference range.",
                "Low blood sugar (hypoglycemia) can lead to shakiness, dizziness, sweating, fatigue, or difficulty concentrating.",
                "Consume a fast-acting carbohydrate if experiencing symptoms. Consult your doctor to adjust meal schedules or medications.",
            ),
            "hi": (
                "रक्त शर्करा (ब्लड शुगर) सामान्य उपवास सीमा से कम है।",
                "निम्न रक्त शर्करा (हाइपोग्लाइसीमिया) से चक्कर, कंपकंपी, पसीना और कमजोरी हो सकती है।",
                "तुरंत हल्का मीठा या फल लें और अपने चिकित्सक से परामर्श करके अपनी दवा और आहार की समीक्षा करें।",
            ),
            "mr": (
                "रक्तातील साखर (ब्लड शुगर) सामान्य पातळीपेक्षा कमी आहे.",
                "कमी साखरेमुळे चक्कर येणे, थरथरणे, घाम येणे आणि थकवा जाणवू शकतो.",
                "लक्षणे आढळल्यास त्वरित ग्लुकोज किंवा फळे घ्या आणि डॉक्टरांचा सल्ला घ्या.",
            ),
            "gu": (
                "બ્લડ સુગર સામાન્ય ઉપવાસ મર્યાદા કરતા ઓછું છે.",
                "ઓછી સુગરથી ચક્કર આવવા, ધ્રૂજારી અને અશક્તિ અનુભવાઈ શકે છે.",
                "તુરંત થોડું ગળ્યું લો અને તમારા ડોક્ટર સાથે આહાર અને દવા અંગે ચર્ચા કરો.",
            ),
        },
        "NORMAL": {
            "en": (
                "Fasting blood glucose is within the normal expected reference range.",
                "Indicates healthy glycemic regulation and normal cellular energy metabolism at the time of testing.",
                "Maintain healthy dietary habits, regular physical activity, and routine annual wellness checks.",
            ),
            "hi": (
                "उपवास रक्त शर्करा सामान्य सीमा में है।",
                "यह दर्शाता है कि शरीर में शर्करा का संतुलन ठीक है।",
                "संतुलित आहार, नियमित व्यायाम जारी रखें और समय-समय पर स्वास्थ्य जांच कराएं।",
            ),
            "mr": (
                "रक्तातील साखर सामान्य मर्यादेत आहे.",
                "शरीरातील साखरेचे प्रमाण संतुलित असल्याचे दर्शवते.",
                "संतुलित आहार व नियमित व्यायाम सुरू ठेवा आणि नियमित तपासणी करा.",
            ),
            "gu": (
                "બ્લડ સુગર સામાન્ય મર્યાદામાં છે.",
                "આ દર્શાવે છે કે શરીરનું શર્કરા નિયંત્રણ સામાન્ય છે.",
                "સંતુલિત આહાર અને નિયમિત કસરત ચાલુ રાખો.",
            ),
        },
        "HIGH": {
            "en": (
                "Fasting blood glucose is elevated above normal fasting limits.",
                "Elevated glucose may indicate impaired glucose tolerance, prediabetes, or insulin resistance. Persistent elevation can affect cardiovascular and metabolic health.",
                "Focus on low-glycemic foods, reduce refined sugars, increase physical activity, and consult your doctor for confirmatory HbA1c testing.",
            ),
            "hi": (
                "रक्त शर्करा सामान्य उपवास सीमा से अधिक है।",
                "बढ़ा हुआ ग्लूकोज इंसुलिन प्रतिरोध या प्री-डायबिटीज का संकेत हो सकता है। लंबे समय तक बढ़ा रहने से हृदय और गुर्दे पर प्रभाव पड़ सकता है।",
                "मीठे और परिष्कृत भोजन से बचें, पैदल चलें और डॉक्टर से HbA1c जांच के लिए परामर्श लें।",
            ),
            "mr": (
                "रक्तातील साखर सामान्य पातळीपेक्षा जास्त आहे.",
                "वाढलेली साखर प्रीडायबेटिस किंवा इन्सुलिन प्रतिकाराचे लक्षण असू शकते.",
                "साखरेचे प्रमाण कमी करा, नियमित चालणे ठेवा आणि डॉक्टरांकडून HbA1c चाचणी करून घ्या.",
            ),
            "gu": (
                "બ્લડ સુગર સામાન્ય મર્યાદા કરતા વધારે છે.",
                "વધારે સુગર પ્રી-ડાયાબિટીસ અથવા ઇન્સ્યુલિન પ્રતિકાર દર્શાવી શકે છે.",
                "મીઠાઈ અને પ્રોસેસ્ડ ફૂડ ઓછું કરો, કસરત કરો અને ડોક્ટર પાસે HbA1c ટેસ્ટ કરાવો.",
            ),
        },
        "CRITICAL": {
            "en": (
                "CRITICAL ALERT: Fasting blood glucose is in the critical alert range.",
                "Extremely high or low glucose levels require immediate medical intervention to avoid acute metabolic complications.",
                "Urgent medical attention is advised. Please contact your physician or visit the nearest emergency facility promptly.",
            ),
            "hi": (
                "गंभीर चेतावनी: रक्त शर्करा अत्यधिक गंभीर स्तर पर है।",
                "अत्यधिक स्तर से गंभीर चयापचय समस्याएं हो सकती हैं।",
                "तत्काल चिकित्सकीय सहायता लें। कृपया तुरंत अपने डॉक्टर या नजदीकी अस्पताल से संपर्क करें।",
            ),
            "mr": (
                "तातडीचा इशारा: रक्तातील साखर अत्यंत धोकादायक पातळीवर आहे.",
                "अतिउच्च किंवा अत्यंत कमी साखरेमुळे तीव्र आरोग्य समस्या उद्भवू शकतात.",
                "त्वरित वैद्यकीय सल्ला घ्या. जवळच्या रुग्णालयात किंवा डॉक्टरांकडे जा.",
            ),
            "gu": (
                "તાત્કાલિક ચેતવણી: બ્લડ સુગર ગંભીર સ્તરે છે.",
                "અત્યંત વધારે કે ઓછી સુગરથી ગંભીર સમસ્યાઓ થઈ શકે છે.",
                "તાત્કાલિક ડોક્ટરની સલાહ લો અથવા નજીકની હોસ્પિટલનો સંપર્ક કરો.",
            ),
        },
    },
    "Hemoglobin": {
        "LOW": {
            "en": (
                "Hemoglobin level is lower than the expected reference range.",
                "Low hemoglobin suggests reduced oxygen transport, commonly associated with nutritional anemia (iron/folate/B12 deficiency) or blood loss.",
                "Consult your doctor for complete blood count (CBC) evaluation. Consider iron-rich foods (greens, legumes) under medical guidance.",
            ),
            "hi": (
                "हीमोग्लोबिन का स्तर सामान्य से कम है।",
                "कम हीमोग्लोबिन एनीमिया या पोषण संबंधी कमी (आयरन/विटामिन B12) का संकेत हो सकता है।",
                "डॉक्टर से सलाह लें, हरी सब्जियां और दालें खाएं और खुद से दवा न लें।",
            ),
            "mr": (
                "हिमोग्लोबिनचे प्रमाण सामान्यपेक्षा कमी आहे.",
                "कमी हिमोग्लोबिन अशक्तपणा किंवा लोहाच्या कमतरतेचे लक्षण असू शकते.",
                "डॉक्टरांचा सल्ला घ्या आणि आहारात पालेभाज्या व पौष्टिक अन्नाचा समावेश करा.",
            ),
            "gu": (
                "હિમોગ્લોબિન સામાન્ય કરતા ઓછું છે.",
                "ઓછું હિમોગ્લોબિન એનિમિયા અથવા આયર્નની ઉણપ દર્શાવે છે.",
                "ડોક્ટરની સલાહ લો અને આહારમાં લીલા શાકભાજી ઉમેરો.",
            ),
        },
        "NORMAL": {
            "en": (
                "Hemoglobin is within the normal reference range.",
                "Indicates adequate red blood cell oxygen-carrying capacity supporting tissue oxygenation.",
                "Continue balanced nutrition with adequate iron, vitamins, and protein.",
            ),
            "hi": (
                "हीमोग्लोबिन सामान्य सीमा में है।",
                "यह शरीर में स्वस्थ रक्त और पर्याप्त ऑक्सीजन आपूर्ति को दर्शाता है।",
                "संतुलित पौष्टिक आहार बनाए रखें।",
            ),
            "mr": (
                "हिमोग्लोबिन सामान्य पातळीत आहे.",
                "शरीरात रक्त आणि ऑक्सिजनचा पुरवठा योग्य असल्याचे दर्शवते.",
                "संतुलित आहार चालू ठेवा.",
            ),
            "gu": (
                "હિમોગ્લોબિન સામાન્ય મર્યાદામાં છે.",
                "શરીરમાં રક્ત પરિભ્રમણ અને ઓક્સિજન યોગ્ય પ્રમાણમાં છે.",
                "પૌષ્ટિક આહાર ચાલુ રાખો.",
            ),
        },
        "HIGH": {
            "en": (
                "Hemoglobin is elevated above the normal reference threshold.",
                "Elevated hemoglobin may occur with dehydration, smoking, high-altitude adaptation, or bone marrow overproduction.",
                "Ensure proper daily hydration and consult your physician to evaluate underlying causes.",
            ),
            "hi": (
                "हीमोग्लोबिन का स्तर सामान्य से अधिक है।",
                "यह निर्जलीकरण (डिहाइड्रेशन) या अन्य कारणों से हो सकता है।",
                "खूब पानी पिएं और चिकित्सक से परामर्श लें।",
            ),
            "mr": (
                "हिमोग्लोबिन सामान्यपेक्षा जास्त आहे.",
                "पाण्याची कमतरता किंवा इतर कारणांमुळे असे होऊ शकते.",
                "भरपूर पाणी प्या आणि डॉक्टरांचा सल्ला घ्या.",
            ),
            "gu": (
                "હિમોગ્લોબિન સામાન્ય કરતા વધારે છે.",
                "પાણીની અછત અથવા અન્ય કારણોથી આવું થઈ શકે છે.",
                "પુષ્કળ પાણી પીવો અને ડોક્ટરનો સંપર્ક કરો.",
            ),
        },
        "CRITICAL": {
            "en": (
                "CRITICAL ALERT: Hemoglobin is severely abnormal.",
                "Critically low levels can impair vital organ oxygenation; severe elevation increases blood viscosity.",
                "Urgent medical consultation or hospital evaluation is necessary.",
            ),
            "hi": (
                "गंभीर चेतावनी: हीमोग्लोबिन अत्यधिक असामान्य स्तर पर है।",
                "अत्यधिक कमी से अंगों को ऑक्सीजन की कमी हो सकती है।",
                "तुरंत निकटतम अस्पताल में आपातकालीन जांच कराएं।",
            ),
            "mr": (
                "तातडीचा इशारा: हिमोग्लोबिन धोकादायक पातळीवर आहे.",
                "अत्यंत कमी प्रमाणामुळे महत्त्वाच्या अवयवांना धोका निर्माण होऊ शकतो.",
                "तातडीने डॉक्टरांशी संपर्क साधा.",
            ),
            "gu": (
                "તાત્કાલિક ચેતવણી: હિમોગ્લોબિન અત્યંત ગંભીર સ્તરે છે.",
                "અંગો સુધી ઓક્સિજન પહોંચવામાં મુશ્કેલી થઈ શકે છે.",
                "તુરંત ડોક્ટર અથવા હોસ્પિટલની મુલાકાત લો.",
            ),
        },
    },
    "Serum Creatinine": {
        "LOW": {
            "en": (
                "Serum creatinine is below expected reference values.",
                "Low creatinine is typically associated with reduced muscle mass, advanced age, or low dietary protein intake.",
                "Ensure adequate dietary protein and consult your physician during your next routine visit.",
            ),
            "hi": (
                "सीरम क्रिएटिनिन सामान्य से कम है।",
                "यह मांसपेशियों की कमी या आहार में प्रोटीन की कमी से जुड़ा हो सकता है।",
                "उचित प्रोटीन युक्त आहार लें और नियमित स्वास्थ्य जांच कराएं।",
            ),
            "mr": (
                "सीरम क्रिएटिनिन सामान्यपेक्षा कमी आहे.",
                "हे स्नायूंचे प्रमाण कमी असणे किंवा प्रथिनांच्या कमतरतेमुळे असू शकते.",
                "योग्य प्रथिनयुक्त आहार घ्या आणि नियमित तपासणी करा.",
            ),
            "gu": (
                "સીરમ ક્રિએટિનાઇન સામાન્ય કરતા ઓછું છે.",
                "આ પ્રોટીન અથવા સ્નાયુના ઓછા પ્રમાણ સાથે સંબંધિત હોઈ શકે છે.",
                "પ્રોટીનયુક્ત આહાર લો અને ડોક્ટરની સલાહ લો.",
            ),
        },
        "NORMAL": {
            "en": (
                "Serum creatinine is within normal clinical limits.",
                "Indicates normal baseline renal filtration efficiency and waste clearance.",
                "Maintain healthy hydration, regular physical activity, and avoid unnecessary NSAID painkiller use.",
            ),
            "hi": (
                "सीरम क्रिएटिनिन सामान्य सीमा में है।",
                "यह गुर्दे (किडनी) के सामान्य कामकाज को दर्शाता है।",
                "पर्याप्त पानी पिएं और बिना डॉक्टर की सलाह के दर्द निवारक दवाएं न लें।",
            ),
            "mr": (
                "सीरम क्रिएटिनिन सामान्य मर्यादेत आहे.",
                "मूत्रपिंड (किडनी) योग्य प्रकारे कार्य करत असल्याचे दर्शवते.",
                "भरपूर पाणी प्या आणि विनाकारण पेनकिलर गोळ्या घेणे टाळा.",
            ),
            "gu": (
                "સીરમ ક્રિએટિનાઇન સામાન્ય મર્યાદામાં છે.",
                "આ કિડની યોગ્ય રીતે કાર્ય કરી રહી હોવાનું દર્શાવે છે.",
                "યોગ્ય પ્રમાણમાં પાણી પીવો અને પેઇનકિલર દવાઓથી બચો.",
            ),
        },
        "HIGH": {
            "en": (
                "Serum creatinine is elevated above normal reference thresholds.",
                "Elevated creatinine may reflect decreased kidney filtration function, dehydration, high muscle breakdown, or certain medications.",
                "Stay well-hydrated, avoid non-steroidal anti-inflammatory drugs (NSAIDs), and consult a doctor or nephrologist for renal function panel and eGFR review.",
            ),
            "hi": (
                "सीरम क्रिएटिनिन सामान्य से अधिक है।",
                "बढ़ा हुआ क्रिएटिनिन गुर्दे की कार्यक्षमता में कमी या डिहाइड्रेशन का संकेत हो सकता है।",
                "पर्याप्त पानी पिएं, पेनकिलर दवाओं से बचें और डॉक्टर से किडनी फंक्शन टेस्ट (KFT) करवाएं।",
            ),
            "mr": (
                "सीरम क्रिएटिनिन सामान्यपेक्षा जास्त आहे.",
                "वाढलेले क्रिएटिनिन किडनीच्या कार्यात अडथळा किंवा पाण्याची कमतरता दर्शवू शकते.",
                "भरपूर पाणी प्या, पेनकिलर टाळा आणि डॉक्टरांकडून किडनीची तपासणी करून घ्या.",
            ),
            "gu": (
                "સીરમ ક્રિએટિનાઇન સામાન્ય કરતા વધારે છે.",
                "વધારે ક્રિએટિનાઇન કિડનીની ક્ષમતામાં ઘટાડો અથવા ડિહાઇડ્રેશન દર્શાવી શકે છે.",
                "પાણી પીવો, પેઇનકિલર ટાળો અને કિડનીની તપાસ કરાવો.",
            ),
        },
        "CRITICAL": {
            "en": (
                "CRITICAL ALERT: Serum creatinine is significantly elevated.",
                "Marked elevation can indicate acute kidney injury or severe renal impairment requiring immediate clinical evaluation.",
                "Promptly seek medical evaluation at a hospital or specialist kidney clinic.",
            ),
            "hi": (
                "गंभीर चेतावनी: सीरम क्रिएटिनिन अत्यधिक उच्च है।",
                "यह किडनी को तत्काल नुकसान का संकेत हो सकता है।",
                "तुरंत अस्पताल या किडनी विशेषज्ञ (नेफ्रोलॉजिस्ट) से संपर्क करें।",
            ),
            "mr": (
                "तातडीचा इशारा: सीरम क्रिएटिनिन अत्यंत धोकादायक पातळीवर आहे.",
                "हे किडनीला तातडीने धोका असल्याचे दर्शवू शकते.",
                "त्वरित रुग्णालयात किंवा मूत्रपिंड तज्ञांशी संपर्क साधा.",
            ),
            "gu": (
                "તાત્કાલિક ચેતવણી: સીરમ ક્રિએટિનાઇન ઘણું વધારે છે.",
                "આ કિડનીની ગંભીર સમસ્યા દર્શાવી શકે છે.",
                "તાત્કાલિક હોસ્પિટલ અથવા કિડની નિષ્ણાતનો સંપર્ક કરો.",
            ),
        },
    },
    "White Blood Cell Count": {
        "LOW": {
            "en": (
                "White blood cell count (WBC) is below standard reference range.",
                "Leukopenia may increase susceptibility to infections and can be caused by viral infections, autoimmune conditions, or medications.",
                "Practice good hand hygiene, avoid exposure to active infections, and consult your doctor for a differential count.",
            ),
            "hi": (
                "सफेद रक्त कोशिका (WBC) की संख्या सामान्य से कम है।",
                "कम WBC संक्रमण से लड़ने की क्षमता को प्रभावित कर सकता है।",
                "संक्रमण से बचें, साफ-सफाई रखें और डॉक्टर से परामर्श लें।",
            ),
            "mr": (
                "पांढऱ्या रक्तपेशींचे (WBC) प्रमाण सामान्यपेक्षा कमी आहे.",
                "कमी WBC मुळे संसर्ग होण्याची शक्यता वाढू शकते.",
                "स्वच्छता राखा, आजारी व्यक्तींपासून दूर राहा आणि डॉक्टरांचा सल्ला घ्या.",
            ),
            "gu": (
                "શ્વેત રક્તકણ (WBC) સામાન્ય કરતા ઓછા છે.",
                "ઓછા WBC થી ચેપ સામે લડવાની ક્ષમતા ઘટી શકે છે.",
                "સ્વચ્છતા રાખો અને ડોક્ટરની સલાહ લો.",
            ),
        },
        "NORMAL": {
            "en": (
                "White blood cell count is within normal physiological limits.",
                "Indicates normal baseline immune surveillance and absence of acute leukocytosis or leukopenia.",
                "Maintain healthy sleep, nutrition, and physical activity to support immune health.",
            ),
            "hi": (
                "WBC की संख्या सामान्य सीमा में है।",
                "यह सामान्य रोग प्रतिरोधक क्षमता को दर्शाता है।",
                "स्वस्थ जीवनशैली और पौष्टिक आहार जारी रखें।",
            ),
            "mr": (
                "WBC प्रमाण सामान्य मर्यादेत आहे.",
                "रोगप्रतिकारशक्ती सामान्य असल्याचे दर्शवते.",
                "नियमित व्यायाम आणि चांगला आहार सुरू ठेवा.",
            ),
            "gu": (
                "WBC સામાન્ય મર્યાદામાં છે.",
                "આ રોગપ્રતિકારક શક્તિ સામાન્ય હોવાનું દર્શાવે છે.",
                "સારો આહાર અને પૂરતી ઊંઘ લો.",
            ),
        },
        "HIGH": {
            "en": (
                "White blood cell count is elevated above normal reference values.",
                "Leukocytosis is most frequently an immune response to acute bacterial or viral infection, inflammation, tissue injury, or physical stress.",
                "Monitor for fever, cough, or pain. Consult your doctor for physical examination and targeted infectious workup.",
            ),
            "hi": (
                "WBC की संख्या सामान्य से अधिक है।",
                "बढ़ा हुआ WBC आमतौर पर शरीर में किसी संक्रमण या सूजन से लड़ने का संकेत है।",
                "बुखार या दर्द पर ध्यान दें और डॉक्टर से जांच करवाएं।",
            ),
            "mr": (
                "WBC प्रमाण सामान्यपेक्षा जास्त आहे.",
                "वाढलेले WBC शरीरात संसर्ग किंवा सूज असल्याचे दर्शवू शकते.",
                "ताप किंवा खोकल्याकडे लक्ष द्या आणि डॉक्टरांचा सल्ला घ्या.",
            ),
            "gu": (
                "WBC સામાન્ય કરતા વધારે છે.",
                "વધારે WBC શરીરમાં ચેપ અથવા સોજો દર્શાવી શકે છે.",
                "તાવ અથવા દુખાવાની સ્થિતિમાં ડોક્ટર પાસે તપાસ કરાવો.",
            ),
        },
        "CRITICAL": {
            "en": (
                "CRITICAL ALERT: White blood cell count is in the critical threshold.",
                "Extremely low or high WBC counts indicate severe bone marrow suppression, severe systemic infection, or hematologic disorders.",
                "Urgent medical attention is advised. Please visit an emergency clinic promptly.",
            ),
            "hi": (
                "गंभीर चेतावनी: WBC अत्यधिक गंभीर स्तर पर है।",
                "अत्यधिक स्तर गंभीर संक्रमण या रक्त विकार का संकेत हो सकता है।",
                "तुरंत आपातकालीन चिकित्सा सहायता लें।",
            ),
            "mr": (
                "तातडीचा इशारा: WBC अत्यंत धोकादायक पातळीवर आहे.",
                "हे गंभीर संसर्ग किंवा रक्तविकाराचे लक्षण असू शकते.",
                "त्वरित रुग्णालयात जा.",
            ),
            "gu": (
                "તાત્કાલિક ચેતવણી: WBC ગંભીર સ્તરે છે.",
                "આ ગંભીર ચેપ અથવા રક્તની સમસ્યા હોઈ શકે છે.",
                "તાત્કાલિક હોસ્પિટલ પહોંચો.",
            ),
        },
    },
    "Platelet Count": {
        "LOW": {
            "en": (
                "Platelet count is below the normal reference range.",
                "Thrombocytopenia increases bleeding risk and can occur following viral illnesses (e.g. dengue), autoimmune states, or medications.",
                "Avoid contact sports or medications that thin blood (e.g., aspirin). Seek immediate care if unusual bruising or bleeding occurs.",
            ),
            "hi": (
                "प्लेटलेट काउंट सामान्य से कम है।",
                "कम प्लेटलेट से रक्तस्राव का खतरा बढ़ सकता है (जैसे डेंगू या वायरल बुखार के बाद)।",
                "चोट से बचें, खून पतला करने वाली दवाएं न लें और डॉक्टर से संपर्क करें।",
            ),
            "mr": (
                "प्लेटलेट काउंट सामान्यपेक्षा कमी आहे.",
                "कमी प्लेटलेट्समुळे रक्तस्रावाचा धोका वाढू शकतो (उदा. डेंग्यूनंतर).",
                "दुखापतींपासून सावध राहा आणि डॉक्टरांचा सल्ला घ्या.",
            ),
            "gu": (
                "પ્લેટલેટ સામાન્ય કરતા ઓછા છે.",
                "ઓછા પ્લેટલેટથી રક્તસ્ત્રાવનું જોખમ વધી શકે છે.",
                "ઈજાથી બચો અને ડોક્ટરની સલાહ લો.",
            ),
        },
        "NORMAL": {
            "en": (
                "Platelet count is within standard physiological limits.",
                "Indicates normal primary hemostasis and blood clotting capability.",
                "No specific action required. Continue regular preventive health practices.",
            ),
            "hi": (
                "प्लेटलेट काउंट सामान्य सीमा में है।",
                "रक्त का थक्का जमने की प्रक्रिया सामान्य है।",
                "नियमित स्वास्थ्य का ध्यान रखें।",
            ),
            "mr": (
                "प्लेटलेट काउंट सामान्य आहे.",
                "रक्त गोठण्याची क्षमता योग्य असल्याचे दर्शवते.",
                "आरोग्याची काळजी घ्या.",
            ),
            "gu": (
                "પ્લેટલેટ સામાન્ય મર્યાદામાં છે.",
                "રક્ત જામવાની ક્ષમતા સામાન્ય છે.",
                "સ્વાસ્થ્યની કાળજી રાખો.",
            ),
        },
        "HIGH": {
            "en": (
                "Platelet count is elevated above normal reference thresholds.",
                "Thrombocytosis is commonly reactive to systemic inflammation, iron deficiency, or recent infection.",
                "Maintain hydration and consult your physician to investigate underlying reactive causes.",
            ),
            "hi": (
                "प्लेटलेट काउंट सामान्य से अधिक है।",
                "यह शरीर में सूजन या हालिया संक्रमण की प्रतिक्रिया हो सकती है।",
                "पर्याप्त पानी पिएं और डॉक्टर से परामर्श लें।",
            ),
            "mr": (
                "प्लेटलेट काउंट सामान्यपेक्षा जास्त आहे.",
                "हे शरीरात सूज किंवा संसर्गाची प्रतिक्रिया असू शकते.",
                "पाणी भरपूर प्या आणि डॉक्टरांना दाखवा.",
            ),
            "gu": (
                "પ્લેટલેટ સામાન્ય કરતા વધારે છે.",
                "આ સોજા અથવા ચેપની પ્રતિક્રિયા હોઈ શકે છે.",
                "પાણી પીવો અને ડોક્ટરની સલાહ લો.",
            ),
        },
        "CRITICAL": {
            "en": (
                "CRITICAL ALERT: Platelet count is dangerously abnormal.",
                "Critically low platelets carry spontaneous hemorrhage risks; severe thrombocytosis increases thrombosis risks.",
                "Urgent medical attention is required. Contact a hematologist or emergency department.",
            ),
            "hi": (
                "गंभीर चेतावनी: प्लेटलेट काउंट अत्यधिक गंभीर स्तर पर है।",
                "अत्यधिक कम प्लेटलेट से आंतरिक रक्तस्राव का खतरा होता है।",
                "तुरंत आपातकालीन चिकित्सा विभाग से संपर्क करें।",
            ),
            "mr": (
                "तातडीचा इशारा: प्लेटलेट्स धोकादायक पातळीवर आहेत.",
                "रक्तस्रावाचा मोठा धोका संभवतो.",
                "तातडीने रुग्णालयात जा.",
            ),
            "gu": (
                "તાત્કાલિક ચેતવણી: પ્લેટલેટ ગંભીર સ્તરે છે.",
                "રક્તસ્ત્રાવનો મોટો ખતરો રહે છે.",
                "તાત્કાલિક હોસ્પિટલ પહોંચો.",
            ),
        },
    },
    "Total Cholesterol": {
        "NORMAL": {
            "en": (
                "Total cholesterol is within desirable reference boundaries.",
                "Supports vascular health and reduces long-term atherosclerotic risk.",
                "Continue heart-healthy nutrition rich in fiber and unsaturated fats.",
            ),
            "hi": (
                "टोटल कोलेस्ट्रॉल सामान्य सीमा में है।",
                "यह हृदय और रक्त वाहिकाओं के अच्छे स्वास्थ्य का संकेत है।",
                "फाइबर युक्त आहार लें और नियमित व्यायाम करें।",
            ),
            "mr": (
                "टोटल कोलेस्ट्रॉल सामान्य पातळीत आहे.",
                "हे हृदयाच्या चांगल्या आरोग्याचे लक्षण आहे.",
                "संतुलित व पौष्टिक आहार सुरू ठेवा.",
            ),
            "gu": (
                "ટોટલ કોલેસ્ટ્રોલ સામાન્ય મર્યાદામાં છે.",
                "આ હૃદયના સારા સ્વાસ્થ્ય માટે સારું છે.",
                "કસરત અને સારો આહાર ચાલુ રાખો.",
            ),
        },
        "HIGH": {
            "en": (
                "Total cholesterol exceeds recommended clinical thresholds.",
                "Hypercholesterolemia increases arterial plaque buildup risk over time, influencing cardiovascular health.",
                "Limit saturated and trans fats, increase dietary soluble fiber, engage in aerobic exercise, and consult your doctor for a complete lipid profile.",
            ),
            "hi": (
                "टोटल कोलेस्ट्रॉल सामान्य से अधिक है।",
                "बढ़ा हुआ कोलेस्ट्रॉल रक्त धमनियों में रुकावट और दिल की बीमारी का खतरा बढ़ा सकता है।",
                "तले-भुने और वसायुक्त भोजन से बचें, टहलें और लिपिड प्रोफाइल की डॉक्टर से समीक्षा करवाएं।",
            ),
            "mr": (
                "टोटल कोलेस्ट्रॉल सामान्यपेक्षा जास्त आहे.",
                "वाढलेले कोलेस्ट्रॉल रक्तवाहिन्यांमध्ये अडथळा आणि हृदयविकाराचा धोका वाढवू शकते.",
                "तळलेले अन्न टाळा, व्यायाम करा आणि डॉक्टरांकडून लिपिड प्रोफाइल तपासा.",
            ),
            "gu": (
                "ટોટલ કોલેસ્ટ્રોલ સામાન્ય કરતા વધારે છે.",
                "વધારે કોલેસ્ટ્રોલ હૃદયની બીમારીઓનું જોખમ વધારે છે.",
                "તળેલો ખોરાક ઓછો કરો, કસરત કરો અને ડોક્ટરની સલાહ લો.",
            ),
        },
    },
}


def get_clinical_guidance(
    canonical_name: Optional[str],
    test_name: str,
    value: Optional[float],
    value_text: Optional[str],
    unit: Optional[str],
    classification: Optional[str],
    reference_low: Optional[float],
    reference_high: Optional[float],
    language: str = "en",
) -> Tuple[str, str, str]:
    """
    Generate deterministic, patient-friendly clinical guidance for a laboratory test.

    Returns:
        Tuple of (alert_message, possible_health_implications, precautions_and_next_steps)
    """
    lang = language.lower() if language else "en"
    if lang not in {"en", "hi", "mr", "gu"}:
        lang = "en"

    status = (classification or "REQUIRES_REVIEW").upper()
    display_name = canonical_name or test_name or "Medical Test"
    val_str = f"{value}" if value is not None else (value_text or "Recorded Value")
    unit_str = f" {unit}" if unit else ""
    ref_str = (
        f"{reference_low} - {reference_high}{unit_str}"
        if reference_low is not None and reference_high is not None
        else "Clinical reference interval"
    )

    # 1. Exact canonical name match
    if canonical_name and canonical_name in CLINICAL_GUIDANCE:
        guidance_map = CLINICAL_GUIDANCE[canonical_name]
        if status in guidance_map:
            lang_dict = guidance_map[status]
            if lang in lang_dict:
                return lang_dict[lang]
            return lang_dict.get("en", lang_dict[next(iter(lang_dict))])

    # 2. Status-specific generic deterministic fallbacks
    if status == "LOW":
        if lang == "hi":
            return (
                f"{display_name} ({val_str}{unit_str}) सामान्य संदर्भ सीमा से कम है।",
                "कम स्तर पोषण संबंधी कमी, धीमी उत्पादन दर या विशिष्ट शारीरिक कारणों से हो सकता है।",
                "इस परिणाम पर अपने डॉक्टर से चर्चा करें और कारण जानने के लिए आवश्यक जांच करवाएं।",
            )
        elif lang == "mr":
            return (
                f"{display_name} ({val_str}{unit_str}) सामान्य पातळीपेक्षा कमी आहे.",
                "कमी प्रमाण पोषणाची कमतरता किंवा शारीरिक बदलांमुळे असू शकते.",
                "आपल्या डॉक्टरांशी चर्चा करा आणि आवश्यक तपासण्या करा.",
            )
        elif lang == "gu":
            return (
                f"{display_name} ({val_str}{unit_str}) સામાન્ય મર્યાદા કરતા ઓછું છે.",
                "ઓછું સ્તર પોષણની ઉણપ અથવા અન્ય શારીરિક કારણોથી હોઈ શકે છે.",
                "તમારા ડોક્ટર સાથે પરામર્શ કરો.",
            )
        return (
            f"{display_name} ({val_str}{unit_str}) is below the standard reference range ({ref_str}).",
            "A lower-than-normal value may indicate reduced production, increased loss, nutritional factors, or specific physiological variations.",
            "Discuss this result with your healthcare professional to evaluate possible causes and determine whether follow-up testing is advised.",
        )

    elif status == "HIGH":
        if lang == "hi":
            return (
                f"{display_name} ({val_str}{unit_str}) सामान्य सीमा से अधिक है।",
                "बढ़ा हुआ स्तर शरीर में तनाव, सूजन, या चयापचय में बदलाव का संकेत हो सकता है।",
                "अपने डॉक्टर से परामर्श लें और जीवनशैली व आहार में आवश्यक सुधार करें।",
            )
        elif lang == "mr":
            return (
                f"{display_name} ({val_str}{unit_str}) सामान्य पातळीपेक्षा जास्त आहे.",
                "वाढलेली पातळी शरीरातील सूज किंवा चयापचयातील बदलांचे लक्षण असू शकते.",
                "डॉक्टरांचा सल्ला घ्या आणि योग्य जीवनशैलीचे पालन करा.",
            )
        elif lang == "gu":
            return (
                f"{display_name} ({val_str}{unit_str}) સામાન્ય મર્યાદા કરતા વધારે છે.",
                "વધારે સ્તર સોજો અથવા મેટાબોલિક ફેરફારો દર્શાવી શકે છે.",
                "ડોક્ટરની સલાહ લો અને આહારમાં ફેરફાર કરો.",
            )
        return (
            f"{display_name} ({val_str}{unit_str}) is above the normal reference threshold ({ref_str}).",
            "An elevated level may point to increased metabolic demand, inflammation, or organ-specific physiological response.",
            "Consult your physician for clinical correlation. Avoid self-diagnosis or unprescribed adjustments.",
        )

    elif status == "CRITICAL":
        if lang == "hi":
            return (
                f"गंभीर चेतावनी: {display_name} ({val_str}{unit_str}) अत्यधिक गंभीर स्तर पर है।",
                "गंभीर असामान्य स्तर से तीव्र स्वास्थ्य समस्याएं हो सकती हैं।",
                "तुरंत चिकित्सकीय सहायता लें। कृपया तुरंत अपने डॉक्टर या नजदीकी अस्पताल से संपर्क करें।",
            )
        elif lang == "mr":
            return (
                f"तातडीचा इशारा: {display_name} ({val_str}{unit_str}) धोकादायक पातळीवर आहे.",
                "अत्यंत असामान्य प्रमाणामुळे तीव्र आरोग्य समस्या उद्भवू शकतात.",
                "त्वरित वैद्यकीय सल्ला घ्या किंवा जवळच्या रुग्णालयात जा.",
            )
        elif lang == "gu":
            return (
                f"તાત્કાલિક ચેતવણી: {display_name} ({val_str}{unit_str}) ગંભીર સ્તરે છે.",
                "અત્યંત અસામાન્ય સ્તરથી ગંભીર જોખમ થઈ શકે છે.",
                "તાત્કાલિક ડોક્ટર અથવા હોસ્પિટલ પહોંચો.",
            )
        return (
            f"CRITICAL ALERT: {display_name} ({val_str}{unit_str}) is in the critical alert zone ({ref_str}).",
            "Critically abnormal values can lead to acute physiological instability if left unaddressed.",
            "Immediate medical evaluation is recommended. Please contact your treating clinician or urgent care without delay.",
        )

    elif status == "NORMAL":
        if lang == "hi":
            return (
                f"{display_name} ({val_str}{unit_str}) सामान्य संदर्भ सीमा में है।",
                "यह परीक्षण के समय इस बायोमार्कर के लिए सामान्य शारीरिक कार्यप्रणाली को दर्शाता है।",
                "स्वस्थ जीवनशैली बनाए रखें और नियमित वार्षिक स्वास्थ्य जांच जारी रखें।",
            )
        elif lang == "mr":
            return (
                f"{display_name} ({val_str}{unit_str}) सामान्य मर्यादेत आहे.",
                "हे शरीरातील सामान्य कार्यप्रणाली दर्शवते.",
                "नियमित व्यायाम, चांगला आहार आणि वेळोवेळी आरोग्य तपासणी सुरू ठेवा.",
            )
        elif lang == "gu":
            return (
                f"{display_name} ({val_str}{unit_str}) સામાન્ય મર્યાદામાં છે.",
                "આ સામાન્ય શારીરિક કાર્ય દર્શાવે છે.",
                "સ્વસ્થ જીવનશૈલી અને નિયમિત તપાસ ચાલુ રાખો.",
            )
        return (
            f"{display_name} ({val_str}{unit_str}) is within the normal expected reference range ({ref_str}).",
            "Indicates normal physiological baseline for this parameter at the time of testing.",
            "Continue standard healthy lifestyle habits and regular periodic wellness checkups.",
        )

    # 3. REQUIRES REVIEW or unclassified
    if lang == "hi":
        return (
            f"{display_name} ({val_str}) की संदर्भ सीमा से सीधी तुलना नहीं हो सकी।",
            "सटीक मूल्यांकन के लिए प्रयोगशाला की अपनी संदर्भ सीमा और विधि की जांच आवश्यक है।",
            "मूल रिपोर्ट की जांच करें और अपने डॉक्टर या प्रयोगशाला से पुष्टि करें।",
        )
    elif lang == "mr":
        return (
            f"{display_name} ({val_str}) चे वर्गीकरण करता आले नाही.",
            "सविस्तर माहितीसाठी प्रयोगशाळेच्या मूळ संदर्भ मर्यादेची तपासणी आवश्यक आहे.",
            "मूळ अहवाल तपासा आणि आपल्या डॉक्टरांचा सल्ला घ्या.",
        )
    elif lang == "gu":
        return (
            f"{display_name} ({val_str}) નું સામાન્ય વર્ગીકરણ થઈ શક્યું નથી.",
            "લેબોરેટરીના ચોક્કસ સંદર્ભ સાથે સરખામણી કરવી જરૂરી છે.",
            "મૂળ રિપોર્ટ જુઓ અને ડોક્ટરની સલાહ લો.",
        )
    return (
        f"{display_name} ({val_str}) requires clinical review against original laboratory reference ranges.",
        "Clinical significance depends on specific laboratory methodology, specimen collection timing, and individual medical history.",
        "Check original laboratory report for lab-specific reference ranges and consult your doctor for verification.",
    )
