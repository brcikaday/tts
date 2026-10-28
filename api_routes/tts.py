from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user
from schemas.tts import TTSRequest,TTSResponse
from services import tts_service
from sqlalchemy.orm import Session
from db.session import get_db
from services.document_service import get_document
from services.system_log_service import log_system_event


tts_router = APIRouter(prefix="/tts", tags=["tts"])

@tts_router.post("/",response_model=TTSResponse )
async def tts_translate(requests: TTSRequest , current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    
    if requests.document_id is not None:
        get_document(current_user.id, requests.document_id, db)
    text = requests.text
    language = requests.language
    voice = requests.voice

    
    audio_url,duration = tts_service.process_tts(text,language,voice)

    if not audio_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail= "Internal server error")
    
    response = TTSResponse(
        document_id=requests.document_id,
        audio_url=audio_url,
        duration_seconds=duration,
        language=language,
        voice=voice
    )
    log_system_event(db, current_user.id, "TTS_GENERATED", "Generated speech audio")
    return response

