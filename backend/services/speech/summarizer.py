import re
import logging
from typing import Optional

logger = logging.getLogger("doctor_translator.summarizer")

def generate_clinical_summary(transcription: str, translation: str, source_lang: str) -> str:
    """
    Generates an AI-assisted clinical summary highlighting symptoms, complaints, and patient notes.
    """
    text_to_analyze = translation.strip() if translation else transcription.strip()
    if not text_to_analyze:
        return "No clinical content available to summarize."
        
    sentences = [s.strip() for s in re.split(r'[.!?\n]+', text_to_analyze) if len(s.strip()) > 3]
    
    # Extract clinical keyword indicators
    symptoms = []
    lower_text = text_to_analyze.lower()
    
    symptom_keywords = {
        "fever": "Fever / Pyrexia",
        "bukhar": "Fever / Pyrexia",
        "حمى": "Fever / Pyrexia",
        "cough": "Cough / Respiratory irritation",
        "khansi": "Cough",
        "سعال": "Cough",
        "pain": "Localized Pain",
        "dard": "Pain / Discomfort",
        "ألم": "Pain",
        "headache": "Cephalea / Headache",
        "sar dard": "Headache",
        "صداع": "Headache",
        "stomach": "Abdominal / Gastrointestinal discomfort",
        "pait": "Abdominal pain",
        "معدة": "Gastric pain",
        "chest": "Thoracic / Chest sensation",
        "seena": "Chest discomfort",
        "صدر": "Chest discomfort",
        "breathing": "Dyspnea / Breathing difficulty",
        "saans": "Shortness of breath",
        "تنفس": "Dyspnea"
    }
    
    for kw, sym_name in symptom_keywords.items():
        if kw in lower_text:
            if sym_name not in symptoms:
                symptoms.append(sym_name)
                
    summary_parts = []
    
    # Main clinical synopsis
    if len(sentences) <= 2:
        main_summary = " ".join(sentences)
    else:
        main_summary = sentences[0] + ". " + sentences[1] + "."
        
    summary_parts.append(f"• Summary: {main_summary}")
    
    if symptoms:
        summary_parts.append(f"• Identified Symptoms: {', '.join(symptoms)}")
    else:
        summary_parts.append("• Category: General Doctor / Patient Consultation")
        
    return "\n".join(summary_parts)
