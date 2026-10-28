from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from schemas.ai import SummarizeRequest, SummarizeResponse, AskRequest, AskResponse , PodcastRequest, PodcastResponse, ScriptLine
from services import ai_service,podcast_service
from sqlalchemy.orm import Session
from db.session import get_db
from services.system_log_service import log_system_event


ai_router = APIRouter( tags=["ai"])

@ai_router.post("/summarise", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    summary_data = ai_service.summarise_text(request.text, request.language)
    
    response = SummarizeResponse(**summary_data)
    log_system_event(db, current_user.id, "SUMMARY_GENERATED", "Generated document summary")
    return response

@ai_router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    answer_data = ai_service.ask_question(request.text, request.question)  # Assuming the answer is in English
    
    response = AskResponse(**answer_data)
    log_system_event(db, current_user.id, "QUESTION_ANSWERED", "Answered document question")
    return response

@ai_router.post("/podcast", response_model=PodcastResponse)
async def create_podcast(request: PodcastRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    audio_url, duration, script = podcast_service.process_podcast(request.text, request.language, request.host_a_voice, request.host_b_voice)
    
    response = PodcastResponse(script=script, audio_url=audio_url, duration_seconds=duration)
    log_system_event(db, current_user.id, "PODCAST_GENERATED", "Generated podcast audio")
    return response
