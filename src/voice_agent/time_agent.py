"""Supervisor Conversational & Multilingual Voice Time Agent.
Provides low-friction voice note and conversational logging for site supervisors across disciplines,
supporting English, Hindi, and Hinglish vernacular, extracting structured micro-events, quantities,
and impediments.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from src.extraction.extractor_interface import ExtractedEvent

# Vernacular domain keyword mappings
HINGLISH_KEYWORDS = {
    "action": {
        "completed": ["khatam", "ho gaya", "complete", "done", "pura ho gaya", "finished", "cleared", "ho chuka"],
        "started": ["shuru kiya", "start", "chalu kiya", "lagaya", "commenced", "shuru hua"],
        "blocked": ["ruk gaya", "band hai", "blocked", "nahi hua", "paani bhar gaya", "atak gaya", "problem hai", "delay", "hold"],
        "progress": ["chal raha hai", "in progress", "ongoing", "kar rahe hai", "work in progress"]
    },
    "discipline": {
        "Civil": ["concrete", "excavation", "khudai", "pedestal", "foundation", "rcc", "casting", "curing", "trench", "grouting", "anchor bolt"],
        "Piping": ["spool", "line", "welding", "weld", "pipe", "fit-up", "fitup", "butt weld", "hydrotest", "flange", "erect"],
        "Electrical": ["cable", "pulling", "substation", "mcc", "transformer", "termination", "tray", "switchgear", "earthing"],
        "Instrumentation": ["loop", "calibration", "transmitter", "dcs", "plc", "sensor", "scada", "marshaling", "impulse tube"],
        "Mechanical": ["pump", "compressor", "alignment", "motor", "skid", "laser alignment", "bearing", "coupling"],
        "HSE": ["safety", "walkdown", "gas test", "ptw", "permit", "toolbox", "fire water", "hazard", "ppe"]
    }
}


class VoiceTimeAgent:
    def __init__(self):
        pass

    def detect_language(self, text: str) -> str:
        lower = text.lower()
        hinglish_markers = ["aaj", "ho gaya", "shuru", "hai", "paani", "ka", "ki", "tha", "rahe", "gaya"]
        if any(w in lower.split() for w in hinglish_markers):
            return "hinglish"
        return "en"

    def parse_voice_log(self, voice_transcript: str, supervisor_name: str = "Field Supervisor", site_location: Optional[str] = None) -> Dict[str, Any]:
        """Parses speech-to-text transcript or supervisor chat into a structured ExtractedEvent."""
        text = voice_transcript.strip()
        lang = self.detect_language(text)
        lower = text.lower()

        # 1. Action Type Detection
        action_type = "in-progress"
        for act, keywords in HINGLISH_KEYWORDS["action"].items():
            if any(k in lower for k in keywords):
                action_type = act
                break

        # 2. Discipline Detection
        detected_discipline = "General"
        max_discipline_hits = 0
        for disc, terms in HINGLISH_KEYWORDS["discipline"].items():
            hits = sum(1 for t in terms if t in lower)
            if hits > max_discipline_hits:
                max_discipline_hits = hits
                detected_discipline = disc

        # 3. Location Extraction
        loc = site_location or "Field Site"
        loc_patterns = [
            r"(unit\s*\d+[\w\s]*?(?:pump house|manifold|battery limit|pipe rack|substation)?)",
            r"(at\s+[A-Za-z0-9\s\-]+(?:area|station|manifold|skid|trench))",
            r"(bay\s*\d+[\-\d]*)",
        ]
        for pat in loc_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                loc = m.group(1).strip()
                break

        # 4. Quantity Extraction (e.g. 45 m3, 2 joints, 120 meters)
        qty = 0.0
        qty_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m3|cubic meter|meter|meters|joints|spools|welds|inch-dia)", lower)
        if qty_match:
            try:
                qty = float(qty_match.group(1))
            except Exception:
                qty = 0.0

        # 5. Crew Size Extraction (e.g. 12 workers, 4 welders)
        crew = 0
        crew_match = re.search(r"(\d+)\s*(?:workers|welders|men|people|fitters|laborers|technicians|gang)", lower)
        if crew_match:
            try:
                crew = int(crew_match.group(1))
            except Exception:
                crew = 0

        # 6. Delay / Bottleneck Extraction
        delay = None
        delay_patterns = [
            r"((?:crane\s+(?:got\s+)?delayed|rain|waterlogging|not backfilled|unready|leakage|material shortage)[^\.]*)",
            r"((?:blocked due to|stopped because|atak gaya|paani bhar gaya|problem hai|delay hai)[^\.]+)",
            r"(?:delayed by\s+[^\.]+)",
        ]
        for pat in delay_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                delay = m.group(1).strip(". ") if m.groups() and m.group(1) else m.group(0).strip(". ")
                break

        # 7. Generate clean activity description
        activity_desc = text
        if len(activity_desc) > 120:
            sentences = text.split(".")
            activity_desc = sentences[0].strip()

        event = ExtractedEvent(
            event_id=f"EVT-VOICE-{uuid.uuid4().hex[:6]}",
            activity_description=activity_desc,
            discipline=detected_discipline,
            event_date=datetime.now().strftime("%Y-%m-%d"),
            action_type=action_type,
            location=loc,
            quantity_done=qty,
            crew_size=crew,
            delay_reason=delay,
            raw_snippet=text,
            source_language=lang
        )

        # Natural Conversational Confirmation Message
        confirmation_msg = self._generate_confirmation(event, supervisor_name)

        return {
            "event": event,
            "confirmation_message": confirmation_msg,
            "detected_language": lang,
            "raw_transcript": text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def transcribe_audio_bytes(self, audio_bytes: bytes, language: str = "hi-IN") -> str:
        """Transcribes raw audio bytes (wav) to text using speech_recognition.
        Supports Hindi ('hi-IN') and English ('en-IN', 'en-US').
        """
        import io
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        try:
            with io.BytesIO(audio_bytes) as audio_file:
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)
                    try:
                        return recognizer.recognize_google(audio_data, language=language)
                    except sr.UnknownValueError:
                        # Try alternate language
                        alt_lang = "en-IN" if language == "hi-IN" else "hi-IN"
                        try:
                            return recognizer.recognize_google(audio_data, language=alt_lang)
                        except Exception:
                            return "[Speech was not recognized clearly. Please speak into the mic again or use text input.]"
                    except Exception as e:
                        return f"[Transcription network notice: {str(e)}. Please type or verify mic input.]"
        except Exception as e:
            return f"[Audio processing error: {str(e)}]"

    def _generate_confirmation(self, event: ExtractedEvent, supervisor_name: str) -> str:
        qty_str = f" Quantity logged: {event.quantity_done}." if event.quantity_done > 0 else ""
        delay_str = f" ⚠️ Impediment flagged: '{event.delay_reason}'." if event.delay_reason else ""
        status_emoji = {"started": "🚀", "completed": "✅", "in-progress": "⚡", "blocked": "🛑"}.get(event.action_type, "📋")
        
        return (
            f"{status_emoji} Received, Supervisor {supervisor_name}! Logged for **{event.discipline}**: "
            f"*{event.activity_description}* [{event.action_type.upper()} at {event.location}]."
            f"{qty_str}{delay_str} Ready for real-time schedule linking."
        )

