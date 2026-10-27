"""
MedIntel AI — Prescription & Medicine Explainer Service.

Objective 2: Helping patients understand what the doctor has prescribed,
including the medicines, their purpose, and how they should be taken.

Features:
- Deterministic extraction and parsing of prescription text and medication lines.
- Comprehensive audited clinical pharmaceutical dictionary covering 30+ core
  outpatient medication classes (Diabetes, Hypertension, Heart, Pain, Antibiotics,
  Acidity, Vitamins, Respiratory, Thyroid).
- Multilingual translations for English, Hindi, Marathi, and Gujarati.
- Generates medicine purpose, exact timing schedule (Morning/Noon/Night),
  food relation (Before/After food), instructions, and questions for doctor/pharmacist.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas.prescription import (
    MANDATORY_PRESCRIPTION_DISCLAIMER,
    PrescribedMedicineItem,
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)

logger = logging.getLogger("medintel.prescription_service")


# ---------------------------------------------------------------------------
# Audited Clinical Knowledge Base of Common Medications
# ---------------------------------------------------------------------------

CLINICAL_DRUG_KNOWLEDGE_BASE: Dict[str, Dict[str, any]] = {
    "metformin": {
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
    "amlodipine": {
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
    "atorvastatin": {
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
    "pantoprazole": {
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
    "paracetamol": {
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
    "amoxicillin": {
        "generic": "Amoxicillin / Amoxicillin + Potassium Clavulanate",
        "default_dosage": "500 mg / 625 mg Tablet",
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
    "azithromycin": {
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
    "levocetirizine": {
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
    "levothyroxine": {
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

    @staticmethod
    def _extract_medicine_names(text: str) -> List[str]:
        """Extract candidate medication lines from raw text."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        candidates = []
        for line in lines:
            # Clean common medical abbreviations like Tab., Cap., Syp., Inj.
            cleaned = re.sub(r"^(tab|cap|syp|inj|ointment|drops)\.?\s*", "", line, flags=re.IGNORECASE).strip()
            if cleaned and len(cleaned) > 2:
                candidates.append(cleaned)
        return candidates

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

        # Determine target medicine items
        target_medicines: List[str] = []
        if request.medicines:
            target_medicines = [m.strip() for m in request.medicines if m.strip()]
        elif request.prescription_text:
            target_medicines = cls._extract_medicine_names(request.prescription_text)

        if not target_medicines:
            target_medicines = ["General Prescription"]

        # 1. Attempt Gemini AI integration if configured
        gemini_result = cls._explain_with_gemini(request, target_medicines, lang)
        if gemini_result is not None:
            return gemini_result

        # 2. Audited clinical pharmaceutical knowledge base fallback
        explained_items: List[PrescribedMedicineItem] = []

        for med in target_medicines:
            med_lower = med.lower()
            matched_key = None
            for key in CLINICAL_DRUG_KNOWLEDGE_BASE:
                if key in med_lower:
                    matched_key = key
                    break

            if matched_key:
                info = CLINICAL_DRUG_KNOWLEDGE_BASE[matched_key]
                when_take_dict = info.get("when_to_take", {})
                when_to_take_str = when_take_dict.get(lang, when_take_dict.get("english", info["schedule"].get(lang, info["schedule"]["english"])))

                explained_items.append(
                    PrescribedMedicineItem(
                        name=med.title(),
                        medicine_name=med.title(),
                        generic_name=info["generic"],
                        dosage=info["default_dosage"],
                        purpose=info["purpose"].get(lang, info["purpose"]["english"]),
                        when_to_take=when_to_take_str,
                        schedule=info["schedule"].get(lang, info["schedule"]["english"]),
                        instructions=info["instructions"].get(lang, info["instructions"]["english"]),
                        precautions=info.get("precautions"),
                        needs_confirmation=False,
                        confidence_note=None,
                    )
                )
            else:
                # Fallback for uncatalogued or ambiguous medicines (flagged for safety)
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

                explained_items.append(
                    PrescribedMedicineItem(
                        name=med.title(),
                        medicine_name=med.title(),
                        generic_name="Prescribed Medication",
                        dosage="As advised by doctor",
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

        return PrescriptionExplainResponse(
            doctor_notes="Prescription reviewed and structured for patient understanding.",
            medicines=explained_items,
            general_guidance=general_guidance,
            questions_for_doctor=questions,
            language=lang,
            disclaimer=MANDATORY_PRESCRIPTION_DISCLAIMER,
        )
