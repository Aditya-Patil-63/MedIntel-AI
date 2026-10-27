"""
MedIntel AI — Prescription & Medicine Explainer Service.

Objective 2: Helping patients understand what the doctor has prescribed,
including the medicines, their purpose, and how they should be taken.

Features:
- Deterministic extraction and parsing of prescription text, medication lines, dosage, and schedules.
- Robust header and doctor advice filtering to separate doctor advice from prescribed medications.
- Comprehensive audited clinical pharmaceutical dictionary covering 40+ core outpatient medications
  and common Indian brand names (Metformin, Telmisartan, Amlodipine, Atorvastatin, Pantoprazole,
  Augmentin, Paracetamol/Dolo, Azithromycin, Levocetirizine/Montair, Thyronorm, Shelcal, etc.).
- Multilingual translations for English, Hindi, Marathi, and Gujarati.
- Exact table schema alignment (Medicine Name, Purpose, Dosage, When to Take).
- Safety guardrails: Uncatalogued or ambiguous extractions flag pharmacist/doctor confirmation.
- Gemini integration must NOT override doctor's instructions.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas.prescription import (
    MANDATORY_PRESCRIPTION_DISCLAIMER,
    PrescribedMedicineItem,
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)

logger = logging.getLogger("medintel.prescription_service")


# ---------------------------------------------------------------------------
# Audited Clinical Knowledge Base of Common Medications (40+ Drugs & Brands)
# ---------------------------------------------------------------------------

CLINICAL_DRUG_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    # 1. Diabetes
    "metformin": {
        "aliases": ["metformin", "glycomet", "glucophage"],
        "generic": "Metformin Hydrochloride",
        "default_dosage": "500 mg Tablet",
        "classes": "Anti-diabetic (Biguanide)",
        "purpose": {
            "english": "Controls blood sugar levels and improves body's sensitivity to insulin in type 2 diabetes.",
            "hindi": "टाइप 2 मधुमेह में रक्त शर्करा (ब्लड शुगर) को नियंत्रित करने और इंसुलिन संवेदनशीलता सुधारने के लिए उपयोग किया जाता है।",
            "marathi": "टाइप २ मधुमेहामध्ये रक्तातील साखर (ब्लड शुगर) नियंत्रित करण्यासाठी आणि इन्सुलिनची कार्यक्षमता वाढवण्यासाठी वापरले जाते.",
            "gujarati": "ટાઇપ 2 ડાયાબિટીસમાં બ્લડ સુગરને નિયંત્રિત કરવા અને ઇન્સ્યુલિન કાર્યક્ષમતા સુધારવા માટે વપરાય છે.",
        },
        "when_to_take": {
            "english": "With or immediately after meals (Twice daily)",
            "hindi": "भोजन के साथ या भोजन के तुरंत बाद (दिन में दो बार)",
            "marathi": "जेवणासोबत किंवा जेवणानंतर लगेच (दिवसातून दोन वेळा)",
            "gujarati": "જમવાની સાથે અથવા જમ્યા પછી તરત જ (દિવસમાં બે વાર)",
        },
        "schedule": {
            "english": "Twice daily (Morning & Night) — Taken with or immediately after meals.",
            "hindi": "दिन में दो बार (सुबह और रात) — भोजन के साथ या भोजन के तुरंत बाद लें।",
            "marathi": "दिवसातून दोन वेळा (सकाळी आणि रात्री) — जेवणासोबत किंवा जेवणानंतर लगेच घ्या.",
            "gujarati": "દિવસમાં બે વાર (સવાર અને સાંજ) — જમવાની સાથે અથવા જમ્યા પછી તરત જ લો.",
        },
        "instructions": {
            "english": "Swallow whole with a full glass of water. Do not skip meals while taking this medication. Avoid excess alcohol.",
            "hindi": "एक गिलास पानी के साथ पूरी गोली निगलें। दवा लेते समय भोजन न छोड़ें। अधिक शराब के सेवन से बचें।",
            "marathi": "पाण्यासोबत गोळी पूर्ण गिळा. ही गोळी घेताना जेवण चुकवू नका. जास्त मद्यपान टाळा.",
            "gujarati": "પાણી સાથે આખી ગોળી ગળી જાઓ. દવા લેતી વખતે ભોજન ન છોડો. વધુ પડતો દારૂ પીવાનું ટાળો.",
        },
        "precautions": "Inform your doctor if you experience persistent nausea, severe stomach upset, or extreme fatigue.",
    },
    "glimepiride": {
        "aliases": ["glimepiride", "amaryl", "zoryl"],
        "generic": "Glimepiride",
        "default_dosage": "1 mg / 2 mg Tablet",
        "classes": "Anti-diabetic (Sulfonylurea)",
        "purpose": {
            "english": "Helps the pancreas release more insulin to lower high blood glucose levels.",
            "hindi": "रक्त शर्करा कम करने के लिए अग्न्याशय से अधिक इंसुलिन स्रावित करने में मदद करता है।",
            "marathi": "रक्तातील साखर कमी करण्यासाठी स्वादुपिंडातून अधिक इन्सुलिन तयार करण्यास मदत करते.",
            "gujarati": "બ્લડ સુગર ઘટાડવા માટે સ્વાદુપિંડમાંથી વધુ ઇન્સ્યુલિન ઉત્પન્ન કરવામાં મદદ કરે છે.",
        },
        "when_to_take": {
            "english": "Just before or with breakfast (Morning)",
            "hindi": "नाश्ते से ठीक पहले या नाश्ते के साथ (सुबह)",
            "marathi": "नाश्त्याच्या आधी किंवा नाश्त्यासोबत (सकाळी)",
            "gujarati": "નાસ્તાની તરત પહેલાં અથવા નાસ્તા સાથે (સવારે)",
        },
        "schedule": {
            "english": "Once daily (Morning) — Take just before or with breakfast.",
            "hindi": "दिन में एक बार (सुबह) — नाश्ते से ठीक पहले या नाश्ते के साथ लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — नाश्त्याच्या आधी किंवा नाश्त्यासोबत घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — નાસ્તાની તરત પહેલાં અથવા નાસ્તા સાથે લો.",
        },
        "instructions": {
            "english": "Take at the exact same time every morning. Always keep glucose sweets or candy nearby in case you feel dizzy or shaky.",
            "hindi": "रोज सुबह एक ही समय पर लें। चक्कर या घबराहट होने पर तुरंत खाने के लिए मीठी कैंडी पास रखें।",
            "marathi": "दररोज सकाळी एकाच वेळी घ्या. चक्कर किंवा थरथर जाणवल्यास खाण्यासाठी गोड पदार्थ जवळ ठेवा.",
            "gujarati": "રોજ સવારે એક જ સમયે લો. ચક્કર કે ધ્રૂજારી આવે તો ખાવા માટે મીઠાઈ કે કેન્ડી સાથે રાખો.",
        },
        "precautions": "Risk of low blood sugar (hypoglycemia) if meals are skipped.",
    },
    "dapagliflozin": {
        "aliases": ["dapagliflozin", "forxiga", "oxra", "dapa"],
        "generic": "Dapagliflozin (SGLT2 Inhibitor)",
        "default_dosage": "10 mg Tablet",
        "classes": "Anti-diabetic & Cardiorenal Protector",
        "purpose": {
            "english": "Removes excess blood sugar through urine and protects kidneys and heart function.",
            "hindi": "पेशाब के माध्यम से अतिरिक्त रक्त शर्करा को बाहर निकालता है और गुर्दे तथा हृदय की कार्यप्रणाली की रक्षा करता है।",
            "marathi": "मूत्रावाटे जास्तीची साखर बाहेर टाकते आणि मूत्रपिंड व हृदयाच्या आरोग्याचे रक्षण करते.",
            "gujarati": "પેશાબ દ્વારા વધારાની ખાંડ બહાર કાઢે છે અને કિડની તથા હૃદયને રક્ષણ આપે છે.",
        },
        "when_to_take": {
            "english": "Once daily in the morning with or without food",
            "hindi": "सुबह एक बार भोजन के साथ या बिना भोजन के",
            "marathi": "सकाळी एकदा जेवणासोबत किंवा जेवणाशिवाय",
            "gujarati": "સવારે એક વાર જમ્યા સાથે અથવા જમ્યા વગર",
        },
        "schedule": {
            "english": "Once daily (Morning) — With or without meals.",
            "hindi": "दिन में एक बार (सुबह) — भोजन के साथ या बिना भोजन के लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — जेवणासोबत किंवा जेवणाशिवाय घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — જમ્યા સાથે અથવા જમ્યા વગર લો.",
        },
        "instructions": {
            "english": "Drink adequate water throughout the day to avoid dehydration and maintain genital hygiene.",
            "hindi": "दिन भर पर्याप्त पानी पिएं ताकि निर्जलीकरण (डिहाइड्रेशन) न हो।",
            "marathi": "डिहायड्रेशन टाळण्यासाठी दिवसभरात भरपूर पाणी प्या.",
            "gujarati": "ડિહાઇડ્રેશન ટાળવા માટે દિવસ દરમિયાન પૂરતું પાણી પીવો.",
        },
        "precautions": "Monitor for symptoms of urinary tract infections or excessive thirst.",
    },
    "vildagliptin": {
        "aliases": ["vildagliptin", "galvus", "jalra"],
        "generic": "Vildagliptin (DPP-4 Inhibitor)",
        "default_dosage": "50 mg Tablet",
        "classes": "Anti-diabetic (DPP-4 Inhibitor)",
        "purpose": {
            "english": "Stimulates the pancreas to produce insulin after meals and reduces glucagon production.",
            "hindi": "भोजन के बाद इंसुलिन उत्पादन बढ़ाने और ग्लूकोज स्तर को नियंत्रित करने में मदद करता है।",
            "marathi": "जेवणानंतर इन्सुलिन तयार करण्यास मदत करते आणि रक्तातील साखर नियंत्रित ठेवते.",
            "gujarati": "જમ્યા પછી ઇન્સ્યુલિન ઉત્પાદન વધારવામાં મદદ કરે છે અને બ્લડ સુગર નિયંત્રિત રાખે છે.",
        },
        "when_to_take": {
            "english": "Once or twice daily with or after meals",
            "hindi": "दिन में एक या दो बार भोजन के साथ या भोजन के बाद",
            "marathi": "दिवसातून १ किंवा २ वेळा जेवणासोबत किंवा जेवणानंतर",
            "gujarati": "દિવસમાં 1 અથવા 2 વાર જમ્યા સાથે અથવા જમ્યા પછી",
        },
        "schedule": {
            "english": "Once or twice daily — Taken with or after meals.",
            "hindi": "दिन में 1 या 2 बार — भोजन के साथ या बाद में लें।",
            "marathi": "दिवसातून १ किंवा २ वेळा — जेवणासोबत किंवा जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં 1 અથવા 2 વાર — જમવાની સાથે અથવા જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "Swallow with water. Can be combined with metformin as prescribed.",
            "hindi": "पानी के साथ लें। डॉक्टर की सलाह अनुसार मेटफॉर्मिन के साथ भी ली जा सकती है।",
            "marathi": "पाण्यासोबत घ्या. डॉक्टरांच्या सल्ल्यानुसार मेटफॉर्मिनसोबत घेता येते.",
            "gujarati": "પાણી સાથે લો. ડૉક્ટરની સલાહ મુજબ અન્ય દવા સાથે લઈ શકાય.",
        },
        "precautions": "Periodic liver function testing may be advised by your physician.",
    },

    # 2. Hypertension & Cardiovascular
    "amlodipine": {
        "aliases": ["amlodipine", "stamlo", "amlopres"],
        "generic": "Amlodipine Besylate",
        "default_dosage": "5 mg Tablet",
        "classes": "Antihypertensive (Calcium Channel Blocker)",
        "purpose": {
            "english": "Relaxes blood vessel walls to lower high blood pressure and reduce heart workload.",
            "hindi": "रक्त वाहिकाओं को शिथिल करके उच्च रक्तचाप (हाई बीपी) को कम करता है और हृदय का तनाव घटाता है।",
            "marathi": "रक्तवाहिन्या शिथिल करून उच्च रक्तदाब (हाय बीपी) नियंत्रित करते आणि हृदयाचा ताण कमी करते.",
            "gujarati": "રક્તવાહિનીઓને રિલેક્સ કરીને હાઈ બ્લડ પ્રેશર ઘટાડે છે અને હૃદયનો તણાવ ઓછો કરે છે.",
        },
        "when_to_take": {
            "english": "Once daily with or without food (Morning or Evening)",
            "hindi": "दिन में एक बार भोजन के साथ या बिना भोजन के (सुबह या शाम)",
            "marathi": "दिवसातून एकदा जेवणासोबत किंवा जेवणाशिवाय (सकाळी किंवा संध्याकाळी)",
            "gujarati": "દિવસમાં એક વાર જમ્યા સાથે અથવા જમ્યા વગર (સવાર અથવા સાંજ)",
        },
        "schedule": {
            "english": "Once daily (Morning or Evening) — With or without food.",
            "hindi": "दिन में एक बार (सुबह या शाम) — भोजन के साथ या बिना भोजन के लें।",
            "marathi": "दिवसातून एकदा (सकाळी किंवा संध्याकाळी) — जेवणासोबत किंवा जेवणाशिवाय घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર અથવા સાંજ) — જમ્યા સાથે અથવા જમ્યા વગર લો.",
        },
        "instructions": {
            "english": "Take regularly at a fixed hour. Do not stop abruptly even if your blood pressure feels normal.",
            "hindi": "नियमित रूप से एक निश्चित समय पर लें। बीपी सामान्य लगने पर भी दवा अचानक बंद न करें।",
            "marathi": "दररोज एकाच ठराविक वेळी घ्या. रक्तदाब सामान्य वाटला तरीही औषध अचानक बंद करू नका.",
            "gujarati": "રોજ નિયત સમયે લો. બ્લડ પ્રેશર સામાન્ય લાગે તો પણ અચાનક દવા બંધ ન કરશો.",
        },
        "precautions": "Mild ankle swelling or dizziness upon standing up quickly may occur initially.",
    },
    "telmisartan": {
        "aliases": ["telmisartan", "telma", "telmikind"],
        "generic": "Telmisartan",
        "default_dosage": "40 mg Tablet",
        "classes": "Antihypertensive (Angiotensin Receptor Blocker)",
        "purpose": {
            "english": "Lowers elevated blood pressure and protects kidneys and heart from hypertension damage.",
            "hindi": "उच्च रक्तचाप को कम करता है और गुर्दे तथा हृदय को हाइपरटेंशन के नुकसान से बचाता है।",
            "marathi": "उच्च रक्तदाब कमी करते आणि मूत्रपिंड (किडनी) व हृदयाचे उच्च दाबापासून रक्षण करते.",
            "gujarati": "હાઈ બ્લડ પ્રેશર ઘટાડે છે અને કિડની તથા હૃદયને નુકસાનથી સુરક્ષિત રાખે છે.",
        },
        "when_to_take": {
            "english": "Once daily in the morning with a glass of water",
            "hindi": "रोज सुबह एक गिलास पानी के साथ (दिन में एक बार)",
            "marathi": "दररोज सकाळी एक ग्लास पाण्यासोबत (दिवसातून एकदा)",
            "gujarati": "રોજ સવારે એક ગ્લાસ પાણી સાથે (દિવસમાં એક વાર)",
        },
        "schedule": {
            "english": "Once daily (Morning) — Taken with a glass of water.",
            "hindi": "दिन में एक बार (सुबह) — एक गिलास पानी के साथ लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — एक ग्लास पाण्यासोबत घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — એક ગ્લાસ પાણી સાથે લો.",
        },
        "instructions": {
            "english": "Drink adequate water throughout the day. Check your blood pressure weekly.",
            "hindi": "दिन भर पर्याप्त पानी पिएं। सप्ताह में एक बार अपने रक्तचाप की जांच करें।",
            "marathi": "दिवसभरात पुरेसे पाणी प्या. आठवड्यातून एकदा रक्तदाब तपासा.",
            "gujarati": "દિવસ દરમિયાન પૂરતું પાણી પીવો. અઠવાડિયામાં એકવાર બ્લડ પ્રેશર માપો.",
        },
        "precautions": "Do not take potassium supplements without consulting your prescribing doctor.",
    },
    "losartan": {
        "aliases": ["losartan", "losar", "cozaar"],
        "generic": "Losartan Potassium",
        "default_dosage": "50 mg Tablet",
        "classes": "Antihypertensive (ARB)",
        "purpose": {
            "english": "Lowers blood pressure, relaxes blood vessels, and reduces risk of stroke in hypertensive patients.",
            "hindi": "रक्तचाप कम करता है, धमनियों को शिथिल करता है और स्ट्रोक के जोखिम को घटाता है।",
            "marathi": "रक्तदाब कमी करते, रक्तवाहिन्या मोकळ्या करते आणि पक्षाघाताचा (स्ट्रोक) धोका कमी करते.",
            "gujarati": "બ્લડ પ્રેશર ઘટાડે છે, નળીઓને રિલેક્સ કરે છે અને સ્ટ્રોકનું જોખમ ઓછું કરે છે.",
        },
        "when_to_take": {
            "english": "Once daily with or without food (Morning)",
            "hindi": "दिन में एक बार भोजन के साथ या बिना भोजन के (सुबह)",
            "marathi": "दिवसातून एकदा जेवणासोबत किंवा जेवणाशिवाय (सकाळी)",
            "gujarati": "દિવસમાં એક વાર જમ્યા સાથે અથવા જમ્યા વગર (સવારે)",
        },
        "schedule": {
            "english": "Once daily (Morning) — With or without meals.",
            "hindi": "दिन में एक बार (सुबह) — भोजन के साथ या बिना भोजन के लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — जेवणासोबत किंवा जेवणाशिवाय घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — જમ્યા સાથે અથવા જમ્યા વગર લો.",
        },
        "instructions": {
            "english": "Take at the same time each day. Avoid rising too fast from sitting positions.",
            "hindi": "रोज एक ही समय पर लें। अचानक तेजी से उठने से बचें।",
            "marathi": "दररोज एकाच वेळी घ्या. बसल्या जागेवरून एकदम उठणे टाळा.",
            "gujarati": "રોજ નિયત સમયે લો. બેઠા પછી અચાનક ઝડપથી ઊભા ન થવું.",
        },
        "precautions": "Do not combine with other salt substitutes containing potassium without physician approval.",
    },
    "atorvastatin": {
        "aliases": ["atorvastatin", "atorva", "lipitor", "atorlip"],
        "generic": "Atorvastatin Calcium",
        "default_dosage": "10 mg / 20 mg Tablet",
        "classes": "Lipid-lowering agent (Statin)",
        "purpose": {
            "english": "Lowers bad LDL cholesterol and triglycerides in blood while protecting arteries from plaque buildup.",
            "hindi": "रक्त में खराब एलडीएल कोलेस्ट्रॉल और ट्राइग्लिसराइड्स को कम करता है और धमनियों में रुकावट रोकता है।",
            "marathi": "रक्तातील वाईट कोलेस्ट्रॉल (LDL) कमी करते आणि रक्तवाहिन्यांमध्ये अडथळे (ब्लॉकेज) होण्यापासून रोखते.",
            "gujarati": "લોહીમાં ખરાબ કોલેસ્ટ્રોલ (LDL) ઘટાડે છે અને હૃદયની નળીઓમાં બ્લોકેજ થતું અટકાવે છે.",
        },
        "when_to_take": {
            "english": "At bedtime after dinner (Night)",
            "hindi": "रात को सोते समय भोजन के बाद (रात)",
            "marathi": "रात्री झोपताना जेवणानंतर (रात्री)",
            "gujarati": "રાત્રે સૂતી વખતે જમ્યા પછી (સાંજ/રાત્રે)",
        },
        "schedule": {
            "english": "Once daily at Night (Bedtime) — Taken after dinner.",
            "hindi": "दिन में एक बार रात को (सोते समय) — रात के भोजन के बाद लें।",
            "marathi": "दिवसातून एकदा रात्री (झोपताना) — रात्रीच्या जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં એક વાર રાત્રે (સૂતી વખતે) — રાત્રિના ભોજન પછી લો.",
        },
        "instructions": {
            "english": "Cholesterol synthesis peaks at night, so take this pill after dinner. Maintain a low-oil healthy diet.",
            "hindi": "शरीर में कोलेस्ट्रॉल निर्माण रात में अधिक होता है, इसलिए रात को लें। कम तेल वाला स्वस्थ आहार लें।",
            "marathi": "शरीरात कोलेस्ट्रॉल रात्री जास्त तयार होते, त्यामुळे रात्री घ्या. कमी तेलाचा पौष्टिक आहार ठेवा.",
            "gujarati": "શરીરમાં કોલેસ્ટ્રોલ રાત્રે વધુ બને છે, તેથી રાત્રે લો. ઓછા તેલવાળો પૌષ્ટિક આહાર રાખો.",
        },
        "precautions": "Report any unexplained muscle pain or extreme weakness to your doctor.",
    },
    "rosuvastatin": {
        "aliases": ["rosuvastatin", "rosuvas", "crestor", "rosave"],
        "generic": "Rosuvastatin Calcium",
        "default_dosage": "10 mg / 20 mg Tablet",
        "classes": "Potent Lipid-lowering agent (Statin)",
        "purpose": {
            "english": "Significantly lowers bad cholesterol (LDL) and prevents heart attacks and stroke.",
            "hindi": "खराब कोलेस्ट्रॉल (एलडीएल) को तेजी से घटाता है और दिल के दौरे (हार्ट अटैक) तथा स्ट्रोक से बचाता है।",
            "marathi": "वाईट कोलेस्ट्रॉल (LDL) मोठ्या प्रमाणावर कमी करते आणि हृदयविकाराचा झटका व पक्षाघातापासून बचाव करते.",
            "gujarati": "ખરાબ કોલેસ્ટ્રોલ ઘટાડે છે અને હાર્ટ અટેક તથા સ્ટ્રોકથી રક્ષણ આપે છે.",
        },
        "when_to_take": {
            "english": "Once daily at night after dinner",
            "hindi": "रात को भोजन के बाद (दिन में एक बार)",
            "marathi": "रात्री जेवणानंतर (दिवसातून एकदा)",
            "gujarati": "રાત્રે જમ્યા પછી (દિવસમાં એક વાર)",
        },
        "schedule": {
            "english": "Once daily at Night — Taken after dinner.",
            "hindi": "दिन में एक बार रात को — भोजन के बाद लें।",
            "marathi": "दिवसातून एकदा रात्री — जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં એક વાર રાત્રે — જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "Take whole with water. Avoid excess fatty, fried, or processed food.",
            "hindi": "पानी के साथ पूरी गोली लें। अधिक चिकनाई या तला-भुना खाना न खाएं।",
            "marathi": "पाण्यासोबत पूर्ण गोळी घ्या. तेलकट आणि तळलेले पदार्थ खाणे टाळा.",
            "gujarati": "પાણી સાથે આખી ગોળી લો. તેલવાળો અને તળેલો ખોરાક ટાળો.",
        },
        "precautions": "Notify physician if severe muscle cramps or unexplained brown urine develops.",
    },
    "aspirin": {
        "aliases": ["aspirin", "ecosprin", "disprin", "asa"],
        "generic": "Aspirin (Acetylsalicylic Acid)",
        "default_dosage": "75 mg / 150 mg Tablet",
        "classes": "Antiplatelet / Blood Thinner",
        "purpose": {
            "english": "Prevents blood platelets from clumping together to prevent blood clots, heart attack, and stroke.",
            "hindi": "रक्त के थक्के बनने से रोकता है (खून पतला करता है) ताकि हार्ट अटैक और स्ट्रोक से बचाव हो सके।",
            "marathi": "रक्ताच्या गुठळ्या होण्यास प्रतिबंध करते (रक्त पातळ करते) आणि हृदयविकाराचा झटका टाळते.",
            "gujarati": "લોહીની ગંઠાઈઓ બનતી અટકાવે છે (લોહી પાતળું કરે છે) અને હાર્ટ અટેકથી રક્ષણ આપે છે.",
        },
        "when_to_take": {
            "english": "Once daily immediately after lunch or dinner (with food)",
            "hindi": "भोजन के तुरंत बाद (दोपहर या रात के खाने के बाद)",
            "marathi": "जेवणानंतर लगेच (दुपारच्या किंवा रात्रीच्या जेवणानंतर)",
            "gujarati": "જમ્યા પછી તરત જ (બપોરના અથવા રાત્રિના ભોજન પછી)",
        },
        "schedule": {
            "english": "Once daily — Always take immediately AFTER meals with water.",
            "hindi": "दिन में एक बार — हमेशा भोजन के तुरंत बाद पानी के साथ लें।",
            "marathi": "दिवसातून एकदा — नेहमी जेवणानंतर लगेच पाण्यासोबत घ्या.",
            "gujarati": "દિવસમાં એક વાર — હંમેશા જમ્યા પછી તરત જ પાણી સાથે લો.",
        },
        "instructions": {
            "english": "NEVER take on an empty stomach to prevent gastric irritation. Swallow whole.",
            "hindi": "पेट में जलन से बचने के लिए इसे कभी खाली पेट न लें। पूरी गोली निगलें।",
            "marathi": "पोटातील जळजळ टाळण्यासाठी उपाशीपोटी कधीही घेऊ नका. गोळी पूर्ण गिळा.",
            "gujarati": "પેટમાં બળતરા ટાળવા માટે ક્યારેય ભૂખ્યા પેટે ન લેવી. આખી ગોળી ગળી જવી.",
        },
        "precautions": "Inform your dentist or surgeon that you take blood thinners before any procedure.",
    },
    "clopidogrel": {
        "aliases": ["clopidogrel", "clopilet", "plavix"],
        "generic": "Clopidogrel Bisulfate",
        "default_dosage": "75 mg Tablet",
        "classes": "Antiplatelet",
        "purpose": {
            "english": "Keeps blood flowing smoothly and prevents arterial clots in patients with heart stents or stroke risk.",
            "hindi": "धमनियों में खून का थक्का जमने से रोकता है, विशेषकर स्टेंट लगने के बाद या स्ट्रोक के जोखिम में।",
            "marathi": "धमन्यांमध्ये रक्ताची गुठळी होण्यापासून रोखते, विशेषतः हृदयविकार किंवा स्टेंट बसवल्यानंतर.",
            "gujarati": "હૃદયમાં સ્ટેન્ટ મૂક્યા પછી અથવા હાર્ટ અટેક પછી લોહીની ગંઠાઈ બનતી અટકાવે છે.",
        },
        "when_to_take": {
            "english": "Once daily with or after meals at a fixed time",
            "hindi": "भोजन के साथ या बाद में एक निश्चित समय पर (दिन में एक बार)",
            "marathi": "जेवणासोबत किंवा जेवणानंतर एकाच ठराविक वेळी (दिवसातून एकदा)",
            "gujarati": "જમ્યા સાથે અથવા જમ્યા પછી નિયત સમયે (દિવસમાં એક વાર)",
        },
        "schedule": {
            "english": "Once daily — Taken with or after meals.",
            "hindi": "दिन में एक बार — भोजन के साथ या बाद में लें।",
            "marathi": "दिवसातून एकदा — जेवणासोबत किंवा जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં એક વાર — જમ્યા સાથે અથવા જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "Take at the exact same hour every day. Do not discontinue without cardiologist approval.",
            "hindi": "रोजाना ठीक उसी समय लें। हृदय रोग विशेषज्ञ की सलाह के बिना बंद न करें।",
            "marathi": "दररोज एकाच वेळी घ्या. डॉक्टरांच्या सल्ल्याशिवाय बंद करू नका.",
            "gujarati": "રોજ એક જ સમયે લો. ડૉક્ટરની મંજૂરી વિના દવા બંધ ન કરો.",
        },
        "precautions": "Be cautious with sharp objects; easy bruising or minor bleeding may take longer to stop.",
    },
    "metoprolol": {
        "aliases": ["metoprolol", "betaloc", "metolar"],
        "generic": "Metoprolol Succinate / Tartrate",
        "default_dosage": "25 mg / 50 mg Tablet",
        "classes": "Antihypertensive & Antiarrhythmic (Beta Blocker)",
        "purpose": {
            "english": "Slows rapid heart rate, lowers blood pressure, and relieves chest pain (angina).",
            "hindi": "तेज दिल की धड़कन को सामान्य करता है, रक्तचाप कम करता है और सीने के दर्द से राहत देता है।",
            "marathi": "हृदयाचे जलद ठोके नियंत्रित करते, रक्तदाब कमी करते आणि छातीतील वेदना कमी करते.",
            "gujarati": "હૃદયના ઝડપી ધબકારા નિયંત્રિત કરે છે, બ્લડ પ્રેશર ઘટાડે છે અને છાતીના દુખાવામાં રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "Once or twice daily with or immediately after meals",
            "hindi": "दिन में एक या दो बार भोजन के तुरंत बाद",
            "marathi": "दिवसातून १ किंवा २ वेळा जेवणानंतर लगेच",
            "gujarati": "દિવસમાં 1 અથવા 2 વાર જમ્યા પછી તરત જ",
        },
        "schedule": {
            "english": "Once or twice daily — Taken with or immediately after food.",
            "hindi": "दिन में 1 या 2 बार — भोजन के साथ या तुरंत बाद लें।",
            "marathi": "दिवसातून १ किंवा २ वेळा — जेवणासोबत किंवा लगेच घ्या.",
            "gujarati": "દિવસમાં 1 અથવા 2 વાર — જમ્યા પછી તરત જ લો.",
        },
        "instructions": {
            "english": "Check your resting pulse rate regularly. Do not stop abruptly to avoid rebound high blood pressure.",
            "hindi": "नियमित रूप से अपनी नब्ज (पल्स) जांचें। इसे अचानक बंद न करें।",
            "marathi": "आपली नाडी (पल्स) नियमित तपासा. हे औषध अचानक बंद करू नका.",
            "gujarati": "તમારા પલ્સ રેટ નિયમિત માપો. અચાનક દવા બંધ કરશો નહીં.",
        },
        "precautions": "May mask signs of low blood sugar (such as rapid heart rate) in diabetic individuals.",
    },

    # 3. Gastrointestinal & Acidity
    "pantoprazole": {
        "aliases": ["pantoprazole", "pan", "pantocid", "pantodac"],
        "generic": "Pantoprazole Sodium",
        "default_dosage": "40 mg Tablet / Capsule",
        "classes": "Gastrointestinal (Proton Pump Inhibitor)",
        "purpose": {
            "english": "Reduces excess stomach acid to relieve heartburn, acidity, acid reflux, and prevent gastric ulcers.",
            "hindi": "पेट में अतिरिक्त एसिड को कम करके सीने में जलन, गैस, एसिडिटी और अल्सर से राहत दिलाता है।",
            "marathi": "पोटातील ॲसिड कमी करून छातीतील जळजळ, ॲसिडिटी, गॅस आणि अल्सरपासून आराम देतो.",
            "gujarati": "પેટમાં એસિડનું પ્રમાણ ઘટાડી છાતીમાં બળતરા, એસિડિટી અને અલ્સરથી રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "30 to 60 minutes before breakfast on empty stomach (Morning)",
            "hindi": "नाश्ते से 30 से 60 मिनट पहले खाली पेट (सुबह)",
            "marathi": "नाश्त्याच्या ३० ते ६० मिनिटे आधी उपाशीपोटी (सकाळी)",
            "gujarati": "નાસ્તાના 30 થી 60 મિનિટ પહેલાં ભૂખ્યા પેટે (સવારે)",
        },
        "schedule": {
            "english": "Once daily (Morning) — Take 30 to 60 minutes BEFORE breakfast on an empty stomach.",
            "hindi": "दिन में एक बार (सुबह) — नाश्ते से 30 से 60 मिनट पहले खाली पेट लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — नाश्त्याच्या ३० ते ६० मिनिटे आधी उपाशीपोटी घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — નાસ્તાના 30 થી 60 મિનિટ પહેલાં ભૂખ્યા પેટે લો.",
        },
        "instructions": {
            "english": "Must be taken on an empty stomach for maximum effectiveness. Swallow whole without crushing.",
            "hindi": "सर्वोत्तम परिणाम के लिए खाली पेट ही लें। गोली को चबाएं या तोड़ें नहीं, सीधे निगलें।",
            "marathi": "चांगल्या परिणामासाठी उपाशीपोटीच घ्या. गोळी चावू नका, थेट गिळा.",
            "gujarati": "સંપૂર્ણ અસર માટે ભૂખ્યા પેટે જ લો. ગોળી ચાવ્યા વિના સીધી ગળી જાઓ.",
        },
        "precautions": "Avoid very spicy or deep-fried food while recovering from gastritis.",
    },
    "omeprazole": {
        "aliases": ["omeprazole", "omez", "prilosec"],
        "generic": "Omeprazole",
        "default_dosage": "20 mg Capsule",
        "classes": "Antacid / Proton Pump Inhibitor",
        "purpose": {
            "english": "Lowers stomach acid secretion to treat gastric acid reflux, peptic ulcers, and dyspepsia.",
            "hindi": "पेट में एसिड के स्राव को कम करके एसिडिटी, पेट के छाले और अपच को ठीक करता है।",
            "marathi": "पोटातील आम्ल कमी करून ॲसिडिटी, अल्सर आणि अपचन यावर उपचार करते.",
            "gujarati": "પેટમાં એસિડનું પ્રમાણ ઘટાડી એસિડિટી, અલ્સર અને અપચામાં રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "30 minutes before morning meal on empty stomach",
            "hindi": "सुबह के भोजन से 30 मिनट पहले खाली पेट",
            "marathi": "सकाळच्या जेवणाआधी ३० मिनिटे उपाशीपोटी",
            "gujarati": "સવારના ભોજનના 30 મિનિટ પહેલાં ભૂખ્યા પેટે",
        },
        "schedule": {
            "english": "Once daily (Morning) — 30 minutes before breakfast.",
            "hindi": "दिन में एक बार (सुबह) — नाश्ते से 30 मिनट पहले लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — नाश्त्याच्या ३० मिनिटे आधी घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — નાસ્તાના 30 મિનિટ પહેલાં લો.",
        },
        "instructions": {
            "english": "Take with water before food. Do not chew the capsule beads.",
            "hindi": "भोजन से पहले पानी के साथ लें। कैप्सूल को चबाएं नहीं।",
            "marathi": "जेवणाआधी पाण्यासोबत घ्या. कॅप्सूल चावू नका.",
            "gujarati": "ભોજન પહેલાં પાણી સાથે લો. કેપ્સ્યુલ ચાવવી નહીં.",
        },
        "precautions": "Long-term unmonitored use should be discussed with your physician.",
    },
    "rabeprazole": {
        "aliases": ["rabeprazole", "razo", "happi", "parit"],
        "generic": "Rabeprazole Sodium",
        "default_dosage": "20 mg Tablet",
        "classes": "Proton Pump Inhibitor",
        "purpose": {
            "english": "Provides fast relief from acidity, heartburn, and stomach acid irritation.",
            "hindi": "एसिडिटी, सीने की जलन और पेट में गैस से तेजी से राहत दिलाता है।",
            "marathi": "ॲसिडिटी, छातीतील जळजळ आणि पोटातील गॅसपासून जलद आराम देतो.",
            "gujarati": "એસિડિટી, છાતીમાં બળતરા અને પેટના ગૅસમાંથી ઝડપી રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "Once daily before breakfast in the morning",
            "hindi": "सुबह नाश्ते से पहले खाली पेट (दिन में एक बार)",
            "marathi": "सकाळी नाश्त्यापूर्वी उपाशीपोटी (दिवसातून एकदा)",
            "gujarati": "સવારે નાસ્તા પહેલાં ભૂખ્યા પેટે (દિવસમાં એક વાર)",
        },
        "schedule": {
            "english": "Once daily (Morning) — On empty stomach.",
            "hindi": "दिन में एक बार (सुबह) — खाली पेट लें।",
            "marathi": "दिवसातून एकदा (सकाळी) — उपाशीपोटी घ्या.",
            "gujarati": "દિવસમાં એક વાર (સવાર) — ભૂખ્યા પેટે લો.",
        },
        "instructions": {
            "english": "Swallow whole with plain water 30 minutes prior to eating.",
            "hindi": "खाने से 30 मिनट पहले सादे पानी के साथ सीधे निगलें।",
            "marathi": "खाण्यापूर्वी ३० मिनिटे साध्या पाण्यासोबत गिळा.",
            "gujarati": "જમવાના 30 મિનિટ પહેલાં સાદા પાણી સાથે ગળી જાઓ.",
        },
        "precautions": "Avoid late-night heavy meals to minimize nocturnal acid reflux.",
    },
    "domperidone": {
        "aliases": ["domperidone", "vomistop", "motilium"],
        "generic": "Domperidone",
        "default_dosage": "10 mg Tablet / Syrup",
        "classes": "Antiemetic & Prokinetic",
        "purpose": {
            "english": "Relieves nausea, vomiting, feeling of fullness, and promotes healthy stomach emptying.",
            "hindi": "उल्टी, मतली, पेट भारी लगना और अपच से राहत दिलाता है।",
            "marathi": "मळमळ, उलट्या, पोट फुगणे आणि अपचन यावर आराम देतो.",
            "gujarati": "ઉબકા, ઉલટી, પેટ ભારે લાગવું અને અપચામાં રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "15 to 30 minutes before meals (Twice or thrice daily)",
            "hindi": "भोजन से 15 से 30 मिनट पहले (दिन में दो या तीन बार)",
            "marathi": "जेवणाच्या १५ ते ३० मिनिटे आधी (दिवसातून २ किंवा ३ वेळा)",
            "gujarati": "જમવાના 15 થી 30 મિનિટ પહેલાં (દિવસમાં 2 અથવા 3 વાર)",
        },
        "schedule": {
            "english": "Before meals (15–30 min prior) — Maximum 3 times daily.",
            "hindi": "भोजन से 15-30 मिनट पहले लें — दिन में अधिकतम 3 बार।",
            "marathi": "जेवणाच्या १५-३० मिनिटे आधी घ्या — दिवसातून जास्तीत जास्त ३ वेळा.",
            "gujarati": "જમવાના 15-30 મિનિટ પહેલાં લો — દિવસમાં વધુમાં વધુ 3 વાર.",
        },
        "instructions": {
            "english": "Take prior to food so it activates gut motility before meal reaches stomach.",
            "hindi": "भोजन से पहले ही लें ताकि यह भोजन पचने में मदद कर सके।",
            "marathi": "जेवणापूर्वीच घ्या जेणेकरून अन्न पचण्यास मदत होईल.",
            "gujarati": "જમ્યા પહેલાં જ લો જેથી પાચનમાં મદદ મળે.",
        },
        "precautions": "Inform physician if you have underlying heart rhythm concerns.",
    },

    # 4. Pain & Fever
    "paracetamol": {
        "aliases": ["paracetamol", "crocin", "dolo", "calpol", "pcm"],
        "generic": "Paracetamol / Acetaminophen",
        "default_dosage": "500 mg / 650 mg Tablet",
        "classes": "Analgesic & Antipyretic (Pain & Fever Reliever)",
        "purpose": {
            "english": "Relieves mild to moderate pain (headache, body ache) and reduces elevated body temperature (fever).",
            "hindi": "हल्के से मध्यम दर्द (सिरदर्द, बदन दर्द) से राहत देता है और बुखार को कम करता है।",
            "marathi": "डोकेदुखी, अंगदुखी यांसारख्या वेदना कमी करते आणि ताप कमी करण्यासाठी उपयोगी आहे.",
            "gujarati": "માથાનો દુખાવો, શરીરનો દુખાવો ઓછો કરે છે અને તાવ ઘટાડે છે.",
        },
        "when_to_take": {
            "english": "After food as needed for fever or pain (Every 6–8 hours)",
            "hindi": "बुखार या दर्द होने पर भोजन के बाद (हर 6 से 8 घंटे में)",
            "marathi": "ताप किंवा वेदना असल्यास जेवणानंतर (दर ६ ते ८ तासांनी)",
            "gujarati": "તાવ કે દુખાવો હોય ત્યારે જમ્યા પછી (દર 6 થી 8 કલાકે)",
        },
        "schedule": {
            "english": "As needed (SOS) or every 6–8 hours after food — Maximum 3 to 4 times per day.",
            "hindi": "आवश्यकतानुसार (SOS) या भोजन के बाद हर 6 से 8 घंटे में — दिन में अधिकतम 3 से 4 बार।",
            "marathi": "गरज असेल तेव्हा (SOS) किंवा जेवणानंतर दर ६ ते ८ तासांनी — दिवसातून जास्तीत जास्त ३ ते ४ वेळा.",
            "gujarati": "જરૂર પડે ત્યારે (SOS) અથવા જમ્યા પછી દર 6 થી 8 કલાકે — દિવસમાં વધુમાં વધુ 3 થી 4 વખત.",
        },
        "instructions": {
            "english": "Always take after food with water. Do not exceed 4,000 mg in 24 hours to protect your liver.",
            "hindi": "हमेशा भोजन के बाद पानी के साथ लें। लिवर की सुरक्षा के लिए 24 घंटे में 4000 मिलीग्राम से अधिक न लें।",
            "marathi": "नेहमी जेवणानंतर पाण्यासोबत घ्या. यकृताच्या (लिव्हर) आरोग्यासाठी २४ तासांत ४००० मि.ग्रॅ. पेक्षा जास्त घेऊ नका.",
            "gujarati": "હંમેશા જમ્યા પછી પાણી સાથે લો. લિવરની સુરક્ષા માટે 24 કલાકમાં 4000 મિલિગ્રામથી વધુ ન લો.",
        },
        "precautions": "Do not combine with other cold/cough medications that already contain paracetamol.",
    },
    "ibuprofen": {
        "aliases": ["ibuprofen", "brufen", "advil"],
        "generic": "Ibuprofen",
        "default_dosage": "400 mg Tablet",
        "classes": "NSAID (Anti-inflammatory & Pain Reliever)",
        "purpose": {
            "english": "Reduces swelling, inflammation, dental pain, arthritis, and muscular discomfort.",
            "hindi": "सूजन, जोड़ों का दर्द, दांत दर्द और मांसपेशियों के दर्द को कम करता है।",
            "marathi": "सूज, सांधेदुखी, दातदुखी आणि स्नायूंच्या वेदना कमी करण्यासाठी वापरले जाते.",
            "gujarati": "સોજો, સાંધાનો દુખાવો, દાંતનો દુખાવો અને સ્નાયુઓના દુખાવામાં રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "Strictly after meals with a glass of water",
            "hindi": "भोजन के बाद एक गिलास पानी के साथ",
            "marathi": "जेवणानंतर एक ग्लास पाण्यासोबत",
            "gujarati": "જમ્યા પછી એક ગ્લાસ પાણી સાથે",
        },
        "schedule": {
            "english": "Twice or thrice daily after food — Never on empty stomach.",
            "hindi": "दिन में 2 से 3 बार भोजन के बाद — कभी खाली पेट न लें।",
            "marathi": "दिवसातून २ ते ३ वेळा जेवणानंतर — कधीही उपाशीपोटी घेऊ नका.",
            "gujarati": "દિવસમાં 2 થી 3 વાર જમ્યા પછી — ક્યારેય ભૂખ્યા પેટે ન લો.",
        },
        "instructions": {
            "english": "Always take with food or milk to safeguard stomach lining.",
            "hindi": "पेट की सुरक्षा के लिए हमेशा भोजन या दूध के साथ लें।",
            "marathi": "पोटाच्या संरक्षणासाठी नेहमी अन्नासोबत किंवा दुधासोबत घ्या.",
            "gujarati": "પેટની સુરક્ષા માટે હંમેશા ખોરાક કે દૂધ સાથે લો.",
        },
        "precautions": "Avoid if you have history of peptic ulcers or severe kidney disease.",
    },
    "aceclofenac": {
        "aliases": ["aceclofenac", "zerodol", "hifenac"],
        "generic": "Aceclofenac",
        "default_dosage": "100 mg Tablet",
        "classes": "NSAID (Pain & Joint Inflammation Reliever)",
        "purpose": {
            "english": "Relieves acute pain and inflammation in arthritis, backache, and sports injuries.",
            "hindi": "गठिया, पीठ दर्द, और चोट के तेज दर्द व सूजन से राहत दिलाता है।",
            "marathi": "संधिवात, पाठदुखी आणि दुखापतीच्या तीव्र वेदना व सूज कमी करते.",
            "gujarati": "સાંધાનો દુખાવો, કમરનો દુખાવો અને સોજો ઘટાડવામાં ઝડપી રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "Twice daily after meals (Morning & Night)",
            "hindi": "भोजन के बाद दिन में दो बार (सुबह और रात)",
            "marathi": "जेवणानंतर दिवसातून दोन वेळा (सकाळी आणि रात्री)",
            "gujarati": "જમ્યા પછી દિવસમાં બે વાર (સવાર અને સાંજ)",
        },
        "schedule": {
            "english": "Twice daily — Strictly after breakfast and dinner.",
            "hindi": "दिन में दो बार — नाश्ते और रात के खाने के बाद लें।",
            "marathi": "दिवसातून दोन वेळा — नाश्त्यानंतर आणि जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં બે વાર — નાસ્તા અને જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "Drink adequate water. Can be combined with an antacid (e.g. Pantoprazole) if advised.",
            "hindi": "भरपूर पानी पिएं। एसिडिटी से बचने के लिए एंटासिड के साथ ले सकते हैं।",
            "marathi": "पुरेसे पाणी प्या. ॲसिडिटी टाळण्यासाठी गॅसच्या गोळीसोबत घेण्याचा सल्ला दिला जातो.",
            "gujarati": "પૂરતું પાણી પીવો. એસિડિટીથી બચવા માટે એન્ટાસિડ સાથે લઈ શકાય.",
        },
        "precautions": "Take for the shortest duration necessary for pain relief.",
    },

    # 5. Antibiotics
    "amoxicillin": {
        "aliases": ["amoxicillin", "mox", "novamox"],
        "generic": "Amoxicillin",
        "default_dosage": "500 mg Capsule / Tablet",
        "classes": "Antibiotic (Penicillin group)",
        "purpose": {
            "english": "Treats bacterial infections of throat, chest, ear, sinus, and urinary tract.",
            "hindi": "गले, फेफड़ों, कान, साइनस और मूत्र मार्ग के जीवाणु संक्रमण (बैक्टीरियल इन्फेक्शन) का इलाज करता है।",
            "marathi": "घसा, छाती, कान, सायनस आणि मूत्राशयाच्या जिवाणू संसर्गावर (बॅक्टेरियल इन्फेक्शन) उपचार करते.",
            "gujarati": "ગળા, છાતી, કાન, સાઇનસ અને પેશાબના બેક્ટેરિયલ ઇન્ફેક્શનની સારવાર કરે છે.",
        },
        "when_to_take": {
            "english": "With or after meals at fixed intervals (Twice or thrice daily)",
            "hindi": "भोजन के साथ या बाद में निश्चित समय पर (दिन में 2 या 3 बार)",
            "marathi": "जेवणासोबत किंवा जेवणानंतर ठराविक वेळी (दिवसातून २ किंवा ३ वेळा)",
            "gujarati": "જમવાની સાથે અથવા પછી નિયત સમયે (દિવસમાં 2 અથવા 3 વાર)",
        },
        "schedule": {
            "english": "Twice or thrice daily at fixed intervals (e.g., every 8 or 12 hours) — Taken with or after meals.",
            "hindi": "निश्चित अंतराल पर दिन में दो या तीन बार — भोजन के साथ या बाद में लें।",
            "marathi": "ठराविक अंतराने दिवसातून २ किंवा ३ वेळा — जेवणासोबत किंवा जेवणानंतर घ्या.",
            "gujarati": "નિયત સમયે દિવસમાં બે અથવા ત્રણ વાર — જમવાની સાથે અથવા જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "CRITICAL: Complete the full 5 to 7 day course prescribed by your doctor even if you feel completely fine.",
            "hindi": "महत्वपूर्ण: ठीक महसूस होने पर भी डॉक्टर द्वारा लिखा गया 5 से 7 दिनों का पूरा कोर्स अवश्य समाप्त करें।",
            "marathi": "महत्त्वाचे: बरे वाटले तरीही डॉक्टरांनी दिलेला ५ ते ७ दिवसांचा संपूर्ण कोर्स पूर्ण करा.",
            "gujarati": "મહત્વપૂર્ણ: સારું લાગે તો પણ ડૉક્ટરે લખેલો 5 થી 7 દિવસનો આખો કોર્સ પૂર્ણ કરો.",
        },
        "precautions": "Inform doctor immediately if you develop skin rash, swelling, or severe watery diarrhea.",
    },
    "augmentin": {
        "aliases": ["augmentin", "amoxyclav", "moxikind-cv", "clavulanate"],
        "generic": "Amoxicillin + Potassium Clavulanate",
        "default_dosage": "625 mg Tablet",
        "classes": "Broad-spectrum Antibiotic",
        "purpose": {
            "english": "Overcomes bacterial antibiotic resistance to treat resistant respiratory, skin, and dental infections.",
            "hindi": "प्रतिरोधी बैक्टीरिया को नष्ट करके फेफड़ों, त्वचा, दांत और कान के गंभीर संक्रमण को ठीक करता है।",
            "marathi": "प्रतिकार करणाऱ्या जिवाणूंचा नाश करून फुफ्फुसे, त्वचा आणि दातांच्या संसर्गावर मात करते.",
            "gujarati": "ફેફસાં, ચામડી, દાંત અને કાનના ગંભીર બેક્ટેરિયલ ઇન્ફેક્શનને અસરકારક રીતે મટાડે છે.",
        },
        "when_to_take": {
            "english": "At the start of a meal with water (Twice daily)",
            "hindi": "भोजन शुरू करते समय पानी के साथ (दिन में दो बार)",
            "marathi": "जेवण सुरू करताना पाण्यासोबत (दिवसातून दोन वेळा)",
            "gujarati": "જમવાની શરૂઆતમાં પાણી સાથે (દિવસમાં બે વાર)",
        },
        "schedule": {
            "english": "Twice daily (Every 12 hours) — Take at the start of a meal to optimize absorption and reduce stomach upset.",
            "hindi": "दिन में दो बार (हर 12 घंटे में) — पेट की खराबी से बचने के लिए भोजन के आरंभ में लें।",
            "marathi": "दिवसातून दोन वेळा (दर १२ तासांनी) — पोटाचा त्रास टाळण्यासाठी जेवणाच्या सुरुवातीला घ्या.",
            "gujarati": "દિવસમાં બે વાર (દર 12 કલાકે) — પેટની તકલીફ ટાળવા ભોજનની શરૂઆતમાં લો.",
        },
        "instructions": {
            "english": "Must complete the full prescribed course without skipping. Swallow whole.",
            "hindi": "बिना नागा किए पूरा कोर्स अवश्य समाप्त करें। गोली पूरी निगलें।",
            "marathi": "कोणतीही गोळी न चुकवता संपूर्ण कोर्स पूर्ण करा. गोळी पूर्ण गिळा.",
            "gujarati": "એકપણ દિવસ ચૂક્યા વિના આખો કોર્સ પૂરો કરો. ગોળી આખી ગળી જવી.",
        },
        "precautions": "Probiotics or curd may help prevent mild antibiotic-associated looseness.",
    },
    "azithromycin": {
        "aliases": ["azithromycin", "azithral", "zithromax", "azee"],
        "generic": "Azithromycin",
        "default_dosage": "500 mg Tablet",
        "classes": "Antibiotic (Macrolide)",
        "purpose": {
            "english": "Fights respiratory and soft-tissue bacterial infections by stopping bacterial growth.",
            "hindi": "श्वसन तंत्र और फेफड़ों के जीवाणु संक्रमण को रोकता है और बैक्टीरिया के विकास को समाप्त करता है।",
            "marathi": "श्वसनमार्ग आणि छातीतील जिवाणू संसर्ग रोखून बॅक्टेरियाची वाढ थांबवतो.",
            "gujarati": "શ્વાસનળી અને ફેફસાંના બેક્ટેરિયલ ઇન્ફેક્શન સામે લડે છે અને બેક્ટેરિયાનો નાશ કરે છે.",
        },
        "when_to_take": {
            "english": "1 hour before or 2 hours after meals (Once daily)",
            "hindi": "भोजन से 1 घंटा पहले या भोजन के 2 घंटे बाद (दिन में एक बार)",
            "marathi": "जेवणाच्या १ तास आधी किंवा जेवणानंतर २ तासांनी (दिवसातून एकदा)",
            "gujarati": "જમવાના 1 કલાક પહેલાં અથવા જમ્યા પછી 2 કલાકે (દિવસમાં એક વાર)",
        },
        "schedule": {
            "english": "Once daily for 3 to 5 days — Take 1 hour before or 2 hours after meals with water.",
            "hindi": "दिन में एक बार (3 से 5 दिनों के लिए) — भोजन से 1 घंटा पहले या भोजन के 2 घंटे बाद लें।",
            "marathi": "दिवसातून एकदा (३ ते ५ दिवसांसाठी) — जेवणाच्या १ तास आधी किंवा जेवणानंतर २ तासांनी घ्या.",
            "gujarati": "દિવસમાં એક વાર (3 થી 5 દિવસ માટે) — જમવાના 1 કલાક પહેલાં અથવા જમ્યા પછી 2 કલાકે લો.",
        },
        "instructions": {
            "english": "Take at the exact same hour each day. Complete the full short course without missing any dose.",
            "hindi": "रोज ठीक उसी समय लें। कोई भी खुराक छोड़े बिना पूरा कोर्स समाप्त करें।",
            "marathi": "दररोज एकाच वेळी घ्या. कोणतीही गोळी न वगळता संपूर्ण कोर्स पूर्ण करा.",
            "gujarati": "રોજ બરાબર એ જ સમયે લો. એકપણ ડોઝ ચૂક્યા વિના સંપૂર્ણ કોર્સ પૂરો કરો.",
        },
        "precautions": "Do not take antacids containing aluminum or magnesium at the same time.",
    },
    "cefixime": {
        "aliases": ["cefixime", "taxim-o", "zifi", "mahacef"],
        "generic": "Cefixime Trihydrate",
        "default_dosage": "200 mg Tablet",
        "classes": "Cephalosporin Antibiotic (3rd Gen)",
        "purpose": {
            "english": "Treats typhoid, urinary tract, ear, and throat bacterial infections.",
            "hindi": "टाइफाइड, मूत्र मार्ग (यूटीआई), कान और गले के जीवाणु संक्रमण को ठीक करता है।",
            "marathi": "टायफॉइड, मूत्रमार्ग, कान आणि घशाच्या संसर्गावर प्रभावी उपाय.",
            "gujarati": "ટાઇફોઇડ, પેશાબના ઇન્ફેક્શન, કાન અને ગળાના બેક્ટેરિયલ ચેપની સારવાર કરે છે.",
        },
        "when_to_take": {
            "english": "Twice daily after meals (Every 12 hours)",
            "hindi": "भोजन के बाद दिन में दो बार (हर 12 घंटे में)",
            "marathi": "जेवणानंतर दिवसातून दोन वेळा (दर १२ तासांनी)",
            "gujarati": "જમ્યા પછી દિવસમાં બે વાર (દર 12 કલાકે)",
        },
        "schedule": {
            "english": "Twice daily — Taken with or after meals.",
            "hindi": "दिन में दो बार — भोजन के बाद लें।",
            "marathi": "दिवसातून दोन वेळा — जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં બે વાર — જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "Complete the full 7–14 days course as prescribed for typhoid or UTI.",
            "hindi": "डॉक्टर द्वारा निर्धारित 7 से 14 दिनों का पूरा कोर्स समाप्त करें।",
            "marathi": "डॉक्टरांनी सांगितलेला संपूर्ण ७ ते १४ दिवसांचा कोर्स पूर्ण करा.",
            "gujarati": "ડૉક્ટરે લખેલો 7 થી 14 દિવસનો પૂરો કોર્સ પૂર્ણ કરો.",
        },
        "precautions": "Take doses spaced equally 12 hours apart for optimal blood levels.",
    },

    # 6. Respiratory & Allergy
    "levocetirizine": {
        "aliases": ["levocetirizine", "levocet", "vozacet"],
        "generic": "Levocetirizine Dihydrochloride",
        "default_dosage": "5 mg Tablet",
        "classes": "Antihistamine (Anti-allergy)",
        "purpose": {
            "english": "Relieves allergic symptoms like runny nose, sneezing, itchy eyes, and skin hives.",
            "hindi": "एलर्जी के लक्षणों जैसे बहती नाक, छींकें, आंखों में खुजली और त्वचा पर चकत्तों से राहत दिलाता है।",
            "marathi": "वाहणारे नाक, शिंका, डोळ्यांची खाज आणि त्वचेवरील ॲलर्जी यांसारख्या लक्षणांवर आराम देतो.",
            "gujarati": "વહેતું નાક, છીંક, આંખોમાં ખંજવાળ અને ત્વચાની એલર્જીના લક્ષણોથી રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "At bedtime before sleeping (Night)",
            "hindi": "रात को सोने से पहले (रात)",
            "marathi": "रात्री झोपण्यापूर्वी (रात्री)",
            "gujarati": "રાત્રે સૂતા પહેલાં (સાંજ/રાત્રે)",
        },
        "schedule": {
            "english": "Once daily at Night (Bedtime) — With or without food.",
            "hindi": "दिन में एक बार रात को (सोते समय) — भोजन के साथ या बिना भोजन के लें।",
            "marathi": "दिवसातून एकदा रात्री (झोपण्यापूर्वी) — जेवणासोबत किंवा जेवणाशिवाय घ्या.",
            "gujarati": "દિવસમાં એક વાર રાત્રે (સૂતી વખતે) — જમ્યા સાથે અથવા જમ્યા વગર લો.",
        },
        "instructions": {
            "english": "May cause mild drowsiness. Best taken before sleeping. Avoid driving immediately after taking.",
            "hindi": "हल्की नींद आ सकती है, इसलिए सोने से पहले लेना बेहतर है। लेने के बाद वाहन न चलाएं।",
            "marathi": "हलकी गुंगी येऊ शकते, म्हणून झोपण्यापूर्वी घेणे योग्य. घेतल्यानंतर गाडी चालवणे टाळा.",
            "gujarati": "હળવી સુસ્તી આવી શકે છે, તેથી સૂતા પહેલાં લેવી શ્રેષ્ઠ છે. લીધા પછી ડ્રાઇવિંગ ન કરો.",
        },
        "precautions": "Avoid alcohol consumption while on antihistamine medication.",
    },
    "montelukast": {
        "aliases": ["montelukast", "montair", "telekast", "singulair"],
        "generic": "Montelukast Sodium (often + Levocetirizine)",
        "default_dosage": "10 mg Tablet",
        "classes": "Leukotriene Receptor Antagonist (Anti-asthma / Allergy)",
        "purpose": {
            "english": "Prevents asthma attacks, relieves allergic rhinitis, chest tightness, and chronic cough.",
            "hindi": "दमा (अस्थमा) के हमलों को रोकता है, सांस की नली की सूजन कम करता है और पुरानी खांसी में आराम देता है।",
            "marathi": "दम्याचा त्रास (अस्थमा) रोखते, श्वसननलिकेची सूज कमी करते आणि खोकल्यापासून आराम देते.",
            "gujarati": "દમ (અસ્થમા) ના હુમલા અટકાવે છે, શ્વાસનળીનો સોજો ઘટાડે છે અને ઉધરસમાં રાહત આપે છે.",
        },
        "when_to_take": {
            "english": "Once daily at night (Bedtime)",
            "hindi": "रात को सोते समय (दिन में एक बार)",
            "marathi": "रात्री झोपताना (दिवसातून एकदा)",
            "gujarati": "રાત્રે સૂતી વખતે (દિવસમાં એક વાર)",
        },
        "schedule": {
            "english": "Once daily at Night — With or without food.",
            "hindi": "दिन में एक बार रात को — भोजन के साथ या बिना भोजन के लें।",
            "marathi": "दिवसातून एकदा रात्री — जेवणासोबत किंवा जेवणाशिवाय घ्या.",
            "gujarati": "દિવસમાં એક વાર રાત્રે — જમ્યા સાથે અથવા જમ્યા વગર લો.",
        },
        "instructions": {
            "english": "Take regularly every evening even when you have no active asthma symptoms.",
            "hindi": "लक्षण न होने पर भी डॉक्टर द्वारा बताई गई अवधि तक नियमित लें।",
            "marathi": "लक्षणे नसली तरीही डॉक्टरांनी सांगितलेल्या कालावधीपर्यंत नियमित घ्या.",
            "gujarati": "લક્ષણો ન હોય તો પણ ડૉક્ટરની સલાહ મુજબ નિયમિત લો.",
        },
        "precautions": "This is a preventive medication and does not treat sudden acute breathlessness attacks.",
    },

    # 7. Thyroid
    "levothyroxine": {
        "aliases": ["levothyroxine", "thyronorm", "eltroxin", "synthroid"],
        "generic": "Levothyroxine Sodium",
        "default_dosage": "25 / 50 / 100 mcg Tablet",
        "classes": "Thyroid Hormone Replacement",
        "purpose": {
            "english": "Replaces insufficient thyroid hormone to regulate energy, weight, and metabolism (Hypothyroidism).",
            "hindi": "थायरॉयड ग्रंथि में हार्मोन की कमी को पूरा करता है ताकि ऊर्जा, वजन और चयापचय सामान्य रहे।",
            "marathi": "थायरॉईड संप्रेरकाची कमतरता भरून काढते जेणेकरून शरीराची ऊर्जा, वजन आणि चयापचय संतुलित राहील.",
            "gujarati": "થાઇરોઇડ હોર્મોનની ઉણપ પૂરી કરે છે જેથી વજન, એનર્જી અને પાચનક્રિયા નિયંત્રિત રહે.",
        },
        "when_to_take": {
            "english": "Early morning 30–60 minutes before tea/breakfast on empty stomach",
            "hindi": "सुबह जल्दी चाय/नाश्ते से 30-60 मिनट पहले खाली पेट",
            "marathi": "सकाळी लवकर चहा/नाश्त्याच्या ३०-६० मिनिटे आधी उपाशीपोटी",
            "gujarati": "સવારે વહેલા ચા/નાસ્તાના 30-60 મિનિટ પહેલાં ભૂખ્યા પેટે",
        },
        "schedule": {
            "english": "Once daily early Morning — 30 to 60 minutes BEFORE tea, coffee, or breakfast on an empty stomach.",
            "hindi": "रोज सुबह जल्दी खाली पेट — चाय, कॉफी या नाश्ते से 30 से 60 मिनट पहले सादे पानी के साथ लें।",
            "marathi": "दररोज सकाळी उपाशीपोटी — चहा, कॉफी किंवा नाश्त्याच्या ३० ते ६० मिनिटे आधी साध्या पाण्यासोबत घ्या.",
            "gujarati": "રોજ સવારે વહેલા ભૂખ્યા પેટે — ચા, કોફી કે નાસ્તાના 30 થી 60 મિનિટ પહેલાં સાદા પાણી સાથે લો.",
        },
        "instructions": {
            "english": "Take strictly with plain water only. Do not take with milk, tea, or calcium/iron tablets.",
            "hindi": "केवल सादे पानी के साथ लें। दूध, चाय, या कैल्शियम/आयरन की गोलियों के साथ न लें।",
            "marathi": "फक्त साध्या पाण्यासोबतच घ्या. दूध, चहा किंवा कॅल्शियम/आयर्नच्या गोळ्यांसोबत घेऊ नका.",
            "gujarati": "માત્ર સાદા પાણી સાથે લો. દૂધ, ચા અથવા કેલ્શિયમ/આયર્નની ગોળીઓ સાથે ન લો.",
        },
        "precautions": "Requires routine TSH blood tests every 3–6 months to calibrate the correct dose.",
    },

    # 8. Vitamins & Minerals
    "cholecalciferol": {
        "aliases": ["cholecalciferol", "vitamin d3", "calcirol", "d3 60k"],
        "generic": "Cholecalciferol (Vitamin D3)",
        "default_dosage": "60,000 IU Capsule / Sachet",
        "classes": "Vitamin Supplement (Bone & Immunity)",
        "purpose": {
            "english": "Boosts low Vitamin D levels, improves calcium absorption, and strengthens bones and immunity.",
            "hindi": "विटामिन डी की कमी पूरी करता है, हड्डियों को मजबूत बनाता है और रोग प्रतिरोधक क्षमता बढ़ाता है।",
            "marathi": "व्हिटॅमिन डी ची कमतरता भरून काढते, हाडे मजबूत करते आणि रोगप्रतिकारक शक्ती वाढवते.",
            "gujarati": "વિટામિન ડી3 ની ઉણપ પૂરી કરે છે, હાડકાં મજબૂત કરે છે અને રોગપ્રતિકારક શક્તિ વધારે છે.",
        },
        "when_to_take": {
            "english": "Once weekly with a glass of milk after a meal",
            "hindi": "सप्ताह में एक बार भोजन के बाद दूध के साथ",
            "marathi": "आठवड्यातून एकदा जेवणानंतर दुधासोबत",
            "gujarati": "અઠવાડિયામાં એક વાર જમ્યા પછી દૂધ સાથે",
        },
        "schedule": {
            "english": "Once weekly — Taken with milk or after a meal containing fat for best absorption.",
            "hindi": "सप्ताह में एक बार — अच्छे अवशोषण के लिए भोजन के बाद दूध के साथ लें।",
            "marathi": "आठवड्यातून एकदा — चांगल्या परिणामासाठी जेवणानंतर दुधासोबत घ्या.",
            "gujarati": "અઠવાડિયામાં એક વાર — વધુ સારી અસર માટે જમ્યા પછી દૂધ સાથે લો.",
        },
        "instructions": {
            "english": "Choose a fixed day of the week (e.g. Every Sunday) to ensure consistency.",
            "hindi": "सप्ताह का एक निश्चित दिन (जैसे हर रविवार) तय करें ताकि भूल न हो।",
            "marathi": "आठवड्यातील एक ठराविक दिवस (उदा. दर रविवारी) ठरवून नियमित घ्या.",
            "gujarati": "અઠવાડિયાનો એક નક્કી દિવસ (જેમ કે દર રવિવારે) રાખીને નિયમિત લો.",
        },
        "precautions": "Do not take daily unless specifically instructed by your physician.",
    },
    "shelcal": {
        "aliases": ["shelcal", "calcium", "cipcal"],
        "generic": "Calcium Carbonate + Vitamin D3",
        "default_dosage": "500 mg Tablet",
        "classes": "Mineral Supplement",
        "purpose": {
            "english": "Strengthens bones, teeth, and prevents osteopenia or osteoporosis.",
            "hindi": "हड्डियों और दांतों को मजबूत बनाता है तथा ऑस्टियोपोरोसिस से बचाता है।",
            "marathi": "हाडे आणि दात मजबूत करते तसेच हाडे ठिसूळ होण्यापासून रोखते.",
            "gujarati": "હાડકાં અને દાંત મજબૂત કરે છે અને ઓસ્ટિઓપોરોસિસથી બચાવે છે.",
        },
        "when_to_take": {
            "english": "Once daily after meals with water",
            "hindi": "दिन में एक बार भोजन के बाद पानी के साथ",
            "marathi": "दिवसातून एकदा जेवणानंतर पाण्यासोबत",
            "gujarati": "દિવસમાં એક વાર જમ્યા પછી પાણી સાથે",
        },
        "schedule": {
            "english": "Once daily — Taken after lunch or dinner.",
            "hindi": "दिन में एक बार — दोपहर या रात के भोजन के बाद लें।",
            "marathi": "दिवसातून एकदा — दुपारच्या किंवा रात्रीच्या जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં એક વાર — બપોરના અથવા રાત્રિના ભોજન પછી લો.",
        },
        "instructions": {
            "english": "Take at least 2 hours apart from thyroid medications or iron supplements.",
            "hindi": "थायरॉयड की दवा या आयरन की गोली से कम से कम 2 घंटे का अंतर रखें।",
            "marathi": "थायरॉईडचे औषध किंवा लोहाच्या (आयर्न) गोळ्यांपासून किमान २ तासांचे अंतर ठेवा.",
            "gujarati": "થાઇરોઇડની દવા કે આયર્નની ગોળીઓથી ઓછામાં ઓછું 2 કલાકનું અંતર રાખો.",
        },
        "precautions": "Drink adequate water to prevent kidney stone formation.",
    },
    "neurobion": {
        "aliases": ["neurobion", "becosules", "b-complex", "b complex", "cobalamin"],
        "generic": "Vitamin B-Complex (B1, B6, B12)",
        "default_dosage": "1 Tablet / Capsule daily",
        "classes": "Nutritional / Nerve Supplement",
        "purpose": {
            "english": "Nourishes nerve function, relieves burning sensation in hands/feet, and reduces mouth ulcers.",
            "hindi": "नसों के स्वास्थ्य में सुधार करता है, हाथ-पैरों की झनझनाहट कम करता है और मुंह के छालों में आराम देता है।",
            "marathi": "मज्जातंतूंच्या (नसांच्या) कार्याला चालना देते, हात-पायांची मुंग्या येणे कमी करते आणि तोंडातील अल्सर बरे करते.",
            "gujarati": "ચેતાતંત્રને સ્વસ્થ રાખે છે, હાથ-પગમાં ખાલી ચડવી ઓછી કરે છે અને મોંના ચાંદા મટાડે છે.",
        },
        "when_to_take": {
            "english": "Once daily after breakfast or lunch",
            "hindi": "दिन में एक बार नाश्ते या दोपहर के भोजन के बाद",
            "marathi": "दिवसातून एकदा नाश्त्यानंतर किंवा दुपारच्या जेवणानंतर",
            "gujarati": "દિવસમાં એક વાર નાસ્તા કે બપોરના ભોજન પછી",
        },
        "schedule": {
            "english": "Once daily — After meals.",
            "hindi": "दिन में एक बार — भोजन के बाद लें।",
            "marathi": "दिवसातून एकदा — जेवणानंतर घ्या.",
            "gujarati": "દિવસમાં એક વાર — જમ્યા પછી લો.",
        },
        "instructions": {
            "english": "May cause harmless bright yellow discoloration of urine.",
            "hindi": "पेशाब का रंग हल्का पीला हो सकता है जो पूरी तरह सामान्य और हानिरहित है।",
            "marathi": "लघवीचा रंग पिवळसर होऊ शकतो, हे सामान्य आणि निरुपद्रवी आहे.",
            "gujarati": "પેશાબનો રંગ પીળો થઈ શકે છે, જે સામાન્ય છે અને ચિંતા કરવાની જરૂર નથી.",
        },
        "precautions": "Take regularly with meals for optimum nutritional absorption.",
    },
}

# General guidance templates by language
GENERAL_GUIDANCE_TEMPLATES = {
    "english": (
        "Take all medications with a glass of plain water at consistent times daily. "
        "Do not stop or adjust prescribed dosages without consulting your doctor. "
        "Keep medicines stored in a cool, dry place away from direct sunlight."
    ),
    "hindi": (
        "सभी दवाएं रोजाना एक निश्चित समय पर एक गिलास सादे पानी के साथ लें। "
        "अपने डॉक्टर से सलाह किए बिना किसी भी दवा की खुराक बंद या कम-ज्यादा न करें। "
        "दवाओं को धूप और नमी से दूर ठंडी व सूखी जगह पर रखें।"
    ),
    "marathi": (
        "सर्व औषधे दररोज एका ठराविक वेळी एक ग्लास साध्या पाण्यासोबत घ्या. "
        "डॉक्टरांच्या सल्ल्याशिवाय कोणताही डोस बंद किंवा बदलू नका. "
        "औषधे सूर्यप्रकाश आणि दमटपणापासून दूर थंड व कोरड्या जागी ठेवा."
    ),
    "gujarati": (
        "બધી દવાઓ રોજ નિયત સમયે એક ગ્લાસ સાદા પાણી સાથે લો. "
        "ડૉક્ટરની સલાહ લીધા વિના ડોઝ બંધ કે ફેરફાર કરશો નહીં. "
        "દવાઓને સૂર્યપ્રકાશ અને ભેજથી દૂર ઠંડી અને સૂકી જગ્યાએ રાખો."
    ),
}

QUESTIONS_FOR_DOCTOR_TEMPLATES = {
    "english": [
        "How long should I continue taking these medicines?",
        "Are there any specific foods or drinks I need to avoid while on this medication?",
        "What should I do if I accidentally miss a dose?",
        "When should I schedule my next follow-up visit or test?",
    ],
    "hindi": [
        "मुझे यह दवाएं कितने दिनों या महीनों तक जारी रखनी हैं?",
        "क्या इन दवाओं के दौरान मुझे किसी विशेष खाद्य पदार्थ या पेय से परहेज करना है?",
        "अगर मैं कोई खुराक लेना भूल जाऊं तो मुझे क्या करना चाहिए?",
        "मुझे दोबारा डॉक्टर के पास जांच के लिए कब आना चाहिए?",
    ],
    "marathi": [
        "ही औषधे मला किती दिवस किंवा महिने चालू ठेवावी लागतील?",
        "या औषधांसोबत मला कोणत्या खाद्यपदार्थांचे पथ्य (परहेज) पाळावे लागेल?",
        "एखादा डोस घ्यायचा विसरल्यास मी काय करावे?",
        "पुढील तपासणीसाठी मला कधी यावे लागेल?",
    ],
    "gujarati": [
        "આ દવાઓ મારે કેટલા દિવસ કે મહિના સુધી ચાલુ રાખવાની છે?",
        "આ દવાઓ લેતી વખતે કયા ખોરાક કે પીણાંની પરેજી રાખવી જોઈએ?",
        "જો હું કોઈ ડોઝ લેવાનું ભૂલી જાઉં તો મારે શું કરવું?",
        "ડૉક્ટર પાસે ફરીથી ક્યારે ચેક-અપ માટે જવું?",
    ],
}


class PrescriptionService:
    """Service class for parsing prescriptions and generating structured medicine explanations."""

    DOSAGE_PATTERN = re.compile(
        r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g|gm|iu|units?)|(?:\d+)\s*(?:tablets?|tabs?|capsules?|caps?|drops?|puffs?|tsp|tbsp))\b",
        re.IGNORECASE,
    )

    SCHEDULE_PATTERN = re.compile(
        r"(\b[0-2]\s*-\s*[0-2]\s*-\s*[0-2]\b|"
        r"\b(?:once|twice|thrice|three times)\s+daily\b|"
        r"\b(?:before|after)\s+(?:meals?|food|breakfast|dinner|lunch)\b|"
        r"\b(?:empty stomach|at bedtime|at night|in morning|morning|evening|night|sos|od|bd|bid|tds|tid|qid|hs)\b)",
        re.IGNORECASE,
    )

    HEADER_PATTERN = re.compile(
        r"^(?:dr[\.\s]|doctor\b|patient\b|pt[\.\s]|name\s*:|age\s*:|gender\s*:|sex\s*:|date\s*:|reg(?:\s*no)?[\.\s:]|opd\b|ipd\b)|"
        r"\b(?:clinic|hospital|dispensary|nursing\s+home|healthcare|mbbs|bams|bhms)\b",
        re.IGNORECASE,
    )

    RX_HEADER_PATTERN = re.compile(r"^rx(?:\s*\(.*?\))?[:\s]*$", re.IGNORECASE)

    ADVICE_START_PATTERN = re.compile(
        r"^(?:advice|advise|adv|notes?|instructions?|follow[-\s]*up|review|diet|lifestyle|diagnosis|dx)\b[:\s]*(.*)",
        re.IGNORECASE,
    )

    @classmethod
    def _extract_prescription_content(cls, text: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Intelligently parse raw prescription or OCR text into candidate medicine rows
        and extracted clinical advice/notes, filtering clinic headers and metadata.
        """
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidate_items: List[Dict[str, Any]] = []
        advice_lines: List[str] = []
        in_advice_section = False

        for line in lines:
            # 1. Filter headers and metadata
            if cls.HEADER_PATTERN.search(line):
                continue
            if cls.RX_HEADER_PATTERN.match(line):
                continue

            # 2. Check for doctor advice section
            m_adv = cls.ADVICE_START_PATTERN.match(line)
            if m_adv:
                in_advice_section = True
                content = m_adv.group(1).strip()
                if content:
                    advice_lines.append(content)
                continue

            if in_advice_section:
                cleaned_adv = re.sub(r"^[•\-\*\d+\.\)]\s*", "", line).strip()
                if cleaned_adv:
                    advice_lines.append(cleaned_adv)
                continue

            # 3. Clean medication line
            cleaned = re.sub(r"^(?:\d+[\.\)\-:]\s*|[•\-\*]\s*)", "", line).strip()
            cleaned = re.sub(
                r"^(?:tab(?:let)?|cap(?:sule)?|syp(?:rup)?|inj(?:ection)?|ointment|drops|cream|gel|lotion|spray|inhaler)\.?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            ).strip()

            if not cleaned or len(cleaned) < 2:
                continue

            # Extract dosage hint if present in line
            dose_match = cls.DOSAGE_PATTERN.search(cleaned)
            extracted_dose = dose_match.group(1).strip() if dose_match else None

            # Extract timing hint if present in line
            timing_matches = cls.SCHEDULE_PATTERN.findall(cleaned)
            extracted_timing = " ".join(timing_matches).strip() if timing_matches else None

            # Check if line contains illegible / ambiguous markers
            is_ambiguous = bool(re.search(r"\?|unclear|illegible|dose unclear|unidentified", cleaned, re.IGNORECASE))

            candidate_items.append({
                "raw_line": line,
                "cleaned_name": cleaned,
                "extracted_dosage": extracted_dose,
                "extracted_timing": extracted_timing,
                "is_ambiguous": is_ambiguous,
            })

        return candidate_items, advice_lines

    @classmethod
    def _find_matching_drug(cls, query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find matching medication from the audited knowledge base using aliases."""
        q_lower = query.lower()
        for key, data in CLINICAL_DRUG_KNOWLEDGE_BASE.items():
            if key in q_lower:
                return key, data
            for alias in data.get("aliases", []):
                if re.search(rf"\b{re.escape(alias)}\b", q_lower):
                    return key, data
        return None

    @classmethod
    def _format_when_to_take(
        cls,
        extracted_timing: Optional[str],
        default_dict: Dict[str, str],
        lang: str,
    ) -> str:
        """Combine extracted prescription timing into patient-friendly plain language."""
        if not extracted_timing:
            return default_dict.get(lang, default_dict.get("english", ""))

        t_lower = extracted_timing.lower()

        # Localized frequency mapping
        freq_desc = None
        if re.search(r"\b1\s*-\s*0\s*-\s*1\b", t_lower):
            freq_desc = {
                "english": "Twice daily (1-0-1: Morning & Night)",
                "hindi": "दिन में दो बार (1-0-1: सुबह और रात)",
                "marathi": "दिवसातून दोन वेळा (1-0-1: सकाळी आणि रात्री)",
                "gujarati": "દિવસમાં બે વાર (1-0-1: સવાર અને સાંજ)",
            }.get(lang, "Twice daily (Morning & Night)")
        elif re.search(r"\b1\s*-\s*0\s*-\s*0\b", t_lower):
            freq_desc = {
                "english": "Once daily (1-0-0: Morning)",
                "hindi": "दिन में एक बार (1-0-0: सुबह)",
                "marathi": "दिवसातून एकदा (1-0-0: सकाळी)",
                "gujarati": "દિવસમાં એક વાર (1-0-0: સવારે)",
            }.get(lang, "Once daily (Morning)")
        elif re.search(r"\b0\s*-\s*0\s*-\s*1\b", t_lower):
            freq_desc = {
                "english": "Once daily at Bedtime (0-0-1: Night)",
                "hindi": "दिन में एक बार रात को (0-0-1: सोते समय)",
                "marathi": "दिवसातून एकदा रात्री (0-0-1: झोपताना)",
                "gujarati": "દિવસમાં એક વાર રાત્રે (0-0-1: સૂતી વખતે)",
            }.get(lang, "Once daily at Night")
        elif re.search(r"\b1\s*-\s*1\s*-\s*1\b", t_lower):
            freq_desc = {
                "english": "Three times daily (1-1-1: Morning, Noon & Night)",
                "hindi": "दिन में तीन बार (1-1-1: सुबह, दोपहर और रात)",
                "marathi": "दिवसातून तीन वेळा (1-1-1: सकाळी, दुपारी आणि रात्री)",
                "gujarati": "દિવસમાં ત્રણ વાર (1-1-1: સવાર, બપોર અને સાંજ)",
            }.get(lang, "Three times daily")
        elif re.search(r"\bsos\b", t_lower):
            freq_desc = {
                "english": "As needed (SOS) when symptoms occur",
                "hindi": "आवश्यकतानुसार (SOS) जब लक्षण महसूस हों",
                "marathi": "गरज असेल तेव्हा (SOS) लक्षणे जाणवल्यावर",
                "gujarati": "જરૂર પડે ત્યારે (SOS) લક્ષણો જણાય ત્યારે",
            }.get(lang, "As needed (SOS)")
        elif re.search(r"\b(?:once|1 time)\s+daily\b|\bod\b", t_lower):
            freq_desc = {
                "english": "Once daily",
                "hindi": "दिन में एक बार",
                "marathi": "दिवसातून एकदा",
                "gujarati": "દિવસમાં એક વાર",
            }.get(lang, "Once daily")
        elif re.search(r"\b(?:twice|2 times)\s+daily\b|\bbid\b|\bbd\b", t_lower):
            freq_desc = {
                "english": "Twice daily",
                "hindi": "दिन में दो बार",
                "marathi": "दिवसातून दोन वेळा",
                "gujarati": "દિવસમાં બે વાર",
            }.get(lang, "Twice daily")

        # Localized food relation mapping
        food_desc = None
        if re.search(r"\bafter\s+(?:meals?|food|breakfast|lunch|dinner)\b", t_lower):
            food_desc = {
                "english": "After meals",
                "hindi": "भोजन के बाद",
                "marathi": "जेवणानंतर",
                "gujarati": "જમ્યા પછી",
            }.get(lang, "After meals")
        elif re.search(r"\bbefore\s+(?:meals?|food|breakfast|lunch|dinner)\b|\bempty\s+stomach\b", t_lower):
            food_desc = {
                "english": "Before meals (on empty stomach)",
                "hindi": "भोजन से पहले (खाली पेट)",
                "marathi": "जेवणाआधी (उपाशीपोटी)",
                "gujarati": "જમ્યા પહેલાં (ભૂખ્યા પેટે)",
            }.get(lang, "Before meals")
        elif re.search(r"\bwith\s+(?:meals?|food)\b", t_lower):
            food_desc = {
                "english": "With meals",
                "hindi": "भोजन के साथ",
                "marathi": "जेवणासोबत",
                "gujarati": "જમવાની સાથે",
            }.get(lang, "With meals")

        if freq_desc and food_desc:
            return f"{freq_desc} - {food_desc}"
        if freq_desc:
            return freq_desc
        if food_desc:
            return food_desc

        return default_dict.get(lang, default_dict.get("english", extracted_timing))

    @classmethod
    def _explain_with_gemini(
        cls,
        request: PrescriptionExplainRequest,
        target_medicines: List[str],
        lang: str,
    ) -> Optional[PrescriptionExplainResponse]:
        """Optionally use Gemini API to retrieve plain-language details for each medicine."""
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        if not api_key or not str(api_key).strip():
            return None

        key_str = str(api_key).strip()
        # Google AI Studio Gemini API keys begin with 'AIzaSy'.
        # Skip live network call if key is synthetic placeholder or mock.
        if not key_str.startswith("AIzaSy"):
            return None

        try:
            import json
            from google import genai
            from google.genai import types

            http_opts = types.HttpOptions(
                timeout=5000,
                retry_options=types.HttpRetryOptions(attempts=1),
            )
            client = genai.Client(api_key=key_str, http_options=http_opts)

            system_instruction = (
                "You are MedIntel AI's Educational Prescription Explainer assistant. "
                "Your role is to help patients understand what the doctor has prescribed in a structured table. "
                "For each identified medicine, you MUST output:\n"
                "- Medicine Name: The identified medicine name\n"
                "- Purpose: A simple explanation of what the medicine is used for\n"
                "- Dosage: The prescribed dose, such as '2 ml', '1 tablet', or '500 mg'\n"
                "- When to Take: The prescribed timing, such as 'Before meals', 'After meals', or 'At bedtime'\n"
                "- needs_confirmation: Boolean. If handwriting or transcription cannot confidently identify the medicine or dose, set to true.\n"
                "- confidence_note: Guidance prompting confirmation by pharmacist or doctor if needs_confirmation is true.\n"
                "MANDATORY SAFETY BOUNDARIES:\n"
                "1. Gemini-generated information must NOT override the doctor's prescribed instructions.\n"
                "2. If handwriting is illegible or dosage is ambiguous, flag it for confirmation by a pharmacist or doctor rather than guessing.\n"
                f"3. Translate all explanations into the requested language: {lang} (English, Hindi, Marathi, Gujarati).\n"
                "4. Strictly return JSON matching the specified schema."
            )

            prompt = (
                f"Prescription Input Data:\n"
                f"Prescription raw text: {request.prescription_text or 'None'}\n"
                f"Identified medicine lines: {target_medicines}\n"
                f"Language: {lang}\n\n"
                "Provide the response strictly as a JSON object with this structure:\n"
                "{\n"
                '  "doctor_notes": "...",\n'
                '  "medicines": [\n'
                "    {\n"
                '      "name": "...",\n'
                '      "medicine_name": "...",\n'
                '      "generic_name": "...",\n'
                '      "dosage": "...",\n'
                '      "purpose": "...",\n'
                '      "when_to_take": "...",\n'
                '      "schedule": "...",\n'
                '      "instructions": "...",\n'
                '      "precautions": "...",\n'
                '      "needs_confirmation": false,\n'
                '      "confidence_note": null\n'
                "    }\n"
                "  ],\n"
                '  "general_guidance": "...",\n'
                '  "questions_for_doctor": ["..."]\n'
                "}"
            )

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=2048,
                response_mime_type="application/json",
            )

            response = client.models.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash"),
                contents=prompt,
                config=config,
            )

            if not response or not getattr(response, "text", None):
                return None

            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()

            parsed = json.loads(raw_text)
            med_items: List[PrescribedMedicineItem] = []
            for item in parsed.get("medicines", []):
                med_items.append(
                    PrescribedMedicineItem(
                        name=item.get("name") or item.get("medicine_name") or "Prescribed Drug",
                        medicine_name=item.get("medicine_name") or item.get("name"),
                        generic_name=item.get("generic_name"),
                        dosage=item.get("dosage", "As prescribed"),
                        purpose=item.get("purpose", ""),
                        when_to_take=item.get("when_to_take") or item.get("schedule", "As directed by physician"),
                        schedule=item.get("schedule") or item.get("when_to_take", ""),
                        instructions=item.get("instructions", "Take as advised by your physician."),
                        precautions=item.get("precautions"),
                        needs_confirmation=bool(item.get("needs_confirmation", False)),
                        confidence_note=item.get("confidence_note"),
                    )
                )

            return PrescriptionExplainResponse(
                doctor_notes=parsed.get("doctor_notes", "Prescription analyzed via Gemini AI integration."),
                medicines=med_items,
                general_guidance=parsed.get("general_guidance") or GENERAL_GUIDANCE_TEMPLATES.get(lang, GENERAL_GUIDANCE_TEMPLATES["english"]),
                questions_for_doctor=parsed.get("questions_for_doctor") or QUESTIONS_FOR_DOCTOR_TEMPLATES.get(lang, QUESTIONS_FOR_DOCTOR_TEMPLATES["english"]),
                language=lang,
                disclaimer=MANDATORY_PRESCRIPTION_DISCLAIMER,
            )
        except Exception as exc:
            logger.warning("Gemini prescription explanation fallback to clinical knowledge base: %s", exc)
            return None

    @classmethod
    def explain_prescription(cls, request: PrescriptionExplainRequest) -> PrescriptionExplainResponse:
        """Process prescription request and return clear structured medication instructions."""
        lang = (request.language or "english").strip().lower()
        if lang not in ["english", "hindi", "marathi", "gujarati"]:
            lang = "english"

        extracted_advice: List[str] = []
        candidate_items: List[Dict[str, Any]] = []

        if request.medicines:
            for m in request.medicines:
                if not m or not m.strip():
                    continue
                cleaned = m.strip()
                dose_match = cls.DOSAGE_PATTERN.search(cleaned)
                timing_matches = cls.SCHEDULE_PATTERN.findall(cleaned)
                candidate_items.append({
                    "raw_line": cleaned,
                    "cleaned_name": cleaned,
                    "extracted_dosage": dose_match.group(1).strip() if dose_match else None,
                    "extracted_timing": " ".join(timing_matches).strip() if timing_matches else None,
                    "is_ambiguous": bool(re.search(r"\?|unclear|illegible|dose unclear|unidentified", cleaned, re.IGNORECASE)),
                })
        elif request.prescription_text and request.prescription_text.strip():
            candidate_items, extracted_advice = cls._extract_prescription_content(request.prescription_text)

        if not candidate_items:
            candidate_items = [{
                "raw_line": "General Prescription",
                "cleaned_name": "General Prescription",
                "extracted_dosage": "As prescribed",
                "extracted_timing": None,
                "is_ambiguous": True,
            }]

        target_medicines = [item["cleaned_name"] for item in candidate_items]

        # 1. Attempt Gemini AI integration if configured
        gemini_result = cls._explain_with_gemini(request, target_medicines, lang)
        if gemini_result is not None:
            return gemini_result

        # 2. Audited clinical pharmaceutical knowledge base fallback
        explained_items: List[PrescribedMedicineItem] = []

        for item in candidate_items:
            cleaned_line = item["cleaned_name"]
            extracted_dose = item["extracted_dosage"]
            extracted_timing = item["extracted_timing"]
            is_ambiguous = item["is_ambiguous"]

            match_result = cls._find_matching_drug(cleaned_line)

            if match_result and not is_ambiguous:
                drug_key, info = match_result
                dosage_str = extracted_dose if extracted_dose else info["default_dosage"]
                when_to_take_str = cls._format_when_to_take(extracted_timing, info.get("when_to_take", {}), lang)
                schedule_str = info["schedule"].get(lang, info["schedule"]["english"])

                # Clean display medicine name
                display_name = cleaned_line.title()
                # If the line was very long due to instructions, trim to concise title
                if len(display_name.split()) > 3 and drug_key.title() in display_name:
                    display_name = drug_key.title()
                    if extracted_dose:
                        display_name = f"{display_name} {extracted_dose}"

                explained_items.append(
                    PrescribedMedicineItem(
                        name=display_name,
                        medicine_name=display_name,
                        generic_name=info["generic"],
                        dosage=dosage_str,
                        purpose=info["purpose"].get(lang, info["purpose"]["english"]),
                        when_to_take=when_to_take_str,
                        schedule=schedule_str,
                        instructions=info["instructions"].get(lang, info["instructions"]["english"]),
                        precautions=info.get("precautions"),
                        needs_confirmation=False,
                        confidence_note=None,
                    )
                )
            else:
                # Fallback for uncatalogued or ambiguous medications (flagged for safety)
                if lang == "hindi":
                    purpose = "चिकित्सक द्वारा आपकी स्थिति के उपचार हेतु निर्धारित विशेष औषधि।"
                    schedule = "दिन में 1 या 2 बार — डॉक्टर के निर्देशानुसार भोजन के बाद लें।"
                    instructions = "पानी के साथ पूरी गोली लें। डॉक्टर द्वारा निर्धारित पूरा कोर्स समाप्त करें।"
                    when_to_take_str = "डॉक्टर या फार्मासिस्ट के निर्देशानुसार"
                elif lang == "marathi":
                    purpose = "तुमच्या आरोग्याच्या स्थितीनुसार डॉक्टरांनी दिलेले योग्य औषध."
                    schedule = "दिवसातून १ किंवा २ वेळा — डॉक्टरांच्या सूचनेनुसार जेवणानंतर घ्या."
                    instructions = "पाण्यासोबत गोळी पूर्ण घ्या. डॉक्टरांनी सांगितलेला संपूर्ण कोर्स पूर्ण करा."
                    when_to_take_str = "डॉक्टर किंवा फार्मासिस्टच्या सल्ल्यानुसार"
                elif lang == "gujarati":
                    purpose = "તમારા સ્વાસ્થ્યની સ્થિતિ અનુસાર ડૉક્ટર દ્વારા સૂચવેલ યોગ્ય દવા."
                    schedule = "દિવસમાં 1 અથવા 2 વાર — ડૉક્ટરની સલાહ મુજબ જમ્યા પછી લો."
                    instructions = "પાણી સાથે આખી ગોળી લો. ડૉક્ટરે સૂચવેલ સંપૂર્ણ કોર્સ પૂરો કરો."
                    when_to_take_str = "ડૉક્ટર અથવા ફાર્માસિસ્ટની સલાહ મુજબ"
                else:
                    purpose = "Medication prescribed by your doctor to manage and treat your diagnosed symptoms."
                    schedule = "Take as prescribed by your physician (typically 1–2 times daily after food)."
                    instructions = "Swallow with plain water. Complete the entire duration prescribed by your doctor."
                    when_to_take_str = "As advised by doctor or pharmacist (confirm timing before taking)"

                if extracted_timing:
                    when_to_take_str = f"{extracted_timing} (confirm timing with pharmacist)"

                dosage_str = extracted_dose if extracted_dose else "As advised by doctor"

                explained_items.append(
                    PrescribedMedicineItem(
                        name=cleaned_line.title(),
                        medicine_name=cleaned_line.title(),
                        generic_name="Prescribed Medication",
                        dosage=dosage_str,
                        purpose=purpose,
                        when_to_take=when_to_take_str,
                        schedule=schedule,
                        instructions=instructions,
                        precautions="Always consult your pharmacist or doctor if you experience unusual side effects.",
                        needs_confirmation=True,
                        confidence_note=(
                            "Handwriting recognition or drug catalog could not verify this medication with high confidence. "
                            "Please confirm the exact medicine name and dosage with your pharmacist or doctor before taking."
                        ),
                    )
                )

        general_guidance = GENERAL_GUIDANCE_TEMPLATES.get(lang, GENERAL_GUIDANCE_TEMPLATES["english"])
        questions = QUESTIONS_FOR_DOCTOR_TEMPLATES.get(lang, QUESTIONS_FOR_DOCTOR_TEMPLATES["english"])

        if extracted_advice:
            doctor_notes_str = "Doctor Advice: " + "; ".join(extracted_advice)
        else:
            doctor_notes_str = "Prescription reviewed and structured for patient understanding."

        return PrescriptionExplainResponse(
            doctor_notes=doctor_notes_str,
            medicines=explained_items,
            general_guidance=general_guidance,
            questions_for_doctor=questions,
            language=lang,
            disclaimer=MANDATORY_PRESCRIPTION_DISCLAIMER,
        )
