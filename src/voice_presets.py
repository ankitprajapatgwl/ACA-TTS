"""
Voice preset system for ai4bharat/indic-parler-tts.

Design notes:
- Every speaker name below is copied verbatim from the official HF model
  card's speaker table (18 officially supported languages). No persona
  names are invented. Naming a real, official speaker is what gives the
  model consistent, repeatable voices per its own documentation.
- Each preset maps to a single, fixed `description` string. The same
  preset key always resolves to the exact same description text, which is
  the reproducibility guarantee required by the model card (randomizing
  wording per request would break voice consistency).
- Every description includes the literal phrase "very clear audio" per
  the model card's quality guidance.
"""

import logging

logger = logging.getLogger("voice_presets")

# ---------------------------------------------------------------------------
# Section 3 reference table: officially supported languages, their full
# speaker rosters, and the recommended (best-naturalness) speakers.
#
# Kashmiri is mentioned on the model card as "unofficially supported" but no
# named speakers are published for it, so no preset can be built for it here
# without inventing a name (explicitly disallowed) -- it is intentionally
# omitted. Chhattisgarhi and Punjabi ARE unofficially supported but DO have
# published speaker names, so presets are included for them.
# ---------------------------------------------------------------------------
LANGUAGES = {
    "assamese": {"speakers": ["Amit", "Sita", "Poonam", "Rakesh"], "recommended": ["Amit", "Sita"], "emotion_support": True, "official": True},
    "bengali": {"speakers": ["Arjun", "Aditi", "Tapan", "Rashmi", "Arnav", "Riya"], "recommended": ["Arjun", "Aditi"], "emotion_support": True, "official": True},
    "bodo": {"speakers": ["Bikram", "Maya", "Kalpana"], "recommended": ["Bikram", "Maya"], "emotion_support": True, "official": True},
    "chhattisgarhi": {"speakers": ["Bhanu", "Champa"], "recommended": ["Bhanu", "Champa"], "emotion_support": False, "official": False},
    "dogri": {"speakers": ["Karan"], "recommended": ["Karan"], "emotion_support": True, "official": True},
    "english": {
        "speakers": ["Thoma", "Mary", "Swapna", "Dinesh", "Meera", "Jatin", "Aakash", "Sneha", "Kabir", "Tisha",
                     "Chingkhei", "Thoiba", "Priya", "Tarun", "Gauri", "Nisha", "Raghav", "Kavya", "Ravi", "Vikas", "Riya"],
        "recommended": ["Thoma", "Mary"], "emotion_support": False, "official": True,
    },
    "gujarati": {"speakers": ["Yash", "Neha"], "recommended": ["Yash", "Neha"], "emotion_support": False, "official": True},
    "hindi": {"speakers": ["Rohit", "Divya", "Aman", "Rani"], "recommended": ["Rohit", "Divya"], "emotion_support": False, "official": True},
    "kannada": {"speakers": ["Suresh", "Anu", "Chetan", "Vidya"], "recommended": ["Suresh", "Anu"], "emotion_support": True, "official": True},
    "malayalam": {"speakers": ["Anjali", "Anju", "Harish"], "recommended": ["Anjali", "Harish"], "emotion_support": True, "official": True},
    "manipuri": {"speakers": ["Laishram", "Ranjit"], "recommended": ["Laishram", "Ranjit"], "emotion_support": False, "official": True},
    "marathi": {"speakers": ["Sanjay", "Sunita", "Nikhil", "Radha", "Varun", "Isha"], "recommended": ["Sanjay", "Sunita"], "emotion_support": True, "official": True},
    "nepali": {"speakers": ["Amrita"], "recommended": ["Amrita"], "emotion_support": True, "official": True},
    "odia": {"speakers": ["Manas", "Debjani"], "recommended": ["Manas", "Debjani"], "emotion_support": False, "official": True},
    "punjabi": {"speakers": ["Divjot", "Gurpreet"], "recommended": ["Divjot", "Gurpreet"], "emotion_support": False, "official": False},
    "sanskrit": {"speakers": ["Aryan"], "recommended": ["Aryan"], "emotion_support": True, "official": True},
    "tamil": {"speakers": ["Kavitha", "Jaya"], "recommended": ["Jaya"], "emotion_support": True, "official": True},
    "telugu": {"speakers": ["Prakash", "Lalitha", "Kiran"], "recommended": ["Prakash", "Lalitha"], "emotion_support": False, "official": True},
}

# Emotion tags officially supported for the 10 languages flagged above.
# Advanced/optional: append e.g. f"{description} speaking in a Happy tone."
# to a custom_description for one of these languages if desired.
EMOTION_TAGS = [
    "Command", "Anger", "Narration", "Conversation", "Disgust", "Fear",
    "Happy", "Neutral", "Proper Noun", "News", "Sad", "Surprise",
]

# ---------------------------------------------------------------------------
# Preset table: preset_key -> {language, speaker, description}
#
# At least one preset per officially-supported-with-known-speakers language,
# plus 2-3 extra pace/tone variants for the most commonly used languages
# (Hindi, English, Bengali, Tamil, Telugu, Marathi), each using a different
# real speaker name from that language's roster.
# ---------------------------------------------------------------------------
PRESETS = {
    # Assamese
    "assamese_male_narrator": {
        "language": "assamese", "speaker": "Amit",
        "description": "Amit's voice is calm and measured, speaking at a normal pace with a moderate pitch. The recording is very clear audio with almost no background noise.",
    },
    # Bengali
    "bengali_male_narrator": {
        "language": "bengali", "speaker": "Arjun",
        "description": "Arjun's voice is steady and clear, delivered at a normal pace with a moderate pitch, captured in very clear audio with minimal background noise.",
    },
    "bengali_female_narrator": {
        "language": "bengali", "speaker": "Aditi",
        "description": "Aditi speaks with a slightly higher pitch in a close-sounding environment. Her voice is clear, with subtle emotional depth and a normal pace, all captured in very clear audio.",
    },
    "bengali_male_casual": {
        "language": "bengali", "speaker": "Tapan",
        "description": "Tapan's voice is relaxed and conversational, speaking at a slightly faster pace with a moderate pitch, in a close recording that is very clear audio with almost no background noise.",
    },
    "bengali_female_formal": {
        "language": "bengali", "speaker": "Rashmi",
        "description": "Rashmi's voice is formal and articulate, speaking at a normal, measured pace with a slightly higher pitch, captured in very clear audio with a close, distant-free recording.",
    },
    # Bodo
    "bodo_male_narrator": {
        "language": "bodo", "speaker": "Bikram",
        "description": "Bikram's voice is warm and steady, speaking at a normal pace with a moderate pitch, recorded in very clear audio with almost no background noise.",
    },
    # Chhattisgarhi
    "chhattisgarhi_male_narrator": {
        "language": "chhattisgarhi", "speaker": "Bhanu",
        "description": "Bhanu's voice is friendly and even, speaking at a normal pace with a moderate pitch, captured in very clear audio with a close recording and minimal background noise.",
    },
    # Dogri
    "dogri_male_narrator": {
        "language": "dogri", "speaker": "Karan",
        "description": "Karan's voice is confident and clear, speaking at a normal pace with a moderate pitch, in a close recording that is very clear audio with almost no background noise.",
    },
    # English
    "english_male_narrator": {
        "language": "english", "speaker": "Thoma",
        "description": "Thoma's voice is deep and resonant, speaking at a normal, measured pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    "english_female_narrator": {
        "language": "english", "speaker": "Mary",
        "description": "Mary's voice is bright and articulate, speaking at a normal pace with a slightly higher pitch, in a close recording that is very clear audio with minimal background noise.",
    },
    "english_male_casual": {
        "language": "english", "speaker": "Dinesh",
        "description": "Dinesh's voice is casual and relaxed, speaking at a slightly faster pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    "english_female_calm": {
        "language": "english", "speaker": "Meera",
        "description": "Meera's voice is calm and soothing, speaking at a slightly slower pace with a low pitch, recorded in very clear audio with almost no background noise.",
    },
    # Gujarati
    "gujarati_male_narrator": {
        "language": "gujarati", "speaker": "Yash",
        "description": "Yash's voice is steady and clear, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    # Hindi
    "hindi_male_narrator": {
        "language": "hindi", "speaker": "Rohit",
        "description": "Rohit's voice is confident and clear, speaking at a normal pace with a moderate pitch, in a close recording that is very clear audio with almost no background noise.",
    },
    "hindi_female_teacher": {
        "language": "hindi", "speaker": "Divya",
        "description": "Divya's voice is monotone yet slightly fast in delivery, with a very close recording that is very clear audio and almost has no background noise.",
    },
    "hindi_male_casual": {
        "language": "hindi", "speaker": "Aman",
        "description": "Aman's voice is casual and warm, speaking at a slightly faster pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    "hindi_female_formal": {
        "language": "hindi", "speaker": "Rani",
        "description": "Rani's voice is formal and articulate, speaking at a normal, deliberate pace with a slightly higher pitch, in a very clear audio recording with minimal background noise.",
    },
    # Kannada
    "kannada_male_narrator": {
        "language": "kannada", "speaker": "Suresh",
        "description": "Suresh's voice is steady and grounded, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    # Malayalam
    "malayalam_female_narrator": {
        "language": "malayalam", "speaker": "Anjali",
        "description": "Anjali's voice is expressive and warm, speaking at a normal pace with a moderate pitch, in a close recording that is very clear audio with minimal background noise.",
    },
    # Manipuri
    "manipuri_male_narrator": {
        "language": "manipuri", "speaker": "Laishram",
        "description": "Laishram's voice is calm and clear, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    # Marathi
    "marathi_male_narrator": {
        "language": "marathi", "speaker": "Sanjay",
        "description": "Sanjay's voice is deep and confident, speaking at a normal pace with a moderate pitch, in a close recording that is very clear audio with almost no background noise.",
    },
    "marathi_female_narrator": {
        "language": "marathi", "speaker": "Sunita",
        "description": "Sunita's voice is warm and articulate, speaking at a normal pace with a slightly higher pitch, captured in very clear audio with minimal background noise.",
    },
    "marathi_male_casual": {
        "language": "marathi", "speaker": "Nikhil",
        "description": "Nikhil's voice is relaxed and conversational, speaking at a slightly faster pace with a moderate pitch, in very clear audio with almost no background noise.",
    },
    "marathi_female_calm": {
        "language": "marathi", "speaker": "Radha",
        "description": "Radha's voice is gentle and soothing, speaking at a slightly slower pace with a low pitch, recorded in very clear audio with minimal background noise.",
    },
    # Nepali
    "nepali_female_narrator": {
        "language": "nepali", "speaker": "Amrita",
        "description": "Amrita's voice is clear and steady, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    # Odia
    "odia_male_narrator": {
        "language": "odia", "speaker": "Manas",
        "description": "Manas's voice is calm and even, speaking at a normal pace with a moderate pitch, in a close recording that is very clear audio with almost no background noise.",
    },
    # Punjabi
    "punjabi_male_narrator": {
        "language": "punjabi", "speaker": "Divjot",
        "description": "Divjot's voice is energetic and clear, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    # Sanskrit
    "sanskrit_male_narrator": {
        "language": "sanskrit", "speaker": "Aryan",
        "description": "Aryan's voice is measured and resonant, speaking at a normal, deliberate pace with a moderate pitch, in a close recording that is very clear audio with almost no background noise.",
    },
    # Tamil
    "tamil_female_narrator": {
        "language": "tamil", "speaker": "Jaya",
        "description": "Jaya's voice is clear and expressive, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    "tamil_female_casual": {
        "language": "tamil", "speaker": "Kavitha",
        "description": "Kavitha's voice is warm and conversational, speaking at a slightly faster pace with a moderate pitch, in very clear audio with minimal background noise.",
    },
    # Telugu
    "telugu_male_narrator": {
        "language": "telugu", "speaker": "Prakash",
        "description": "Prakash's voice is steady and confident, speaking at a normal pace with a moderate pitch, captured in very clear audio with almost no background noise.",
    },
    "telugu_female_narrator": {
        "language": "telugu", "speaker": "Lalitha",
        "description": "Lalitha's voice is warm and articulate, speaking at a normal pace with a slightly higher pitch, in a close recording that is very clear audio with minimal background noise.",
    },
    "telugu_male_casual": {
        "language": "telugu", "speaker": "Kiran",
        "description": "Kiran's voice is relaxed and even, speaking at a slightly faster pace with a moderate pitch, recorded in very clear audio with almost no background noise.",
    },
}

# Safe fallback preset used whenever an unknown/missing preset_key is given.
# A Hindi recommended speaker, as suggested by the spec.
DEFAULT_PRESET_KEY = "hindi_male_narrator"

# Relative speed clauses -- phrased relative to "usual" so they never
# contradict whatever absolute pace wording already exists in a preset's
# base description.
_SPEED_HINTS = {
    "slow": "The delivery is noticeably slower and more deliberate than usual.",
    "normal": "",
    "fast": "The delivery is slightly faster-paced than usual.",
}


def list_presets() -> dict:
    """Return {preset_key: {language, speaker, description}} for all presets."""
    return {
        key: {"language": p["language"], "speaker": p["speaker"], "description": p["description"]}
        for key, p in PRESETS.items()
    }


def get_preset_info(preset_key: str = None) -> dict:
    """
    Return the full preset dict ({language, speaker, description}) for a
    known preset_key. Falls back to DEFAULT_PRESET_KEY (with a logged
    warning) for an unknown or missing key -- never raises.
    """
    if preset_key and preset_key in PRESETS:
        return PRESETS[preset_key]
    if preset_key:
        logger.warning(
            "Unknown preset_key '%s'. Falling back to default preset '%s'. Valid keys: %s",
            preset_key, DEFAULT_PRESET_KEY, ", ".join(sorted(PRESETS.keys())),
        )
    return PRESETS[DEFAULT_PRESET_KEY]


def get_description(preset_key: str = None, custom_description: str = None) -> str:
    """
    Resolve the description string to send to the model.

    Resolution order:
    1. custom_description, if provided, is used as-is (full override).
    2. Else preset_key, if it matches a known preset, returns that
       preset's fixed description_template.
    3. Else falls back to DEFAULT_PRESET_KEY, logging a warning rather
       than raising -- an unknown preset_key never breaks the request.
    """
    if custom_description:
        return custom_description
    return get_preset_info(preset_key)["description"]


def apply_speed_hint(description: str, speed: str = "normal") -> str:
    """
    Append a natural-language pace clause to `description`, phrased
    relatively ("...than usual") so it never contradicts the base
    description's existing pace wording. speed in {"slow", "normal", "fast"};
    any other value is treated as "normal" (no-op) rather than raising.
    """
    hint = _SPEED_HINTS.get(speed, "")
    if not hint:
        return description
    return f"{description} {hint}"


def validate_input(job_input: dict) -> str:
    """
    Validate an incoming job['input'] payload.

    Returns None if valid, otherwise a human-readable error message that
    lists valid preset keys / speed values so the caller can fail loudly
    and helpfully instead of silently.
    """
    if not job_input or not job_input.get("text"):
        return "Missing required field 'text'."

    preset_key = job_input.get("preset_key")
    if preset_key and preset_key not in PRESETS and not job_input.get("custom_description"):
        return (
            f"Unknown preset_key '{preset_key}'. Valid preset keys: "
            f"{', '.join(sorted(PRESETS.keys()))}"
        )

    speed = job_input.get("speed", "normal")
    if speed not in _SPEED_HINTS:
        return f"Invalid speed '{speed}'. Must be one of: {', '.join(_SPEED_HINTS.keys())}"

    return None
