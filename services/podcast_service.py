import re
import difflib
import logging
from core.config import settings
from fastapi import HTTPException,status
from services.tts_service import translate_text, text_to_speech
from services.preprocessing_service import preprocess_text, restore_placeholders
from services.ai_service import load_groq
from pydub import AudioSegment
from io import BytesIO
import json
import os
import uuid

logger = logging.getLogger(__name__)

MARKER_PREFIX = "LINEBREAKXXXX"
MARKER_TOKEN_PATTERN = re.compile(r'\b[A-Za-z]{6,20}\s*\d+')



def generate_script(text: str) -> list:
    """
    Generates a script from the given text using the Groq API.

    Args:
        text (str): The input text to generate a script from.

    Returns:
        list: A list of script segments.
    """
    client = load_groq()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": '''You are a podcast script writer. Convert the given text into a natural, 
engaging conversation between two hosts, Host A and Host B, discussing 
the key points of the material in an accessible, conversational way.

Rules:
- Alternate speakers naturally, as a real conversation would
- Keep each line concise — one idea per line, not long monologues
- Host A introduces topics and asks questions; Host B explains and elaborates, 
  but both should contribute naturally, not rigidly stick to one role
- Do not invent facts not present in the source text
- Respond with ONLY a valid JSON array, no other text before or after it
- Each item in the array must be an object with exactly two fields: 
  "host" (either "A" or "B") and "line" (the spoken dialogue text)

Example format:
[
  {"host": "A", "line": "Welcome back! Today we're diving into something fascinating."},
  {"host": "B", "line": "That's right — let's start with the basics."}
]'''
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.5,
    )
    if not response.choices or not response.choices[0].message:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to generate script")
    
    script = response.choices[0].message.content

    try:
        script_json = json.loads(script)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to parse script JSON")


    return script_json



def preprocess_and_join_lines(scripts: list) -> tuple:
    """
    Preprocesses each dialogue line independently, then joins the results
    with LINEBREAKXXXX<n> markers.

    Markers must be inserted AFTER preprocessing, not before: preprocess_text
    runs an NER/scientific-word pass meant to protect real technical terms,
    and it was misclassifying the raw LINEBREAKXXXX markers as protectable
    "terms" too, wrapping them in their own TERMZERO placeholder. That made
    a marker's survival depend on an extra, unnecessary placeholder
    round-trip through Khaya, on top of the marker's own corruption risk.
    Preprocessing lines before the markers exist removes that layer.

    Each line is preprocessed on its own so scientific words in different
    lines don't collide, but their local TERMZERO0.. keys (which restart at
    0 every call) are re-keyed into one globally unique placeholder_map
    before the lines are joined.

    Returns:
        tuple: (joined_text, combined_placeholder_map)
    """
    combined_placeholder_map = {}
    preprocessed_lines = []
    next_index = 0

    for segment in scripts:
        result = preprocess_text(segment['line'])
        line_text = result["preprocessed_text"]

        for local_key, original_word in result["placeholder_map"].items():
            global_key = f"TERMZERO{next_index}"
            line_text = re.sub(rf'\b{local_key}\b', global_key, line_text)
            combined_placeholder_map[global_key] = original_word
            next_index += 1

        preprocessed_lines.append(line_text)

    joined_text = ""
    for i, line_text in enumerate(preprocessed_lines):
        joined_text += line_text
        if i < len(preprocessed_lines) - 1:
            joined_text += " LINEBREAKXXXX" + str(i) + " "

    return joined_text, combined_placeholder_map


def split_tranlated_lines(translated_text: str , host_order: list) -> list:
    """
    Splits the translated text back into individual lines using the
    LINEBREAKXXXX<n> markers. A single exact regex split breaks the moment
    Khaya corrupts a marker (dropped/substituted/inserted character, or an
    inserted space) - the same corruption modes observed on TERMZERO
    placeholders in preprocessing_service.restore_placeholders. This applies
    the same fix: find marker-shaped tokens loosely, then resolve each one
    to the closest expected marker via difflib when it isn't an exact match.

    A marker that was dropped entirely (no repairable trace) can't be
    recovered this way - text on either side of it would end up merged
    into one line with no way to know where the host switch happened, so
    that case still raises the mismatch error.

    Args:
        translated_text (str): The translated text with markers.
        host_order (list): The expected host ("A"/"B") for each line.

    Returns:
        list: A list of {"host", "line"} dicts.
    """
    expected_marker_count = len(host_order) - 1

    if expected_marker_count <= 0:
        line = translated_text.strip()
        if not line:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Empty line found in translated text")
        return [{"host": host_order[0], "line": line}]

    expected_markers = [f"{MARKER_PREFIX}{i}" for i in range(expected_marker_count)]
    unresolved = set(expected_markers)
    boundaries = []

    for match in MARKER_TOKEN_PATTERN.finditer(translated_text):
        token = match.group()

        if token in expected_markers:
            marker = token
        else:
            candidates = difflib.get_close_matches(token, unresolved, n=1, cutoff=0.8)
            marker = candidates[0] if candidates else None

        if marker is None or marker not in unresolved:
            continue

        boundaries.append((match.start(), match.end()))
        unresolved.discard(marker)

    if unresolved:
        logger.warning(
            f"Podcast line markers {sorted(unresolved)} were not found in translated output — "
            f"likely dropped entirely by the translation API; can't safely split host lines"
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Mismatch between translated lines and host order")

    boundaries.sort(key=lambda b: b[0])
    lines = []
    cursor = 0
    for start, end in boundaries:
        lines.append(translated_text[cursor:start])
        cursor = end
    lines.append(translated_text[cursor:])

    if len(lines) != len(host_order):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Mismatch between translated lines and host order")

    segments = []
    for host, line in zip(host_order, lines):
        if not line.strip():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Empty line found in translated text")
        segments.append({"host": host, "line": line.strip()})
    return segments



def translate_lines_individually(scripts: list, language: str) -> list:
    """
    Fallback used when the single-call marker approach can't be trusted:
    translates each dialogue line in its own Khaya call, so there's no
    LINEBREAKXXXX marker to lose and host attribution never depends on
    reconstructing structure from the API's response. Costs one Khaya
    call per line - only used after the cheap single-call path has
    already failed for this request.
    """
    segments = []
    for segment in scripts:
        result = preprocess_text(segment['line'])
        translated = translate_text(result["preprocessed_text"], language)
        restored = restore_placeholders(translated, result["placeholder_map"])
        segments.append({"host": segment['host'], "line": restored.strip()})
    return segments


def process_podcast(text: str, language: str , host_a_voice: str, host_b_voice: str) -> tuple:
    """
    Processes the podcast script by generating a script, translating it, and converting it to speech.

    Args:
        text (str): The input text to generate a podcast script from.
        language (str): The target language for translation and TTS.

    Returns:
        list: A list of processed podcast segments with audio data.
    """
    script = generate_script(text)
    host_order = [segment['host'] for segment in script]
    joined_text, placeholder_map = preprocess_and_join_lines(script)

    translated_text = translate_text(joined_text, language)
    restored_text = restore_placeholders(translated_text, placeholder_map)

    try:
        segments = split_tranlated_lines(restored_text, host_order)
    except HTTPException:
        logger.warning(
            "Podcast marker mismatch on single-call translation; "
            "falling back to translating each line individually"
        )
        segments = translate_lines_individually(script, language)

    combined_audio = AudioSegment.empty()

    for segment in segments:
        voice = settings.DEFAULT_MALE_VOICE if segment['host'] == 'A' else settings.DEFAULT_FEMALE_VOICE
        audio_data = text_to_speech(segment['line'], language, voice)
        received_audio = AudioSegment.from_file(BytesIO(audio_data), format="wav")
        combined_audio += received_audio

    audio_dir = os.path.abspath(settings.AUDIO_STORAGE_PATH)
    os.makedirs(audio_dir, exist_ok=True)
    audio_file_path = os.path.join(audio_dir, f"{uuid.uuid4()}.wav")
    combined_audio.export(audio_file_path, format="wav")
    audio_url = f"/audio/{os.path.basename(audio_file_path)}"
    duration = combined_audio.duration_seconds

    return audio_url, duration, segments