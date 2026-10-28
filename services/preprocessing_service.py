from core.config import settings
from fastapi import HTTPException,status
import re
import json
import difflib
import logging
from services.detection_service import detect_risky_words

logger = logging.getLogger(__name__)

PLACEHOLDER_TOKEN_PATTERN = re.compile(r'\b[A-Za-z]{4,14}\s*\d+\b')

def load_scientific_words():
    """
    Loads the scientific words from the JSON file.
    """
    try:
        with open(settings.SCIENTIFIC_WORDS_FILE, 'r') as f:
             protection_data = json.load(f)
             wordlist = protection_data['words']

        return set(wordlist.keys())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not load scientific words")    
    

def preprocess_text(text: str , scientific_words: list = None) -> dict:

    if scientific_words is None:
        scientific_words = load_scientific_words()



    # Remove special characters and extra spaces
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,!?\'-]', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    model_flagged_words = detect_risky_words(text)
    # Remove scientific words
    replaced_words = {}
    counter = 0
    placeholder_term = "TERMZERO"

    combined_words = set(scientific_words).union(set(model_flagged_words))

    def replacer(match):
        nonlocal counter
        original_text = match.group()
        placeholder = placeholder_term + str(counter)
        counter += 1
        replaced_words[placeholder] = original_text
        return placeholder

    for word in combined_words:    
        pattern = rf'\b{word}\b'        
        cleaned_text = re.sub(pattern, replacer, cleaned_text, flags=re.IGNORECASE)

    return {
        "preprocessed_text": cleaned_text,
        "placeholder_map": replaced_words
    }



def restore_placeholders(text: str, placeholder_map: dict) -> str:
    
    if not placeholder_map:
        return text

    unresolved_keys = set(placeholder_map.keys())
    result_parts = []
    last_end = 0

    for match in PLACEHOLDER_TOKEN_PATTERN.finditer(text):
        token = match.group()

        if token in placeholder_map and token in unresolved_keys:
            key = token
        else:
            candidates = difflib.get_close_matches(token, unresolved_keys, n=1, cutoff=0.55)
            key = candidates[0] if candidates else None

        result_parts.append(text[last_end:match.start()])
        last_end = match.end()

        if key is None:
            logger.warning(
                f"Found placeholder-shaped token '{token}' in translated output that doesn't confidently "
                f"match any remaining placeholder — too corrupted to repair; removed from output"
            )
            continue

        result_parts.append(placeholder_map[key])
        unresolved_keys.discard(key)

    result_parts.append(text[last_end:])
    restored_text = "".join(result_parts)

    for key in unresolved_keys:
        logger.warning(
            f"Placeholder for '{placeholder_map[key]}' (key: {key}) never appeared in translated output — "
            f"likely dropped entirely by the translation API"
        )

    return restored_text