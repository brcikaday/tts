from core.config import settings
from fastapi import HTTPException,status
from groq import Groq
from services.tts_service import translate_text, text_to_speech
from services.preprocessing_service import preprocess_text, restore_placeholders



def load_groq():
    """
    Initializes the Groq client with the API key from settings.
    """
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        return client
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not initialize Groq client")

    

def summarise_text(text: str, language: str) -> dict:

    client = load_groq()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant that summarizes text. Please provide a concise summary of the following text."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        temperature=0.5,
    )
    if  not response.choices or not response.choices[0].message:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to generate summary")
    summary = response.choices[0].message.content
    preprocessed_summary = preprocess_text(summary)
    processed_summary = preprocessed_summary["preprocessed_text"]
    placeholder_map = preprocessed_summary["placeholder_map"]

    translated_summary = translate_text(processed_summary, language)
    restored_summary = restore_placeholders(translated_summary, placeholder_map)

    return {
        "summary": restored_summary,
        "word_count": len(restored_summary.split()),
    }


def ask_question(text: str, question: str) -> dict:
    client = load_groq()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful assistant that answers questions. Please provide a concise answer to the following question."
            },
            {
                "role": "user",
                "content": f"{text}\n\nQuestion: {question}"
            }
        ],
        temperature=0.5,
    )

    if not response.choices or not response.choices[0].message:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to generate answer")

    answer = response.choices[0].message.content

    return {
        "answer": answer,
    }