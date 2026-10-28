from core.config import settings,VOICE_MAP
import requests
from fastapi import HTTPException,status
import re
from pydub import AudioSegment
from io import BytesIO
import os
import uuid
from services.preprocessing_service import preprocess_text, restore_placeholders



def translate_text(text: str, language: str) -> str:
    """
    Translates the given text to the specified target language using the Ghana NLP API.

    Args:
        text (str): The text to be translated.
        language (str): The language code to translate the text into.

    Returns:
        str: The translated text.
    """

    if language == "twi":
        accepted_language = "eng-twi"
    elif language == "ewe":
        accepted_language = "eng-ewe"
    elif language == "ga":
        accepted_language = "eng-gaa"
    elif language == "fante":
        accepted_language = "eng-fat"
    elif language == "dagaare":
        accepted_language = "eng-dag"
    elif language == "hausa":
        accepted_language = "eng-hau"
    elif language == "dagbani":
        accepted_language = "eng-dag"
    elif language == "nzema":
        accepted_language = "eng-nze"
    elif language == "kasem":
        accepted_language = "eng-xsm"
    elif language == "gonja":
        accepted_language = "eng-gjn"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language")

    api_key = settings.GHANA_NLP_API_KEY
    url = "https://translation-api.ghananlp.org/v2/translate"
    
    response = requests.post(url,
                              json={ "in": text,"lang": accepted_language},
                              headers={"Ocp-Apim-Subscription-Key": api_key})

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Translation service failed")



def text_to_speech(text: str, language: str, voice: str) -> bytes:
    """
    Converts the given text to speech using the Ghana NLP API.

    Args:
        text (str): The text to be converted to speech.
        language (str): The language code for the speech output.
        voice (str): The voice to be used for the speech output.

    Returns:
        bytes: The audio data in bytes format.
    """

    if language == "twi":
        accepted_language = "twi"
    elif language == "ewe":
        accepted_language = "ewe"
    elif language == "ga":
        accepted_language = "gaa"
    elif language == "fante":
        accepted_language = "fat"
    elif language == "dagaare":
        accepted_language = "dag"
    elif language == "hausa":
        accepted_language = "hau"
    elif language == "dagbani":
        accepted_language = "dag"
    elif language == "nzema":
        accepted_language = "nze"
    elif language == "kasem":
        accepted_language = "xsm"
    elif language == "gonja":
        accepted_language = "gjn"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language")

    api_key = settings.GHANA_NLP_API_KEY
    url = "https://translation-api.ghananlp.org/tts/v2/synthesize"
    
    response = requests.post(url,
                              json={"text": text, "language": accepted_language, 'speaker_id': voice},
                              headers={"Ocp-Apim-Subscription-Key": api_key})

    if response.status_code == 200:
        return response.content
    else:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Text-to-Speech service failed")
    


def chunk_text(text: str, chunk_size: int = 1000) -> list:

    sentences = re.split(r'(?<=[.!?]) +', text) 
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def process_tts(text: str, language: str, voice: str = "Kofi") -> tuple:
    speaker_id = VOICE_MAP.get(voice, "male_low")

    result = preprocess_text(text)
    preprocessed_result = result["preprocessed_text"]
    placeholder_map = result["placeholder_map"]
    chunks = chunk_text(preprocessed_result)
    combined_audio = AudioSegment.empty()

    for chunk in chunks:
        translated_text = translate_text(chunk, language)
        real_translated_text = restore_placeholders(translated_text, placeholder_map)
        audio_data = text_to_speech(real_translated_text, language, voice=speaker_id)
        received_audio = AudioSegment.from_file(BytesIO(audio_data), format="wav")
        combined_audio = combined_audio + received_audio

    audio_dir = os.path.abspath(settings.AUDIO_STORAGE_PATH)
    os.makedirs(audio_dir, exist_ok=True)
    audio_file_path = os.path.join(audio_dir, f"{uuid.uuid4()}.wav")
    combined_audio.export(audio_file_path, format="wav")
    audio_url = f"/audio/{os.path.basename(audio_file_path)}"
    duration = combined_audio.duration_seconds

    return audio_url, duration